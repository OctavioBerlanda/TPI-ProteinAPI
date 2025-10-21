from typing import Dict, Any, Optional
from src.business.sequence_service import SequenceComparisonService, SequenceValidationError
from src.business.swissmodel_service import SwissModelService, SwissModelIntegrationError
from src.data.repositories import ProteinComparisonRepository, UserRepository

class ComparisonManager:
    """Gestor principal para las comparaciones de proteínas"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.sequence_service = SequenceComparisonService(max_mutations=None)  # Sin límite de mutaciones
        self.swissmodel_service = SwissModelService(config or {}) if config else None
    
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
            
            # Verificar si ya existe una comparación con las mismas secuencias para este usuario
            existing_comparison = ProteinComparisonRepository.get_comparison_by_sequences_and_user(
                user_id=user.id,
                original_sequence=validation_result['original_sequence'],
                mutated_sequence=validation_result['mutated_sequence']
            )
            
            if existing_comparison:
                print(f"✅ Comparación existente encontrada (ID: {existing_comparison.id}), reutilizando...")
                result['success'] = True
                result['comparison_id'] = existing_comparison.id
                result['message'] = "Comparación existente encontrada y reutilizada"
                return result
            
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
    
    def create_comparison_with_swissmodel(self, username: str, email: str, original_sequence: str, 
                                       mutated_sequence: str, comparison_name: str = None, 
                                       description: str = None, enable_swissmodel: bool = True) -> Dict[str, Any]:
        """
        Crea una nueva comparación de proteínas con integración SwissModel
        
        Args:
            username: Nombre del usuario
            email: Email del usuario
            original_sequence: Secuencia original
            mutated_sequence: Secuencia mutada
            comparison_name: Nombre opcional para la comparación
            description: Descripción opcional
            enable_swissmodel: Si habilitar predicción con SwissModel
            
        Returns:
            Dict con el resultado de la operación incluyendo modelos 3D
        """
        result = {
            'success': False,
            'comparison_id': None,
            'errors': [],
            'data': {},
            'swissmodel_results': {
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
            
            # 2. Si SwissModel está habilitado, procesar estructuras 3D
            if enable_swissmodel and self.swissmodel_service:
                try:
                    result['swissmodel_results'] = self._process_swissmodel_predictions(
                        comparison_id, original_sequence, mutated_sequence, comparison_name
                    )
                    
                    # Actualizar el estado de la comparación a completada
                    self._update_comparison_swissmodel_data(comparison_id, result['swissmodel_results'])
                    
                except SwissModelIntegrationError as e:
                    result['errors'].append(f"Error en SwissModel: {str(e)}")
                    # No fallar toda la comparación por errores de SwissModel
                    
            result['success'] = True
            return result
            
        except Exception as e:
            result['errors'].append(f"Error procesando comparación: {str(e)}")
            return result
    
    def _process_swissmodel_predictions(self, comparison_id: int, original_sequence: str, mutated_sequence: str, comparison_name: str = None) -> Dict[str, Any]:
        """
        Procesa las predicciones de SwissModel para ambas secuencias con una jerarquía de métodos.
        """
        if not comparison_name:
            comparison_name = f"comparison_{comparison_id}"

        # --- Paso 0: Verificar si ya existen modelos para esta comparación ---
        from src.data.repositories import ProteinComparisonRepository
        existing_comparison = ProteinComparisonRepository.get_comparison_by_id(comparison_id)

        if (existing_comparison and
            existing_comparison.original_model_path and
            existing_comparison.mutated_model_path and
            existing_comparison.original_confidence_score is not None and
            existing_comparison.mutated_confidence_score is not None):

            print("✅ Modelos ya existen para esta comparación, reutilizando...")

            # Verificar que los archivos realmente existen
            import os
            original_path = existing_comparison.original_model_path
            mutated_path = existing_comparison.mutated_model_path
            
            # Resolver rutas absolutas si son relativas
            if not os.path.isabs(original_path):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                original_path = os.path.join(project_root, original_path)
            
            if not os.path.isabs(mutated_path):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                mutated_path = os.path.join(project_root, mutated_path)
            
            original_exists = os.path.exists(original_path)
            mutated_exists = os.path.exists(mutated_path)

            if original_exists and mutated_exists:
                print("   📁 Ambos archivos de modelo encontrados, retornando datos existentes")

                # Retornar datos existentes sin volver a descargar
                return {
                    'original': {
                        'model_path': existing_comparison.original_model_path,
                        'model_url': existing_comparison.original_prediction_url,
                        'confidence': existing_comparison.original_confidence_score,
                        'job_id': existing_comparison.swissmodel_job_id.split(',')[0] if existing_comparison.swissmodel_job_id else None
                    },
                    'mutated': {
                        'model_path': existing_comparison.mutated_model_path,
                        'model_url': existing_comparison.mutated_prediction_url,
                        'confidence': existing_comparison.mutated_confidence_score,
                        'job_id': existing_comparison.swissmodel_job_id.split(',')[-1] if existing_comparison.swissmodel_job_id else None
                    },
                    'comparison': {
                        'rmsd_value': existing_comparison.rmsd_value or 0.0,
                        'structural_changes': existing_comparison.structural_changes
                    }
                }
            else:
                print(f"   ⚠️ Archivos faltantes - Original: {'✅' if original_exists else '❌'} ({original_path}), Mutado: {'✅' if mutated_exists else '❌'} ({mutated_path})")
                print("   🔄 Re-descargando modelos faltantes...")

        # --- Paso 1: Limpiar modelos antiguos antes de generar nuevos ---
        try:
            # Obtener el user_id de la comparación actual
            comparison = ProteinComparisonRepository.get_comparison_by_id(comparison_id)
            if comparison and comparison.user_id:
                print("🧹 Limpiando modelos antiguos del usuario...")
                cleanup_stats = self.swissmodel_service.cleanup_old_models(
                    user_id=comparison.user_id,
                    keep_recent=3  # Mantener las 3 comparaciones más recientes
                )
                if cleanup_stats['files_deleted'] > 0:
                    print(f"   ✅ Liberados {cleanup_stats['space_freed_mb']:.1f} MB de espacio")
        except Exception as e:
            print(f"   ⚠️ Error en limpieza (continuando): {str(e)}")

        # --- Paso 2: Predecir estructura ORIGINAL con SwissModel ---
        print("➡️  Paso 1: Prediciendo estructura de la secuencia ORIGINAL con SwissModel...")
        original_job_name = f"{comparison_name}_original"
        original_result = self.swissmodel_service.predict_structure(
            original_sequence, original_job_name, return_all_models=True
        )

        # --- Paso 2: Predecir estructura MUTADA con SwissModel ---
        print("\n➡️  Paso 2: Prediciendo estructura de la secuencia MUTADA con SwissModel...")
        mutated_job_name = f"{comparison_name}_mutated"
        mutated_result = self.swissmodel_service.predict_structure(
            mutated_sequence, mutated_job_name, return_all_models=True
        )

        # --- Paso 3: Comparar ambas estructuras ---
        print("\n➡️  Paso 3: Comparando ambas estructuras...")
        structural_comparison = self.swissmodel_service.compare_structures(
            original_result, mutated_result
        )

        return {
            'original': original_result.get('best_model', original_result),
            'mutated': mutated_result.get('best_model', mutated_result),
            'comparison': structural_comparison
        }
    def _update_comparison_swissmodel_data(self, comparison_id: int, swissmodel_results: Dict[str, Any]):
        """
        Actualiza la comparación con los datos de SwissModel
        
        Args:
            comparison_id: ID de la comparación
            swissmodel_results: Resultados de SwissModel
        """
        try:
            repo = ProteinComparisonRepository()
            
            import json
            
            original = swissmodel_results.get('original', {})
            mutated = swissmodel_results.get('mutated', {})
            comparison = swissmodel_results.get('comparison', {})
            
            # Convertir structural_changes a JSON si es un diccionario
            structural_changes = comparison.get('structural_changes')
            if structural_changes and isinstance(structural_changes, dict):
                structural_changes = json.dumps(structural_changes)
            
            # Extraer datos avanzados de análisis
            mutated_advanced = mutated.get('structural_analysis', {})
            stability_data = mutated.get('stability_analysis', {})
            functional_data = mutated.get('functional_analysis', {})
            dynamics_data = mutated.get('dynamics_analysis', {})
            
            update_data = {
                'original_model_path': original.get('model_path'),
                'mutated_model_path': mutated.get('model_path'),
                'original_prediction_url': original.get('model_url'),
                'mutated_prediction_url': mutated.get('model_url'),
                'original_confidence_score': float(original.get('confidence', 0.0)),
                'mutated_confidence_score': float(mutated.get('confidence', 0.0)),
                'swissmodel_job_id': f"{original.get('job_id', '')},{mutated.get('job_id', '')}",
                'processing_time': float(original.get('processing_time', 0.0) + mutated.get('processing_time', 0.0)),
                'structural_changes': structural_changes,
                'rmsd_value': float(comparison.get('rmsd_value', 0.0)),
                
                # Nuevos campos para análisis avanzado
                'stability_change_score': float(stability_data.get('stability_change_score', 0.0)),
                'functional_impact_score': float(functional_data.get('functional_impact_score', 0.0)),
                'dynamics_change_score': float(dynamics_data.get('dynamics_change_score', 0.0)),
                'thermal_stability_change': float(stability_data.get('thermal_stability_change', 0.0)),
                'folding_energy_change': float(stability_data.get('folding_energy_change', 0.0)),
                'active_site_disruption': functional_data.get('active_site_disruption', False),
                
                'status': 'completed'
            }
            
            repo.update_comparison(comparison_id, update_data)
            
        except Exception as e:
            print(f"Error actualizando datos de SwissModel: {e}")
            # No lanzar excepción para no interrumpir el flujo
