"""
Servicio de integración con SwissModel
Maneja la comunicación con la API de SwissModel y el procesamiento de modelos 3D
"""
import os
import json
import gzip
import time
import requests
import tempfile
import numpy as np
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime
from pathlib import Path
from Bio.Blast import NCBIWWW, NCBIXML
import re
from .sequence_service import SequenceValidator
from Bio.PDB import MMCIFParser, PDBParser, Superimposer, ShrakeRupley
from Bio.PDB.Polypeptide import is_aa
import io
from .consensus_model import ConsensusModelBuilder
from .mutation_scoring import MutationDescriptor, MutationEnvironment, MutationScorer
from .mutation_report import build_mutation_report

class SwissModelIntegrationError(Exception):
    """Excepción personalizada para errores de integración con SwissModel"""
    pass

class SwissModelService:
    """
    Servicio para integración con SwissModel
    Soporta la API web y SWISS-MODEL para predicciones
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el servicio de SwissModel
        
        Args:
            config: Configuración con endpoints y credenciales
        """
        self.config = config
        self.api_endpoint = config.get('SWISSMODEL_API_ENDPOINT', 'https://swissmodel.expasy.org/')
        self.models_directory = config.get('MODELS_DIRECTORY', 'models/swissmodel')
        self.timeout = config.get('API_TIMEOUT', 300)  # 5 minutos
        
        # Crear directorio de modelos si no existe
        Path(self.models_directory).mkdir(parents=True, exist_ok=True)

        self.consensus_builder = ConsensusModelBuilder(
            max_templates=config.get('SWISSMODEL_CONSENSUS_TEMPLATES', 3)
        )
        self.mutation_scorer = MutationScorer()
        self.structure_parser = PDBParser(QUIET=True)

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
        Parsea un archivo CIF de SwissModel para extraer la pLDDT promedio.
        La pLDDT se almacena en la columna B-factor.
        """
        try:
            parser = MMCIFParser(QUIET=True)
            structure = parser.get_structure("swissmodel_structure", cif_path)
            
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
    
    def predict_structure(self, sequence: str, job_name: str = None, return_all_models: bool = False) -> Dict[str, Any]:
        """
        Predice la estructura 3D de una secuencia de proteína usando SWISS-MODEL
        
        Args:
            sequence: Secuencia de aminoácidos
            job_name: Nombre opcional para el trabajo
            return_all_models: Si True, devuelve todos los modelos generados, no solo el mejor
            
        Returns:
            Dict con información del modelo predicho
        """
        start_time = time.time()
        clean_sequence = sequence.strip()
        
        try:
            print(f"🔬 Iniciando predicción de estructura para secuencia de {len(clean_sequence)} residuos...")
            print(f"   📄 Secuencia: {clean_sequence[:50]}{'...' if len(clean_sequence) > 50 else ''}")
            print(f"   🎯 Modo: {'MÚLTIPLES MODELOS' if return_all_models else 'MEJOR MODELO'}")
            
            # Validar longitud mínima requerida por SWISS-MODEL
            if len(clean_sequence) < 30:
                print(f"   ❌ ERROR: Secuencia demasiado corta ({len(clean_sequence)} < 30 residuos)")
                raise SwissModelIntegrationError(
                    f"La secuencia debe tener al menos 30 residuos para usar SWISS-MODEL. "
                    f"Secuencia actual: {len(clean_sequence)} residuos."
                )
            
            # Usar SWISS-MODEL directamente para el modelado 3D
            result = self._predict_with_swiss_model(clean_sequence, job_name, return_all_models)
                
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            return result
            
        except Exception as e:
            raise SwissModelIntegrationError(f"Error en predicción de estructura: {str(e)}")
    
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
                'analysis_method': 'swissmodel_comparison'
            }
            
            return comparison
            
        except Exception as e:
            raise SwissModelIntegrationError(f"Error comparando estructuras: {str(e)}")
    
    def _predict_with_swiss_model(self, sequence: str, job_name: str, return_all_models: bool = False) -> Dict[str, Any]:
        """
        Predice la estructura usando la API de SWISS-MODEL siguiendo el flujo asíncrono de 3 pasos:
        1. Enviar trabajo (POST)
        2. Verificar estado (GET polling)
        3. Descargar modelo final (GET)
        """
        sequence = sequence.strip()
        if not job_name:
            job_name = f"swiss_model_{int(time.time())}"
            
        print(f"🔬 Iniciando predicción con SWISS-MODEL para: {job_name}")
        start_time = time.time()
        
        # Obtener el token desde la configuración
        api_token = self.config.get('SWISS_MODEL_TOKEN')
        if not api_token:
            raise SwissModelIntegrationError("No se encontró el token de SWISS-MODEL en la configuración.")

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
                raise SwissModelIntegrationError(f"SWISS-MODEL no devolvió un project_id válido. Response: {project_data}")
                
            print(f"✅ Trabajo enviado exitosamente. Project ID: {project_id}")
            
        except requests.exceptions.RequestException as e:
            raise SwissModelIntegrationError(f"Error al enviar trabajo a SWISS-MODEL: {e}")

        # --- PASO 2: Verificar el estado del trabajo (Polling) ---
        print("⏳ Paso 2: Verificando estado del trabajo...")
        status_url = f"https://swissmodel.expasy.org/project/{project_id}/models/summary/"
        
        # Aumentar tiempo de espera para secuencias largas
        sequence_length = len(sequence)
        if sequence_length > 200:
            max_attempts = 120  # 120 intentos x 10 segundos = 20 minutos para secuencias largas
            print(f"   ⏱️ Secuencia larga detectada ({sequence_length} residuos). Tiempo máximo: 20 minutos")
        else:
            max_attempts = 90  # 90 intentos x 10 segundos = 15 minutos para secuencias normales
            print(f"   ⏱️ Tiempo máximo de espera: 15 minutos")
        
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
                    raise SwissModelIntegrationError(f"El trabajo en SWISS-MODEL falló: {error_msg}")
                elif job_status in ["PENDING", "RUNNING", "QUEUED", "INITIALISED"]:
                    print(f"   ⏳ Trabajo en progreso ({job_status})... esperando 10 segundos")
                    time.sleep(10)
                else:
                    print(f"   ⚠️ Estado desconocido: {job_status}... continuando")
                    time.sleep(10)
                    
            except requests.exceptions.RequestException as e:
                print(f"   ⚠️ Error en verificación {attempt}: {e}")
                if attempt >= max_attempts:
                    raise SwissModelIntegrationError(f"Error persistente verificando estado: {e}")
                time.sleep(10)
                
        else:
            # Se agotaron los intentos sin completar
            timeout_minutes = max_attempts * 10 / 60  # Convertir a minutos
            raise SwissModelIntegrationError(f"El trabajo en SWISS-MODEL tardó más de {timeout_minutes:.0f} minutos en completarse. Las secuencias largas pueden requerir más tiempo.")

        # --- PASO 3: Descargar el/los modelo(s) final(es) ---
        print("📥 Paso 3: Descargando modelo(s) final(es)...")
        
        # Debug: Mostrar la estructura completa de status_data
        print(f"   🔍 DEBUG - Claves en status_data: {list(status_data.keys())}")
        print(f"   🔍 DEBUG - status_data completo: {json.dumps(status_data, indent=2)[:1000]}...")
        
        # Extraer información de los modelos
        models = status_data.get("models", [])
        
        # Si no hay modelos en el summary, intentar obtenerlos del endpoint de modelos directos
        if not models:
            print(f"   ⚠️ No se encontraron modelos en summary. Intentando endpoint alternativo...")
            try:
                # Intentar obtener modelos directamente
                models_url = f"https://swissmodel.expasy.org/project/{project_id}/models/"
                models_response = requests.get(models_url, headers=headers, timeout=30)
                models_response.raise_for_status()
                models_data = models_response.json()
                
                if isinstance(models_data, list):
                    models = models_data
                    print(f"   ✅ Encontrados {len(models)} modelo(s) desde endpoint de modelos")
                elif isinstance(models_data, dict) and "models" in models_data:
                    models = models_data["models"]
                    print(f"   ✅ Encontrados {len(models)} modelo(s) desde endpoint de modelos")
            except Exception as e:
                print(f"   ⚠️ Error al obtener modelos desde endpoint alternativo: {e}")
            
        if not models:
            print(f"   ❌ ERROR: SWISS-MODEL no pudo generar modelos para esta secuencia.")
            print(f"   ℹ️ Posibles razones:")
            print(f"      • La secuencia es demasiado corta ({len(sequence)} aa)")
            print(f"      • No se encontraron plantillas homólogas en PDB")
            print(f"      • La secuencia no tiene similitud con proteínas conocidas")
            print(f"   💡 Sugerencia: Use AlphaFold para secuencias sin homólogos conocidos")
            raise SwissModelIntegrationError(
                f"SWISS-MODEL no pudo generar modelos para esta secuencia de {len(sequence)} aminoácidos. "
                f"No se encontraron plantillas homólogas en la base de datos PDB. "
                f"Considere usar AlphaFold para predicciones ab initio."
            )
        
        print(f"   📊 Se generaron {len(models)} modelo(s)")
        
        # Debug: Mostrar información de cada modelo
        for i, model in enumerate(models):
            print(f"   📋 Modelo {i+1}: GMQE={model.get('gmqe', 'N/A')}, QMEAN={model.get('qmean', {}).get('z_score', 'N/A') if isinstance(model.get('qmean'), dict) else 'N/A'}")
        
        # Determinar cuáles modelos procesar
        models_to_process = models if return_all_models else [models[0]]
        print(f"   🎯 Procesando {len(models_to_process)} modelo(s) ({'TODOS' if return_all_models else 'SOLO MEJOR'})")
        
        results = []
        best_result = None
        best_gmqe = -1
        
        for i, model in enumerate(models_to_process):
            model_suffix = f"_{i+1}" if return_all_models and len(models_to_process) > 1 else ""
            current_job_name = f"{job_name}{model_suffix}"
            
            model_url = model.get("coordinates_url")
            if not model_url:
                print(f"   ⚠️ Modelo {i+1}: No se encontró URL de descarga, saltando")
                continue
            
            print(f"🔗 URL del modelo {i+1}: {model_url}")
            
            # Descargar el modelo
            model_path = self._download_swiss_model_file(model_url, current_job_name, headers)
            
            # Extraer métricas de calidad
            gmqe_score = model.get("gmqe", 0.0)
            qmean_score = model.get("qmean", {}).get("z_score", -4.0) if isinstance(model.get("qmean"), dict) else -4.0
            
            if gmqe_score > 0:
                confidence = gmqe_score * 100
                confidence_source = "GMQE"
            else:
                confidence = max(0, min(100, 100 * (1 - abs(qmean_score) / 4.0)))
                confidence_source = "QMEAN"
            
            # Información de la proteína (solo del primer modelo para evitar duplicados)
            protein_info = {}
            if i == 0 and "target" in status_data:
                target_info = status_data["target"]
                if isinstance(target_info, dict):
                    protein_info = {
                        "protein_name": target_info.get("description", "Unknown Protein"),
                        "organism": target_info.get("organism", "Unknown"),
                        "uniprot_id": target_info.get("uniprot_ac", None)
                    }
            
            model_info = {
                "model_id": model.get("model_id", None),
                "model_status": model.get("status", None),
                "gmqe_score": gmqe_score,
                "confidence_source": confidence_source
            }
            protein_info.update(model_info)
            
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
                'model_count': len(models),
                'model_info': model,
                'project_info': status_data
            }
            result.update(protein_info)
            
            results.append(result)
            
            # Track best model
            if gmqe_score > best_gmqe:
                best_gmqe = gmqe_score
                best_result = result
        
        if not results:
            raise SwissModelIntegrationError("No se pudo descargar ningún modelo válido")
        
        processing_time = time.time() - start_time
        print(f"✅ Predicción completada en {processing_time:.1f}s")
        if best_result and best_result.get("protein_name"):
            print(f"   🧬 Proteína identificada: {best_result['protein_name']}")
        if best_result and best_result.get("model_id"):
            print(f"   🆔 Mejor modelo ID: {best_result['model_id']}")
        
        # Debug: Mostrar resumen final
        if return_all_models:
            print(f"   📊 RESULTADO FINAL: {len(results)} modelos procesados, mejor GMQE: {best_gmqe:.3f}")
            for i, res in enumerate(results):
                print(f"      Modelo {i+1}: GMQE={res.get('gmqe_score', 'N/A'):.3f}, Confianza={res.get('confidence', 'N/A')}%")
        else:
            print(f"   📊 RESULTADO FINAL: 1 modelo, GMQE={best_result.get('gmqe_score', 'N/A'):.3f}, Confianza={best_result.get('confidence', 'N/A')}%")
        
        # Devolver resultado según el modo
        consensus_payload = None
        if return_all_models and results:
            consensus_filename = os.path.join(
                self.models_directory, f"{job_name}_consensus.pdb"
            )
            try:
                consensus_result = self.consensus_builder.build(
                    results,
                    consensus_filename,
                    sequence_length=len(sequence),
                )
                consensus_payload = {
                    'consensus_path': consensus_result.path,
                    'coverage': consensus_result.coverage,
                    'residue_sasa': consensus_result.residue_sasa,
                    'weights_used': consensus_result.weights_used,
                    'template_count': consensus_result.template_count,
                    'residue_conservation': consensus_result.residue_conservation,
                    'residue_consensus': consensus_result.residue_consensus,
                }
                print(
                    f"   🤝 Modelo consenso generado ({consensus_result.template_count} plantillas, cobertura {consensus_result.coverage:.2f})"
                )
            except Exception as exc:
                print(f"   ⚠️ No se pudo construir el modelo consenso: {exc}")

        if return_all_models:
            return {
                'models': results,
                'best_model': best_result,
                'consensus_model': consensus_payload,
                'processing_time': processing_time
            }
        else:
            best_result['processing_time'] = processing_time
            if consensus_payload:
                best_result['consensus_model'] = consensus_payload
            return best_result

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
                    first_line_upper = first_line.upper()
                    valid_prefixes = ('HEADER', 'TITLE', 'REMARK', 'DATA_', 'ATOM')
                    if not first_line or first_line_upper.startswith(valid_prefixes):
                        print(f"✅ Modelo descargado y descomprimido: {filename} ({len(content)} bytes)")
                    else:
                        print(f"⚠️ Archivo descargado pero formato inusual. Primera línea: {first_line[:50]}...")
                    return file_path
            except UnicodeDecodeError:
                print(f"⚠️ Archivo parece ser binario, pero guardado como: {filename}")
                return file_path
            
        except Exception as e:
            raise SwissModelIntegrationError(f"Error descargando modelo de SWISS-MODEL: {str(e)}")
    
    
    
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

    def apply_mutations_to_pdb(self, pdb_path: str, mutations: List[Tuple[int, str, str]], output_path: str) -> str:
        """
        Aplica mutaciones a un archivo PDB cambiando los nombres de residuos
        
        Args:
            pdb_path: Ruta al archivo PDB original
            mutations: Lista de tuplas (posición_1based, aa_original, aa_mutado)
            output_path: Ruta donde guardar el PDB mutado
            
        Returns:
            Ruta del archivo PDB mutado
        """
        from Bio.PDB import PDBParser, PDBIO
        from Bio.PDB.Polypeptide import three_to_one, one_to_three
        
        # Diccionario de conversión de 1-letter a 3-letter
        aa_dict = {
            'A': 'ALA', 'R': 'ARG', 'N': 'ASN', 'D': 'ASP', 'C': 'CYS',
            'Q': 'GLN', 'E': 'GLU', 'G': 'GLY', 'H': 'HIS', 'I': 'ILE',
            'L': 'LEU', 'K': 'LYS', 'M': 'MET', 'F': 'PHE', 'P': 'PRO',
            'S': 'SER', 'T': 'THR', 'W': 'TRP', 'Y': 'TYR', 'V': 'VAL'
        }
        
        try:
            # Parsear el PDB
            parser = PDBParser(QUIET=True)
            structure = parser.get_structure("protein", pdb_path)
            
            # Aplicar mutaciones
            for model in structure:
                for chain in model:
                    for residue in chain:
                        res_id = residue.get_id()
                        pos = res_id[1]  # Posición del residuo (1-based)
                        
                        # Buscar si esta posición tiene mutación
                        for mut_pos, orig_aa, mut_aa in mutations:
                            if pos == mut_pos:
                                # Verificar que el aa original coincida
                                current_aa = three_to_one(residue.get_resname())
                                if current_aa == orig_aa:
                                    # Cambiar el resname
                                    new_resname = aa_dict.get(mut_aa.upper())
                                    if new_resname:
                                        residue.resname = new_resname
                                        print(f"   🔄 Mutación aplicada: {orig_aa}{pos} -> {mut_aa}")
                                    else:
                                        print(f"   ⚠️ Aminoácido mutado desconocido: {mut_aa}")
                                else:
                                    print(f"   ⚠️ AA original no coincide en pos {pos}: esperado {orig_aa}, encontrado {current_aa}")
                                break
            
            # Guardar el PDB mutado
            io = PDBIO()
            io.set_structure(structure)
            io.save(output_path)
            
            print(f"   💾 PDB mutado guardado en: {output_path}")
            return output_path
            
        except Exception as e:
            raise SwissModelIntegrationError(f"Error aplicando mutaciones al PDB: {str(e)}")

    def apply_mutations_with_model_combination(self, sorted_models: List[Dict[str, Any]], mutations: List[Tuple[int, str, str]], output_path: str) -> str:
        """
        Aplica mutaciones combinando partes de diferentes modelos homólogos
        
        Args:
            sorted_models: Lista de modelos ordenados por GMQE descendente
            mutations: Lista de mutaciones [(pos, orig_aa, mut_aa), ...]
            output_path: Ruta donde guardar el PDB combinado
            
        Returns:
            Ruta del archivo PDB combinado
        """
        import time
        from Bio.PDB import PDBParser, PDBIO, Superimposer
        from Bio.PDB.Polypeptide import three_to_one, one_to_three
        
        start_time = time.time()
        
        if not sorted_models:
            raise SwissModelIntegrationError("No hay modelos para combinar")
        
        # Usar el mejor modelo como base
        base_model_path = sorted_models[0]['model_path']
        parser = PDBParser(QUIET=True)
        base_structure = parser.get_structure("base", base_model_path)
        
        # Para cada mutación, intentar usar un modelo alternativo si está disponible
        mutation_positions = {pos for pos, _, _ in mutations}
        
        # Si hay más de un modelo, usar el segundo mejor para posiciones mutadas
        if len(sorted_models) > 1:
            alt_model_path = sorted_models[1]['model_path']  # Segundo mejor modelo
            alt_structure = parser.get_structure("alt", alt_model_path)
            
            # Superponer estructuras para alinear
            superimposer = Superimposer()
            base_atoms = list(base_structure.get_atoms())
            alt_atoms = list(alt_structure.get_atoms())
            
            # Solo superponer si tienen el mismo número de átomos
            if len(base_atoms) == len(alt_atoms):
                superimposer.set_atoms(base_atoms, alt_atoms)
                superimposer.apply(alt_structure.get_atoms())
                print(f"   🔄 Modelos superpuestos (RMSD: {superimposer.rms:.2f} Å)")
                
                # Para posiciones mutadas, copiar residuos del modelo alternativo
                print(f"   🔄 Iniciando copia de coordenadas para {len(mutation_positions)} posiciones mutadas...")
                copied_positions = 0
                for model in base_structure:
                    for chain in model:
                        for residue in chain:
                            # Check timeout (max 30 seconds for this step)
                            if time.time() - start_time > 30:
                                print(f"   ⚠️ Timeout en copia de coordenadas, continuando...")
                                break
                                
                            res_id = residue.get_id()
                            pos = res_id[1]
                            
                            if pos in mutation_positions:
                                # Buscar el residuo correspondiente en el modelo alternativo
                                for alt_model in alt_structure:
                                    for alt_chain in alt_model:
                                        for alt_residue in alt_chain:
                                            alt_res_id = alt_residue.get_id()
                                            if alt_res_id[1] == pos:
                                                # Copiar coordenadas del residuo alternativo
                                                for atom in residue:
                                                    try:
                                                        alt_atom = alt_residue[atom.get_name()]
                                                        atom.set_coord(alt_atom.get_coord())
                                                    except KeyError:
                                                        # El átomo no existe en el residuo alternativo, continuar
                                                        continue
                                                copied_positions += 1
                                                print(f"   🔄 Copiadas coordenadas de residuo {pos} del modelo alternativo ({copied_positions}/{len(mutation_positions)})")
                                                break
                                        else:
                                            continue
                                        break
                                    else:
                                        continue
                                    break
        
        print(f"   🔄 Aplicando cambios de aminoácidos para {len(mutations)} mutaciones...")
        # Aplicar cambios de aminoácidos
        aa_dict = {
            'A': 'ALA', 'R': 'ARG', 'N': 'ASN', 'D': 'ASP', 'C': 'CYS',
            'Q': 'GLN', 'E': 'GLU', 'G': 'GLY', 'H': 'HIS', 'I': 'ILE',
            'L': 'LEU', 'K': 'LYS', 'M': 'MET', 'F': 'PHE', 'P': 'PRO',
            'S': 'SER', 'T': 'THR', 'W': 'TRP', 'Y': 'TYR', 'V': 'VAL'
        }
        
        mutations_applied = 0
        for model in base_structure:
            for chain in model:
                for residue in chain:
                    # Check timeout (max 60 seconds total for mutation application)
                    if time.time() - start_time > 60:
                        print(f"   ⚠️ Timeout en aplicación de mutaciones, continuando...")
                        break
                        
                    res_id = residue.get_id()
                    pos = res_id[1]
                    
                    for mut_pos, orig_aa, mut_aa in mutations:
                        if pos == mut_pos:
                            current_aa = three_to_one(residue.get_resname())
                            if current_aa == orig_aa:
                                new_resname = aa_dict.get(mut_aa.upper())
                                if new_resname:
                                    # Cambiar el resname manteniendo conectividad
                                    old_resname = residue.resname
                                    residue.resname = new_resname
                                    
                                    # Para mutaciones críticas, mantener solo átomos backbone
                                    if self._is_critical_mutation(orig_aa, mut_aa):
                                        self._preserve_backbone_atoms_only(residue, mut_aa)
                                    
                                    mutations_applied += 1
                                    print(f"   🔄 Mutación aplicada: {orig_aa}{pos} -> {mut_aa} ({old_resname} -> {new_resname}) [{mutations_applied}/{len(mutations)}]")
                                else:
                                    print(f"   ⚠️ Aminoácido mutado desconocido: {mut_aa}")
                            else:
                                print(f"   ⚠️ AA original no coincide en pos {pos}: esperado {orig_aa}, encontrado {current_aa}")
                            break
        
        # Guardar el PDB combinado
        print(f"   💾 Guardando estructura combinada...")
        io = PDBIO()
        io.set_structure(base_structure)
        io.save(output_path)
        
        # Validar y limpiar el archivo PDB generado
        self._validate_and_clean_pdb(output_path)
        
        print(f"   💾 PDB combinado guardado y validado en: {output_path}")
        return output_path

    def _is_critical_mutation(self, orig_aa: str, mut_aa: str) -> bool:
        """
        Determina si una mutación es crítica (cambio drástico de propiedades)
        que podría requerir preservar solo el backbone
        """
        # Cambios de tamaño dramáticos o carga
        critical_pairs = [
            ('W', 'G'), ('F', 'G'), ('Y', 'G'),  # Grande a pequeño
            ('K', 'D'), ('R', 'E'), ('D', 'K'),  # Cambio de carga
            ('P', 'G'), ('G', 'P'),  # Proline changes
            ('C', 'A'), ('M', 'A')   # Loss of special properties
        ]
        return (orig_aa, mut_aa) in critical_pairs or (mut_aa, orig_aa) in critical_pairs

    def _preserve_backbone_atoms_only(self, residue, mut_aa: str):
        """
        Para mutaciones críticas, mantiene solo átomos del backbone
        para prevenir distorsiones estructurales
        """
        backbone_atoms = ['N', 'CA', 'C', 'O']
        atoms_to_remove = []
        
        for atom in residue:
            if atom.get_name() not in backbone_atoms:
                atoms_to_remove.append(atom.get_id())
        
        # Remover átomos de cadena lateral para evitar conflictos
        for atom_id in atoms_to_remove:
            residue.detach_child(atom_id)
        
        print(f"       🔧 Cadena lateral removida para mutación crítica -> {mut_aa}")

    def _validate_and_clean_pdb(self, pdb_path: str):
        """
        Valida y limpia el archivo PDB para asegurar conectividad proper
        """
        try:
            # Leer y reescribir el PDB para limpiar posibles inconsistencias
            with open(pdb_path, 'r') as f:
                lines = f.readlines()
            
            # Filtrar líneas válidas y mantener conectividad
            cleaned_lines = []
            for line in lines:
                # Mantener HEADER, ATOM, TER, END records esenciales
                if line.startswith(('HEADER', 'ATOM  ', 'HETATM', 'TER   ', 'END   ', 'CONECT')):
                    cleaned_lines.append(line)
            
            # Reescribir archivo limpio
            with open(pdb_path, 'w') as f:
                f.writelines(cleaned_lines)
            
            print(f"   ✅ Archivo PDB validado y limpiado: {len(cleaned_lines)} líneas")
            
        except Exception as e:
            print(f"   ⚠️ Warning: No se pudo limpiar el PDB: {e}")

    def predict_mutated_from_original_models(self, original_result: Dict[str, Any], mutations: List[Tuple[int, str, str]], job_name: str) -> Dict[str, Any]:
        """
        Predice la estructura mutada aplicando mutaciones a los modelos de la secuencia original
        
        Args:
            original_result: Resultado de predicción de la secuencia original (con return_all_models=True)
            mutations: Lista de mutaciones [(pos, orig_aa, mut_aa), ...]
            job_name: Nombre para el trabajo mutado
            
        Returns:
            Dict con información del modelo mutado
        """
        if 'models' not in original_result:
            raise SwissModelIntegrationError("El resultado original no contiene modelos múltiples")
        
        models = original_result['models']
        if not models:
            raise SwissModelIntegrationError("No hay modelos disponibles en el resultado original")
        
        # Ordenar modelos por GMQE descendente
        sorted_models = sorted(models, key=lambda x: x.get('gmqe_score', 0), reverse=True)
        best_model = sorted_models[0]
        original_pdb_path = best_model['model_path']
        
        # Crear nombre para el PDB mutado
        mutated_pdb_path = original_pdb_path.replace('.pdb', '_mutated.pdb')
        if job_name:
            mutated_pdb_path = os.path.join(self.models_directory, f"{job_name}_mutated.pdb")
        
        # Aplicar mutaciones con combinación de modelos
        print(f"🔬 Aplicando {len(mutations)} mutación(es) combinando modelos...")
        mutated_pdb_path = self.apply_mutations_with_model_combination(sorted_models, mutations, mutated_pdb_path)
        
        # Copiar información del modelo original, ajustando para la mutada
        mutated_result = best_model.copy()
        mutated_result.update({
            'model_path': mutated_pdb_path,
            'prediction_method': 'mutation_from_homology_models_combined',
            'mutations_applied': mutations,
            'original_model_path': original_pdb_path,
            'confidence': max(0, best_model.get('confidence', 0) - 5),  # Menos reducción por combinación
            'confidence_source': f"{best_model.get('confidence_source', 'Unknown')} (combined models)"
        })
        
        print(f"✅ Modelo mutado generado con confianza {mutated_result['confidence']:.1f}%")
        return mutated_result

    def predict_mutated_structure_advanced(
        self,
        original_result: Dict[str, Any],
        mutations: List[Tuple[int, str, str]],
        job_name: str,
        mutated_sequence: str,
    ) -> Dict[str, Any]:
        """Construye la estructura mutada usando plantillas consenso y puntuaciones fisicoquímicas."""

        if not mutations:
            raise SwissModelIntegrationError("Se requieren mutaciones para generar un modelo mutado")

        if 'models' not in original_result or not original_result['models']:
            raise SwissModelIntegrationError("El resultado original no contiene plantillas suficientes")

        descriptors = [
            MutationDescriptor(position=pos, original=orig, mutated=mut)
            for pos, orig, mut in mutations
        ]

        mutated_job_name = job_name or f"mutated_{int(time.time())}"
        mutated_templates = self.predict_structure(
            mutated_sequence,
            f"{mutated_job_name}_consensus",
            return_all_models=True,
        )

        mutated_models = mutated_templates.get('models', [])
        if not mutated_models:
            raise SwissModelIntegrationError("SWISS-MODEL no devolvió plantillas para la secuencia mutada")

        mutated_consensus = mutated_templates.get('consensus_model') or {}
        mutated_consensus_path = mutated_consensus.get('consensus_path') or mutated_models[0]['model_path']

        original_consensus = original_result.get('consensus_model') or {}
        original_consensus_path = original_consensus.get('consensus_path')
        if not original_consensus_path:
            best_original = original_result.get('best_model') or original_result['models'][0]
            original_consensus_path = best_original['model_path']

        residue_sasa = mutated_consensus.get('residue_sasa', {})
        residue_conservation = mutated_consensus.get('residue_conservation', {})
        environments = {
            descriptor.position: MutationEnvironment(
                sasa=residue_sasa.get(descriptor.position),
                is_surface=(
                    residue_sasa.get(descriptor.position) is not None
                    and residue_sasa.get(descriptor.position) >= 80.0
                ),
                conservation=residue_conservation.get(descriptor.position),
            )
            for descriptor in descriptors
        }

        mutation_scores = self.mutation_scorer.score_mutations(descriptors, environments)
        structural_metrics = self._compute_structural_metrics(
            original_consensus_path,
            mutated_consensus_path,
            descriptors,
        )
        structural_metrics['coverage'] = mutated_consensus.get('coverage', 1.0)

        base_confidence_candidates = [model.get('confidence', 0.0) for model in mutated_models if model.get('confidence') is not None]
        if base_confidence_candidates:
            base_confidence = float(np.mean(base_confidence_candidates))
        else:
            base_confidence = float(mutated_models[0].get('confidence', 0.0))

        confidence_penalty = self._derive_confidence_penalty(
            mutation_scores,
            structural_metrics,
        )
        confidence = max(0.0, base_confidence - confidence_penalty)

        mutated_result = mutated_models[0].copy()
        mutated_result.update({
            'model_path': mutated_consensus_path,
            'consensus_model': mutated_consensus,
            'prediction_method': 'consensus_mutation_pipeline_v2',
            'mutations_applied': [descriptor.notation() for descriptor in descriptors],
            'original_model_path': original_consensus_path,
            'confidence': round(confidence, 2),
            'confidence_source': f"Consensus penalty {confidence_penalty:.2f}",
            'physicochemical_scores': mutation_scores,
            'structural_metrics': structural_metrics,
            'templates_used': len(mutated_models),
            'processing_time': mutated_templates.get('processing_time'),
        })

        reports_dir = Path(self.models_directory) / "reports"
        report_path = build_mutation_report(
            reports_dir / f"{mutated_job_name}_mutation_report.html",
            descriptors,
            mutation_scores,
            structural_metrics,
            mutated_consensus,
            base_confidence,
            confidence,
        )
        mutated_result['mutation_report_path'] = str(report_path)

        print(
            "✅ Predicción mutada avanzada completada",
            f"— Confianza ajustada: {mutated_result['confidence']:.1f}%",
        )
        print(
            f"   📊 ΔΔG media: {mutation_scores['aggregate']['mean_ddg']:.2f} kcal/mol (impacto {mutation_scores['aggregate']['impact_level']})"
        )
        if structural_metrics.get('global_rmsd') is not None:
            print(
                f"   📐 RMSD global: {structural_metrics['global_rmsd']:.2f} Å | Cobertura: {structural_metrics['coverage']:.2f}"
            )

        return mutated_result

    def _compute_structural_metrics(
        self,
        original_path: str,
        mutated_path: str,
        descriptors: List[MutationDescriptor],
    ) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {
            'global_rmsd': None,
            'local_rmsd': {},
            'rmsd_max': None,
            'sasa_original': None,
            'sasa_mutated': None,
            'sasa_delta': None,
            'aligned_residues': 0,
            'sequence_overlap': None,
            'coverage': None,
        }

        try:
            original_structure = self.structure_parser.get_structure('original_consensus', original_path)
            mutated_structure = self.structure_parser.get_structure('mutated_consensus', mutated_path)
        except Exception as exc:
            metrics['error'] = f"No se pudieron cargar las estructuras para análisis: {exc}"
            return metrics

        ca_original, ca_mutated = self._collect_ca_atoms(original_structure, mutated_structure)
        if ca_original and len(ca_original) == len(ca_mutated) and len(ca_original) >= 3:
            super_imposer = Superimposer()
            super_imposer.set_atoms(ca_original, ca_mutated)
            super_imposer.apply(mutated_structure.get_atoms())
            metrics['global_rmsd'] = round(super_imposer.rms, 3)
            metrics['aligned_residues'] = len(ca_original)

        sr = ShrakeRupley()
        sr.compute(original_structure, level='R')
        sr.compute(mutated_structure, level='R')
        metrics['sasa_original'] = round(self._sum_residue_sasa(original_structure), 2)
        metrics['sasa_mutated'] = round(self._sum_residue_sasa(mutated_structure), 2)
        metrics['sasa_delta'] = round(metrics['sasa_mutated'] - metrics['sasa_original'], 2)

        local_values = []
        for descriptor in descriptors:
            atoms_original, atoms_mutated = self._collect_local_atoms(
                original_structure, mutated_structure, descriptor.position
            )
            if atoms_original and len(atoms_original) == len(atoms_mutated) and len(atoms_original) >= 3:
                local_super = Superimposer()
                local_super.set_atoms(atoms_original, atoms_mutated)
                local_rmsd = round(local_super.rms, 3)
                metrics['local_rmsd'][descriptor.notation()] = local_rmsd
                local_values.append(local_rmsd)
            else:
                metrics['local_rmsd'][descriptor.notation()] = None

        if local_values:
            metrics['rmsd_max'] = max(local_values)

        total_original = sum(1 for residue in original_structure.get_residues() if is_aa(residue, standard=True))
        total_mutated = sum(1 for residue in mutated_structure.get_residues() if is_aa(residue, standard=True))
        overlap_denominator = max(1, min(total_original, total_mutated))
        overlap = metrics['aligned_residues'] / overlap_denominator if overlap_denominator else 0.0
        metrics['sequence_overlap'] = round(overlap, 3)
        metrics['coverage'] = metrics['sequence_overlap']

        return metrics

    def _collect_ca_atoms(self, structure_a, structure_b) -> Tuple[List[Any], List[Any]]:
        atoms_a: List[Any] = []
        atoms_b: List[Any] = []
        for chain_a, chain_b in zip(structure_a.get_chains(), structure_b.get_chains()):
            residues_a = [residue for residue in chain_a if is_aa(residue, standard=True)]
            residues_b = [residue for residue in chain_b if is_aa(residue, standard=True)]
            length = min(len(residues_a), len(residues_b))
            for idx in range(length):
                residue_a = residues_a[idx]
                residue_b = residues_b[idx]
                if 'CA' in residue_a and 'CA' in residue_b:
                    atoms_a.append(residue_a['CA'])
                    atoms_b.append(residue_b['CA'])
        return atoms_a, atoms_b

    def _collect_local_atoms(
        self,
        structure_a,
        structure_b,
        position: int,
        window: int = 4,
    ) -> Tuple[List[Any], List[Any]]:
        atoms_a: List[Any] = []
        atoms_b: List[Any] = []

        for chain_a, chain_b in zip(structure_a.get_chains(), structure_b.get_chains()):
            residues_a = [residue for residue in chain_a if is_aa(residue, standard=True)]
            residues_b = [residue for residue in chain_b if is_aa(residue, standard=True)]
            length = min(len(residues_a), len(residues_b))
            for idx in range(length):
                residue_a = residues_a[idx]
                residue_b = residues_b[idx]
                if abs(residue_a.id[1] - position) <= window:
                    for atom_name in ('N', 'CA', 'C', 'O', 'CB'):
                        if atom_name in residue_a and atom_name in residue_b:
                            atoms_a.append(residue_a[atom_name])
                            atoms_b.append(residue_b[atom_name])

        return atoms_a, atoms_b

    def _sum_residue_sasa(self, structure) -> float:
        total = 0.0
        for residue in structure.get_residues():
            if is_aa(residue, standard=True):
                total += getattr(residue, 'sasa', 0.0)
        return total

    def _derive_confidence_penalty(
        self,
        mutation_scores: Dict[str, Any],
        structural_metrics: Dict[str, Any],
    ) -> float:
        aggregate = mutation_scores.get('aggregate', {})
        mean_ddg = aggregate.get('mean_ddg', 0.0)
        max_ddg = aggregate.get('max_ddg', 0.0)
        penalty = 0.0

        penalty += max(0.0, mean_ddg) * 5.5
        penalty += max(0.0, max_ddg - 0.5) * 2.5

        global_rmsd = structural_metrics.get('global_rmsd')
        if global_rmsd is not None:
            penalty += max(0.0, global_rmsd - 0.6) * 12.0

        coverage = structural_metrics.get('coverage', 1.0)
        penalty += max(0.0, 1.0 - coverage) * 35.0

        local_peak = structural_metrics.get('rmsd_max')
        if local_peak is not None:
            penalty += max(0.0, local_peak - 0.8) * 5.0

        return round(min(45.0, penalty), 2)


def create_swissmodel_service(config: Dict[str, Any]) -> SwissModelService:
    """
    Factory function para crear instancia del servicio SwissModel
    
    Args:
        config: Configuración de la aplicación
        
    Returns:
        Instancia configurada de SwissModelService
    """
    return SwissModelService(config)
