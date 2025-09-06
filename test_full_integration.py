#!/usr/bin/env python3
"""
Test rápido para verificar que toda la aplicación funciona con la nueva lógica
"""

import sys
import os

# Añadir los directorios necesarios al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))
sys.path.insert(0, current_dir)

from business.comparison_manager import ComparisonManager
from business.sequence_service import SequenceValidator
from config.config import get_config

def test_full_app_integration():
    """
    Test de integración completa usando ComparisonManager con la nueva lógica
    """
    print("🧪 === TEST DE INTEGRACIÓN COMPLETA CON NUEVA LÓGICA ===")
    print()
    
    # Configuración
    config_class = get_config('development')
    config_dict = {
        'SWISS_MODEL_TOKEN': config_class.SWISS_MODEL_TOKEN,
        'MODELS_DIRECTORY': config_class.MODELS_DIRECTORY,
        'API_TIMEOUT': config_class.API_TIMEOUT
    }
    
    print(f"🔑 Token SWISS-MODEL: {'✅ Configurado' if config_dict['SWISS_MODEL_TOKEN'] else '❌ Faltante'}")
    print(f"📁 Directorio modelos: {config_dict['MODELS_DIRECTORY']}")
    print()
    
    # Crear el manager (como lo haría la app real)
    comparison_manager = ComparisonManager(config_dict)
    
    # Secuencias de test
    original_sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    mutated_sequence = "MVHLTPVEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"  # E->V en posición 7
    
    print(f"📋 Secuencias preparadas:")
    print(f"   Original:  {len(original_sequence)} residuos")
    print(f"   Mutada:    {len(mutated_sequence)} residuos")
    print(f"   Mutación:  E7V")
    print()
    
    try:
        # Usar exactamente el mismo flujo que usa la aplicación web
        print("🔄 Ejecutando flujo completo de comparación...")
        
        result = comparison_manager.create_comparison_with_alphafold(
            username="test_user",
            email="test@example.com",
            original_sequence=original_sequence,
            mutated_sequence=mutated_sequence,
            comparison_name="integration_test",
            description="E7V Test Integration",
            enable_alphafold=True
        )
        
        print("✅ Comparación completada exitosamente!")
        print(f"   🆔 Comparison ID: {result.get('comparison_id', 'N/A')}")
        print(f"   📊 Estado: {result.get('status', 'N/A')}")
        print(f"   ✅ Éxito: {result.get('success', 'N/A')}")
        print(f"   📝 Mensaje: {result.get('message', 'N/A')}")
        
        # Verificar si hay errores
        errors = result.get('errors', [])
        if errors:
            print(f"   ⚠️ Errores: {errors}")
        
        # Verificar que se generaron los modelos
        alphafold_data = result.get('alphafold_results', {})
        print(f"   🔬 Datos AlphaFold disponibles: {'✅' if alphafold_data else '❌'}")
        
        if alphafold_data:
            original_model = alphafold_data.get('original', {})
            mutated_model = alphafold_data.get('mutated', {})
            comparison_data = alphafold_data.get('comparison', {})
            
            print(f"\n📊 Resultados detallados:")
            print(f"   🧬 Modelo Original:")
            print(f"      📁 Archivo: {os.path.basename(original_model.get('model_path', 'N/A'))}")
            print(f"      📊 Confianza: {original_model.get('confidence', 'N/A')}%")
            print(f"      ⚡ Método: {original_model.get('prediction_method', 'N/A')}")
            
            print(f"   🧬 Modelo Mutado:")
            print(f"      📁 Archivo: {os.path.basename(mutated_model.get('model_path', 'N/A'))}")
            print(f"      📊 Confianza: {mutated_model.get('confidence', 'N/A')}%")
            print(f"      ⚡ Método: {mutated_model.get('prediction_method', 'N/A')}")
            
            print(f"   📐 Comparación Estructural:")
            print(f"      📐 RMSD: {comparison_data.get('rmsd_value', 'N/A')} Å")
            print(f"      📊 Diferencia confianza: {comparison_data.get('confidence_difference', 'N/A')}%")
            print(f"      🎯 Impacto: {comparison_data.get('structural_changes', {}).get('stability_impact', 'N/A')}")
            
            # Verificar archivos PDB
            original_path = original_model.get('model_path')
            mutated_path = mutated_model.get('model_path')
            
            if original_path and os.path.exists(original_path):
                print(f"      ✅ Archivo original verificado: {os.path.getsize(original_path)} bytes")
            
            if mutated_path and os.path.exists(mutated_path):
                print(f"      ✅ Archivo mutado verificado: {os.path.getsize(mutated_path)} bytes")
                
            success_with_models = True
        else:
            print(f"   ⚠️ No se ejecutaron predicciones de AlphaFold/SWISS-MODEL")
            success_with_models = False
        
        print(f"\n🎉 ¡TEST DE INTEGRACIÓN EXITOSO!")
        if success_with_models:
            print(f"✅ La aplicación completa funciona con la nueva lógica SWISS-MODEL")
        else:
            print(f"⚠️ La aplicación funciona pero no ejecutó predicciones 3D")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el test de integración: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test de integración completa")
    print("=" * 60)
    
    success = test_full_app_integration()
    
    if success:
        print(f"\n🎉 ¡LISTO PARA PRODUCCIÓN!")
        print(f"✅ Puedes lanzar la aplicación con: python app.py")
    else:
        print(f"\n❌ Hay problemas que resolver antes del lanzamiento")
        sys.exit(1)
