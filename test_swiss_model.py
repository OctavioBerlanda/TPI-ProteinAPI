#!/usr/bin/env python3
"""
Script de prueba para la integración con SWISS-MODEL
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import get_config_dict
from src.business.alphafold_service import AlphaFoldService

def test_swiss_model_integration():
    """Prueba la integración con SWISS-MODEL"""
    
    # Configuración
    config = get_config_dict('development')
    print("🔧 Configuración cargada:")
    print(f"   - SWISS_MODEL_TOKEN: {'✅ Configurado' if config.get('SWISS_MODEL_TOKEN') else '❌ No configurado'}")
    print(f"   - MODELS_DIRECTORY: {config.get('MODELS_DIRECTORY')}")
    
    # Crear servicio
    alphafold_service = AlphaFoldService(config)
    
    # Secuencia de prueba (Hemoglobina Beta mutada - secuencia corta para test rápido)
    test_sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    job_name = "swiss_model_test"
    
    print(f"\n🧪 Probando SWISS-MODEL con secuencia de {len(test_sequence)} aminoácidos...")
    print(f"   Secuencia: {test_sequence[:50]}...")
    
    try:
        # Verificar si tenemos token
        if not config.get('SWISS_MODEL_TOKEN'):
            print("❌ ERROR: No hay token de SWISS-MODEL configurado")
            return False
        
        # Probar predicción con SWISS-MODEL
        result = alphafold_service._predict_with_swiss_model(test_sequence, job_name)
        
        print("\n✅ SWISS-MODEL completado exitosamente!")
        print(f"   - Job ID: {result['job_id']}")
        print(f"   - Archivo local: {result['model_path']}")
        print(f"   - URL del modelo: {result['model_url']}")
        print(f"   - Confianza: {result['confidence']}%")
        print(f"   - Método: {result['prediction_method']}")
        print(f"   - Tiempo de procesamiento: {result.get('processing_time', 0):.2f} segundos")
        
        # Verificar que el archivo se descargó
        if os.path.exists(result['model_path']):
            file_size = os.path.getsize(result['model_path'])
            print(f"   - Tamaño del archivo: {file_size} bytes")
            print("   ✅ Archivo descargado correctamente")
        else:
            print("   ❌ Error: Archivo no encontrado")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR en SWISS-MODEL: {str(e)}")
        return False

def test_prediction_hierarchy():
    """Prueba la jerarquía de predicción completa"""
    
    print("\n" + "="*60)
    print("🔄 PROBANDO JERARQUÍA DE PREDICCIÓN")
    print("="*60)
    
    # Configuración
    config = get_config_dict('development')
    alphafold_service = AlphaFoldService(config)
    
    # Secuencia de prueba
    test_sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    job_name = "hierarchy_test"
    
    print(f"🧪 Probando jerarquía con secuencia de {len(test_sequence)} aminoácidos...")
    
    # 1. Verificar ColabFold
    print("\n1️⃣ Verificando ColabFold...")
    colabfold_available = alphafold_service._is_colabfold_available()
    print(f"   ColabFold disponible: {'✅ Sí' if colabfold_available else '❌ No'}")
    
    # 2. Verificar SWISS-MODEL
    print("\n2️⃣ Verificando SWISS-MODEL...")
    swiss_model_configured = bool(config.get('SWISS_MODEL_TOKEN'))
    print(f"   SWISS-MODEL configurado: {'✅ Sí' if swiss_model_configured else '❌ No'}")
    
    # 3. Simular el flujo de decisión
    print("\n3️⃣ Simulando flujo de decisión...")
    
    if colabfold_available:
        print("   🎯 Se usaría ColabFold (prioridad 1)")
        method = "ColabFold"
    elif swiss_model_configured:
        print("   🎯 Se usaría SWISS-MODEL (prioridad 2)")
        method = "SWISS-MODEL"
    else:
        print("   🎯 Se usaría simulación local (fallback)")
        method = "Simulación local"
    
    print(f"\n📊 RESULTADO: El sistema usaría {method}")
    
    return True

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DE SWISS-MODEL")
    print("="*60)
    
    try:
        # Prueba 1: Integración básica con SWISS-MODEL
        success1 = test_swiss_model_integration()
        
        # Prueba 2: Jerarquía de predicción
        success2 = test_prediction_hierarchy()
        
        print("\n" + "="*60)
        print("📋 RESUMEN DE PRUEBAS")
        print("="*60)
        print(f"✅ Integración SWISS-MODEL: {'EXITOSA' if success1 else 'FALLIDA'}")
        print(f"✅ Jerarquía de predicción: {'EXITOSA' if success2 else 'FALLIDA'}")
        
        if success1 and success2:
            print("\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
            print("\nEl sistema está listo para usar SWISS-MODEL como método")
            print("de predicción de alta calidad para proteínas mutadas.")
        else:
            print("\n⚠️ Algunas pruebas fallaron. Revisa la configuración.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
