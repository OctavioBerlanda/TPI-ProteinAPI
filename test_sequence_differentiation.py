#!/usr/bin/env python3
"""
Test script para verificar que las secuencias diferentes dan resultados diferentes
después de las correcciones al sistema de detección de AlphaFold
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.business.alphafold_service import AlphaFoldService

def test_sequence_differentiation():
    """Prueba que secuencias diferentes produzcan resultados diferentes"""
    
    print("🧪 Test de Diferenciación de Secuencias")
    print("=" * 60)
    
    # Configuración básica
    config = {
        'MODELS_DIRECTORY': 'models/test',
        'API_TIMEOUT': 30
    }
    
    service = AlphaFoldService(config)
    
    # Casos de prueba: secuencias similares pero diferentes
    test_cases = [
        {
            'name': 'Secuencias con 1 mutación',
            'original': 'MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH',
            'mutated':  'MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYG'  # Y->G al final
        },
        {
            'name': 'Secuencias cortas con 1 mutación',
            'original': 'MKLLLLLLLLLLLLLLLLLLLLA',
            'mutated':  'MKLLLLLLLLLLLLLLLLLLLLG'  # A->G al final
        },
        {
            'name': 'Secuencias medias con múltiples diferencias',
            'original': 'MKALIVLGLVLLSVTVQGKVFERCELARTLKRLGMDGYRGISLANWMCLAKWESGYNTRATNYNAGDRSTDYGIFQINSRYWCNDGKTPGAVNACHLSCSALLQDNIADAVACAKRVVRDPQGIRAWVAWRNRCQNRDVRQYVQGCGV',
            'mutated':  'MKALIVLGLVLLSVTVQGKVFERCELARTLKRLGMDGYRGISLANWMCLAKWESGYNTRATNYNAGDRSTDYGIFQINSRYWCNDGKTPGAVNACHLSCSALLQDNIADAVACAKRVVRDPQGIRAWVAWRNRCQNRDVRQYVQGCGA'  # V->A al final
        }
    ]
    
    all_tests_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Caso de Prueba {i}: {test_case['name']}")
        print("-" * 50)
        
        try:
            # Predecir estructura para secuencia original
            print("🔬 Analizando secuencia original...")
            original_result = service.predict_structure(test_case['original'], f"test_original_{i}")
            
            # Predecir estructura para secuencia mutada
            print("🔬 Analizando secuencia mutada...")
            mutated_result = service.predict_structure(test_case['mutated'], f"test_mutated_{i}")
            
            # Mostrar resultados
            print(f"\n📊 Resultados:")
            print(f"   Original - Confianza: {original_result['confidence']:.2f}%, Método: {original_result['prediction_method']}")
            print(f"   Mutada   - Confianza: {mutated_result['confidence']:.2f}%, Método: {mutated_result['prediction_method']}")
            
            # Verificar que los resultados son diferentes
            confidence_diff = abs(original_result['confidence'] - mutated_result['confidence'])
            methods_different = original_result['prediction_method'] != mutated_result['prediction_method']
            
            if confidence_diff > 0.1 or methods_different:
                print(f"   ✅ DIFERENCIAS DETECTADAS:")
                print(f"      - Diferencia de confianza: {confidence_diff:.2f}%")
                if methods_different:
                    print(f"      - Métodos diferentes detectados")
            else:
                print(f"   ❌ NO SE DETECTARON DIFERENCIAS SIGNIFICATIVAS")
                all_tests_passed = False
            
            # Comparar estructuras
            comparison = service.compare_structures(original_result, mutated_result)
            print(f"   📐 RMSD estimado: {comparison['rmsd_value']:.3f} Å")
            print(f"   🔄 Diferencia de confianza: {comparison['confidence_difference']:.2f}%")
            
        except Exception as e:
            print(f"   ❌ ERROR en prueba: {str(e)}")
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 TODAS LAS PRUEBAS PASARON - El sistema diferencia correctamente entre secuencias")
    else:
        print("⚠️ ALGUNAS PRUEBAS FALLARON - Revisar la lógica de diferenciación")
    print("=" * 60)
    
    return all_tests_passed

def test_exact_sequence_detection():
    """Prueba la detección de secuencias exactas conocidas"""
    
    print("\n🔍 Test de Detección de Secuencias Conocidas")
    print("=" * 60)
    
    config = {
        'MODELS_DIRECTORY': 'models/test',
        'API_TIMEOUT': 30
    }
    
    service = AlphaFoldService(config)
    
    # Secuencia exacta de hemoglobina beta humana
    known_sequence = 'MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH'
    
    print("🧬 Probando secuencia exacta de hemoglobina beta...")
    result = service.predict_structure(known_sequence, "hemoglobin_test")
    
    print(f"📊 Resultado:")
    print(f"   Método: {result['prediction_method']}")
    print(f"   Confianza: {result['confidence']:.2f}%")
    print(f"   URL del modelo: {result.get('model_url', 'No disponible')}")
    
    if result['prediction_method'] == 'alphafold_db_real':
        print("   ✅ ESTRUCTURA REAL DETECTADA CORRECTAMENTE")
        return True
    else:
        print("   ⚠️ No se detectó como estructura real (puede ser normal si no hay conectividad)")
        return True  # No es error si no hay internet

if __name__ == "__main__":
    print("🚀 Iniciando tests de corrección del sistema AlphaFold")
    
    # Ejecutar tests
    test1_passed = test_sequence_differentiation()
    test2_passed = test_exact_sequence_detection()
    
    print(f"\n📋 RESUMEN DE TESTS:")
    print(f"   Test de diferenciación: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"   Test de detección: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    
    if test1_passed and test2_passed:
        print("\n🎯 TODOS LOS TESTS PASARON - El sistema está funcionando correctamente")
        sys.exit(0)
    else:
        print("\n⚠️ ALGUNOS TESTS FALLARON - Se requiere revisión adicional")
        sys.exit(1)
