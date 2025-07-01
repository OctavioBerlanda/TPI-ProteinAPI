#!/usr/bin/env python3
"""
Script para regenerar los modelos CIF con el formato mejorado compatible con NGL
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config_dict
from src.business.alphafold_service import AlphaFoldService

def regenerate_demo_models():
    """Regenerar los modelos CIF con el formato mejorado"""
    print("🔧 Regenerando modelos CIF con formato mejorado")
    print("=" * 60)
    
    config = get_config_dict()
    alphafold_service = AlphaFoldService(config)
    
    # Secuencias de las comparaciones existentes
    demo_sequences = {
        "Hemoglobina Beta E6V_original": "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH",
        "Hemoglobina Beta E6V_mutated": "MVHLTPVEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    }
    
    models_generated = {}
    
    for name, sequence in demo_sequences.items():
        print(f"🧪 Generando modelo mejorado: {name}")
        
        try:
            # Usar el servicio de AlphaFold para generar el nuevo modelo
            result = alphafold_service.predict_structure(sequence, name)
            
            if result.get('model_path'):
                models_generated[name] = {
                    'path': result['model_path'],
                    'confidence': result.get('confidence', 95.0)
                }
                print(f"   ✅ Generado: {result['model_path']}")
                print(f"   📊 Confianza: {result.get('confidence', 95.0):.1f}%")
                
                # Verificar que el archivo existe y tiene contenido
                if os.path.exists(result['model_path']):
                    size = os.path.getsize(result['model_path'])
                    print(f"   📁 Tamaño: {size} bytes")
                    
                    # Mostrar las primeras líneas para verificar el formato
                    with open(result['model_path'], 'r') as f:
                        lines = [f.readline().strip() for _ in range(5)]
                        print(f"   📋 Primeras líneas:")
                        for line in lines:
                            if line:
                                print(f"      {line}")
                else:
                    print(f"   ❌ Error: Archivo no existe")
                    
            else:
                print(f"   ❌ Error: {result.get('error', 'Error desconocido')}")
                
        except Exception as e:
            print(f"   ❌ Excepción: {e}")
        
        print()
    
    if models_generated:
        print("🎉 ¡Modelos regenerados exitosamente!")
        print("\n📋 Resumen:")
        for name, info in models_generated.items():
            print(f"   - {name}: {info['path']}")
        
        print(f"\n🌐 Para probar:")
        print(f"1. Reinicia la aplicación Flask")
        print(f"2. Ve a: http://localhost:5000/comparison/2/alphafold")
        print(f"3. Prueba cargar los modelos 3D")
        
    else:
        print("❌ No se pudo generar ningún modelo")

if __name__ == "__main__":
    regenerate_demo_models()
