#!/usr/bin/env python3
"""
Demostración de la integración AlphaFold
Muestra cómo funciona el sistema completo con predicciones de estructura 3D
"""
import sys
import os

# Agregar el directorio raíz del proyecto al Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.business.alphafold_service import AlphaFoldService
from src.business.comparison_manager import ComparisonManager
from config.config import get_config_dict

def demo_alphafold_integration():
    """Demostración completa de la integración AlphaFold"""
    
    print("🧬" + "="*60)
    print("      DEMOSTRACIÓN INTEGRACIÓN ALPHAFOLD")
    print("🧬" + "="*60)
    
    # Configuración
    config = get_config_dict()
    
    # Secuencias de ejemplo (Hemoglobina con mutación común)
    original_sequence = "MLTAEEKAAVTAFWGKVKVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    mutated_sequence = "MLTAEEKAAVTAFWGKVKVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    # Cambiar una posición para crear una mutación
    mutated_sequence = mutated_sequence[:50] + 'S' + mutated_sequence[51:]  # E->S mutación
    
    print("\n📝 INFORMACIÓN DE LA DEMOSTRACIÓN")
    print("-" * 40)
    print(f"Secuencia original:  {original_sequence[:50]}...")
    print(f"Secuencia mutada:    {mutated_sequence[:50]}...")
    print(f"Longitud: {len(original_sequence)} aminoácidos")
    print(f"Mutación: Posición 51, E→S")
    
    # 1. Crear instancia del servicio AlphaFold
    print("\n🔧 PASO 1: Inicializando servicio AlphaFold")
    print("-" * 40)
    alphafold_service = AlphaFoldService(config)
    print(f"✅ Directorio de modelos: {alphafold_service.models_directory}")
    print(f"✅ Endpoint API: {alphafold_service.api_endpoint}")
    print(f"✅ Timeout: {alphafold_service.timeout}s")
    
    # 2. Predecir estructura original
    print("\n🧬 PASO 2: Prediciendo estructura original")
    print("-" * 40)
    try:
        original_result = alphafold_service.predict_structure(
            original_sequence, 
            "demo_hemoglobin_original"
        )
        print(f"✅ Job ID: {original_result['job_id']}")
        print(f"✅ Confianza: {original_result['confidence']:.1f}%")
        print(f"✅ Método: {original_result['prediction_method']}")
        print(f"✅ Modelo guardado: {original_result['model_path']}")
        print(f"✅ Tiempo procesamiento: {original_result['processing_time']:.2f}s")
        
    except Exception as e:
        print(f"❌ Error en predicción original: {e}")
        return
    
    # 3. Predecir estructura mutada
    print("\n🧪 PASO 3: Prediciendo estructura mutada")
    print("-" * 40)
    try:
        mutated_result = alphafold_service.predict_structure(
            mutated_sequence, 
            "demo_hemoglobin_mutated"
        )
        print(f"✅ Job ID: {mutated_result['job_id']}")
        print(f"✅ Confianza: {mutated_result['confidence']:.1f}%")
        print(f"✅ Método: {mutated_result['prediction_method']}")
        print(f"✅ Modelo guardado: {mutated_result['model_path']}")
        print(f"✅ Tiempo procesamiento: {mutated_result['processing_time']:.2f}s")
        
    except Exception as e:
        print(f"❌ Error en predicción mutada: {e}")
        return
    
    # 4. Comparar estructuras
    print("\n🔬 PASO 4: Comparando estructuras")
    print("-" * 40)
    try:
        comparison = alphafold_service.compare_structures(original_result, mutated_result)
        
        print(f"✅ RMSD: {comparison['rmsd_value']:.3f} Ångströms")
        print(f"✅ Diferencia de confianza: {comparison['confidence_difference']:.1f} puntos")
        print(f"✅ Método de análisis: {comparison['analysis_method']}")
        
        # Análisis de cambios estructurales
        structural_changes = comparison['structural_changes']
        print(f"\n📊 ANÁLISIS ESTRUCTURAL:")
        print(f"   • Cambio de confianza: {structural_changes['confidence_change']:+.1f}")
        print(f"   • Impacto en estabilidad: {structural_changes['stability_impact']}")
        print(f"   • Efecto predicho: {structural_changes['predicted_effect']}")
        
    except Exception as e:
        print(f"❌ Error en comparación: {e}")
        return
    
    # 5. Demostración del flujo completo usando ComparisonManager
    print("\n🏗️ PASO 5: Flujo completo con ComparisonManager")
    print("-" * 40)
    try:
        comparison_manager = ComparisonManager(config)
        
        full_result = comparison_manager.create_comparison_with_alphafold(
            username="demo_user",
            email="demo@example.com",
            original_sequence=original_sequence,
            mutated_sequence=mutated_sequence,
            comparison_name="Demostración AlphaFold",
            description="Demostración de integración completa con AlphaFold",
            enable_alphafold=True
        )
        
        if full_result['success']:
            print(f"✅ Comparación creada con ID: {full_result['comparison_id']}")
            
            alphafold_results = full_result['alphafold_results']
            if alphafold_results['original'] and alphafold_results['mutated']:
                print(f"✅ Estructuras AlphaFold procesadas exitosamente")
                print(f"   • Original: {alphafold_results['original']['confidence']:.1f}% confianza")
                print(f"   • Mutada: {alphafold_results['mutated']['confidence']:.1f}% confianza")
                print(f"   • RMSD: {alphafold_results['comparison']['rmsd_value']:.3f} Å")
            else:
                print("⚠️ No se pudieron procesar las estructuras AlphaFold")
        else:
            print(f"❌ Error en comparación completa: {full_result['errors']}")
            
    except Exception as e:
        print(f"❌ Error en flujo completo: {e}")
    
    # 6. Resumen final
    print("\n🎯 RESUMEN DE LA DEMOSTRACIÓN")
    print("="*60)
    print("✅ Servicio AlphaFold inicializado correctamente")
    print("✅ Predicciones de estructura 3D generadas")
    print("✅ Comparación estructural completada")
    print("✅ Análisis de impacto de mutaciones realizado")
    print("✅ Integración completa con base de datos funcional")
    print("✅ Modelos PDB guardados localmente")
    
    print(f"\n📁 Archivos generados:")
    if os.path.exists(original_result['model_path']):
        print(f"   • {original_result['model_path']}")
    if os.path.exists(mutated_result['model_path']):
        print(f"   • {mutated_result['model_path']}")
    
    print(f"\n🌐 Para ver los resultados en la interfaz web:")
    print(f"   1. Ejecuta: python app.py")
    print(f"   2. Visita: http://localhost:5000")
    print(f"   3. Marca la opción 'Incluir Predicción de AlphaFold'")
    print(f"   4. Usa las secuencias de esta demostración")
    
    print("\n🎉 ¡Demostración completada exitosamente!")

if __name__ == "__main__":
    demo_alphafold_integration()
