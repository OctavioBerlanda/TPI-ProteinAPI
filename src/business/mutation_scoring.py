"""Utility classes for physicochemical mutation scoring.

Provides access to BLOSUM62 substitution scores, Grantham distances, and
heuristic \u0394\u0394G estimates that can be composed to grade mutation impact.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Tuple

# BLOSUM62 substitution matrix (symmetric)
BLOSUM62: Dict[str, Dict[str, int]] = {
    'A': {'A': 4, 'C': 0, 'D': -2, 'E': -1, 'F': -2, 'G': 0, 'H': -2, 'I': -1, 'K': -1, 'L': -1,
          'M': -1, 'N': -2, 'P': -1, 'Q': -1, 'R': -1, 'S': 1, 'T': 0, 'V': 0, 'W': -3, 'Y': -2},
    'C': {'A': 0, 'C': 9, 'D': -3, 'E': -4, 'F': -2, 'G': -3, 'H': -3, 'I': -1, 'K': -3, 'L': -1,
          'M': -1, 'N': -3, 'P': -3, 'Q': -3, 'R': -3, 'S': -1, 'T': -1, 'V': -1, 'W': -2, 'Y': -2},
    'D': {'A': -2, 'C': -3, 'D': 6, 'E': 2, 'F': -3, 'G': -1, 'H': -1, 'I': -3, 'K': -1, 'L': -4,
          'M': -3, 'N': 1, 'P': -1, 'Q': 0, 'R': -2, 'S': 0, 'T': -1, 'V': -3, 'W': -4, 'Y': -3},
    'E': {'A': -1, 'C': -4, 'D': 2, 'E': 5, 'F': -3, 'G': -2, 'H': 0, 'I': -3, 'K': 1, 'L': -3,
          'M': -2, 'N': 0, 'P': -1, 'Q': 2, 'R': 0, 'S': 0, 'T': -1, 'V': -2, 'W': -3, 'Y': -2},
    'F': {'A': -2, 'C': -2, 'D': -3, 'E': -3, 'F': 6, 'G': -3, 'H': -1, 'I': 0, 'K': -3, 'L': 0,
          'M': 0, 'N': -3, 'P': -4, 'Q': -3, 'R': -3, 'S': -2, 'T': -2, 'V': -1, 'W': 1, 'Y': 3},
    'G': {'A': 0, 'C': -3, 'D': -1, 'E': -2, 'F': -3, 'G': 6, 'H': -2, 'I': -4, 'K': -2, 'L': -4,
          'M': -3, 'N': 0, 'P': -2, 'Q': -2, 'R': -2, 'S': 0, 'T': -2, 'V': -3, 'W': -2, 'Y': -3},
    'H': {'A': -2, 'C': -3, 'D': -1, 'E': 0, 'F': -1, 'G': -2, 'H': 8, 'I': -3, 'K': -1, 'L': -3,
          'M': -2, 'N': 1, 'P': -2, 'Q': 0, 'R': 0, 'S': -1, 'T': -2, 'V': -3, 'W': -2, 'Y': 2},
    'I': {'A': -1, 'C': -1, 'D': -3, 'E': -3, 'F': 0, 'G': -4, 'H': -3, 'I': 4, 'K': -3, 'L': 2,
          'M': 1, 'N': -3, 'P': -3, 'Q': -3, 'R': -3, 'S': -2, 'T': -1, 'V': 3, 'W': -3, 'Y': -1},
    'K': {'A': -1, 'C': -3, 'D': -1, 'E': 1, 'F': -3, 'G': -2, 'H': -1, 'I': -3, 'K': 5, 'L': -2,
          'M': -1, 'N': 0, 'P': -1, 'Q': 1, 'R': 2, 'S': 0, 'T': -1, 'V': -2, 'W': -3, 'Y': -2},
    'L': {'A': -1, 'C': -1, 'D': -4, 'E': -3, 'F': 0, 'G': -4, 'H': -3, 'I': 2, 'K': -2, 'L': 4,
          'M': 2, 'N': -3, 'P': -3, 'Q': -2, 'R': -2, 'S': -2, 'T': -1, 'V': 1, 'W': -2, 'Y': -1},
    'M': {'A': -1, 'C': -1, 'D': -3, 'E': -2, 'F': 0, 'G': -3, 'H': -2, 'I': 1, 'K': -1, 'L': 2,
          'M': 5, 'N': -2, 'P': -2, 'Q': 0, 'R': -1, 'S': -1, 'T': -1, 'V': 1, 'W': -1, 'Y': -1},
    'N': {'A': -2, 'C': -3, 'D': 1, 'E': 0, 'F': -3, 'G': 0, 'H': 1, 'I': -3, 'K': 0, 'L': -3,
          'M': -2, 'N': 6, 'P': -2, 'Q': 0, 'R': 0, 'S': 1, 'T': 0, 'V': -3, 'W': -4, 'Y': -2},
    'P': {'A': -1, 'C': -3, 'D': -1, 'E': -1, 'F': -4, 'G': -2, 'H': -2, 'I': -3, 'K': -1, 'L': -3,
          'M': -2, 'N': -2, 'P': 7, 'Q': -1, 'R': -2, 'S': -1, 'T': -1, 'V': -2, 'W': -4, 'Y': -3},
    'Q': {'A': -1, 'C': -3, 'D': 0, 'E': 2, 'F': -3, 'G': -2, 'H': 0, 'I': -3, 'K': 1, 'L': -2,
          'M': 0, 'N': 0, 'P': -1, 'Q': 5, 'R': 1, 'S': 0, 'T': -1, 'V': -2, 'W': -2, 'Y': -1},
    'R': {'A': -1, 'C': -3, 'D': -2, 'E': 0, 'F': -3, 'G': -2, 'H': 0, 'I': -3, 'K': 2, 'L': -2,
          'M': -1, 'N': 0, 'P': -2, 'Q': 1, 'R': 5, 'S': -1, 'T': -1, 'V': -3, 'W': -3, 'Y': -2},
    'S': {'A': 1, 'C': -1, 'D': 0, 'E': 0, 'F': -2, 'G': 0, 'H': -1, 'I': -2, 'K': 0, 'L': -2,
          'M': -1, 'N': 1, 'P': -1, 'Q': 0, 'R': -1, 'S': 4, 'T': 1, 'V': -2, 'W': -3, 'Y': -2},
    'T': {'A': 0, 'C': -1, 'D': -1, 'E': -1, 'F': -2, 'G': -2, 'H': -2, 'I': -1, 'K': -1, 'L': -1,
          'M': -1, 'N': 0, 'P': -1, 'Q': -1, 'R': -1, 'S': 1, 'T': 5, 'V': 0, 'W': -2, 'Y': -2},
    'V': {'A': 0, 'C': -1, 'D': -3, 'E': -2, 'F': -1, 'G': -3, 'H': -3, 'I': 3, 'K': -2, 'L': 1,
          'M': 1, 'N': -3, 'P': -2, 'Q': -2, 'R': -3, 'S': -2, 'T': 0, 'V': 4, 'W': -3, 'Y': -1},
    'W': {'A': -3, 'C': -2, 'D': -4, 'E': -3, 'F': 1, 'G': -2, 'H': -2, 'I': -3, 'K': -3, 'L': -2,
          'M': -1, 'N': -4, 'P': -4, 'Q': -2, 'R': -3, 'S': -3, 'T': -2, 'V': -3, 'W': 11, 'Y': 2},
    'Y': {'A': -2, 'C': -2, 'D': -3, 'E': -2, 'F': 3, 'G': -3, 'H': 2, 'I': -1, 'K': -2, 'L': -1,
          'M': -1, 'N': -2, 'P': -3, 'Q': -1, 'R': -2, 'S': -2, 'T': -2, 'V': -1, 'W': 2, 'Y': 7},
}

# Grantham distances (symmetric); values omitted default to 0.
GRANTHAM_DISTANCE: Dict[Tuple[str, str], int] = {
    ('A', 'R'): 112, ('A', 'N'): 111, ('A', 'D'): 126, ('A', 'C'): 195, ('A', 'Q'): 91,
    ('A', 'E'): 107, ('A', 'G'): 60, ('A', 'H'): 86, ('A', 'I'): 94, ('A', 'L'): 96,
    ('A', 'K'): 106, ('A', 'M'): 84, ('A', 'F'): 113, ('A', 'P'): 27, ('A', 'S'): 99,
    ('A', 'T'): 58, ('A', 'W'): 148, ('A', 'Y'): 112, ('A', 'V'): 64,
    ('R', 'N'): 86, ('R', 'D'): 96, ('R', 'C'): 180, ('R', 'Q'): 43, ('R', 'E'): 54,
    ('R', 'G'): 125, ('R', 'H'): 29, ('R', 'I'): 97, ('R', 'L'): 102, ('R', 'K'): 26,
    ('R', 'M'): 91, ('R', 'F'): 97, ('R', 'P'): 103, ('R', 'S'): 110, ('R', 'T'): 71,
    ('R', 'W'): 101, ('R', 'Y'): 77, ('R', 'V'): 96,
    ('N', 'D'): 23, ('N', 'C'): 139, ('N', 'Q'): 46, ('N', 'E'): 42, ('N', 'G'): 80,
    ('N', 'H'): 68, ('N', 'I'): 149, ('N', 'L'): 153, ('N', 'K'): 94, ('N', 'M'): 142,
    ('N', 'F'): 158, ('N', 'P'): 91, ('N', 'S'): 46, ('N', 'T'): 65, ('N', 'W'): 174,
    ('N', 'Y'): 143, ('N', 'V'): 133,
    ('D', 'C'): 154, ('D', 'Q'): 61, ('D', 'E'): 45, ('D', 'G'): 94, ('D', 'H'): 81,
    ('D', 'I'): 168, ('D', 'L'): 172, ('D', 'K'): 101, ('D', 'M'): 160, ('D', 'F'): 177,
    ('D', 'P'): 108, ('D', 'S'): 65, ('D', 'T'): 85, ('D', 'W'): 181, ('D', 'Y'): 160,
    ('D', 'V'): 152,
    ('C', 'Q'): 154, ('C', 'E'): 170, ('C', 'G'): 159, ('C', 'H'): 174, ('C', 'I'): 198,
    ('C', 'L'): 198, ('C', 'K'): 202, ('C', 'M'): 196, ('C', 'F'): 205, ('C', 'P'): 169,
    ('C', 'S'): 112, ('C', 'T'): 149, ('C', 'W'): 215, ('C', 'Y'): 194, ('C', 'V'): 192,
    ('Q', 'E'): 29, ('Q', 'G'): 87, ('Q', 'H'): 24, ('Q', 'I'): 109, ('Q', 'L'): 113,
    ('Q', 'K'): 53, ('Q', 'M'): 101, ('Q', 'F'): 116, ('Q', 'P'): 76, ('Q', 'S'): 68,
    ('Q', 'T'): 42, ('Q', 'W'): 130, ('Q', 'Y'): 99, ('Q', 'V'): 96,
    ('E', 'G'): 98, ('E', 'H'): 40, ('E', 'I'): 134, ('E', 'L'): 138, ('E', 'K'): 56,
    ('E', 'M'): 126, ('E', 'F'): 140, ('E', 'P'): 93, ('E', 'S'): 80, ('E', 'T'): 65,
    ('E', 'W'): 152, ('E', 'Y'): 122, ('E', 'V'): 121,
    ('G', 'H'): 98, ('G', 'I'): 135, ('G', 'L'): 138, ('G', 'K'): 127, ('G', 'M'): 127,
    ('G', 'F'): 153, ('G', 'P'): 42, ('G', 'S'): 56, ('G', 'T'): 59, ('G', 'W'): 184,
    ('G', 'Y'): 147, ('G', 'V'): 109,
    ('H', 'I'): 94, ('H', 'L'): 99, ('H', 'K'): 32, ('H', 'M'): 87, ('H', 'F'): 100,
    ('H', 'P'): 77, ('H', 'S'): 89, ('H', 'T'): 47, ('H', 'W'): 115, ('H', 'Y'): 83,
    ('H', 'V'): 84,
    ('I', 'L'): 5, ('I', 'K'): 102, ('I', 'M'): 10, ('I', 'F'): 21, ('I', 'P'): 95,
    ('I', 'S'): 142, ('I', 'T'): 89, ('I', 'W'): 61, ('I', 'Y'): 33, ('I', 'V'): 29,
    ('L', 'K'): 107, ('L', 'M'): 15, ('L', 'F'): 22, ('L', 'P'): 98, ('L', 'S'): 145,
    ('L', 'T'): 92, ('L', 'W'): 61, ('L', 'Y'): 36, ('L', 'V'): 32,
    ('K', 'M'): 95, ('K', 'F'): 102, ('K', 'P'): 103, ('K', 'S'): 121, ('K', 'T'): 78,
    ('K', 'W'): 110, ('K', 'Y'): 85, ('K', 'V'): 97,
    ('M', 'F'): 28, ('M', 'P'): 87, ('M', 'S'): 135, ('M', 'T'): 81, ('M', 'W'): 67,
    ('M', 'Y'): 36, ('M', 'V'): 21,
    ('F', 'P'): 114, ('F', 'S'): 155, ('F', 'T'): 103, ('F', 'W'): 40, ('F', 'Y'): 22,
    ('F', 'V'): 50,
    ('P', 'S'): 74, ('P', 'T'): 38, ('P', 'W'): 147, ('P', 'Y'): 110, ('P', 'V'): 68,
    ('S', 'T'): 58, ('S', 'W'): 177, ('S', 'Y'): 144, ('S', 'V'): 124,
    ('T', 'W'): 128, ('T', 'Y'): 92, ('T', 'V'): 69,
    ('W', 'Y'): 37, ('W', 'V'): 88,
    ('Y', 'V'): 55,
}


AMINO_ACID_PROPERTIES: Dict[str, Dict[str, float]] = {
    # Kyte-Doolittle hydropathy, volume (Ang^3), and charge at pH 7
    'A': {'hydropathy': 1.8, 'volume': 88.6, 'charge': 0},
    'R': {'hydropathy': -4.5, 'volume': 173.4, 'charge': 1},
    'N': {'hydropathy': -3.5, 'volume': 114.1, 'charge': 0},
    'D': {'hydropathy': -3.5, 'volume': 111.1, 'charge': -1},
    'C': {'hydropathy': 2.5, 'volume': 108.5, 'charge': 0},
    'Q': {'hydropathy': -3.5, 'volume': 143.8, 'charge': 0},
    'E': {'hydropathy': -3.5, 'volume': 138.4, 'charge': -1},
    'G': {'hydropathy': -0.4, 'volume': 60.1, 'charge': 0},
    'H': {'hydropathy': -3.2, 'volume': 153.2, 'charge': 0.1},
    'I': {'hydropathy': 4.5, 'volume': 166.7, 'charge': 0},
    'L': {'hydropathy': 3.8, 'volume': 166.7, 'charge': 0},
    'K': {'hydropathy': -3.9, 'volume': 168.6, 'charge': 1},
    'M': {'hydropathy': 1.9, 'volume': 162.9, 'charge': 0},
    'F': {'hydropathy': 2.8, 'volume': 189.9, 'charge': 0},
    'P': {'hydropathy': -1.6, 'volume': 112.7, 'charge': 0},
    'S': {'hydropathy': -0.8, 'volume': 89.0, 'charge': 0},
    'T': {'hydropathy': -0.7, 'volume': 116.1, 'charge': 0},
    'W': {'hydropathy': -0.9, 'volume': 227.8, 'charge': 0},
    'Y': {'hydropathy': -1.3, 'volume': 193.6, 'charge': 0},
    'V': {'hydropathy': 4.2, 'volume': 140.0, 'charge': 0},
}


@dataclass(frozen=True)
class MutationDescriptor:
    """Simple container describing a single point mutation."""

    position: int
    original: str
    mutated: str

    def notation(self) -> str:
        return f"{self.original}{self.position}{self.mutated}"


@dataclass
class MutationEnvironment:
    """Contextual information for a mutation site."""

    sasa: float | None = None
    is_surface: bool | None = None
    secondary_structure: str | None = None
    conservation: float | None = None


@dataclass
class MutationScore:
    """Detailed score for a single mutation."""

    descriptor: MutationDescriptor
    blosum_score: float
    grantham_distance: float
    ddg: float
    hydropathy_delta: float
    volume_delta: float
    charge_delta: float
    classification: str

    def as_dict(self) -> Dict[str, float | str]:
        base = {
            'position': self.descriptor.position,
            'mutation': self.descriptor.notation(),
            'blosum_score': self.blosum_score,
            'grantham_distance': self.grantham_distance,
            'ddg': self.ddg,
            'hydropathy_delta': self.hydropathy_delta,
            'volume_delta': self.volume_delta,
            'charge_delta': self.charge_delta,
            'classification': self.classification,
        }
        return base


class MutationScorer:
    """Combines substitution matrices and residue context to approximate \u0394\u0394G."""

    def __init__(self, default_sasa_threshold: float = 80.0) -> None:
        self.default_sasa_threshold = default_sasa_threshold

    @staticmethod
    def _get_blosum_score(original: str, mutated: str) -> float:
        try:
            return float(BLOSUM62[original][mutated])
        except KeyError:
            return float(BLOSUM62.get(mutated, {}).get(original, 0))

    @staticmethod
    def _get_grantham_distance(original: str, mutated: str) -> float:
        if original == mutated:
            return 0.0
        return float(
            GRANTHAM_DISTANCE.get((original, mutated))
            or GRANTHAM_DISTANCE.get((mutated, original))
            or 0.0
        )

    @staticmethod
    def _property_delta(original: str, mutated: str, prop: str) -> float:
        return float(AMINO_ACID_PROPERTIES.get(mutated, {}).get(prop, 0.0) -
                     AMINO_ACID_PROPERTIES.get(original, {}).get(prop, 0.0))

    def _estimate_ddg(self, descriptor: MutationDescriptor, env: MutationEnvironment,
                      blosum: float, grantham: float) -> float:
        """Estimate \u0394\u0394G (kcal/mol) based on sequence and environment heuristics."""
        hydropathy_delta = self._property_delta(descriptor.original, descriptor.mutated, 'hydropathy')
        volume_delta = self._property_delta(descriptor.original, descriptor.mutated, 'volume') / 100.0
        charge_delta = self._property_delta(descriptor.original, descriptor.mutated, 'charge')

        # Base energy derived from grantham and blosum
        ddg = 0.12 * grantham - 0.05 * blosum

        # Penalise large property changes
        ddg += 0.35 * abs(hydropathy_delta)
        ddg += 0.25 * abs(volume_delta)
        ddg += 1.1 * abs(charge_delta)

        # Environmental adjustments
        sasa = env.sasa if env.sasa is not None else self.default_sasa_threshold
        exposure = min(1.0, max(0.0, sasa / self.default_sasa_threshold))
        # Buried residues (low SASA) magnify the penalty, surface residues dampen it.
        ddg *= 1.25 - 0.5 * exposure

        if env.conservation is not None:
            ddg += 0.5 * env.conservation

        if env.secondary_structure in {'H', 'E'}:  # helix or sheet
            ddg += 0.4

        return round(ddg, 2), hydropathy_delta, volume_delta, charge_delta

    def classify_ddg(self, ddg: float) -> str:
        if ddg <= -0.5:
            return 'stabilizing'
        if ddg < 0.5:
            return 'neutral'
        if ddg < 2.0:
            return 'mildly_destabilizing'
        return 'destabilizing'

    def score_mutations(
        self,
        mutations: Iterable[MutationDescriptor],
        environments: Mapping[int, MutationEnvironment],
    ) -> Dict[str, object]:
        scores: List[MutationScore] = []
        for descriptor in mutations:
            env = environments.get(descriptor.position, MutationEnvironment())
            blosum = self._get_blosum_score(descriptor.original, descriptor.mutated)
            grantham = self._get_grantham_distance(descriptor.original, descriptor.mutated)
            ddg, hydropathy_delta, volume_delta, charge_delta = self._estimate_ddg(
                descriptor, env, blosum, grantham
            )
            classification = self.classify_ddg(ddg)
            scores.append(
                MutationScore(
                    descriptor=descriptor,
                    blosum_score=blosum,
                    grantham_distance=grantham,
                    ddg=ddg,
                    hydropathy_delta=round(hydropathy_delta, 2),
                    volume_delta=round(volume_delta, 2),
                    charge_delta=round(charge_delta, 2),
                    classification=classification,
                )
            )

        if not scores:
            return {
                'per_mutation': [],
                'aggregate': {
                    'mean_ddg': 0.0,
                    'max_ddg': 0.0,
                    'min_blosum': 0.0,
                    'destabilizing_fraction': 0.0,
                    'impact_level': 'neutral'
                },
            }

        ddg_values = [score.ddg for score in scores]
        blosum_values = [score.blosum_score for score in scores]
        destabilizing_fraction = sum(1 for score in scores if score.ddg >= 0.5) / len(scores)
        impact_level = 'moderate'
        if max(ddg_values) < 0.5:
            impact_level = 'low'
        elif max(ddg_values) > 2.5 or destabilizing_fraction > 0.5:
            impact_level = 'high'

        return {
            'per_mutation': [score.as_dict() for score in scores],
            'aggregate': {
                'mean_ddg': round(sum(ddg_values) / len(ddg_values), 2),
                'max_ddg': max(ddg_values),
                'min_blosum': min(blosum_values),
                'destabilizing_fraction': round(destabilizing_fraction, 2),
                'impact_level': impact_level,
            },
        }
