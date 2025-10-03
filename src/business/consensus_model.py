"""Consensus model construction utilities for SwissModel outputs."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple
from Bio.SeqUtils import seq1

import numpy as np
from Bio.PDB import PDBIO, PDBParser, ShrakeRupley, Superimposer
from Bio.PDB.Polypeptide import is_aa


@dataclass
class ConsensusResult:
    path: str
    coverage: float
    residue_sasa: Dict[int, float]
    weights_used: List[float]
    template_count: int
    residue_conservation: Dict[int, float]
    residue_consensus: Dict[int, str]


class ConsensusModelBuilder:
    """Constructs a consensus structure by averaging aligned template coordinates."""

    def __init__(self, max_templates: int = 3) -> None:
        self.max_templates = max_templates
        self.parser = PDBParser(QUIET=True)

    def build(
        self,
        models: Iterable[Dict[str, object]],
        output_path: str,
        sequence_length: int | None = None,
    ) -> ConsensusResult:
        selected = [model for model in models if os.path.exists(str(model.get('model_path', '')))]
        selected = selected[: self.max_templates]
        if not selected:
            raise ValueError("No template models available on disk for consensus building")

        structures = [self.parser.get_structure(f"template_{idx}", str(model['model_path']))
                      for idx, model in enumerate(selected)]
        weights = [max(float(model.get('gmqe_score', 0.1)), 0.05) for model in selected]

        # Align all structures to the first template using CA atoms
        reference = structures[0]
        reference_atoms, structure_atoms = self._collect_alignment_atoms(structures)
        self._superimpose(structures, reference_atoms, structure_atoms)

        # Average coordinates per atom across templates
        residue_lists = [self._collect_residues(structure) for structure in structures]
        min_length = min(len(residues) for residues in residue_lists)
        residue_lists = [residues[:min_length] for residues in residue_lists]

        residue_conservation: Dict[int, float] = {}
        residue_consensus: Dict[int, str] = {}

        for idx in range(min_length):
            _, reference_residue = residue_lists[0][idx]
            atom_coords: Dict[str, List[Tuple[float, np.ndarray]]] = {}
            residue_letter_weights: Dict[str, float] = {}
            for structure_idx, residues in enumerate(residue_lists):
                _, residue = residues[idx]
                for atom in residue:
                    atom_coords.setdefault(atom.get_name(), []).append(
                        (weights[structure_idx], atom.get_coord())
                    )

                letter = self._residue_letter(residue)
                if letter:
                    residue_letter_weights[letter] = residue_letter_weights.get(letter, 0.0) + weights[structure_idx]

            for atom_name, coords in atom_coords.items():
                weights_array = np.array([weight for weight, _ in coords])
                coord_array = np.array([coord for _, coord in coords])
                average = np.average(coord_array, axis=0, weights=weights_array)
                if atom_name in reference_residue:
                    reference_residue[atom_name].set_coord(average)

            residue_id = reference_residue.id[1]
            total_weight = sum(residue_letter_weights.values())
            if total_weight:
                consensus_letter = max(residue_letter_weights.items(), key=lambda item: item[1])[0]
                conservation = residue_letter_weights[consensus_letter] / total_weight
                residue_conservation[residue_id] = round(conservation, 3)
                residue_consensus[residue_id] = consensus_letter
            else:
                residue_conservation[residue_id] = 0.0
                letter = self._residue_letter(reference_residue)
                if letter:
                    residue_consensus[residue_id] = letter

        # Persist the averaged structure
        io = PDBIO()
        io.set_structure(reference)
        io.save(output_path)

        coverage = 1.0
        if sequence_length:
            coverage = min(1.0, max(0.0, min_length / sequence_length))

        residue_sasa = self._compute_sasa(reference)

        return ConsensusResult(
            path=output_path,
            coverage=coverage,
            residue_sasa=residue_sasa,
            weights_used=weights,
            template_count=len(structures),
            residue_conservation=residue_conservation,
            residue_consensus=residue_consensus,
        )

    def _collect_alignment_atoms(self, structures: List) -> Tuple[List, List[List]]:
        ref_atoms: List = []
        all_atoms: List[List] = []
        reference_residues = self._collect_residues(structures[0])
        for structure in structures:
            residues = self._collect_residues(structure)
            atoms = []
            for idx, (_, residue) in enumerate(residues):
                if 'CA' in residue:
                    if structure is structures[0]:
                        ref_atoms.append(residue['CA'])
                    atoms.append(residue['CA'])
            all_atoms.append(atoms)
        return ref_atoms, all_atoms

    def _superimpose(self, structures: List, reference_atoms: List, structure_atoms: List[List]) -> None:
        for structure, atoms in zip(structures[1:], structure_atoms[1:]):
            if len(reference_atoms) == 0 or len(atoms) == 0:
                continue
            atom_pairs = min(len(reference_atoms), len(atoms))
            super_imposer = Superimposer()
            super_imposer.set_atoms(reference_atoms[:atom_pairs], atoms[:atom_pairs])
            super_imposer.apply(structure.get_atoms())

    def _collect_residues(self, structure) -> List[Tuple[str, object]]:
        residues: List[Tuple[str, object]] = []
        for model in structure:
            for chain in model:
                for residue in chain:
                    if is_aa(residue, standard=True):
                        residues.append((chain.id, residue))
        return residues

    def _compute_sasa(self, structure) -> Dict[int, float]:
        sr = ShrakeRupley()
        sr.compute(structure, level='R')
        sasa_map: Dict[int, float] = {}
        for model in structure:
            for chain in model:
                for residue in chain:
                    if is_aa(residue, standard=True):
                        sasa_map[residue.id[1]] = getattr(residue, 'sasa', 0.0)
        return sasa_map

    def _residue_letter(self, residue) -> str | None:
        try:
            return seq1(residue.get_resname(), custom_map={"MSE": "M"})
        except Exception:
            return None
