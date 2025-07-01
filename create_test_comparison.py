#!/usr/bin/env python3
"""
Script para crear una comparación de prueba con datos de AlphaFold
"""
import os
import sys

# Agregar el directorio actual al Python path
sys.path.insert(0, os.getcwd())

def create_test_comparison():
    """Crear una comparación de prueba con datos de AlphaFold"""
    print("🧬 Creando comparación de prueba con AlphaFold")
    print("=" * 60)
    
    from flask import Flask
    from src.business.comparison_manager import ComparisonManager
    from config.config import get_config_dict
    
    # Crear contexto de aplicación Flask
    app = Flask(__name__)
    app.config.update(get_config_dict())
    
    with app.app_context():
        config = get_config_dict()
        comparison_manager = ComparisonManager(config)
        
        # Secuencias de demostración
        original_seq = "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG"
        mutated_seq = "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGFVLAGG"  # Y->F
    
        print(f"🧪 Secuencia original: {original_seq[:30]}...")
        print(f"🔬 Secuencia mutada:   {mutated_seq[:30]}...")
        print(f"🔄 Mutación: Y->F en posición 60")
        print()
        
        try:
            # Crear comparación con AlphaFold
            result = comparison_manager.create_comparison_with_alphafold(
                username="demo_user",
                email="demo@proteins.com",
                original_sequence=original_seq,
                mutated_sequence=mutated_seq,
                comparison_name="Demo con Visualizador 3D",
                description="Comparación de demostración con archivos CIF para el visualizador NGL",
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
                    print(f"📁 Modelo original: {comp_data.get('original_model_path', 'No disponible')}")
                    print(f"📁 Modelo mutado: {comp_data.get('mutated_model_path', 'No disponible')}")
                    print(f"📊 Confianza original: {comp_data.get('original_confidence_score', 0):.1f}%")
                    print(f"📊 Confianza mutada: {comp_data.get('mutated_confidence_score', 0):.1f}%")
                    print(f"📏 RMSD: {comp_data.get('rmsd_value', 0):.3f} Å")
                
                print(f"\n🌐 URLs para testing:")
                print(f"📄 Resultados: http://localhost:5000/comparison/{comparison_id}")
                print(f"🧊 AlphaFold: http://localhost:5000/comparison/{comparison_id}/alphafold")
                print(f"🔗 API Original: http://localhost:5000/api/comparison/{comparison_id}/model/original/view")
                print(f"🔗 API Mutado: http://localhost:5000/api/comparison/{comparison_id}/model/mutated/view")
                
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
