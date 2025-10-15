"""
Configuración de Modeller para mutación de proteínas.
"""

import os
from dotenv import load_dotenv

load_dotenv()

MODELLER_CONFIG = {
    # Licencia académica de Modeller
    'license_key': os.getenv('MODELLER_LICENSE_KEY', 'MODELIRANJE'),
    
    # Nivel de optimización por defecto
    'default_optimization': os.getenv('MODELLER_OPTIMIZATION_LEVEL', 'high'),
    
    # Parámetros de optimización por nivel
    'optimization_params': {
        'low': {
            'conjugate_gradients_iterations': 100,
            'molecular_dynamics_steps': 0,  # Sin MD
            'local_optimization_radius': 8.0
        },
        'medium': {
            'conjugate_gradients_iterations': 300,
            'molecular_dynamics_steps': 100,
            'local_optimization_radius': 10.0
        },
        'high': {
            'conjugate_gradients_iterations': 500,
            'molecular_dynamics_steps': 300,
            'local_optimization_radius': 12.0
        }
    },
    
    # Parámetros de dinámica molecular
    'md_params': {
        'temperature': 300,  # Kelvin
        'equilibration_steps': 50,
        'production_steps': 300
    },
    
    # Umbrales de calidad
    'quality_thresholds': {
        'dope_per_residue_good': -0.03,
        'dope_per_residue_acceptable': 0.0,
        'max_acceptable_dope': 50000
    },
    
    # Opciones de rotámeros
    'rotamer_options': {
        'library': 'dunbrack',  # Biblioteca Dunbrack de rotámeros
        'num_rotamers': 5,  # Número de rotámeros a considerar
        'clash_threshold': 2.0  # Distancia mínima en Angstroms
    }
}


def get_modeller_config():
    """Retorna la configuración de Modeller."""
    return MODELLER_CONFIG


def validate_license():
    """Valida que la licencia de Modeller esté configurada."""
    if not MODELLER_CONFIG['license_key'] or MODELLER_CONFIG['license_key'] == '':
        raise ValueError(
            "Modeller license key no configurada. "
            "Por favor agrega MODELLER_LICENSE_KEY a tu archivo .env"
        )
    return True
