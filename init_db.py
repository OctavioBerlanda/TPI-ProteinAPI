"""
Script para inicializar la base de datos correctamente
Ejecutar: python init_db.py
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.presentation.app import create_app
from src.data.models import db, User

def init_database():
    """Inicializa la base de datos creando todas las tablas"""
    print("🔧 Inicializando base de datos...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Eliminar todas las tablas existentes
            print("⚠️  Eliminando tablas existentes...")
            db.drop_all()
            
            # Crear todas las tablas
            print("✅ Creando nuevas tablas...")
            db.create_all()
            
            # Crear usuario por defecto
            print("👤 Creando usuario por defecto...")
            default_user = User(
                username='admin',
                email='admin@protein.local'
            )
            
            # Verificar si ya existe
            existing_user = User.query.filter_by(username='admin').first()
            if not existing_user:
                db.session.add(default_user)
                db.session.commit()
                print(f"✅ Usuario creado: {default_user.username}")
            else:
                print(f"ℹ️  Usuario ya existe: {existing_user.username}")
            
            print("\n🎉 ¡Base de datos inicializada correctamente!")
            print("📊 Tablas creadas:")
            print("   - users")
            print("   - protein_comparisons")
            
        except Exception as e:
            print(f"\n❌ Error al inicializar base de datos: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    init_database()
