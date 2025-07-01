#!/usr/bin/env python3
"""
Script para limpiar y recrear la base de datos
"""
import sys
import os

# Agregar el directorio raíz del proyecto al Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def reset_database():
    """Limpiar y recrear la base de datos"""
    print("🗑️  Limpiando y recreando la base de datos")
    print("=" * 50)
    
    # Importar la aplicación Flask completa
    from src.presentation.app import create_app
    
    # Crear la aplicación con configuración de desarrollo
    app = create_app('development')
    
    with app.app_context():
        from src.data.models import db
        
        print("🔄 Eliminando todas las tablas...")
        db.drop_all()
        
        print("🏗️  Creando tablas nuevas...")
        db.create_all()
        
        print("✅ Base de datos recreada exitosamente!")
        print()
        
        # Verificar que las tablas estén vacías
        from src.data.models import ProteinComparison, User
        
        users_count = User.query.count()
        comparisons_count = ProteinComparison.query.count()
        
        print(f"👥 Usuarios en la BD: {users_count}")
        print(f"🧬 Comparaciones en la BD: {comparisons_count}")
        
        if users_count == 0 and comparisons_count == 0:
            print("✅ Base de datos limpia y lista para usar")
        else:
            print("⚠️  Algo no salió bien, aún hay datos")

if __name__ == '__main__':
    reset_database()
