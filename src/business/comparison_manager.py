from typing import Dict, Any, Optional
from src.business.sequence_service import SequenceComparisonService, SequenceValidationError
from src.business.swissmodel_service import SwissModelService, SwissModelIntegrationError
from src.data.repositories import ProteinComparisonRepository, UserRepository

class ComparisonManager:
    """Gestor principal para las comparaciones de proteínas"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.sequence_service = SequenceComparisonService(max_mutations=2)
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

        # --- Paso 0: Limpiar modelos antiguos antes de generar nuevos ---
        try:
            # Obtener el user_id de la comparación actual
            from src.data.repositories import ProteinComparisonRepository
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

        # --- Paso 1: Obtener la estructura ORIGINAL con múltiples modelos ---
        print("➡️  Paso 1: Obteniendo estructura de referencia para la secuencia original...")
        print(f"   📄 Secuencia original ({len(original_sequence)} aa): {original_sequence[:30]}{'...' if len(original_sequence) > 30 else ''}")
        original_job_name = f"{comparison_name}_original_ref"
        original_result = self.swissmodel_service.predict_structure(
            original_sequence, original_job_name, return_all_models=True
        )
        
        print(f"   📊 Resultado original: {len(original_result.get('models', []))} modelos disponibles")
        if 'best_model' in original_result:
            best = original_result['best_model']
            print(f"   🏆 Mejor modelo: GMQE={best.get('gmqe_score', 'N/A'):.3f}, Confianza={best.get('confidence', 'N/A')}%")

        # --- Paso 2: Generar la estructura MUTADA aplicando mutaciones a los modelos originales ---
        print("\n➡️  Paso 2: Generando estructura mutada desde modelos originales...")
        print(f"   📄 Secuencia mutada ({len(mutated_sequence)} aa): {mutated_sequence[:30]}{'...' if len(mutated_sequence) > 30 else ''}")
        mutated_job_name = f"{comparison_name}_mutated_pred"
        
        # Obtener las mutaciones
        validation_result = self.sequence_service.validate_and_compare_sequences(original_sequence, mutated_sequence)
        mutations = [(m['position'], m['original_amino_acid'], m['mutated_amino_acid']) for m in validation_result['mutations']['mutations']]
        print(f"   🔄 Mutaciones detectadas: {mutations}")
        
        try:
            print(f"🔬 Aplicando {len(mutations)} mutación(es) usando algoritmos avanzados...")
            mutated_result = self.swissmodel_service.predict_mutated_structure_advanced(
                original_result, mutations, mutated_job_name
            )
            print(f"   ✅ Modelo mutado generado exitosamente")
        except SwissModelIntegrationError as e:
            print(f"⚠️ Falló la predicción mutada desde modelos: {e}. Usando SWISS-MODEL directo como fallback.")
            # Fallback: predecir directamente con SWISS-MODEL
            mutated_result = self.swissmodel_service.predict_structure(
                mutated_sequence, mutated_job_name
            )

        # --- Paso 3: Comparar ambas estructuras (sin cambios) ---
        print("\n➡️  Paso 3: Comparando ambas estructuras...")
        structural_comparison = self.swissmodel_service.compare_structures(
            original_result, mutated_result
        )
        
        # Debug: Verificar que los modelos sean diferentes
        orig_model = original_result.get('best_model', original_result)
        mut_model = mutated_result
        
        print(f"   📊 COMPARACIÓN FINAL:")
        print(f"      Original: {orig_model.get('model_path', 'N/A')}")
        print(f"      Mutada: {mut_model.get('model_path', 'N/A')}")
        print(f"      RMSD: {structural_comparison.get('rmsd_value', 'N/A')}")
        print(f"      Diferencia confianza: {structural_comparison.get('confidence_difference', 'N/A')}")
        
        # Verificar si los archivos son realmente diferentes
        if orig_model.get('model_path') and mut_model.get('model_path'):
            try:
                import os
                orig_size = os.path.getsize(orig_model['model_path']) if os.path.exists(orig_model['model_path']) else 0
                mut_size = os.path.getsize(mut_model['model_path']) if os.path.exists(mut_model['model_path']) else 0
                print(f"      Tamaño archivos: Original={orig_size} bytes, Mutada={mut_size} bytes")
                print(f"      Archivos diferentes: {'SÍ' if orig_size != mut_size else 'NO'}")
            except Exception as e:
                print(f"      Error verificando archivos: {e}")

        return {
            'original': original_result.get('best_model', original_result),
            'mutated': mutated_result,
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
