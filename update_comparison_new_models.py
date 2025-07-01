#!/usr/bin/env python3
"""
Script para actualizar la comparación existente con los nuevos archivos CIF mejorados
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.presentation.app import create_app

def update_comparison_with_new_models():
    """Actualizar la comparación con los nuevos modelos CIF"""
    print("🔧 Actualizando comparación con nuevos modelos CIF")
    print("=" * 60)
    
    # Crear la aplicación Flask
    app = create_app('development')
    
    with app.app_context():
        from src.data.models import db, ProteinComparison
        
        # Buscar la comparación ID 2
        comparison = ProteinComparison.query.filter_by(id=2).first()
        if not comparison:
            print("❌ No se encontró la comparación ID 2")
            return
        
        print(f"📝 Comparación encontrada: {comparison.comparison_name}")
        
        # Nuevos archivos CIF generados
        new_original_path = "models/alphafold\\Hemoglobina Beta E6V_original_1751342175.cif"
        new_mutated_path = "models/alphafold\\Hemoglobina Beta E6V_mutated_1751342179.cif"
        
        # Verificar que los archivos existan
        if not os.path.exists(new_original_path):
            print(f"❌ Archivo original no existe: {new_original_path}")
            return
            
        if not os.path.exists(new_mutated_path):
            print(f"❌ Archivo mutado no existe: {new_mutated_path}")
            return
            
        print(f"✅ Archivo original existe: {new_original_path}")
        print(f"✅ Archivo mutado existe: {new_mutated_path}")
        
        # Actualizar las rutas en la base de datos
        comparison.original_model_path = new_original_path
        comparison.mutated_model_path = new_mutated_path
        
        try:
            db.session.commit()
            print("✅ Comparación actualizada exitosamente!")
            
            # Verificar la actualización
            updated_comp = ProteinComparison.query.filter_by(id=2).first()
            print(f"📁 Modelo original: {updated_comp.original_model_path}")
            print(f"📁 Modelo mutado: {updated_comp.mutated_model_path}")
            
            print(f"\n🌐 URLs para testing:")
            print(f"📄 Resultados: http://localhost:5000/comparison/2")
            print(f"🧊 AlphaFold: http://localhost:5000/comparison/2/alphafold")
            print(f"🔗 API Original: http://localhost:5000/api/comparison/2/model/original/view.cif")
            print(f"🔗 API Mutado: http://localhost:5000/api/comparison/2/model/mutated/view.cif")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error actualizando: {e}")

if __name__ == "__main__":
    update_comparison_with_new_models()
