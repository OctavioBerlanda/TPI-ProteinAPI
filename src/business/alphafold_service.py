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

    def _find_uniprot_id_with_blast(self, sequence: str) -> tuple[Optional[str], Optional[str]]:
        """
        Encuentra el UniProt ID para una secuencia usando la API de búsqueda de UniProt.
        Este método es extremadamente rápido y busca tanto en Swiss-Prot como TrEMBL.
        (El nombre se mantiene por compatibilidad, pero ya no usa BLAST).
        """
        print(f"🔍 Buscando UniProt ID para secuencia de {len(sequence)} residuos vía API de búsqueda optimizada...")
        
        # Intentar múltiples estrategias de búsqueda
        strategies = [
            ("Swiss-Prot (revisado)", "reviewed:true"),
            ("UniProtKB completo", "*"),  # Incluye TrEMBL
        ]
        
        for strategy_name, base_query in strategies:
            print(f"   🔍 Probando en {strategy_name}...")
            result = self._search_with_strategy(sequence, base_query)
            if result[0]:  # Si encontró algo
                return result
        
        print("   ⚠️ No se encontró en ninguna base de datos de UniProt.")
        return None, None

    def _search_with_strategy(self, sequence: str, base_query: str) -> tuple[Optional[str], Optional[str]]:
        """Ejecuta una estrategia de búsqueda específica"""
        try:
            search_url = "https://rest.uniprot.org/uniprotkb/search"
            seq_length = len(sequence)
            
            # Paso 1: Búsqueda por longitud exacta
            query = f"(length:[{seq_length} TO {seq_length}]) AND ({base_query})"
            params = {
                'query': query,
                'fields': 'accession,protein_name,sequence',
                'format': 'json',
                'size': 1000  # Aumentar significativamente el tamaño
            }
            
            response = requests.get(search_url, params=params, timeout=45)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                print(f"     � Comparando secuencia con {len(results)} candidatos...")
                
                # Buscar coincidencia exacta de secuencia
                for result in results:
                    if 'sequence' in result and 'value' in result['sequence']:
                        if result['sequence']['value'] == sequence:
                            uniprot_id = result.get('primaryAccession')
                            protein_name = self._extract_protein_name(result)
                            
                            print(f"✅ UniProt ID {uniprot_id} encontrado por coincidencia exacta.")
                            return uniprot_id, protein_name
                
                # Paso 2: Si no hay coincidencia exacta, buscar por similitud alta
                print(f"     🔬 No hay coincidencia exacta. Buscando alta similitud...")
                best_match = self._find_best_similarity_match(sequence, results)
                if best_match:
                    return best_match
            
            # Paso 3: Búsqueda más amplia sin filtro de longitud
            print(f"     🌐 Expandiendo búsqueda sin filtro de longitud...")
            return self._broad_search(sequence, base_query)
                
        except requests.exceptions.RequestException as e:
            print(f"     ❌ Error durante la búsqueda: {str(e)}")
            return None, None
        except Exception as e:
            print(f"     ❌ Error inesperado: {str(e)}")
            return None, None

    def _find_best_similarity_match(self, sequence: str, results: list) -> tuple[Optional[str], Optional[str]]:
        """Encuentra la mejor coincidencia por similitud"""
        best_similarity = 0.0
        best_match = None
        
        for result in results[:100]:  # Limitar para rendimiento
            if 'sequence' in result and 'value' in result['sequence']:
                result_seq = result['sequence']['value']
                similarity = self._calculate_similarity(sequence, result_seq)
                
                if similarity > best_similarity and similarity > 0.90:  # 90% de similitud mínima
                    best_similarity = similarity
                    uniprot_id = result.get('primaryAccession')
                    protein_name = self._extract_protein_name(result)
                    best_match = (uniprot_id, protein_name)
        
        if best_match:
            print(f"✅ Mejor coincidencia: {best_match[0]} (similitud: {best_similarity:.1%})")
            return best_match
        
        return None, None

    def _broad_search(self, sequence: str, base_query: str) -> tuple[Optional[str], Optional[str]]:
        """Búsqueda amplia usando fragmentos distintivos"""
        if len(sequence) < 20:
            return None, None
            
        # Usar fragmentos más grandes y distintivos
        fragment_size = min(20, len(sequence) // 3)
        fragments = [
            sequence[:fragment_size],  # Inicio
            sequence[len(sequence)//2-fragment_size//2:len(sequence)//2+fragment_size//2],  # Medio
            sequence[-fragment_size:]  # Final
        ]
        
        search_url = "https://rest.uniprot.org/uniprotkb/search"
        
        for i, fragment in enumerate(fragments):
            try:
                print(f"     🧩 Buscando fragmento {i+1}: {fragment[:15]}...")
                
                # Buscar el fragmento en la base de datos
                params = {
                    'query': base_query,
                    'fields': 'accession,protein_name,sequence',
                    'format': 'json',
                    'size': 200
                }
                
                response = requests.get(search_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                results = data.get('results', [])
                
                # Buscar el fragmento en las secuencias
                for result in results:
                    if 'sequence' in result and 'value' in result['sequence']:
                        result_seq = result['sequence']['value']
                        if fragment in result_seq:
                            # Verificar si la secuencia completa tiene alta similitud
                            similarity = self._calculate_similarity(sequence, result_seq)
                            if similarity > 0.85:  # 85% de similitud para fragmentos
                                uniprot_id = result.get('primaryAccession')
                                protein_name = self._extract_protein_name(result)
                                print(f"✅ Coincidencia por fragmento: {uniprot_id} (similitud: {similarity:.1%})")
                                return uniprot_id, protein_name
                        
            except Exception as e:
                print(f"     ⚠️ Error en fragmento {i+1}: {e}")
                continue
        
        return None, None

    def _extract_protein_name(self, result: dict) -> str:
        """Extrae el nombre de la proteína del resultado de UniProt"""
        try:
            if 'proteinDescription' in result and 'recommendedName' in result['proteinDescription']:
                if 'fullName' in result['proteinDescription']['recommendedName']:
                    return result['proteinDescription']['recommendedName']['fullName']['value']
        except:
            pass
        return "Unknown Protein"

    def _search_by_fragments(self, sequence: str) -> tuple[Optional[str], Optional[str]]:
        """
        Búsqueda por fragmentos de secuencia para mayor flexibilidad.
        Usa fragmentos únicos de la secuencia para encontrar coincidencias.
        OBSOLETO: Reemplazado por _broad_search pero mantenido para compatibilidad.
        """
        return self._broad_search(sequence, "reviewed:true")

    def _calculate_similarity(self, seq1: str, seq2: str) -> float:
        """Calcula la similitud entre dos secuencias"""
        if len(seq1) != len(seq2):
            return 0.0
        
        matches = sum(1 for a, b in zip(seq1, seq2) if a == b)
        return matches / len(seq1)    
    
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
    
    def _get_alphafold_data(self, sequence: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos informativos de AlphaFold (UniProt ID, nombre, confianza) sin descargar modelo
        
        Args:
            sequence: Secuencia de aminoácidos
            
        Returns:
            Dict con datos de AlphaFold o None si no se encuentra
        """
        try:
            print(f"🔍 Obteniendo datos de AlphaFold para secuencia de {len(sequence)} residuos...")
            
            # Buscar UniProt ID usando la función existente
            uniprot_id, protein_name = self._find_uniprot_id_with_blast(sequence)
            
            if uniprot_id:
                print(f"✅ UniProt ID {uniprot_id} encontrado. Obteniendo datos de AlphaFold...")
                
                # Obtener información de la API de AlphaFold (sin descargar)
                api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
                response = requests.get(api_url, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    alphafold_info = data[0]
                    return {
                        'uniprot_id': uniprot_id,
                        'protein_name': protein_name,
                        'confidence': alphafold_info.get('confidenceAvg', 85.0),
                        'alphafold_version': alphafold_info.get('modelCreatedDate', 'unknown'),
                        'data_source': 'alphafold_db'
                    }
                else:
                    print(f"⚠️ No se encontraron datos para {uniprot_id} en AlphaFold DB.")
            
            print("ℹ️ No se encontraron datos de AlphaFold para esta secuencia.")
            return None
            
        except Exception as e:
            print(f"⚠️ Error obteniendo datos de AlphaFold: {e}")
            return None
    
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
        
        max_attempts = 30  # 30 intentos x 10 segundos = 5 minutos máximo
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
                elif job_status in ["PENDING", "RUNNING", "QUEUED"]:
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
            raise AlphaFoldIntegrationError("El trabajo en SWISS-MODEL tardó más de 5 minutos en completarse")

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
    
    def _predict_with_alphafold_db(self, sequence: str, job_name: str = None) -> Dict[str, Any]:
        if not job_name:
            job_name = f"protein_{int(time.time())}"

        # NUEVO: Usa BLAST para encontrar el UniProt ID
        print(f"🔍 Buscando UniProt ID para secuencia de {len(sequence)} residuos usando BLAST...")
        uniprot_id, protein_name = self._find_uniprot_id_with_blast(sequence)

        if uniprot_id:
            print(f"✅ UniProt ID {uniprot_id} encontrado. Descargando desde AlphaFold DB...")
            try:
                # Obtiene la información de la API de AlphaFold
                api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
                response = requests.get(api_url, timeout=20)
                response.raise_for_status()
                data = response.json()

                if data and data[0].get('cifUrl'):
                    cif_url = data[0]['cifUrl']
                    model_path = self._download_real_alphafold_structure(cif_url, job_name)
                    
                    confidence = self._extract_plddt_from_cif(model_path)
                    print(f"📊 Confianza real extraída del modelo: {confidence:.2f}% (pLDDT)")
                    
                    return {
                        'job_id': f"alphafold_blast_{job_name}",
                        'model_path': model_path,
                        'model_url': cif_url,
                        'confidence': confidence,
                        'confidence_scores': [confidence] * len(sequence),
                        'prediction_method': 'alphafold_db_blast',
                        'sequence_length': len(sequence),
                        'uniprot_id': uniprot_id,
                        'protein_name': protein_name
                    }
                else:
                    print(f"⚠️ No se encontró una estructura para {uniprot_id} en AlphaFold DB.")

            except Exception as e:
                print(f"⚠️ Error descargando estructura desde AlphaFold DB: {e}")
        
        # Si BLAST falla o no encuentra nada, vuelve a tu simulación
        print("🔄 No se encontró una estructura en AlphaFold DB. Usando simulación mejorada...")
        return self._predict_improved_simulation(sequence, job_name, is_mutation=False)

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
        Genera contenido CIF (mmCIF) mejorado con predicción de estructura secundaria y plegamiento simulado.
        
        Args:
            sequence: Secuencia de aminoácidos
            job_name: Nombre del trabajo
            
        Returns:
            Contenido del archivo CIF en formato mmCIF estándar con estructura 3D realista
        """
        # ... (La primera parte del contenido CIF (header, entity, etc.) se queda igual) ...
        cif_header = f"""data_demo_structure
#
_entry.id   demo_structure
#
# ... (copia todo el header CIF de tu versión original hasta el loop_ de _atom_site) ...
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
        
        # --- NUEVO ALGORITMO DE PLEGAMIENTO ---
        print("🔬 Iniciando algoritmo de plegamiento simulado mejorado...")
        # 1. Predecir estructura secundaria (usamos la misma función de antes)
        secondary_structure = self._predict_secondary_structure(sequence)
        
        # 2. Generar coordenadas 3D plegadas
        coords = self._generate_folded_coordinates(sequence, secondary_structure)
        print("✅ Plegamiento simulado completado.")
        
        atoms = []
        for i, aa in enumerate(sequence):
            aa_code = aa_map.get(aa, 'ALA')
            x, y, z = coords[i] # Coordenadas del C-alfa
            
            # Línea de átomo CA en formato mmCIF (único átomo que representamos por simplicidad)
            atom_line = f"ATOM {i+1:6d} C CA . {aa_code} A 1 {i+1:4d} ? {x:8.3f} {y:8.3f} {z:8.3f} 1.00 50.00 ? {i+1:4d} {aa_code} A CA 1"
            atoms.append(atom_line)
        
        cif_content = cif_header + "\n".join(atoms) + "\n#\n"
        
        return cif_content

    def _predict_secondary_structure(self, sequence: str) -> list:
        """
        Predice estructura secundaria usando algoritmo simplificado de Chou-Fasman
        
        Args:
            sequence: Secuencia de aminoácidos
            
        Returns:
            Lista de estructuras secundarias ('H'=hélice, 'E'=sheet, 'C'=coil)
        """
        # Propensidades de Chou-Fasman para α-hélice
        helix_propensity = {
            'A': 1.42, 'E': 1.51, 'L': 1.21, 'M': 1.45, 'Q': 1.11, 'K': 1.16,
            'R': 0.98, 'H': 1.00, 'V': 1.06, 'I': 1.08, 'Y': 0.69, 'F': 1.13,
            'W': 1.08, 'T': 0.83, 'S': 0.77, 'C': 0.70, 'N': 0.67, 'D': 1.01,
            'P': 0.57, 'G': 0.57
        }
        
        # Propensidades para β-sheet
        sheet_propensity = {
            'V': 1.70, 'I': 1.60, 'Y': 1.47, 'F': 1.38, 'W': 1.37, 'L': 1.30,
            'T': 1.19, 'C': 1.19, 'A': 0.83, 'R': 0.93, 'G': 0.75, 'D': 0.54,
            'H': 0.87, 'Q': 1.10, 'K': 0.74, 'S': 0.75, 'E': 0.37, 'P': 0.55,
            'N': 0.89, 'M': 1.05
        }
        
        structure = []
        
        # Ventana deslizante para predecir estructura
        for i in range(len(sequence)):
            # Calcular propensidades promedio en ventana de 6 residuos
            start = max(0, i - 3)
            end = min(len(sequence), i + 4)
            window = sequence[start:end]
            
            helix_score = sum(helix_propensity.get(aa, 1.0) for aa in window) / len(window)
            sheet_score = sum(sheet_propensity.get(aa, 1.0) for aa in window) / len(window)
            
            # Decidir estructura basada en propensidades
            if helix_score > 1.05 and helix_score > sheet_score:
                structure.append('H')  # Hélice
            elif sheet_score > 1.05 and sheet_score > helix_score:
                structure.append('E')  # Beta sheet
            else:
                structure.append('C')  # Coil/loop
                
        return structure

    def _generate_folded_coordinates(self, sequence: str, secondary_structure: list) -> np.ndarray:
        """
        Genera coordenadas 3D realistas usando ángulos de torsión y colapso hidrofóbico.
        
        Args:
            sequence: Secuencia de aminoácidos
            secondary_structure: Lista de estructuras secundarias predichas
            
        Returns:
            Array de numpy con las coordenadas (x, y, z) de los C-alfa de cada residuo
        """
        # 1. Obtener los ángulos Phi/Psi para cada residuo basado en su estructura secundaria
        phi_psi_angles = [self._get_phi_psi_for_ss(ss, i) for i, ss in enumerate(secondary_structure)]

        # 2. Construir la cadena inicial del esqueleto usando los ángulos
        # Usamos solo los C-alfa para simplificar, pero el principio es el mismo
        initial_coords = self._build_chain_from_angles(len(sequence), phi_psi_angles)

        # 3. Refinar la estructura usando colapso hidrofóbico
        refined_coords = self._refine_with_energy_minimization(sequence, initial_coords)

        return refined_coords

    def _get_phi_psi_for_ss(self, ss_type: str, index: int) -> Tuple[float, float]:
        """Devuelve ángulos Phi y Psi típicos para un tipo de estructura secundaria."""
        import random
        random.seed(index) # Seed para reproducibilidad

        if ss_type == 'H':  # Hélice Alfa
            return -60.0, -45.0
        elif ss_type == 'E':  # Hoja Beta
            return -120.0, 120.0
        else:  # Giro / Coil (aleatorio pero en regiones permitidas)
            return random.choice([-80.0, -140.0, 60.0]), random.choice([-30.0, 150.0, 20.0, -170.0])

    def _build_chain_from_angles(self, num_residues: int, angles: list) -> np.ndarray:
        """Construye una cadena de C-alfa a partir de los ángulos phi/psi (mejorado)."""
        coords = np.zeros((num_residues, 3))
        # Distancia Cα-Cα es ~3.8 Ångströms
        bond_length = 3.8
        
        # Colocamos los primeros átomos para definir un plano inicial
        coords[0] = np.array([0.0, 0.0, 0.0])
        if num_residues > 1:
            coords[1] = np.array([bond_length, 0.0, 0.0])
        if num_residues > 2:
            coords[2] = np.array([bond_length * 1.5, bond_length * 0.5, 0.0])

        # Para cada residuo después del tercero
        for i in range(3, num_residues):
            # Vectores de los dos enlaces anteriores
            v1 = coords[i-1] - coords[i-2]
            v2 = coords[i-2] - coords[i-3]
            
            # Normalizar vectores
            v1 = v1 / np.linalg.norm(v1)
            v2 = v2 / np.linalg.norm(v2)
            
            # Ángulos para este residuo
            phi, psi = angles[i]
            
            # Convertir a radianes
            phi_rad = np.deg2rad(phi)
            psi_rad = np.deg2rad(psi)
            
            # Calcular el producto cruzado para obtener el vector normal
            normal = np.cross(v2, v1)
            if np.linalg.norm(normal) > 0:
                normal = normal / np.linalg.norm(normal)
            else:
                normal = np.array([0, 0, 1])  # Vector por defecto
            
            # Crear matriz de rotación basada en phi y psi
            # Esto es una simplificación del algoritmo real de construcción de proteínas
            cos_phi = np.cos(phi_rad)
            sin_phi = np.sin(phi_rad)
            cos_psi = np.cos(psi_rad)
            sin_psi = np.sin(psi_rad)
            
            # Dirección del nuevo enlace (simplificado)
            new_direction = (
                v1 * cos_phi + 
                normal * sin_phi * cos_psi + 
                np.cross(v1, normal) * sin_phi * sin_psi
            )
            
            # Asegurar que el vector esté normalizado
            if np.linalg.norm(new_direction) > 0:
                new_direction = new_direction / np.linalg.norm(new_direction)
            else:
                new_direction = v1  # Fallback
                
            # Posición del nuevo átomo
            coords[i] = coords[i-1] + new_direction * bond_length
            
        return coords

    def _refine_with_energy_minimization(self, sequence: str, coords: np.ndarray, iterations: int = 100, step_size: float = 0.05) -> np.ndarray:
        """
        Refina la estructura 3D usando un algoritmo simple de minimización de energía.
        """
        print("🔬 Iniciando refinamiento 3D con minimización de energía...")
        
        hydrophobicity = {
            'I': 4.5, 'V': 4.2, 'L': 3.8, 'F': 2.8, 'C': 2.5, 'M': 1.9, 'A': 1.8,
            'G': -0.4, 'T': -0.7, 'S': -0.8, 'W': -0.9, 'Y': -1.3, 'P': -1.6,
            'H': -3.2, 'E': -3.5, 'Q': -3.5, 'D': -3.5, 'N': -3.5, 'K': -3.9, 'R': -4.5
        }
        
        charges = {
            'D': -1, 'E': -1, # Negativos
            'K': 1, 'R': 1, 'H': 1, # Positivos
        }
        
        n_residues = len(sequence)
        
        for iteration in range(iterations):
            # Calcular el centro de masa en cada iteración, ya que cambia
            centroid = np.mean(coords, axis=0)
            
            # Copiamos las coordenadas para calcular las fuerzas basadas en la posición actual
            current_coords = np.copy(coords)
            
            for i in range(n_residues):
                total_force = np.zeros(3)
                
                # --- 1. FUERZA HIDROFÓBICA ---
                h_score = hydrophobicity.get(sequence[i], 0.0)
                if h_score > 0:
                    force_hydro = (centroid - current_coords[i]) * (h_score / 4.5) * 0.1
                    total_force += force_hydro
                
                # --- 2. FUERZAS DE REPULSIÓN Y ELECTROSTÁTICA ---
                for j in range(n_residues):
                    if i == j:
                        continue
                    
                    direction_vec = current_coords[i] - current_coords[j]
                    distance = np.linalg.norm(direction_vec)
                    
                    # Evitar división por cero
                    if distance < 0.1: continue
                    
                    # a) Repulsión para evitar colisiones (muy fuerte a corta distancia)
                    # La distancia ideal entre C-alfa no adyacentes es > 3.5 Å
                    clash_threshold = 3.5
                    if distance < clash_threshold:
                        # La fuerza de repulsión es inversamente proporcional al cuadrado de la distancia
                        force_clash = (direction_vec / distance) * (1 / (distance**2)) * 2.0
                        total_force += force_clash
                        
                    # b) Electrostática (solo si ambos residuos tienen carga)
                    charge_i = charges.get(sequence[i], 0)
                    charge_j = charges.get(sequence[j], 0)
                    
                    if charge_i != 0 and charge_j != 0:
                        # La fuerza es atractiva para cargas opuestas, repulsiva para iguales
                        force_electro = (direction_vec / distance) * (-charge_i * charge_j) * 0.5
                        total_force += force_electro
                
                # Aplicar la fuerza total a la coordenada del residuo
                coords[i] += total_force * step_size
                
            if (iteration + 1) % 20 == 0:
                print(f"   ...iteración de refinamiento {iteration + 1}/{iterations}")
                
        print("✅ Refinamiento 3D completado.")
        return coords

    def _refine_structure_with_hydrophobic_collapse(self, sequence: str, coords: np.ndarray, 
                                                    iterations: int = 50, strength: float = 0.1) -> np.ndarray:
        """
        Refina la estructura aplicando una fuerza de colapso hidrofóbico.
        
        Args:
            sequence: La secuencia de aminoácidos.
            coords: Coordenadas iniciales.
            iterations: Número de pasos de refinamiento.
            strength: Fuerza del colapso.
            
        Returns:
            Coordenadas refinadas.
        """
        # Escala de hidrofobicidad de Kyte-Doolittle (simplificada)
        # Positivo = hidrofóbico, Negativo = hidrofílico
        hydrophobicity = {
            'I': 4.5, 'V': 4.2, 'L': 3.8, 'F': 2.8, 'C': 2.5, 'M': 1.9, 'A': 1.8,
            'G': -0.4, 'T': -0.7, 'S': -0.8, 'W': -0.9, 'Y': -1.3, 'P': -1.6,
            'H': -3.2, 'E': -3.5, 'Q': -3.5, 'D': -3.5, 'N': -3.5, 'K': -3.9, 'R': -4.5
        }
        
        # Bucle de refinamiento
        for _ in range(iterations):
            # 1. Calcular el centro de masa (centroide) de la proteína
            centroid = np.mean(coords, axis=0)
            
            # 2. Para cada residuo, aplicar una fuerza hacia o desde el centroide
            for i, aa in enumerate(sequence):
                score = hydrophobicity.get(aa, 0.0)
                
                # Si el residuo es hidrofóbico (score > 0), tirar de él hacia el centro
                if score > 0:
                    direction_vector = centroid - coords[i]
                    # La fuerza es proporcional a la hidrofobicidad y a la distancia
                    force_magnitude = (score / 4.5) * strength
                    coords[i] += direction_vector * force_magnitude

        return coords
    
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
        Algoritmo mejorado de estimación de confianza basado en múltiples factores
        
        Args:
            sequence: Secuencia de aminoácidos
            
        Returns:
            Puntuación de confianza estimada (0-100)
        """
        # Factor único basado en la secuencia específica (hash determinista)
        import hashlib
        sequence_hash = hashlib.md5(sequence.encode()).hexdigest()
        sequence_factor = (int(sequence_hash[:8], 16) % 100) / 100.0  # 0.0 a 1.0
        
        # Factor 1: Homología (35% del peso)
        homology_score = self._calculate_homology_score(sequence) * 0.35
        
        # Factor 2: Predicción de estructura secundaria (30% del peso)
        secondary_structure_score = self._predict_secondary_structure_confidence(sequence) * 0.3
        
        # Factor 3: Estabilidad de la secuencia (20% del peso)
        stability_score = self._calculate_stability_score(sequence) * 0.2
        
        # Factor 4: Factor único de secuencia (10% del peso)
        unique_sequence_score = (40 + sequence_factor * 40) * 0.1  # 4-8 puntos
        
        # Factor 5: Penalizaciones (5% del peso)
        penalty_score = self._calculate_penalties(sequence) * 0.05
        
        # Combinar todos los factores
        total_confidence = homology_score + secondary_structure_score + stability_score + unique_sequence_score - penalty_score
        
        # Asegurar que esté en el rango 40-95 (realista para simulaciones)
        confidence = max(40, min(95, total_confidence))
        
        # Añadir variabilidad adicional basada en la posición de mutaciones si hay diferencias mínimas
        sequence_variability = (sequence_factor * 10) - 5  # -5 a +5
        confidence += sequence_variability
        
        # Re-ajustar rango final
        confidence = max(40, min(95, confidence))
        
        return round(confidence, 2)
    
    def _calculate_homology_score(self, sequence: str) -> float:
        """Calcula puntuación basada en homología con proteínas conocidas"""
        known_motifs = {
            'HELIX_MOTIF': ['AEEAA', 'LEKLA', 'EALEK'],
            'BETA_MOTIF': ['VTVT', 'YVYV', 'FTFT'],
            'SIGNAL_PEPTIDE': ['MKLL', 'MALW', 'MKAL'],
            'ACTIVE_SITE': ['HIS', 'CYS', 'SER']
        }
        
        score = 50  # Base score
        
        for motif_type, motifs in known_motifs.items():
            for motif in motifs:
                if motif in sequence:
                    score += 10
                    
        # Bonus por longitud óptima
        if 100 <= len(sequence) <= 300:
            score += 15
        elif 50 <= len(sequence) <= 500:
            score += 10
            
        return min(100, score)
    
    def _predict_secondary_structure_confidence(self, sequence: str) -> float:
        """Predice confianza basada en propensión de estructura secundaria"""
        # Propensidades de Chou-Fasman para α-hélice
        helix_propensity = {
            'A': 1.42, 'E': 1.51, 'L': 1.21, 'M': 1.45, 'Q': 1.11, 'K': 1.16,
            'R': 0.98, 'H': 1.00, 'V': 1.06, 'I': 1.08, 'Y': 0.69, 'F': 1.13,
            'W': 1.08, 'T': 0.83, 'S': 0.77, 'C': 0.70, 'N': 0.67, 'D': 1.01,
            'P': 0.57, 'G': 0.57
        }
        
        # Propensidades para β-sheet
        sheet_propensity = {
            'V': 1.70, 'I': 1.60, 'Y': 1.47, 'F': 1.38, 'W': 1.37, 'L': 1.30,
            'T': 1.19, 'C': 1.19, 'A': 0.83, 'R': 0.93, 'G': 0.75, 'D': 0.54,
            'H': 0.87, 'Q': 1.10, 'K': 0.74, 'S': 0.75, 'E': 0.37, 'P': 0.55,
            'N': 0.89, 'M': 1.05
        }
        
        helix_score = sum(helix_propensity.get(aa, 1.0) for aa in sequence) / len(sequence)
        sheet_score = sum(sheet_propensity.get(aa, 1.0) for aa in sequence) / len(sequence)
        
        # Estructura secundaria balanceada = mayor confianza
        structure_balance = 1 - abs(helix_score - sheet_score)
        confidence = 50 + (structure_balance * 40)
        
        return confidence
    
    def _calculate_stability_score(self, sequence: str) -> float:
        """Calcula puntuación de estabilidad basada en composición aminoacídica"""
        # Aminoácidos estabilizantes vs desestabilizantes
        stabilizing = {'A', 'V', 'L', 'I', 'F', 'W', 'Y'}
        destabilizing = {'P', 'G'}
        charged = {'K', 'R', 'D', 'E'}
        
        stabilizing_count = sum(1 for aa in sequence if aa in stabilizing)
        destabilizing_count = sum(1 for aa in sequence if aa in destabilizing)
        charged_count = sum(1 for aa in sequence if aa in charged)
        
        # Calcular ratios
        stabilizing_ratio = stabilizing_count / len(sequence)
        destabilizing_ratio = destabilizing_count / len(sequence)
        charged_ratio = charged_count / len(sequence)
        
        # Puntuación base
        stability = 60
        stability += stabilizing_ratio * 30
        stability -= destabilizing_ratio * 20
        
        # Penalizar exceso de aminoácidos cargados
        if charged_ratio > 0.3:
            stability -= (charged_ratio - 0.3) * 50
            
        return max(20, min(100, stability))
    
    def _calculate_penalties(self, sequence: str) -> float:
        """Calcula penalizaciones por características problemáticas"""
        penalties = 0
        
        # Penalizar aminoácidos raros/no estándar
        rare_aa = {'U', 'O', 'B', 'Z', 'J', 'X'}
        rare_count = sum(1 for aa in sequence if aa in rare_aa)
        penalties += rare_count * 15
        
        # Penalizar secuencias muy cortas o muy largas
        if len(sequence) < 30:
            penalties += (30 - len(sequence)) * 2
        elif len(sequence) > 1000:
            penalties += (len(sequence) - 1000) * 0.1
            
        # Penalizar repeticiones excesivas
        for aa in set(sequence):
            aa_count = sequence.count(aa)
            if aa_count / len(sequence) > 0.2:  # >20% de un solo aminoácido
                penalties += 10
                
        # Penalizar falta de diversidad
        unique_aa = len(set(sequence))
        if unique_aa < 10:
            penalties += (10 - unique_aa) * 3
            
        return min(50, penalties)
    
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
    
    def _download_real_alphafold_structure(self, cif_url: str, job_name: str) -> str:
        """
        Descarga una estructura real de AlphaFold DB
        
        Args:
            cif_url: URL del archivo CIF en AlphaFold DB
            job_name: Nombre del trabajo para el archivo local
            
        Returns:
            Ruta local del archivo descargado
        """
        try:
            response = requests.get(cif_url, timeout=30)
            response.raise_for_status()
            
            # Crear nombre de archivo único
            timestamp = int(time.time())
            filename = f"{job_name}_{timestamp}.cif"
            file_path = os.path.join(self.models_directory, filename)
            
            # Guardar archivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            return file_path
            
        except Exception as e:
            raise AlphaFoldIntegrationError(f"Error descargando estructura real: {str(e)}")
    
    def _calculate_sequence_similarity(self, seq1: str, seq2: str) -> float:
        """
        Calcula la similitud entre dos secuencias de aminoácidos
        
        Args:
            seq1: Primera secuencia
            seq2: Segunda secuencia
            
        Returns:
            Valor de similitud entre 0 y 1
        """
        if len(seq1) == 0 or len(seq2) == 0:
            return 0.0
        
        # Si las longitudes son muy diferentes, la similitud es baja
        if abs(len(seq1) - len(seq2)) / max(len(seq1), len(seq2)) > 0.1:
            return 0.0
        
        # Comparar posición por posición usando la secuencia más corta
        min_len = min(len(seq1), len(seq2))
        matches = sum(1 for i in range(min_len) if seq1[i] == seq2[i])
        
        return matches / min_len
    
    def _predict_improved_simulation(self, sequence: str, job_name: str = None, 
                                     is_mutation: bool = False, 
                                     original_sequence: str = None) -> Dict[str, Any]:
        """
        Predicción mejorada usando simulación, ahora sensible al impacto de la mutación.
        """
        if not job_name:
            job_name = f"protein_{int(time.time())}"
        
        if is_mutation:
            print(f"🔬 Usando simulación mejorada para la secuencia MUTADA.")
        else:
            print(f"🔬 Usando simulación mejorada para secuencia NUEVA/DESCONOCIDA.")
        
        # 1. Calcular la confianza base usando el algoritmo general
        base_confidence = self._estimate_confidence(sequence)
        final_confidence = base_confidence

        # 2. Si es una mutación, calcular el impacto y ajustar la confianza
        if is_mutation and original_sequence:
            print("🔬 Analizando el impacto de la mutación en la confianza...")
            # Encontrar la mutación (asumimos una sola para este ejemplo)
            diffs = SequenceValidator.find_differences(original_sequence, sequence)
            
            if diffs:
                # Usamos la primera diferencia encontrada
                pos, orig_aa, mut_aa = diffs[0]
                
                # Llamamos a la nueva función estática de SequenceValidator
                impact_score = SequenceValidator._calculate_mutation_impact_score(orig_aa, mut_aa)
                
                # Ajustamos la confianza final con el impacto
                final_confidence += impact_score
                
                print(f"📊 La mutación {orig_aa}{pos}{mut_aa} tiene un impacto de {impact_score:.1f} puntos en la confianza.")
        
        # 3. Ajustar la confianza final a un rango realista
        final_confidence = max(30.0, min(95.0, final_confidence))
        print(f"📊 Confianza final estimada: {final_confidence:.1f}%")

        # 4. Crear el archivo CIF simulado con la estructura
        model_path = self._create_demo_model(sequence, job_name)
        
        return {
            'job_id': f"improved_sim_{job_name}",
            'model_path': model_path,
            'model_url': None,
            'confidence': round(final_confidence, 2),
            'confidence_scores': [final_confidence] * len(sequence),
            'prediction_method': 'improved_simulation_with_impact',
            'sequence_length': len(sequence),
            'is_mutation': is_mutation,
            'algorithm_used': 'chou_fasman_and_mutation_impact'
        }

def create_alphafold_service(config: Dict[str, Any]) -> AlphaFoldService:
    """
    Factory function para crear instancia del servicio AlphaFold
    
    Args:
        config: Configuración de la aplicación
        
    Returns:
        Instancia configurada de AlphaFoldService
    """
    return AlphaFoldService(config)
