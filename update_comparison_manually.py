#!/usr/bin/env python3
"""
Script para actualizar manualmente la comparación con los archivos .cif existentes
"""
import sys
import os
import json

# Agregar el directorio raíz del proyecto al Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def update_comparison_manually():
    """Actualizar manualmente la comparación ID 7 con los archivos .cif"""
    print("🔧 Actualizando comparación manualmente")
    print("=" * 50)
    
    # Importar la aplicación Flask completa
    from src.presentation.app import create_app
    
    # Crear la aplicación con configuración de desarrollo
    app = create_app('development')
    
    with app.app_context():
        from src.data.models import db, ProteinComparison
        
        # Buscar la comparación ID 7
        comparison = ProteinComparison.query.filter_by(id=7).first()
        if not comparison:
            print("❌ No se encontró la comparación ID 7")
            return
        
        print(f"📝 Comparación encontrada: {comparison.comparison_name}")
        
        # Definir las rutas de los archivos .cif que sabemos que existen
        original_path = "models/alphafold/Test Hemoglobina Beta - E6V_original_1751337537.cif"
        mutated_path = "models/alphafold/Test Hemoglobina Beta - E6V_mutated_1751337541.cif"
        
        # Verificar que los archivos existan
        if not os.path.exists(original_path):
            print(f"❌ Archivo original no existe: {original_path}")
            return
            
        if not os.path.exists(mutated_path):
            print(f"❌ Archivo mutado no existe: {mutated_path}")
            return
            
        print(f"✅ Archivo original existe: {original_path}")
        print(f"✅ Archivo mutado existe: {mutated_path}")
        
        # Crear datos estructurales simulados
        structural_changes = {
            'confidence_change': 0,
            'stability_impact': 'stable',
            'predicted_effect': 'pathogenic',  # E6V causa anemia falciforme
            'structural_regions_affected': ['beta-globin chain'],
            'domain_changes': 'minor'
        }
        
        # Actualizar los campos
        comparison.original_model_path = original_path
        comparison.mutated_model_path = mutated_path
        comparison.original_confidence_score = 95.0
        comparison.mutated_confidence_score = 94.0
        comparison.alphafold_job_id = "demo_Test Hemoglobina Beta - E6V"
        comparison.processing_time = 8.5
        comparison.structural_changes = json.dumps(structural_changes)
        comparison.rmsd_value = 0.8  # RMSD típico para mutación E6V
        comparison.status = 'completed'
        
        try:
            db.session.commit()
            print("✅ Comparación actualizada exitosamente!")
            
            # Verificar la actualización
            updated_comp = ProteinComparison.query.filter_by(id=7).first()
            print(f"📁 Modelo original: {updated_comp.original_model_path}")
            print(f"📁 Modelo mutado: {updated_comp.mutated_model_path}")
            print(f"📊 Confianza original: {updated_comp.original_confidence_score}%")
            print(f"📊 Confianza mutada: {updated_comp.mutated_confidence_score}%")
            print(f"📏 RMSD: {updated_comp.rmsd_value} Å")
            print(f"📄 Estado: {updated_comp.status}")
            
            print(f"\n🌐 URLs para testing:")
            print(f"📄 Resultados: http://localhost:5000/comparison/7")
            print(f"🧊 AlphaFold: http://localhost:5000/comparison/7/alphafold")
            print(f"🔗 API Original: http://localhost:5000/api/comparison/7/model/original/view")
            print(f"🔗 API Mutado: http://localhost:5000/api/comparison/7/model/mutated/view")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error actualizando: {e}")

if __name__ == '__main__':
    update_comparison_manually()
