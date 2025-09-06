#!/usr/bin/env python3
"""
Script de test para la nueva lógica de SW        print("✅ Resultado para secuencia original:")
        print(f"   🆔 Job ID: {original_result.get('job_id')}")
        print(f"   📁 Archivo modelo: {os.path.basename(original_result.get('model_path', 'N/A'))}")
        print(f"   📊 Confianza: {original_result.get('confidence', 'N/A')}% ({original_result.get('confidence_source', 'N/A')})")
        print(f"   📊 GMQE Score: {original_result.get('gmqe_score', 'N/A')}")
        print(f"   📊 QMEAN Score: {original_result.get('qmean_score', 'N/A')}")
        print(f"   🧬 Proteína: {original_result.get('protein_name', 'N/A')}")
        print(f"   🆔 Modelo ID: {original_result.get('model_id', 'N/A')}")
        print(f"   📊 Modelos generados: {original_result.get('model_count', 'N/A')}")
        print(f"   ⚡ Método: {original_result.get('prediction_method', 'N/A')}")
        print(f"   ⏱️  Tiempo: {original_time:.1f}s")
- SWISS-MODEL: Modelado 3D de proteína original y mutada
- AlphaFold: Solo datos informativos (UniProt ID, nombre, etc.)
"""

import sys
import os
import time

# Añadir los directorios necesarios al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))
sys.path.insert(0, current_dir)

from business.alphafold_service import AlphaFoldService, AlphaFoldIntegrationError
from config.config import get_config

def test_new_swiss_model_logic():
    """
    Test de la nueva lógica simplificada:
    Solo SWISS-MODEL para modelado 3D (sin AlphaFold)
    """
    print("🧪 === TEST DE NUEVA LÓGICA SWISS-MODEL SIMPLIFICADA ===")
    print()
    
    # Configuración
    config_class = get_config('development')
    config = {
        'SWISS_MODEL_TOKEN': config_class.SWISS_MODEL_TOKEN,
        'MODELS_DIRECTORY': config_class.MODELS_DIRECTORY,
        'API_TIMEOUT': config_class.API_TIMEOUT,
        'ALPHAFOLD_API_ENDPOINT': config_class.ALPHAFOLD_API_ENDPOINT
    }
    
    print(f"🔑 Token SWISS-MODEL configurado: {'✅' if config['SWISS_MODEL_TOKEN'] else '❌'}")
    print(f"📁 Directorio de modelos: {config['MODELS_DIRECTORY']}")
    print()
    
    # Crear servicio
    alphafold_service = AlphaFoldService(config)
    
    # Secuencias de test (hemoglobina beta humana y mutación)
    print("📋 Secuencias de test:")
    original_sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    mutated_sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    
    # Aplicar mutación E6V (Glu -> Val en posición 6)
    mutated_sequence_list = list(mutated_sequence)
    mutated_sequence_list[6] = 'V'  # E -> V en posición 7 (índice 6)
    mutated_sequence = ''.join(mutated_sequence_list)
    
    print(f"Original:  {original_sequence[:50]}...")
    print(f"Mutada:    {mutated_sequence[:50]}...")
    print(f"Mutación:  E7V (posición 7)")
    print()
    
    try:
        # === TEST 1: Secuencia Original ===
        print("🔬 TEST 1: Predicción de secuencia ORIGINAL con SWISS-MODEL")
        print("-" * 60)
        
        start_time = time.time()
        original_result = alphafold_service.predict_structure(
            sequence=original_sequence,
            job_name="hemoglobina_beta_original_test"
        )
        original_time = time.time() - start_time
        
        print("✅ Resultado para secuencia original:")
        print(f"   🆔 Job ID: {original_result.get('job_id')}")
        print(f"   📁 Archivo modelo: {os.path.basename(original_result.get('model_path', 'N/A'))}")
        print(f"   📊 Confianza: {original_result.get('confidence', 'N/A')}%")
        print(f"   � QMEAN Score: {original_result.get('qmean_score', 'N/A')}")
        print(f"   🧬 Proteína: {original_result.get('protein_name', 'N/A')}")
        print(f"   🔬 Template: {original_result.get('template_id', 'N/A')}")
        print(f"   ⚡ Método: {original_result.get('prediction_method', 'N/A')}")
        print(f"   ⏱️  Tiempo: {original_time:.1f}s")
        print()
        
        return True, original_result
        
    except AlphaFoldIntegrationError as e:
        print(f"❌ Error de integración: {e}")
        return False, None
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_alphafold_data_only():
    """
    Test específico para verificar que AlphaFold solo devuelve datos
    """
    print("🧪 === TEST DE DATOS DE ALPHAFOLD ===")
    print()
    
    config_class = get_config('development')
    config = {
        'SWISS_MODEL_TOKEN': config_class.SWISS_MODEL_TOKEN,
        'MODELS_DIRECTORY': config_class.MODELS_DIRECTORY,
        'API_TIMEOUT': config_class.API_TIMEOUT,
        'ALPHAFOLD_API_ENDPOINT': config_class.ALPHAFOLD_API_ENDPOINT
    }
    
    alphafold_service = AlphaFoldService(config)
    
    # Secuencia conocida (hemoglobina beta)
    test_sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    
    try:
        print("🔍 Obteniendo solo datos de AlphaFold...")
        alphafold_data = alphafold_service._get_alphafold_data(test_sequence)
        
        if alphafold_data:
            print("✅ Datos de AlphaFold obtenidos:")
            print(f"   🔗 UniProt ID: {alphafold_data.get('uniprot_id')}")
            print(f"   🧬 Nombre: {alphafold_data.get('protein_name')}")
            print(f"   📊 Confianza promedio: {alphafold_data.get('confidence')}%")
            print(f"   📅 Versión: {alphafold_data.get('alphafold_version')}")
            print(f"   🏷️  Fuente: {alphafold_data.get('data_source')}")
        else:
            print("⚠️ No se obtuvieron datos de AlphaFold")
            
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("🚀 Iniciando test de nueva lógica SWISS-MODEL simplificada")
    print("=" * 60)
    print()
    
    # Solo test de SWISS-MODEL
    success, result = test_new_swiss_model_logic()
    
    if success:
        print("🎉 ¡Test completado exitosamente!")
        print("✅ Nueva lógica implementada correctamente")
        
        if result:
            print()
            print("📋 Información del modelo generado:")
            print(f"   📁 Ruta: {result.get('model_path')}")
            print(f"   📊 Confianza final: {result.get('confidence')}%")
    else:
        print("❌ Test falló")
        sys.exit(1)
