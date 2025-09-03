from typing import Dict, Any, Optional
from src.business.sequence_service import SequenceComparisonService, SequenceValidationError
from src.business.alphafold_service import AlphaFoldService, AlphaFoldIntegrationError
from src.data.repositories import ProteinComparisonRepository, UserRepository

class ComparisonManager:
    """Gestor principal para las comparaciones de proteínas"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.sequence_service = SequenceComparisonService(max_mutations=2)
        self.alphafold_service = AlphaFoldService(config or {}) if config else None
    
    def create_comparison(self, username: str, email: str, original_sequence: str, 
                         mutated_sequence: str, comparison_name: str = None, 
                         description: str = None) -> Dict[str, Any]:
        """
        Crea una nueva comparación de proteínas
        
        Args:
            username: Nombre del usuario
            email: Email del usuario
            original_sequence: Secuencia original
            mutated_sequence: Secuencia mutada
            comparison_name: Nombre opcional para la comparación
            description: Descripción opcional
            
        Returns:
            Dict con el resultado de la operación
        """
        result = {
            'success': False,
            'comparison_id': None,
            'validation_result': None,
            'message': '',
            'errors': []
        }
        
        try:
            # Validar secuencias
            validation_result = self.sequence_service.validate_and_compare_sequences(
                original_sequence, mutated_sequence
            )
            
            result['validation_result'] = validation_result
            
            if not validation_result['valid']:
                result['errors'] = validation_result['errors']
                result['message'] = "Las secuencias no son válidas"
                return result
            
            # Obtener o crear usuario
            user = UserRepository.get_or_create_user(username, email)
            
            # Crear comparación en la base de datos
            mutations = validation_result['mutations']
            comparison = ProteinComparisonRepository.create_comparison(
                user_id=user.id,
                original_sequence=validation_result['original_sequence'],
                mutated_sequence=validation_result['mutated_sequence'],
                mutation_positions=mutations['positions'],
                mutations_description=mutations['description'],
                comparison_name=comparison_name or f"Comparación {mutations['description']}",
                description=description
            )
            
            result['success'] = True
            result['comparison_id'] = comparison.id
            result['message'] = "Comparación creada exitosamente"
            
        except Exception as e:
            result['errors'].append(f"Error al crear la comparación: {str(e)}")
            result['message'] = "Error interno del servidor"
        
        return result
    
    def get_comparison_details(self, comparison_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene los detalles de una comparación
        
        Args:
            comparison_id: ID de la comparación
            
        Returns:
            Dict con los detalles de la comparación o None si no existe
        """
        comparison = ProteinComparisonRepository.get_comparison_by_id(comparison_id)
        if not comparison:
            return None
        
        # Recrear el análisis de mutaciones para mostrar detalles
        differences = []
        original = comparison.original_sequence
        mutated = comparison.mutated_sequence
        
        for i, (orig_aa, mut_aa) in enumerate(zip(original, mutated)):
            if orig_aa != mut_aa:
                differences.append((i + 1, orig_aa, mut_aa))
        
        from src.business.sequence_service import SequenceValidator
        mutations_summary = SequenceValidator.get_mutation_summary(differences)
        
        return {
            'comparison': comparison.to_dict(),
            'mutations_analysis': mutations_summary,
            'user': {
                'id': comparison.user.id,
                'username': comparison.user.username,
                'email': comparison.user.email
            }
        }
    
    def get_user_comparisons(self, username: str) -> Dict[str, Any]:
        """
        Obtiene todas las comparaciones de un usuario
        
        Args:
            username: Nombre del usuario
            
        Returns:
            Dict con las comparaciones del usuario
        """
        user = UserRepository.get_user_by_username(username)
        if not user:
            return {
                'success': False,
                'message': 'Usuario no encontrado',
                'comparisons': []
            }
        
        comparisons = ProteinComparisonRepository.get_comparisons_by_user(user.id)
        
        return {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'comparisons': [comp.to_dict() for comp in comparisons]
        }
    
    def create_comparison_with_alphafold(self, username: str, email: str, original_sequence: str, 
                                       mutated_sequence: str, comparison_name: str = None, 
                                       description: str = None, enable_alphafold: bool = True) -> Dict[str, Any]:
        """
        Crea una nueva comparación de proteínas con integración AlphaFold
        
        Args:
            username: Nombre del usuario
            email: Email del usuario
            original_sequence: Secuencia original
            mutated_sequence: Secuencia mutada
            comparison_name: Nombre opcional para la comparación
            description: Descripción opcional
            enable_alphafold: Si habilitar predicción con AlphaFold
            
        Returns:
            Dict con el resultado de la operación incluyendo modelos 3D
        """
        result = {
            'success': False,
            'comparison_id': None,
            'errors': [],
            'data': {},
            'alphafold_results': {
                'original': None,
                'mutated': None,
                'comparison': None
            }
        }
        
        try:
            # 1. Validar secuencias usando el flujo existente
            comparison_result = self.create_comparison(
                username, email, original_sequence, mutated_sequence, 
                comparison_name, description
            )
            
            if not comparison_result['success']:
                return comparison_result
            
            comparison_id = comparison_result['comparison_id']
            result['comparison_id'] = comparison_id
            # No intentar acceder a 'data' ya que create_comparison no lo retorna
            result['message'] = comparison_result.get('message', 'Comparación creada')
            
            # 2. Si AlphaFold está habilitado, procesar estructuras 3D
            if enable_alphafold and self.alphafold_service:
                try:
                    result['alphafold_results'] = self._process_alphafold_predictions(
                        comparison_id, original_sequence, mutated_sequence, comparison_name
                    )
                    
                    # Actualizar el estado de la comparación a completada
                    self._update_comparison_alphafold_data(comparison_id, result['alphafold_results'])
                    
                except AlphaFoldIntegrationError as e:
                    result['errors'].append(f"Error en AlphaFold: {str(e)}")
                    # No fallar toda la comparación por errores de AlphaFold
                    
            result['success'] = True
            return result
            
        except Exception as e:
            result['errors'].append(f"Error procesando comparación: {str(e)}")
            return result
    
    def _process_alphafold_predictions(self, comparison_id: int, original_sequence: str, mutated_sequence: str, comparison_name: str = None) -> Dict[str, Any]:
        """
        Procesa las predicciones de AlphaFold para ambas secuencias con una jerarquía de métodos.
        """
        if not comparison_name:
            comparison_name = f"comparison_{comparison_id}"

        # --- Paso 1: Obtener la estructura ORIGINAL (sin cambios) ---
        print("➡️  Paso 1: Obteniendo estructura de referencia para la secuencia original...")
        original_job_name = f"{comparison_name}_original_ref"
        original_result = self.alphafold_service.predict_structure(
            original_sequence, original_job_name
        )

        # --- Paso 2: Predecir la estructura MUTADA con la mejor herramienta disponible ---
        print("\n➡️  Paso 2: Prediciendo directamente la estructura para la secuencia mutada...")
        mutated_job_name = f"{comparison_name}_mutated_pred"
        
        mutated_result = None
        
        # Jerarquía de predicción:
        # 1. Intentar con ColabFold si está disponible (ideal para predicción de novo)
        if self.alphafold_service._is_colabfold_available():
            try:
                mutated_result = self.alphafold_service._predict_with_colabfold(
                    mutated_sequence, mutated_job_name
                )
            except Exception as e:
                print(f"⚠️ ColabFold falló: {e}. Intentando con SWISS-MODEL.")

        # 2. Si ColabFold no está disponible o falla, intentar con SWISS-MODEL
        if not mutated_result:
            try:
                # Asegúrate de que tu config tenga el token de SWISS-MODEL
                if self.alphafold_service.config.get('SWISS_MODEL_TOKEN'):
                    mutated_result = self.alphafold_service._predict_with_swiss_model(
                        mutated_sequence, mutated_job_name
                    )
                else:
                    print("⚠️ SWISS-MODEL no configurado (falta token).")
            except Exception as e:
                print(f"⚠️ SWISS-MODEL falló: {e}. Usando simulación local como último recurso.")

        # 3. Como último recurso, usar la simulación local
        if not mutated_result:
            print("⚠️ ADVERTENCIA: Usando simulación local como fallback. La calidad será inferior.")
            mutated_result = self.alphafold_service._predict_improved_simulation(
                mutated_sequence, 
                mutated_job_name, 
                is_mutation=True,
                original_sequence=original_sequence
            )

        # --- Paso 3: Comparar ambas estructuras (sin cambios) ---
        print("\n➡️  Paso 3: Comparando ambas estructuras...")
        structural_comparison = self.alphafold_service.compare_structures(
            original_result, mutated_result
        )

        return {
            'original': original_result,
            'mutated': mutated_result,
            'comparison': structural_comparison
        }
    def _update_comparison_alphafold_data(self, comparison_id: int, alphafold_results: Dict[str, Any]):
        """
        Actualiza la comparación con los datos de AlphaFold
        
        Args:
            comparison_id: ID de la comparación
            alphafold_results: Resultados de AlphaFold
        """
        try:
            repo = ProteinComparisonRepository()
            
            import json
            
            original = alphafold_results.get('original', {})
            mutated = alphafold_results.get('mutated', {})
            comparison = alphafold_results.get('comparison', {})
            
            # Convertir structural_changes a JSON si es un diccionario
            structural_changes = comparison.get('structural_changes')
            if structural_changes and isinstance(structural_changes, dict):
                structural_changes = json.dumps(structural_changes)
            
            update_data = {
                'original_model_path': original.get('model_path'),
                'mutated_model_path': mutated.get('model_path'),
                'original_prediction_url': original.get('model_url'),
                'mutated_prediction_url': mutated.get('model_url'),
                'original_confidence_score': float(original.get('confidence', 0.0)),
                'mutated_confidence_score': float(mutated.get('confidence', 0.0)),
                'alphafold_job_id': f"{original.get('job_id', '')},{mutated.get('job_id', '')}",
                'processing_time': float(original.get('processing_time', 0.0) + mutated.get('processing_time', 0.0)),
                'structural_changes': structural_changes,
                'rmsd_value': float(comparison.get('rmsd_value', 0.0)),
                'status': 'completed'
            }
            
            repo.update_comparison(comparison_id, update_data)
            
        except Exception as e:
            print(f"Error actualizando datos de AlphaFold: {e}")
            # No lanzar excepción para no interrumpir el flujo
