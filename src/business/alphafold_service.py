"""
Servicio de integración con AlphaFold
Maneja la comunicación con la API de AlphaFold y el procesamiento de modelos 3D
"""
import os
import json
import time
import requests
import tempfile
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

class AlphaFoldIntegrationError(Exception):
    """Excepción personalizada para errores de integración con AlphaFold"""
    pass

class AlphaFoldService:
    """
    Servicio para integración con AlphaFold
    Soporta tanto la API web como ColabFold local
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el servicio de AlphaFold
        
        Args:
            config: Configuración con endpoints y credenciales
        """
        self.config = config
        self.api_endpoint = config.get('ALPHAFOLD_API_ENDPOINT', 'https://alphafolddb.org/api')
        self.colabfold_endpoint = config.get('COLABFOLD_ENDPOINT', 'http://localhost:8080')
        self.models_directory = config.get('MODELS_DIRECTORY', 'models/alphafold')
        self.timeout = config.get('API_TIMEOUT', 300)  # 5 minutos
        
        # Crear directorio de modelos si no existe
        Path(self.models_directory).mkdir(parents=True, exist_ok=True)
    
    def predict_structure(self, sequence: str, job_name: str = None) -> Dict[str, Any]:
        """
        Predice la estructura 3D de una secuencia de proteína
        
        Args:
            sequence: Secuencia de aminoácidos
            job_name: Nombre opcional para el trabajo
            
        Returns:
            Dict con información del modelo predicho
        """
        start_time = time.time()
        
        try:
            # Intentar primero con ColabFold local si está disponible
            if self._is_colabfold_available():
                result = self._predict_with_colabfold(sequence, job_name)
            else:
                # Fallback a búsqueda en AlphaFold DB o predicción simple
                result = self._predict_with_alphafold_db(sequence, job_name)
                
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            return result
            
        except Exception as e:
            raise AlphaFoldIntegrationError(f"Error en predicción de estructura: {str(e)}")
    
    def compare_structures(self, original_result: Dict, mutated_result: Dict) -> Dict[str, Any]:
        """
        Compara dos estructuras predichas y calcula diferencias estructurales
        
        Args:
            original_result: Resultado de predicción de secuencia original
            mutated_result: Resultado de predicción de secuencia mutada
            
        Returns:
            Dict con análisis comparativo
        """
        try:
            comparison = {
                'rmsd_value': self._calculate_rmsd(original_result, mutated_result),
                'confidence_difference': abs(
                    original_result.get('confidence', 0) - mutated_result.get('confidence', 0)
                ),
                'structural_changes': self._analyze_structural_changes(original_result, mutated_result),
                'comparison_timestamp': datetime.utcnow().isoformat(),
                'analysis_method': 'alphafold_comparison'
            }
            
            return comparison
            
        except Exception as e:
            raise AlphaFoldIntegrationError(f"Error comparando estructuras: {str(e)}")
    
    def _is_colabfold_available(self) -> bool:
        """Verifica si ColabFold está disponible localmente"""
        try:
            response = requests.get(f"{self.colabfold_endpoint}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _predict_with_colabfold(self, sequence: str, job_name: str = None) -> Dict[str, Any]:
        """
        Predice estructura usando ColabFold local
        
        Args:
            sequence: Secuencia de aminoácidos
            job_name: Nombre del trabajo
            
        Returns:
            Dict con resultados de la predicción
        """
        if not job_name:
            job_name = f"protein_{int(time.time())}"
        
        # Preparar datos para el job
        job_data = {
            'sequence': sequence,
            'job_name': job_name,
            'num_models': 1,
            'use_amber': True,
            'use_templates': False
        }
        
        # Enviar trabajo a ColabFold
        response = requests.post(
            f"{self.colabfold_endpoint}/predict",
            json=job_data,
            timeout=self.timeout
        )
        
        if response.status_code != 200:
            raise AlphaFoldIntegrationError(f"Error en ColabFold: {response.text}")
        
        result = response.json()
        
        # Descargar y guardar el modelo
        model_path = self._download_model(result['model_url'], job_name)
        
        return {
            'job_id': result['job_id'],
            'model_path': model_path,
            'model_url': result['model_url'],
            'confidence': result.get('mean_plddt', 0),
            'confidence_scores': result.get('plddt_scores', []),
            'prediction_method': 'colabfold',
            'sequence_length': len(sequence)
        }
    
    def _predict_with_alphafold_db(self, sequence: str, job_name: str = None) -> Dict[str, Any]:
        """
        Busca en AlphaFold DB o usa predicción simplificada
        
        Args:
            sequence: Secuencia de aminoácidos
            job_name: Nombre del trabajo
            
        Returns:
            Dict con resultados de la predicción
        """
        if not job_name:
            job_name = f"protein_{int(time.time())}"
        
        # Simular predicción con valores realistas para demo
        # En producción, aquí iría la integración real con AlphaFold
        
        confidence = self._estimate_confidence(sequence)
        
        # Crear archivo PDB simulado para demo
        model_path = self._create_demo_model(sequence, job_name)
        
        return {
            'job_id': f"demo_{job_name}",
            'model_path': model_path,
            'model_url': None,
            'confidence': confidence,
            'confidence_scores': [confidence] * len(sequence),
            'prediction_method': 'alphafold_simulation',
            'sequence_length': len(sequence)
        }
    
    def _download_model(self, model_url: str, job_name: str) -> str:
        """
        Descarga el modelo 3D desde la URL proporcionada
        
        Args:
            model_url: URL del modelo a descargar
            job_name: Nombre del trabajo para el archivo
            
        Returns:
            Ruta local del archivo descargado
        """
        try:
            response = requests.get(model_url, timeout=30)
            response.raise_for_status()
            
            # Determinar extensión del archivo
            content_type = response.headers.get('content-type', '')
            if 'pdb' in content_type:
                extension = '.pdb'
            elif 'cif' in content_type:
                extension = '.cif'
            else:
                extension = '.pdb'  # Por defecto
            
            # Guardar archivo
            filename = f"{job_name}_{int(time.time())}{extension}"
            file_path = os.path.join(self.models_directory, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return file_path
            
        except Exception as e:
            raise AlphaFoldIntegrationError(f"Error descargando modelo: {str(e)}")
    
    def _create_demo_model(self, sequence: str, job_name: str) -> str:
        """
        Crea un archivo PDB de demostración para testing
        
        Args:
            sequence: Secuencia de aminoácidos
            job_name: Nombre del trabajo
            
        Returns:
            Ruta del archivo PDB creado
        """
        filename = f"{job_name}_{int(time.time())}.cif"
        file_path = os.path.join(self.models_directory, filename)
        
        # Crear contenido CIF básico (formato mmCIF)
        cif_content = self._generate_demo_cif_content(sequence, job_name)
        
        with open(file_path, 'w') as f:
            f.write(cif_content)
        
        return file_path
    
    def _generate_demo_cif_content(self, sequence: str, job_name: str) -> str:
        """
        Genera contenido CIF (mmCIF) de demostración más compatible con NGL
        
        Args:
            sequence: Secuencia de aminoácidos
            job_name: Nombre del trabajo
            
        Returns:
            Contenido del archivo CIF en formato mmCIF estándar
        """
        from datetime import datetime
        
        # Estructura básica mmCIF compatible con NGL
        cif_content = f"""data_demo_structure
#
_entry.id   demo_structure
#
_audit_conform.dict_name       mmcif_pdbx.dic
_audit_conform.dict_version    5.397
#
_entity.id                         1
_entity.type                       polymer
_entity.src_method                 man
_entity.pdbx_description           'Demo protein'
_entity.formula_weight             ?
#
_entity_poly.entity_id   1
_entity_poly.type        'polypeptide(L)'
_entity_poly.nstd_linkage         no
_entity_poly.nstd_monomer         no
_entity_poly.pdbx_seq_one_letter_code
;{sequence}
;
#
_struct.entry_id                  demo_structure
_struct.title                     'Demo protein structure for {job_name}'
#
_struct_asym.id                    A
_struct_asym.pdbx_blank_PDB_chainid_flag   N
_struct_asym.pdbx_modified         N
_struct_asym.entity_id             1
_struct_asym.details               ?
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.pdbx_formal_charge
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
"""

        # Mapeo de aminoácidos a códigos de 3 letras
        aa_map = {
            'A': 'ALA', 'R': 'ARG', 'N': 'ASN', 'D': 'ASP', 'C': 'CYS',
            'Q': 'GLN', 'E': 'GLU', 'G': 'GLY', 'H': 'HIS', 'I': 'ILE',
            'L': 'LEU', 'K': 'LYS', 'M': 'MET', 'F': 'PHE', 'P': 'PRO',
            'S': 'SER', 'T': 'THR', 'W': 'TRP', 'Y': 'TYR', 'V': 'VAL'
        }
        
        # Generar coordenadas atómicas (solo CA para simplificar)
        atoms = []
        for i, aa in enumerate(sequence):
            aa_code = aa_map.get(aa, 'ALA')
            
            # Coordenadas simplificadas en hélice alfa
            angle = i * 2.0 * 3.14159 / 3.6  # 3.6 residuos por vuelta
            x = 8.0 * (angle * 0.1)  # Coordenada X más extendida
            y = 8.0 * (0.1 * i * 0.8)  # Coordenada Y
            z = i * 1.5  # Altura por residuo
            
            # Línea de átomo CA en formato mmCIF
            atom_line = f"ATOM {i+1:6d} C CA . {aa_code} A 1 {i+1:4d} ? {x:8.3f} {y:8.3f} {z:8.3f} 1.00 50.00 ? {i+1:4d} {aa_code} A CA 1"
            atoms.append(atom_line)
        
        # Unir todo el contenido
        cif_content += "\n".join(atoms) + "\n#\n"
        
        return cif_content
    
    def _generate_demo_pdb_content(self, sequence: str, job_name: str) -> str:
        """
        Genera contenido PDB de demostración
        
        Args:
            sequence: Secuencia de aminoácidos
            job_name: Nombre del trabajo
            
        Returns:
            Contenido del archivo PDB
        """
        header = f"""HEADER    DEMO PROTEIN STRUCTURE           {datetime.now().strftime('%d-%b-%y')}   DEMO
TITLE     PROTEIN STRUCTURE PREDICTION FOR {job_name.upper()}
COMPND    MOL_ID: 1;
COMPND   2 MOLECULE: PREDICTED PROTEIN;
COMPND   3 CHAIN: A;
SOURCE    MOL_ID: 1;
SOURCE   2 ORGANISM_SCIENTIFIC: DEMO;
SOURCE   3 EXPRESSION_SYSTEM: ALPHAFOLD PREDICTION;
"""
        
        # Generar coordenadas atómicas simplificadas
        atoms = []
        for i, aa in enumerate(sequence):
            # Coordenadas simplificadas para átomo CA (carbono alfa)
            x = i * 3.8  # Distancia típica entre CA consecutivos
            y = 0.0
            z = 0.0
            
            atom_line = f"ATOM  {i+1:5d}  CA  {aa} A{i+1:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 80.00           C  "
            atoms.append(atom_line)
        
        footer = "END"
        
        return header + "\n".join(atoms) + "\n" + footer
    
    def _estimate_confidence(self, sequence: str) -> float:
        """
        Estima la confianza de predicción basada en características de la secuencia
        
        Args:
            sequence: Secuencia de aminoácidos
            
        Returns:
            Puntuación de confianza estimada (0-100)
        """
        # Algoritmo simplificado para estimación de confianza
        length_score = min(100, len(sequence) * 2)  # Secuencias más largas = más confianza
        
        # Penalizar secuencias con muchos aminoácidos raros
        rare_aa = {'U', 'O', 'B', 'Z', 'J', 'X'}
        rare_count = sum(1 for aa in sequence if aa in rare_aa)
        rare_penalty = rare_count * 10
        
        confidence = max(50, min(95, length_score - rare_penalty))
        return round(confidence, 2)
    
    def _calculate_rmsd(self, original: Dict, mutated: Dict) -> float:
        """
        Calcula RMSD simplificado entre dos estructuras
        
        Args:
            original: Datos de estructura original
            mutated: Datos de estructura mutada
            
        Returns:
            Valor RMSD estimado
        """
        # Simulación de RMSD basada en diferencias de confianza
        conf_diff = abs(original.get('confidence', 0) - mutated.get('confidence', 0))
        
        # RMSD típico está entre 0.5 y 5.0 Angstroms
        rmsd = 0.5 + (conf_diff / 100) * 4.5
        
        return round(rmsd, 3)
    
    def _analyze_structural_changes(self, original: Dict, mutated: Dict) -> Dict[str, Any]:
        """
        Analiza cambios estructurales entre las dos predicciones
        
        Args:
            original: Datos de estructura original
            mutated: Datos de estructura mutada
            
        Returns:
            Dict con análisis de cambios estructurales
        """
        confidence_change = mutated.get('confidence', 0) - original.get('confidence', 0)
        
        analysis = {
            'confidence_change': round(confidence_change, 2),
            'stability_impact': 'stable' if abs(confidence_change) < 5 else 'moderate' if abs(confidence_change) < 15 else 'significant',
            'predicted_effect': 'beneficial' if confidence_change > 0 else 'neutral' if confidence_change == 0 else 'detrimental',
            'structural_regions_affected': [],  # Se podría expandir con análisis más detallado
            'domain_changes': 'none'  # Placeholder para análisis futuro
        }
        
        return analysis

def create_alphafold_service(config: Dict[str, Any]) -> AlphaFoldService:
    """
    Factory function para crear instancia del servicio AlphaFold
    
    Args:
        config: Configuración de la aplicación
        
    Returns:
        Instancia configurada de AlphaFoldService
    """
    return AlphaFoldService(config)
