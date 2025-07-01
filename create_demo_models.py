#!/usr/bin/env python3
"""
Script para crear modelos de demostración para el visualizador 3D
"""
import os
import sys

# Agregar el directorio actual al Python path
sys.path.insert(0, os.getcwd())

from src.business.alphafold_service import AlphaFoldService
from config.config import get_config_dict

def create_demo_models():
    """Crear modelos de demostración para testing"""
    print("🧬 Creando modelos de demostración para el visualizador 3D")
    print("=" * 60)
    
    config = get_config_dict()
    alphafold_service = AlphaFoldService(config)
    
    # Crear directorio de modelos si no existe
    models_dir = "models/alphafold"
    os.makedirs(models_dir, exist_ok=True)
    
    # Secuencias de demostración (pequeñas para testing)
    demo_sequences = {
        "original": "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG",
        "mutated": "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGFVLAGG"  # Y->F mutation
    }
    
    print(f"📁 Directorio de modelos: {models_dir}")
    print(f"🧪 Secuencia original: {demo_sequences['original'][:30]}...")
    print(f"🔬 Secuencia mutada:   {demo_sequences['mutated'][:30]}...")
    print(f"🔄 Mutación: Y->F en posición 60")
    print()
    
    # Generar modelos
    models = {}
    for seq_type, sequence in demo_sequences.items():
        print(f"⚗️  Generando modelo {seq_type}...")
        
        try:
            result = alphafold_service.predict_structure(sequence)
            
            if result['success']:
                model_path = result['model_path']
                confidence_score = result['confidence_score']
                
                # Mover el archivo al directorio correcto si es necesario
                final_path = os.path.join(models_dir, f"demo_{seq_type}_model.pdb")
                if model_path != final_path:
                    import shutil
                    shutil.move(model_path, final_path)
                    model_path = final_path
                
                models[seq_type] = {
                    'path': model_path,
                    'confidence': confidence_score
                }
                
                print(f"   ✅ {seq_type.title()}: {model_path}")
                print(f"   📊 Confianza: {confidence_score:.1f}%")
                
            else:
                print(f"   ❌ Error: {result.get('error', 'Error desconocido')}")
                
        except Exception as e:
            print(f"   ❌ Excepción: {e}")
        
        print()
    
    # Crear comparación demo si ambos modelos fueron generados
    if len(models) == 2:
        print("🔬 Analizando diferencias estructurales...")
        
        try:
            comparison_result = alphafold_service.compare_structures(
                models['original']['path'],
                models['mutated']['path']
            )
            
            if comparison_result['success']:
                rmsd = comparison_result['rmsd_value']
                changes = comparison_result['structural_changes']
                
                print(f"   📏 RMSD: {rmsd:.3f} Ångströms")
                print(f"   🔍 Cambios: {changes}")
                
                # Crear archivo de información
                info_file = os.path.join(models_dir, "demo_comparison_info.txt")
                with open(info_file, 'w') as f:
                    f.write("DEMOSTRACIÓN - Comparación de Estructuras AlphaFold\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Secuencia Original: {demo_sequences['original']}\n")
                    f.write(f"Secuencia Mutada:   {demo_sequences['mutated']}\n\n")
                    f.write(f"Modelos generados:\n")
                    f.write(f"- Original: {models['original']['path']}\n")
                    f.write(f"- Mutado:   {models['mutated']['path']}\n\n")
                    f.write(f"Análisis:\n")
                    f.write(f"- RMSD: {rmsd:.3f} Ångströms\n")
                    f.write(f"- Confianza Original: {models['original']['confidence']:.1f}%\n")
                    f.write(f"- Confianza Mutada: {models['mutated']['confidence']:.1f}%\n")
                    f.write(f"- Cambios: {changes}\n")
                
                print(f"   📄 Información guardada en: {info_file}")
            
        except Exception as e:
            print(f"   ❌ Error en comparación: {e}")
    
    print("\n🎉 ¡Modelos de demostración creados!")
    print("\n📋 Para usar en la aplicación:")
    print("1. Ejecuta la aplicación: python app.py")
    print("2. Crea una nueva comparación con AlphaFold habilitado")
    print("3. Ve a la página de resultados AlphaFold")
    print("4. Los modelos aparecerán en el visualizador 3D")
    print("\n🌐 O accede directamente a los archivos:")
    for seq_type, model in models.items():
        print(f"   - {seq_type.title()}: {model['path']}")

if __name__ == '__main__':
    create_demo_models()
