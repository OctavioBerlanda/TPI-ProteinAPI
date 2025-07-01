#!/usr/bin/env python3
"""
Script para verificar el estado de la base de datos
"""
import sys
import os

# Agregar el directorio raíz del proyecto al Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def check_database():
    """Verificar el estado de las comparaciones en la base de datos"""
    print("🔍 Verificando estado de la base de datos")
    print("=" * 50)
    
    # Importar la aplicación Flask completa
    from src.presentation.app import create_app
    
    # Crear la aplicación con configuración de desarrollo
    app = create_app('development')
    
    with app.app_context():
        from src.data.models import db, ProteinComparison
        
        # Obtener las últimas 5 comparaciones
        comparisons = ProteinComparison.query.order_by(ProteinComparison.created_at.desc()).limit(5).all()
        
        print(f"📊 Total de comparaciones encontradas: {len(comparisons)}")
        print()
        
        for comp in comparisons:
            print(f"🆔 ID: {comp.id}")
            print(f"📝 Nombre: {comp.comparison_name}")
            print(f"👤 Usuario ID: {comp.user_id}")
            print(f"📄 Estado: {comp.status}")
            print(f"📁 Modelo original: {comp.original_model_path}")
            print(f"📁 Modelo mutado: {comp.mutated_model_path}")
            print(f"📊 Confianza original: {comp.original_confidence_score}")
            print(f"📊 Confianza mutada: {comp.mutated_confidence_score}")
            print(f"📏 RMSD: {comp.rmsd_value}")
            print(f"⏰ Creado: {comp.created_at}")
            
            # Verificar si los archivos existen
            if comp.original_model_path:
                import os
                if os.path.exists(comp.original_model_path):
                    print(f"✅ Archivo original existe: {comp.original_model_path}")
                else:
                    print(f"❌ Archivo original NO existe: {comp.original_model_path}")
                    
            if comp.mutated_model_path:
                if os.path.exists(comp.mutated_model_path):
                    print(f"✅ Archivo mutado existe: {comp.mutated_model_path}")
                else:
                    print(f"❌ Archivo mutado NO existe: {comp.mutated_model_path}")
                    
            print("-" * 50)

if __name__ == '__main__':
    check_database()
