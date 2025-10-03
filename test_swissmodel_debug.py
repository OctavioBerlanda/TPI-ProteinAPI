#!/usr/bin/env python3
"""
Script de prueba para debugging de predicciones SwissModel
"""
import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.business.swissmodel_service import SwissModelService
from config.config import get_config

def test_swissmodel_predictions():
    """Prueba las predicciones con secuencias de diferentes longitudes"""

    print("🧪 PRUEBA DE PREDICCIONES SWISSMODEL")
    print("=" * 50)

    # Configurar servicio
    config = get_config()
    service = SwissModelService(config)

    # Secuencias de prueba (largas para que funcionen)
    test_sequences = [
        ("Corta (22aa)", "MAETKGRLIVFLASVWCQDH"),  # Esta fallará
        ("Media (50aa)", "MAETKGRLIVFLASVWCQDHMAETKGRLIVFLASVWCQDHMAETKGRLIV"),  # Esta debería funcionar
        ("Larga (100aa)", "MAETKGRLIVFLASVWCQDHMAETKGRLIVFLASVWCQDHMAETKGRLIVFLASVWCQDHMAETKGRLIVFLASVWCQDHMAETKGRLIVFLASVWCQDH")  # Esta definitivamente funciona
    ]

    for name, sequence in test_sequences:
        print(f"\n🔬 Probando {name}: {len(sequence)} residuos")
        print(f"   Secuencia: {sequence}")

        try:
            result = service.predict_structure(sequence, f"test_{name.lower().replace(' ', '_')}", return_all_models=True)

            if 'models' in result:
                print(f"   ✅ ÉXITO: {len(result['models'])} modelos generados")
                for i, model in enumerate(result['models'][:3]):  # Mostrar primeros 3
                    print(f"      Modelo {i+1}: GMQE={model.get('gmqe_score', 'N/A'):.3f}")
            else:
                print(f"   ✅ ÉXITO: 1 modelo generado, GMQE={result.get('gmqe_score', 'N/A'):.3f}")

        except Exception as e:
            print(f"   ❌ ERROR: {e}")

if __name__ == "__main__":
    test_swissmodel_predictions()