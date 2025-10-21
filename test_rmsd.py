#!/usr/bin/env python3
"""
Script de prueba para la funcionalidad de RMSD con PyMOL
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.config import get_config_dict
from src.business.swissmodel_service import SwissModelService

def test_rmsd_calculation():
    """Prueba el cálculo de RMSD con archivos de ejemplo"""

    # Configurar servicio
    config = get_config_dict()
    swiss_service = SwissModelService(config)

    # Archivos de prueba (deben existir)
    original_pdb = "models/swissmodel/original_test.pdb"
    mutated_pdb = "models/swissmodel/mutated_test.pdb"

    # Verificar que existan los archivos
    if not os.path.exists(original_pdb):
        print(f"❌ Archivo original no encontrado: {original_pdb}")
        return

    if not os.path.exists(mutated_pdb):
        print(f"❌ Archivo mutado no encontrado: {mutated_pdb}")
        return

    print("🔬 Probando cálculo de RMSD...")
    print(f"📁 Original: {original_pdb}")
    print(f"📁 Mutado: {mutated_pdb}")
    print()

    try:
        # Calcular RMSD
        result = swiss_service.calculate_rmsd_with_pymol(original_pdb, mutated_pdb)

        print("📊 RESULTADOS:")
        print(f"   RMSD: {result.get('rmsd', 'N/A')} Å")
        print(f"   Método: {result.get('method', 'N/A')}")
        print(f"   Unidades: {result.get('units', 'N/A')}")
        print()
        print("🔍 INTERPRETACIÓN:")
        print(f"   {result.get('interpretation', 'No disponible')}")
        print()

        if result.get('note'):
            print(f"📝 Nota: {result['note']}")

        if result.get('pymol_output'):
            print("🐍 Salida PyMOL (primeras líneas):")
            lines = result['pymol_output'].split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"   {line}")

    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rmsd_calculation()