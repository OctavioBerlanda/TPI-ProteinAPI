#!/usr/bin/env python3
"""
Script para crear una comparación con secuencias reales de hemoglobina
que se pueden encontrar en AlphaFold DB
"""

import sys
import os

#!/usr/bin/env python3
"""
Script para crear una comparación con secuencias reales de hemoglobina
que se pueden encontrar en AlphaFold DB
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.business.comparison_manager import ComparisonManager

def create_real_hemoglobin_comparison():
    """Crear comparación con secuencias reales de hemoglobina beta"""
    
    # Secuencias reales de hemoglobina beta humana
    # Esta secuencia debería estar en AlphaFold DB (UniProt: P68871)
    original_sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    
    # Secuencia mutada (cambio E6V - mutación real asociada con anemia falciforme)
    mutated_sequence = "MVHLTPVEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    
    print("🧬 Creando comparación con secuencias REALES de hemoglobina beta")
    print("=" * 60)
    print(f"📊 Secuencia original ({len(original_sequence)} aa):")
    print(f"   {original_sequence[:50]}...")
    print(f"📊 Secuencia mutada ({len(mutated_sequence)} aa):")
    print(f"   {mutated_sequence[:50]}...")
    print(f"🔄 Mutación: E6V (Posición 6: E→V)")
    print()
    
    try:
        # Configuración simple
        config = {
            'ALPHAFOLD_API_ENDPOINT': 'https://alphafolddb.org/api',
            'MODELS_DIRECTORY': 'models/alphafold',
            'API_TIMEOUT': 300
        }
        
        # Crear manager
        comparison_manager = ComparisonManager(config)
        
        # Crear comparación con AlphaFold habilitado
        result = comparison_manager.create_comparison_with_alphafold(
            username="demo_real",
            email="demo_real@example.com",
            original_sequence=original_sequence,
            mutated_sequence=mutated_sequence,
            comparison_name="Hemoglobina Beta Real E6V",
            description="Comparación con secuencias reales de hemoglobina beta humana (P68871) - mutación E6V asociada con anemia falciforme",
            enable_alphafold=True
        )
        
        if result['success']:
            comparison_id = result['comparison_id']
            print(f"✅ Comparación creada exitosamente con ID: {comparison_id}")
            
            # Mostrar información de AlphaFold
            alphafold_results = result.get('alphafold_results', {})
            if alphafold_results:
                original_result = alphafold_results.get('original', {})
                mutated_result = alphafold_results.get('mutated', {})
                
                print(f"\n🧊 Resultados de predicción estructural:")
                print(f"   📁 Original: {original_result.get('model_path', 'No disponible')}")
                print(f"   📁 Mutado: {mutated_result.get('model_path', 'No disponible')}")
                print(f"   📊 Confianza original: {original_result.get('confidence', 0):.1f}%")
                print(f"   📊 Confianza mutado: {mutated_result.get('confidence', 0):.1f}%")
                print(f"   🔬 Método: {original_result.get('prediction_method', 'Desconocido')}")
                
            print(f"\n🌐 URLs para testing:")
            print(f"   📄 Resultados: http://localhost:5000/comparison/{comparison_id}")
            print(f"   🧊 AlphaFold: http://localhost:5000/comparison/{comparison_id}/alphafold")
            print(f"   🔗 API Original: http://localhost:5000/api/comparison/{comparison_id}/model/original/view.cif")
            print(f"   🔗 API Mutado: http://localhost:5000/api/comparison/{comparison_id}/model/mutated/view.cif")
            
            print(f"\n🎯 Para ver la estructura REAL de hemoglobina:")
            print(f"   1. Ejecuta: python app.py")
            print(f"   2. Visita: http://localhost:5000/comparison/{comparison_id}/alphafold")
            print(f"   3. Verifica si se descargó una estructura real de AlphaFold DB")
            
        else:
            print("❌ Error creando comparación:")
            for error in result.get('errors', []):
                print(f"   - {error}")
                
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_real_hemoglobin_comparison()
