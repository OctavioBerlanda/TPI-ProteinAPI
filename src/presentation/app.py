import os
import sys

# Agregar el directorio raíz al path si no estamos ejecutando desde la raíz
if 'src' in os.getcwd():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.config import config
from src.data.models import db

def create_app(config_name='default'):
    """Factory function para crear la aplicación Flask"""
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    db.init_app(app)
    
    # Registrar blueprints
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # Crear tablas de base de datos
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tablas de base de datos creadas/verificadas exitosamente")
        except Exception as e:
            print(f"❌ Error al crear tablas de base de datos: {e}")
    
    return app

# Para desarrollo directo
if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
