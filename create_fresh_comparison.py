#!/usr/bin/env python3
"""
Script para crear una nueva comparación desde cero con AlphaFold (.cif)
"""
import sys
import os

# Agregar el directorio raíz del proyecto al Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def create_fresh_comparison():
    """Crear una nueva comparación desde cero con datos de AlphaFold"""
    print("🧬 Creando comparación fresca con AlphaFold (.cif)")
    print("=" * 60)
    
    # Importar la aplicación Flask completa
    from src.presentation.app import create_app
    
    # Crear la aplicación con configuración de desarrollo
    app = create_app('development')
    
    with app.app_context():
        from src.business.comparison_manager import ComparisonManager
        from config.config import get_config_dict
        
        config = get_config_dict()
        comparison_manager = ComparisonManager(config)
        
        # Secuencias de demostración (hemoglobina beta con mutación E6V - anemia falciforme)
        original_seq = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
        mutated_seq = "MVHLTPVEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"  # E6V
        
        print(f"🧪 Secuencia original: {original_seq[:50]}...")
        print(f"🔬 Secuencia mutada:   {mutated_seq[:50]}...")
        print(f"🔄 Mutación: E->V en posición 6 (Glu6Val - anemia falciforme)")
        print(f"📏 Longitud: {len(original_seq)} aminoácidos")
        print()
        
        try:
            print("⚙️  Iniciando procesamiento con AlphaFold...")
            
            # Crear comparación con AlphaFold (esto debería funcionar ahora con nuestra corrección)
            result = comparison_manager.create_comparison_with_alphafold(
                username="test_user",
                email="test@proteins.com",
                original_sequence=original_seq,
                mutated_sequence=mutated_seq,
                comparison_name="Hemoglobina Beta E6V - Test Completo",
                description="Análisis completo de la mutación E6V que causa anemia falciforme usando archivos CIF",
                enable_alphafold=True
            )
            
            if result['success']:
                comparison_id = result['comparison_id']
                print(f"✅ Comparación creada exitosamente!")
                print(f"🆔 ID: {comparison_id}")
                
                # Obtener detalles para verificar el estado final
                details = comparison_manager.get_comparison_details(comparison_id)
                if details:
                    comp_data = details.get('comparison', {})
                    
                    print(f"\n📊 Estado final:")
                    print(f"📄 Estado: {comp_data.get('status', 'unknown')}")
                    print(f"📁 Modelo original: {comp_data.get('original_model_path', 'No disponible')}")
                    print(f"📁 Modelo mutado: {comp_data.get('mutated_model_path', 'No disponible')}")
                    
                    # Verificar que sean archivos .cif
                    original_path = comp_data.get('original_model_path')
                    mutated_path = comp_data.get('mutated_model_path')
                    
                    if original_path:
                        if original_path.endswith('.cif'):
                            print("✅ Modelo original es formato CIF")
                            if os.path.exists(original_path):
                                print(f"✅ Archivo original existe: {os.path.basename(original_path)}")
                            else:
                                print(f"❌ Archivo original NO existe: {original_path}")
                        else:
                            print(f"⚠️  Modelo original NO es CIF: {original_path}")
                    
                    if mutated_path:
                        if mutated_path.endswith('.cif'):
                            print("✅ Modelo mutado es formato CIF")
                            if os.path.exists(mutated_path):
                                print(f"✅ Archivo mutado existe: {os.path.basename(mutated_path)}")
                            else:
                                print(f"❌ Archivo mutado NO existe: {mutated_path}")
                        else:
                            print(f"⚠️  Modelo mutado NO es CIF: {mutated_path}")
                    
                    print(f"\n📈 Métricas:")
                    print(f"📊 Confianza original: {comp_data.get('original_confidence_score', 0)} / 100")
                    print(f"📊 Confianza mutada: {comp_data.get('mutated_confidence_score', 0)} / 100")
                    print(f"📏 RMSD: {comp_data.get('rmsd_value', 0)} Å")
                    print(f"⏱️  Tiempo procesamiento: {comp_data.get('processing_time', 0)} seg")
                
                print(f"\n🌐 URLs para testing:")
                print(f"📄 Resultados: http://localhost:5000/comparison/{comparison_id}")
                print(f"🧊 Visualizador 3D: http://localhost:5000/comparison/{comparison_id}/alphafold")
                print(f"🔗 API Original: http://localhost:5000/api/comparison/{comparison_id}/model/original/view")
                print(f"🔗 API Mutado: http://localhost:5000/api/comparison/{comparison_id}/model/mutated/view")
                
                print(f"\n🎯 Para probar la visualización 3D:")
                print(f"1. La aplicación Flask debe estar corriendo (python run_app.py)")
                print(f"2. Abre: http://localhost:5000/comparison/{comparison_id}/alphafold")
                print(f"3. Usa los botones para cargar los modelos en NGL Viewer")
                
            else:
                print("❌ Error creando comparación:")
                for error in result.get('errors', []):
                    print(f"   - {error}")
                    
        except Exception as e:
            print(f"❌ Excepción: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_fresh_comparison()
