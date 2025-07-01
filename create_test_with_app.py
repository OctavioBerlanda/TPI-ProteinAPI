#!/usr/bin/env python3
"""
Script para crear una comparación de prueba usando la infraestructura completa de la app
"""
import sys
import os

# Agregar el directorio raíz del proyecto al Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def create_test_comparison():
    """Crear una comparación de prueba con datos de AlphaFold"""
    print("🧬 Creando comparación de prueba con AlphaFold (.cif)")
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
        
        # Secuencias de demostración (hemoglobina beta con mutación causante de anemia falciforme)
        original_seq = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
        mutated_seq = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH".replace("E", "V", 1)  # E6V mutación
        
        print(f"🧪 Secuencia original: {original_seq[:50]}...")
        print(f"🔬 Secuencia mutada:   {mutated_seq[:50]}...")
        print(f"🔄 Mutación: E6V (anemia falciforme)")
        print()
        
        try:
            # Crear comparación con AlphaFold
            result = comparison_manager.create_comparison_with_alphafold(
                username="test_user",
                email="test@proteins.com",
                original_sequence=original_seq,
                mutated_sequence=mutated_seq,
                comparison_name="Test Hemoglobina Beta - E6V",
                description="Comparación de demostración con archivos CIF para visualizar la mutación E6V (anemia falciforme)",
                enable_alphafold=True
            )
            
            if result['success']:
                comparison_id = result['comparison_id']
                print(f"✅ Comparación creada exitosamente!")
                print(f"🆔 ID: {comparison_id}")
                
                # Obtener detalles para verificar
                details = comparison_manager.get_comparison_details(comparison_id)
                if details:
                    comp_data = details.get('comparison', {})
                    original_path = comp_data.get('original_model_path', 'No disponible')
                    mutated_path = comp_data.get('mutated_model_path', 'No disponible')
                    
                    print(f"📁 Modelo original: {original_path}")
                    print(f"📁 Modelo mutado: {mutated_path}")
                    
                    # Verificar que sean archivos .cif
                    if original_path and original_path.endswith('.cif'):
                        print("✅ Modelo original es formato CIF")
                    if mutated_path and mutated_path.endswith('.cif'):
                        print("✅ Modelo mutado es formato CIF")
                    
                    print(f"📊 Confianza original: {comp_data.get('original_confidence_score', 0):.1f}%")
                    print(f"📊 Confianza mutada: {comp_data.get('mutated_confidence_score', 0):.1f}%")
                    print(f"📏 RMSD: {comp_data.get('rmsd_value', 0):.3f} Å")
                
                print(f"\n🌐 URLs para testing:")
                print(f"📄 Resultados: http://localhost:5000/comparison/{comparison_id}")
                print(f"🧊 AlphaFold: http://localhost:5000/comparison/{comparison_id}/alphafold")
                print(f"🔗 API Original: http://localhost:5000/api/comparison/{comparison_id}/model/original/view")
                print(f"🔗 API Mutado: http://localhost:5000/api/comparison/{comparison_id}/model/mutated/view")
                
                print(f"\n📝 Para probar la visualización:")
                print(f"1. Ejecuta: python run_app.py")
                print(f"2. Abre: http://localhost:5000/comparison/{comparison_id}/alphafold")
                print(f"3. Usa los botones para cargar los modelos 3D")
                
            else:
                print("❌ Error creando comparación:")
                for error in result.get('errors', []):
                    print(f"   - {error}")
                    
        except Exception as e:
            print(f"❌ Excepción: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_test_comparison()
