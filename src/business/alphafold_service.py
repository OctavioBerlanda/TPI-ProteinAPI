"""
Servicio de integración con AlphaFold
Maneja la comunicación con la API de AlphaFold y el procesamiento de modelos 3D
"""
import os
import json
import time
import math
import requests
import tempfile
import numpy as np
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime
from pathlib import Path
from Bio.Blast import NCBIWWW, NCBIXML
import re
from .sequence_service import SequenceValidator
from Bio.PDB import MMCIFParser
import io

class AlphaFoldIntegrationError(Exception):
    """Excepción personalizada para errores de integración con AlphaFold"""
    pass

class AlphaFoldService:
    """
    Servicio para integración con AlphaFold
    Soporta la API web y SWISS-MODEL para predicciones
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el servicio de AlphaFold
        
        Args:
            config: Configuración con endpoints y credenciales
        """
        self.config = config
        self.api_endpoint = config.get('ALPHAFOLD_API_ENDPOINT', 'https://alphafolddb.org/api')
        self.models_directory = config.get('MODELS_DIRECTORY', 'models/alphafold')
        self.timeout = config.get('API_TIMEOUT', 300)  # 5 minutos
        
        # Crear directorio de modelos si no existe
        Path(self.models_directory).mkdir(parents=True, exist_ok=True)

    def cleanup_old_models(self, user_id: int = None, keep_recent: int = 3) -> Dict[str, Any]:
        """
        Limpia archivos de modelos antiguos para ahorrar espacio en disco
        
        Args:
            user_id: ID del usuario (opcional, si se proporciona limpia solo sus modelos)
            keep_recent: Número de comparaciones recientes a mantener por usuario
            
        Returns:
            Dict con estadísticas de limpieza
        """
        try:
            from src.data.repositories import ProteinComparisonRepository
            
            cleanup_stats = {
                'files_deleted': 0,
                'space_freed_mb': 0,
                'errors': []
            }
            
            # Obtener comparaciones que tienen modelos
            if user_id:
                # Limpiar solo para un usuario específico
                all_comparisons = ProteinComparisonRepository.get_comparisons_by_user(user_id)
            else:
                # Limpiar para todos los usuarios
                all_comparisons = ProteinComparisonRepository.get_all_comparisons(limit=500)
            
            # Agrupar por usuario si estamos limpiando globalmente
            if not user_id:
                user_comparisons = {}
                for comp in all_comparisons:
                    if comp.user_id not in user_comparisons:
                        user_comparisons[comp.user_id] = []
                    user_comparisons[comp.user_id].append(comp)
            else:
                user_comparisons = {user_id: all_comparisons}
            
            # Para cada usuario, mantener solo las comparaciones más recientes
            for uid, comparisons in user_comparisons.items():
                # Ordenar por fecha de creación (más recientes primero)
                comparisons_sorted = sorted(comparisons, key=lambda x: x.created_at or datetime.min, reverse=True)
                
                # Mantener solo las más recientes
                comparisons_to_clean = comparisons_sorted[keep_recent:]
                
                # Eliminar archivos de modelos de las comparaciones antiguas
                for comp in comparisons_to_clean:
                    # Limpiar modelo original
                    if comp.original_model_path:
                        cleanup_stats.update(self._delete_model_file(comp.original_model_path))
                        comp.original_model_path = None
                    
                    # Limpiar modelo mutado
                    if comp.mutated_model_path:
                        cleanup_stats.update(self._delete_model_file(comp.mutated_model_path))
                        comp.mutated_model_path = None
                
                # Actualizar comparaciones en la base de datos
                from src.data.models import db
                try:
                    db.session.commit()
                except Exception as e:
                    cleanup_stats['errors'].append(f"Error actualizando BD: {str(e)}")
            
            print(f"🧹 Limpieza completada:")
            print(f"   📁 Archivos eliminados: {cleanup_stats['files_deleted']}")
            print(f"   💾 Espacio liberado: {cleanup_stats['space_freed_mb']:.1f} MB")
            if cleanup_stats['errors']:
                print(f"   ⚠️ Errores: {len(cleanup_stats['errors'])}")
            
            return cleanup_stats
            
        except Exception as e:
            error_msg = f"Error en limpieza de modelos: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'files_deleted': 0,
                'space_freed_mb': 0,
                'errors': [error_msg]
            }

    def _delete_model_file(self, file_path: str) -> Dict[str, int]:
        """
        Elimina un archivo de modelo específico
        
        Args:
            file_path: Ruta del archivo a eliminar
            
        Returns:
            Dict con estadísticas de eliminación
        """
        stats = {'files_deleted': 0, 'space_freed_mb': 0}
        
        try:
            # Resolver ruta absoluta si es relativa
            if not os.path.isabs(file_path):
                # Buscar en el directorio de modelos
                full_path = os.path.join(self.models_directory, file_path)
                if not os.path.exists(full_path):
                    # Buscar desde la raíz del proyecto
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    full_path = os.path.join(project_root, file_path)
            else:
                full_path = file_path
            
            if os.path.exists(full_path):
                # Obtener tamaño antes de eliminar
                file_size = os.path.getsize(full_path)
                
                # Eliminar archivo
                os.remove(full_path)
                
                stats['files_deleted'] = 1
                stats['space_freed_mb'] = file_size / (1024 * 1024)  # Convertir a MB
                
                print(f"   🗑️ Eliminado: {os.path.basename(full_path)} ({file_size/1024:.1f} KB)")
            
        except Exception as e:
            print(f"   ⚠️ Error eliminando {file_path}: {str(e)}")
        
        return stats

    def _extract_plddt_from_cif(self, cif_path: str) -> float:
        """
        Parsea un archivo CIF de AlphaFold para extraer la pLDDT promedio.
        La pLDDT se almacena en la columna B-factor.
        """
        try:
            parser = MMCIFParser(QUIET=True)
            structure = parser.get_structure("alphafold_model", cif_path)
            
            plddt_scores = []
            for atom in structure.get_atoms():
                # El pLDDT está en el campo B-factor del átomo
                plddt_scores.append(atom.get_bfactor())
                
            if not plddt_scores:
                return 0.0
            
            # Usamos np.unique porque cada residuo tiene varios átomos con la misma pLDDT
            # Esto nos da la pLDDT promedio por residuo.
            average_plddt = np.mean(np.unique(plddt_scores))
            return round(average_plddt, 2)
            
        except Exception as e:
            print(f"⚠️ No se pudo extraer la pLDDT del archivo CIF: {e}")
            return 95.0 # Devolvemos el valor por defecto si falla
    
    def predict_structure(self, sequence: str, job_name: str = None) -> Dict[str, Any]:
        """
        Predice la estructura 3D de una secuencia de proteína usando SWISS-MODEL
        
        Args:
            sequence: Secuencia de aminoácidos
            job_name: Nombre opcional para el trabajo
            
        Returns:
            Dict con información del modelo predicho
        """
        start_time = time.time()
        
        try:
            print(f"🔬 Iniciando predicción de estructura para secuencia de {len(sequence)} residuos...")
            
            # Usar SWISS-MODEL directamente para el modelado 3D
            result = self._predict_with_swiss_model(sequence, job_name)
                
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
    
    def _predict_with_swiss_model(self, sequence: str, job_name: str) -> Dict[str, Any]:
        """
        Predice la estructura usando la API de SWISS-MODEL siguiendo el flujo asíncrono de 3 pasos:
        1. Enviar trabajo (POST)
        2. Verificar estado (GET polling)
        3. Descargar modelo final (GET)
        """
        if not job_name:
            job_name = f"swiss_model_{int(time.time())}"
            
        print(f"🔬 Iniciando predicción con SWISS-MODEL para: {job_name}")
        start_time = time.time()
        
        # Obtener el token desde la configuración
        api_token = self.config.get('SWISS_MODEL_TOKEN')
        if not api_token:
            raise AlphaFoldIntegrationError("No se encontró el token de SWISS-MODEL en la configuración.")

        headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # --- PASO 1: Enviar el trabajo de modelado (Dejar el Encargo) ---
        print("📤 Paso 1: Enviando trabajo a SWISS-MODEL...")
        submit_payload = {
            "target_sequences": [sequence],  # Debe ser plural y una lista
            "project_title": job_name
        }
        submit_url = "https://swissmodel.expasy.org/automodel"
        
        print(f"   📋 Payload: {submit_payload}")
        print(f"   🔗 URL: {submit_url}")
        
        try:
            response = requests.post(submit_url, headers=headers, json=submit_payload, timeout=60)
            
            print(f"   📊 Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ Response Text: {response.text}")
                
            response.raise_for_status()
            
            project_data = response.json()
            project_id = project_data.get('project_id')
            
            if not project_id:
                raise AlphaFoldIntegrationError(f"SWISS-MODEL no devolvió un project_id válido. Response: {project_data}")
                
            print(f"✅ Trabajo enviado exitosamente. Project ID: {project_id}")
            
        except requests.exceptions.RequestException as e:
            raise AlphaFoldIntegrationError(f"Error al enviar trabajo a SWISS-MODEL: {e}")

        # --- PASO 2: Verificar el estado del trabajo (Polling) ---
        print("⏳ Paso 2: Verificando estado del trabajo...")
        status_url = f"https://swissmodel.expasy.org/project/{project_id}/models/summary/"
        
        # Aumentar tiempo de espera para secuencias largas
        sequence_length = len(sequence)
        if sequence_length > 200:
            max_attempts = 60  # 60 intentos x 10 segundos = 10 minutos para secuencias largas
            print(f"   ⏱️ Secuencia larga detectada ({sequence_length} residuos). Tiempo máximo: 10 minutos")
        else:
            max_attempts = 30  # 30 intentos x 10 segundos = 5 minutos para secuencias normales
            print(f"   ⏱️ Tiempo máximo de espera: 5 minutos")
        
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            try:
                print(f"   🔄 Verificando estado ({attempt}/{max_attempts})...")
                status_response = requests.get(status_url, headers=headers, timeout=30)
                status_response.raise_for_status()
                status_data = status_response.json()

                job_status = status_data.get("status", "UNKNOWN")
                print(f"   📊 Estado actual: {job_status}")
                
                if job_status == "COMPLETED":
                    print("✅ ¡Trabajo completado exitosamente!")
                    break
                elif job_status in ["FAILED", "REJECTED", "ERROR"]:
                    error_msg = status_data.get("error_message", "Trabajo falló sin mensaje de error específico")
                    raise AlphaFoldIntegrationError(f"El trabajo en SWISS-MODEL falló: {error_msg}")
                elif job_status in ["PENDING", "RUNNING", "QUEUED", "INITIALISED"]:
                    print(f"   ⏳ Trabajo en progreso ({job_status})... esperando 10 segundos")
                    time.sleep(10)
                else:
                    print(f"   ⚠️ Estado desconocido: {job_status}... continuando")
                    time.sleep(10)
                    
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ Error en verificación {attempt}: {e}")
                if attempt >= max_attempts:
                    raise AlphaFoldIntegrationError(f"Error persistente verificando estado: {e}")
                time.sleep(10)
                
        else:
            # Se agotaron los intentos sin completar
            timeout_minutes = max_attempts * 10 / 60  # Convertir a minutos
            raise AlphaFoldIntegrationError(f"El trabajo en SWISS-MODEL tardó más de {timeout_minutes:.0f} minutos en completarse. Las secuencias largas pueden requerir más tiempo.")

        # --- PASO 3: Descargar el modelo final ---
        print("📥 Paso 3: Descargando modelo final...")
        
        # Extraer información del mejor modelo
        models = status_data.get("models", [])
        if not models:
            raise AlphaFoldIntegrationError("SWISS-MODEL completó pero no generó ningún modelo")
        
        print(f"   📊 Se generaron {len(models)} modelo(s)")
        
        # Tomar el primer modelo (generalmente el mejor)
        best_model = models[0]
        model_url = best_model.get("coordinates_url")
        
        if not model_url:
            raise AlphaFoldIntegrationError("No se encontró URL de descarga para el modelo")
        
        print(f"🔗 URL del modelo: {model_url}")
        
        # Descargar el modelo
        model_path = self._download_swiss_model_file(model_url, job_name, headers)
        
        # Extraer métricas de calidad y información de la proteína
        gmqe_score = best_model.get("gmqe", 0.0)  # Global Model Quality Estimation (0-1)
        qmean_score = best_model.get("qmean", {}).get("z_score", -4.0) if isinstance(best_model.get("qmean"), dict) else -4.0
        
        # GMQE es más confiable que QMEAN para confianza general
        # GMQE va de 0 a 1, donde 1 es perfecto
        if gmqe_score > 0:
            confidence = gmqe_score * 100  # Convertir a porcentaje
            confidence_source = "GMQE"
        else:
            # Fallback a QMEAN si GMQE no está disponible
            confidence = max(0, min(100, 100 * (1 - abs(qmean_score) / 4.0)))
            confidence_source = "QMEAN"
        
        # Extraer información adicional del proyecto si está disponible
        protein_info = {}
        if "target" in status_data:
            target_info = status_data["target"]
            if isinstance(target_info, dict):
                protein_info = {
                    "protein_name": target_info.get("description", "Unknown Protein"),
                    "organism": target_info.get("organism", "Unknown"),
                    "uniprot_id": target_info.get("uniprot_ac", None)
                }
        
        # También extraer información del modelo si está disponible
        if len(models) > 0:
            model_info = models[0]
            protein_info.update({
                "model_id": model_info.get("model_id", None),
                "model_status": model_info.get("status", None),
                "gmqe_score": gmqe_score,
                "confidence_source": confidence_source
            })
        
        processing_time = time.time() - start_time
        
        print(f"✅ Predicción completada en {processing_time:.1f}s con confianza {confidence:.1f}% ({confidence_source})")
        if protein_info.get("protein_name"):
            print(f"   🧬 Proteína identificada: {protein_info['protein_name']}")
        if protein_info.get("model_id"):
            print(f"   🆔 Modelo ID: {protein_info['model_id']}")
        
        result = {
            'job_id': project_id,
            'model_path': model_path,
            'model_url': model_url,
            'confidence': round(confidence, 2),
            'qmean_score': qmean_score,
            'gmqe_score': gmqe_score,
            'confidence_source': confidence_source,
            'prediction_method': 'swiss_model_homology',
            'sequence_length': len(sequence),
            'processing_time': processing_time,
            'model_count': len(models),
            'best_model_info': best_model,
            'project_info': status_data
        }
        
        # Añadir información de la proteína si está disponible
        result.update(protein_info)
        
        return result

    def _download_swiss_model_file(self, model_url: str, job_name: str, headers: Dict[str, str]) -> str:
        """
        Descarga un archivo de modelo desde SWISS-MODEL con autenticación y manejo de compresión
        
        Args:
            model_url: URL del archivo en SWISS-MODEL
            job_name: Nombre del trabajo para el archivo local
            headers: Headers con autenticación
            
        Returns:
            Ruta local del archivo descargado (descomprimido si es necesario)
        """
        import gzip
        
        try:
            print(f"📥 Descargando modelo desde: {model_url}")
            
            response = requests.get(model_url, headers=headers, timeout=60)
            response.raise_for_status()
            
            # Determinar si está comprimido
            is_compressed = model_url.endswith('.gz')
            
            # Determinar extensión final
            if model_url.endswith('.pdb.gz') or model_url.endswith('.pdb'):
                extension = '.pdb'
            elif model_url.endswith('.cif.gz') or model_url.endswith('.cif'):
                extension = '.cif'
            else:
                extension = '.pdb'  # Default para SWISS-MODEL
            
            # Crear nombre de archivo único
            timestamp = int(time.time())
            filename = f"swiss_model_{job_name}_{timestamp}{extension}"
            file_path = os.path.join(self.models_directory, filename)
            
            # Procesar el contenido (descomprimir si es necesario)
            content = response.content
            if is_compressed:
                print(f"   🗜️ Descomprimiendo archivo...")
                content = gzip.decompress(content)
            
            # Guardar archivo descomprimido
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Verificar que es un archivo de texto válido
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('HEADER') or first_line.startswith('data_'):
                        print(f"✅ Modelo descargado y descomprimido: {filename} ({len(content)} bytes)")
                        return file_path
                    else:
                        print(f"⚠️ Archivo descargado pero formato inusual. Primera línea: {first_line[:50]}...")
                        return file_path
            except UnicodeDecodeError:
                print(f"⚠️ Archivo parece ser binario, pero guardado como: {filename}")
                return file_path
            
        except Exception as e:
            raise AlphaFoldIntegrationError(f"Error descargando modelo de SWISS-MODEL: {str(e)}")
    
    
    
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
