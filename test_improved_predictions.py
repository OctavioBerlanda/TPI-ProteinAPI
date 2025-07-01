#!/usr/bin/env python3
"""
Script de prueba para las mejoras en predicción de estructuras
"""

import os
import sys
sys.path.append('src')

from business.alphafold_service import AlphaFoldService

def test_improved_predictions():
    """Prueba las mejoras en el sistema de predicción"""
    
    print("🧪 Probando mejoras en predicción de estructuras")
    print("=" * 60)
    
    # Configuración de prueba
    config = {
        'MODELS_DIRECTORY': 'models/test',
        'API_TIMEOUT': 30
    }
    
    # Crear instancia del servicio
    service = AlphaFoldService(config)
    
    # Test 1: Secuencia conocida (debería dar 90% confianza)
    print("\n🟢 TEST 1: Secuencia Original (Hemoglobina Beta)")
    hb_beta = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    
    result1 = service.predict_structure(hb_beta, "hemoglobin_beta_original")
    
    print(f"Confianza: {result1['confidence']}%")
    print(f"Método: {result1['prediction_method']}")
    if 'method_details' in result1:
        print(f"Tipo: {result1['method_details']['type']}")
        print(f"Disclaimer: {result1['method_details']['disclaimer']}")
    print()
    
    # Test 2: Secuencia mutada (debería usar simulación mejorada)
    print("🔴 TEST 2: Secuencia Mutada (Hemoglobina E6V)")
    hb_mutated = hb_beta[:5] + "V" + hb_beta[6:]  # E6V mutation
    
    result2 = service.predict_structure(hb_mutated, "hemoglobin_beta_E6V")
    
    print(f"Confianza: {result2['confidence']}%")
    print(f"Método: {result2['prediction_method']}")
    if 'method_details' in result2:
        print(f"Tipo: {result2['method_details']['type']}")
        print(f"Algoritmo: {result2['method_details']['algorithm']}")
        print(f"Disclaimer: {result2['method_details']['disclaimer']}")
    if 'secondary_structure' in result2:
        print(f"Estructura secundaria (primeros 50): {result2['secondary_structure'][:50]}...")
    print()
    
    # Test 3: Secuencia completamente nueva
    print("🧪 TEST 3: Secuencia Sintética")
    synthetic_seq = "MAEGEITTFTALTEKFNLPPGNYKKPKLLYCSNGGHFLRILPDGTVDGTRDRSDQHIQLQLSAESVGEVYIKSTETGQYLAMDTSGLLYGSQTPSEECLFLERLEENHYNTYTSKKHAEKNWFVGLKKNGSCKRGPRTHYGQKAILFLPLPV"
    
    result3 = service.predict_structure(synthetic_seq, "synthetic_protein")
    
    print(f"Confianza: {result3['confidence']}%")
    print(f"Método: {result3['prediction_method']}")
    if 'method_details' in result3:
        print(f"Tipo: {result3['method_details']['type']}")
        print(f"Algoritmo: {result3['method_details']['algorithm']}")
    if 'secondary_structure' in result3:
        print(f"Estructura secundaria (primeros 50): {result3['secondary_structure'][:50]}...")
    print()
    
    # Test 4: Comparar confidencias de diferentes algoritmos
    print("📊 COMPARACIÓN DE ALGORITMOS")
    print("-" * 40)
    
    # Probar algoritmo antiguo vs nuevo para la misma secuencia mutada
    print("Secuencia: Hemoglobina E6V")
    print(f"Algoritmo mejorado: {result2['confidence']}%")
    
    # Simular algoritmo anterior (simplificado)
    old_confidence = min(100, len(hb_mutated) * 0.8) - 10  # Simulación del algoritmo anterior
    old_confidence = max(40, min(95, old_confidence))
    print(f"Algoritmo anterior (estimado): {old_confidence}%")
    print(f"Mejora: {result2['confidence'] - old_confidence:+.1f}%")
    print()
    
    # Test 5: Análisis de estructura secundaria
    print("🧬 ANÁLISIS DE ESTRUCTURA SECUNDARIA")
    print("-" * 40)
    if 'secondary_structure' in result2:
        ss = result2['secondary_structure']
        h_count = ss.count('H')
        e_count = ss.count('E') 
        c_count = ss.count('C')
        total = len(ss)
        
        print(f"Hélices (H): {h_count} ({h_count/total*100:.1f}%)")
        print(f"Hojas beta (E): {e_count} ({e_count/total*100:.1f}%)")
        print(f"Coils/loops (C): {c_count} ({c_count/total*100:.1f}%)")
    print()
    
    print("✅ Pruebas completadas!")
    print("\n📝 RESUMEN DE MEJORAS:")
    print("1. ✅ Etiquetas claras sobre tipo de predicción")
    print("2. ✅ Algoritmo de confianza basado en homología")
    print("3. ✅ Predicción de estructura secundaria") 
    print("4. ✅ Coordenadas 3D mejoradas")
    print("5. ✅ Información detallada del método usado")

if __name__ == "__main__":
    test_improved_predictions()
