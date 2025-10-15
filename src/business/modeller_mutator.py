"""
Motor de mutación de proteínas usando Modeller.
Aplica mutaciones puntuales con rotámeros optimizados y refinamiento estructural.
"""

import os
import sys
from typing import Dict, List, Tuple, Any
from pathlib import Path


class ModellerMutator:
    """
    Aplica mutaciones a estructuras PDB usando Modeller con alta precisión.
    NO realiza llamadas a servicios externos, todo es local.
    """
    
    def __init__(self, license_key: str, optimization_level: str = 'high'):
        """
        Inicializa el mutador de Modeller.
        
        Args:
            license_key: Clave de licencia académica de Modeller
            optimization_level: 'low', 'medium', 'high'
        """
        self.license_key = license_key
        self.optimization_level = optimization_level
        
        # Configurar licencia
        os.environ['KEY_MODELLER'] = license_key
        
        # Intentar importar Modeller
        try:
            from modeller import Environ, Model, Selection
            from modeller.optimizers import MolecularDynamics, ConjugateGradients
            from modeller.automodel import assess
            
            self.modeller_available = True
            self.Environ = Environ
            self.Model = Model
            self.Selection = Selection
            self.MolecularDynamics = MolecularDynamics
            self.ConjugateGradients = ConjugateGradients
            self.assess = assess
            
            print("✅ Modeller cargado correctamente")
            
        except ImportError as e:
            self.modeller_available = False
            print(f"⚠️ Modeller no disponible: {e}")
            print("   Instala con: conda install -c salilab modeller")
    
    def mutate_structure(
        self,
        pdb_path: str,
        mutations: List[Tuple[int, str, str]],
        output_path: str,
        optimization_level: str = None
    ) -> Dict[str, Any]:
        """
        Aplica mutaciones al PDB usando Modeller con rotámeros y optimización.
        
        Args:
            pdb_path: Ruta al archivo PDB original
            mutations: Lista de tuplas (posición, aa_original, aa_mutado)
            output_path: Ruta donde guardar el PDB mutado
            optimization_level: Nivel de optimización ('low', 'medium', 'high')
            
        Returns:
            Dict con información del modelo mutado y métricas de calidad
        """
        if not self.modeller_available:
            raise RuntimeError(
                "Modeller no está instalado. "
                "Instala con: conda install -c salilab modeller"
            )
        
        opt_level = optimization_level or self.optimization_level
        
        print(f"🔬 Iniciando mutación con Modeller (nivel: {opt_level})")
        print(f"   📁 Input: {pdb_path}")
        print(f"   🔄 Mutaciones: {mutations}")
        
        # 1. Setup Modeller environment
        env = self._setup_environment()
        
        # 2. Cargar estructura original
        mdl = self._load_structure(env, pdb_path)
        
        # 3. Aplicar cada mutación
        for i, (position, orig_aa, mut_aa) in enumerate(mutations, 1):
            print(f"   🧬 Mutación {i}/{len(mutations)}: {orig_aa}{position}{mut_aa}")
            self._apply_single_mutation(mdl, env, position, orig_aa, mut_aa)
        
        # 4. Optimizar estructura según nivel
        print(f"   ⚙️ Optimizando geometría (nivel {opt_level})...")
        if opt_level == 'high':
            self._optimize_high(mdl)
        elif opt_level == 'medium':
            self._optimize_medium(mdl)
        else:
            self._optimize_low(mdl)
        
        # 5. Evaluar calidad del modelo
        print(f"   📊 Evaluando calidad del modelo...")
        quality_scores = self._assess_quality(mdl)
        
        # 6. Guardar modelo mutado
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        mdl.write(output_path)
        
        print(f"   ✅ Mutación completada: {output_path}")
        print(f"   📈 DOPE score: {quality_scores['dope_score']:.2f}")
        print(f"   📈 DOPE normalizado: {quality_scores['normalized_dope']:.4f}")
        
        return {
            'model_path': output_path,
            'quality_scores': quality_scores,
            'method': 'modeller_rotamers',
            'optimization_level': opt_level,
            'mutations_applied': len(mutations)
        }
    
    def _setup_environment(self):
        """Configura el entorno de Modeller."""
        env = self.Environ()
        
        # Directorios de archivos
        env.io.atom_files_directory = ['.', '/tmp']
        
        # Bibliotecas de topología y parámetros
        env.libs.topology.read(file='$(LIB)/top_heav.lib')
        env.libs.parameters.read(file='$(LIB)/par.lib')
        
        return env
    
    def _load_structure(self, env, pdb_path: str):
        """Carga la estructura PDB."""
        # Extraer nombre base del archivo
        pdb_name = Path(pdb_path).stem
        
        # Configurar directorio
        pdb_dir = str(Path(pdb_path).parent)
        if pdb_dir not in env.io.atom_files_directory:
            env.io.atom_files_directory.append(pdb_dir)
        
        # Cargar modelo
        mdl = self.Model(env, file=pdb_path)
        
        return mdl
    
    def _apply_single_mutation(
        self,
        mdl,
        env,
        position: int,
        orig_aa: str,
        mut_aa: str
    ):
        """
        Aplica una mutación puntual con selección de rotámero óptimo.
        
        Args:
            mdl: Modelo de Modeller
            env: Entorno de Modeller
            position: Posición del residuo (1-based)
            orig_aa: Aminoácido original (código 1-letra)
            mut_aa: Aminoácido mutado (código 1-letra)
        """
        try:
            # Seleccionar el residuo a mutar
            # Modeller usa formato "position:chain"
            # Intentamos con cadena vacía primero
            try:
                sel = self.Selection(mdl.residues[f'{position}:'])
            except:
                # Si falla, intentar con cadena A
                try:
                    sel = self.Selection(mdl.residues[f'{position}:A'])
                except:
                    # Buscar el residuo por número
                    for residue in mdl.residues:
                        if residue.num == position:
                            sel = self.Selection(residue)
                            break
                    else:
                        raise ValueError(f"No se encontró el residuo en posición {position}")
            
            # Convertir aminoácido a código de 3 letras
            mut_restyp = self._aa_to_modeller(mut_aa)
            
            # Aplicar mutación con biblioteca de rotámeros
            sel.mutate(residue_type=mut_restyp)
            
            # Optimización local alrededor de la mutación
            # Seleccionar átomos en un radio de 10Å
            atmsel = self.Selection(mdl).select_sphere(
                center=sel.atoms[0],
                radius=10.0
            )
            
            # Minimización de energía local
            cg = self.ConjugateGradients()
            cg.optimize(atmsel, max_iterations=200, output='NO_REPORT')
            
        except Exception as e:
            print(f"   ⚠️ Error aplicando mutación {orig_aa}{position}{mut_aa}: {e}")
            raise
    
    def _optimize_low(self, mdl):
        """
        Optimización baja: minimización rápida.
        Tiempo: ~10-20 segundos
        """
        atmsel = self.Selection(mdl)
        cg = self.ConjugateGradients()
        cg.optimize(atmsel, max_iterations=100, output='NO_REPORT')
    
    def _optimize_medium(self, mdl):
        """
        Optimización media: minimización estándar.
        Tiempo: ~30-60 segundos
        """
        atmsel = self.Selection(mdl)
        cg = self.ConjugateGradients()
        cg.optimize(atmsel, max_iterations=300, output='NO_REPORT')
    
    def _optimize_high(self, mdl):
        """
        Optimización alta: minimización + dinámica molecular.
        Tiempo: ~1-3 minutos
        Máxima precisión.
        """
        atmsel = self.Selection(mdl)
        
        # 1. Minimización inicial exhaustiva
        cg = self.ConjugateGradients()
        cg.optimize(atmsel, max_iterations=500, output='NO_REPORT')
        
        # 2. Dinámica molecular corta (simula movimientos térmicos)
        md = self.MolecularDynamics(output='NO_REPORT')
        md.optimize(atmsel, temperature=300, max_iterations=300)
        
        # 3. Refinamiento final
        cg.optimize(atmsel, max_iterations=200, output='NO_REPORT')
    
    def _assess_quality(self, mdl) -> Dict[str, float]:
        """
        Evalúa la calidad del modelo mutado usando métricas de Modeller.
        
        Returns:
            Dict con scores de calidad
        """
        atmsel = self.Selection(mdl)
        
        # DOPE score (Discrete Optimized Protein Energy)
        # Valores más negativos = mejor calidad
        # Típicamente entre -50000 y 50000
        try:
            dope_score = atmsel.assess_dope()
        except:
            dope_score = 0.0
        
        # Normalizar por número de residuos
        num_residues = len(mdl.residues)
        normalized_dope = dope_score / num_residues if num_residues > 0 else 0.0
        
        # Clasificación de calidad basada en DOPE normalizado
        if normalized_dope < -0.03:
            quality_level = 'excellent'
        elif normalized_dope < 0.0:
            quality_level = 'good'
        elif normalized_dope < 0.05:
            quality_level = 'acceptable'
        else:
            quality_level = 'poor'
        
        return {
            'dope_score': round(dope_score, 2),
            'normalized_dope': round(normalized_dope, 4),
            'num_residues': num_residues,
            'quality_level': quality_level
        }
    
    @staticmethod
    def _aa_to_modeller(aa: str) -> str:
        """
        Convierte código de aminoácido de 1-letra a código Modeller de 3-letras.
        
        Args:
            aa: Código de 1 letra (ej: 'A', 'R', 'N')
            
        Returns:
            Código de 3 letras Modeller (ej: 'ALA', 'ARG', 'ASN')
        """
        mapping = {
            'A': 'ALA', 'R': 'ARG', 'N': 'ASN', 'D': 'ASP',
            'C': 'CYS', 'Q': 'GLN', 'E': 'GLU', 'G': 'GLY',
            'H': 'HIS', 'I': 'ILE', 'L': 'LEU', 'K': 'LYS',
            'M': 'MET', 'F': 'PHE', 'P': 'PRO', 'S': 'SER',
            'T': 'THR', 'W': 'TRP', 'Y': 'TYR', 'V': 'VAL'
        }
        
        aa_upper = aa.upper()
        if aa_upper not in mapping:
            raise ValueError(f"Aminoácido no reconocido: {aa}")
        
        return mapping[aa_upper]


def create_modeller_mutator(config: Dict[str, Any]) -> ModellerMutator:
    """
    Factory function para crear una instancia de ModellerMutator.
    
    Args:
        config: Dict con configuración (debe incluir 'license_key')
        
    Returns:
        Instancia configurada de ModellerMutator
    """
    license_key = config.get('license_key', '')
    optimization_level = config.get('default_optimization', 'high')
    
    if not license_key:
        raise ValueError(
            "Se requiere license_key para Modeller. "
            "Obtén una licencia académica gratuita en: "
            "https://salilab.org/modeller/registration.html"
        )
    
    return ModellerMutator(license_key, optimization_level)
