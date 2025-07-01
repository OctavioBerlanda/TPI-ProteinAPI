#!/usr/bin/env python3
"""
Test para verificar que hemos restaurado la lógica que funcionaba bien
según MEJORAS_COMPLETADAS.md
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.business.alphafold_service import AlphaFoldService

def test_restored_logic():
    """Test de la lógica restaurada que funcionaba bien"""
    
    print("🔄 Verificando que la lógica restaurada funciona como antes")
    print("=" * 60)
    
    # Configurar servicio
    config = {
        'ALPHAFOLD_API_ENDPOINT': 'https://alphafolddb.org/api',
        'COLABFOLD_ENDPOINT': 'http://localhost:8080',
        'MODELS_DIRECTORY': 'models/alphafold',
        'API_TIMEOUT': 300
    }
    service = AlphaFoldService(config)
    
    # Casos de prueba basados en MEJORAS_COMPLETADAS.md
    test_cases = [
        {
            'name': 'Hemoglobina Beta (secuencia original)',
            'sequence': 'MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH',
            'expected_confidence': 90.0,
            'expected_method': 'alphafold_db_real',
            'expected_type': 'real_structure'
        },
        {
            'name': 'Hemoglobina E6V (mutación)',
            'sequence': 'MVHLTPVEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH',
            'expected_confidence': 81.3,
            'expected_method': 'improved_simulation',
            'expected_type': 'simulation'
        },
        {
            'name': 'Secuencia sintética',
            'sequence': 'MKLLLAVAISLLAALPSMPAVYQLLETKFYLMPSGHCQGVCGMAYPLKGGAAWLVSGSWTDGDLYNKKSKYPDYLQASDGSGYSDGYCDRWEEEPVIHNYPSPTGPFLSPGYVVQEQCICVGEGYKQEKQAAPCTCYQDSGQDSCHNQYSSLQKYKEPSSCKDQCVDNKDVLRQNEHDSKHYSMSSYNQGGDLQAASCRLWQFKHLTAPAMYSRANLPPLNQSESYQIGRSHCEHSRYNMSSSPQ',
            'expected_confidence': 42.0,
            'expected_method': 'improved_simulation',
            'expected_type': 'simulation'
        }
    ]
    
    print("📊 Resultados esperados según MEJORAS_COMPLETADAS.md:")
    print("🟢 TEST 1: Hemoglobina Beta - Confianza: 90.0% - Método: alphafold_db_real")
    print("🔴 TEST 2: Hemoglobina E6V - Confianza: 81.3% - Método: improved_simulation")
    print("🧪 TEST 3: Secuencia Sintética - Confianza: 42.0% - Método: improved_simulation")
    print()
    
    for i, case in enumerate(test_cases, 1):
        print(f"📝 TEST {i}: {case['name']}")
        
        try:
            # Hacer predicción
            result = service.predict_structure(case['sequence'], f"restore_test_{i}")
            
            # Extraer información
            confidence = result.get('confidence', 0)
            method = result.get('prediction_method', 'unknown')
            
            print(f"   ✅ Resultado obtenido:")
            print(f"      - Confianza: {confidence}%")
            print(f"      - Método: {method}")
            
            # Verificar si está cerca de los valores esperados
            confidence_diff = abs(confidence - case['expected_confidence'])
            method_match = method == case['expected_method']
            
            if confidence_diff <= 5.0 and method_match:
                print(f"      ✅ CORRECTO: Resultado similar al esperado")
            else:
                print(f"      ⚠️  DIFERENTE: Esperado {case['expected_confidence']}% con {case['expected_method']}")
                if not method_match:
                    print(f"         - Método esperado: {case['expected_method']}")
                if confidence_diff > 5.0:
                    print(f"         - Diferencia de confianza: {confidence_diff:.1f}%")
                    
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
        
        print()
    
    print("=" * 60)
    print("🏁 Verificación de lógica restaurada completada")
    print()
    print("💡 La lógica debe coincidir con MEJORAS_COMPLETADAS.md:")
    print("   • Estructuras reales: ~90% confianza")
    print("   • Mutaciones conocidas: ~81% confianza")
    print("   • Secuencias nuevas: ~42% confianza")
    print("   • Badges apropiados en la UI")

if __name__ == "__main__":
    test_restored_logic()
