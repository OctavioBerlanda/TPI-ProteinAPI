import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base para la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuración de base de datos
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = os.environ.get('DB_PORT') or '3306'
    DB_NAME = os.environ.get('DB_NAME') or 'protein_comparison_db'
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or ''
    
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de APIs
    ALPHAFOLD_API_BASE_URL = os.environ.get('ALPHAFOLD_API_BASE_URL') or 'https://alphafold.ebi.ac.uk/api'
    UNIPROT_API_BASE_URL = os.environ.get('UNIPROT_API_BASE_URL') or 'https://rest.uniprot.org/uniprotkb'
    ALPHAFOLD_API_ENDPOINT = os.environ.get('ALPHAFOLD_API_ENDPOINT') or 'https://alphafolddb.org/api'
    COLABFOLD_ENDPOINT = os.environ.get('COLABFOLD_ENDPOINT') or 'http://localhost:8080'
    
    # Configuración de AlphaFold
    MODELS_DIRECTORY = os.environ.get('MODELS_DIRECTORY') or 'models/alphafold'
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', '300'))  # 5 minutos por defecto
    MAX_SEQUENCE_LENGTH = int(os.environ.get('MAX_SEQUENCE_LENGTH', '2000'))
    ENABLE_ALPHAFOLD = os.environ.get('ENABLE_ALPHAFOLD', 'true').lower() == 'true'

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name='development'):
    """Obtiene la configuración especificada"""
    return config.get(config_name, DevelopmentConfig)

def get_config_dict(config_name='development'):
    """Obtiene la configuración como diccionario"""
    config_class = get_config(config_name)
    return {
        'ALPHAFOLD_API_ENDPOINT': config_class.ALPHAFOLD_API_ENDPOINT,
        'COLABFOLD_ENDPOINT': config_class.COLABFOLD_ENDPOINT,
        'MODELS_DIRECTORY': config_class.MODELS_DIRECTORY,
        'API_TIMEOUT': config_class.API_TIMEOUT,
        'MAX_SEQUENCE_LENGTH': config_class.MAX_SEQUENCE_LENGTH,
        'ENABLE_ALPHAFOLD': config_class.ENABLE_ALPHAFOLD
    }
