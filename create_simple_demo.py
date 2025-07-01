#!/usr/bin/env python3
"""
Script simplificado para crear archivos PDB de demostración
"""
import os

def create_simple_demo_pdb():
    """Crear archivos PDB de demostración simples"""
    print("🧬 Creando archivos PDB de demostración simples")
    print("=" * 60)
    
    # Crear directorio
    models_dir = "models/alphafold"
    os.makedirs(models_dir, exist_ok=True)
    
    # Contenido PDB básico para demostración (estructura de una hélice alfa simple)
    pdb_content_original = """HEADER    DEMO PROTEIN ORIGINAL                   30-JUN-25   DEMO
TITLE     DEMO ALPHAFOLD STRUCTURE - ORIGINAL
ATOM      1  N   ALA A   1      -8.901   4.127  -0.555  1.00 85.00           N  
ATOM      2  CA  ALA A   1      -8.608   3.135  -1.618  1.00 85.00           C  
ATOM      3  C   ALA A   1      -7.221   2.458  -1.897  1.00 85.00           C  
ATOM      4  O   ALA A   1      -6.632   1.846  -1.015  1.00 85.00           O  
ATOM      5  CB  ALA A   1      -9.025   3.712  -2.970  1.00 85.00           C  
ATOM      6  N   LEU A   2      -6.849   2.515  -3.137  1.00 90.00           N  
ATOM      7  CA  LEU A   2      -5.618   1.867  -3.612  1.00 90.00           C  
ATOM      8  C   LEU A   2      -4.872   2.707  -4.661  1.00 90.00           C  
ATOM      9  O   LEU A   2      -5.276   3.732  -5.219  1.00 90.00           O  
ATOM     10  CB  LEU A   2      -6.012   0.529  -4.273  1.00 90.00           C  
ATOM     11  N   VAL A   3      -3.678   2.321  -4.843  1.00 88.00           N  
ATOM     12  CA  VAL A   3      -2.851   2.983  -5.844  1.00 88.00           C  
ATOM     13  C   VAL A   3      -1.421   2.385  -6.021  1.00 88.00           C  
ATOM     14  O   VAL A   3      -0.892   1.734  -5.135  1.00 88.00           O  
ATOM     15  CB  VAL A   3      -3.489   3.058  -7.237  1.00 88.00           C  
ATOM     16  N   TYR A   4      -0.934   2.572  -7.223  1.00 92.00           N  
ATOM     17  CA  TYR A   4       0.421   2.051  -7.515  1.00 92.00           C  
ATOM     18  C   TYR A   4       1.452   2.991  -8.162  1.00 92.00           C  
ATOM     19  O   TYR A   4       1.142   4.081  -8.665  1.00 92.00           O  
ATOM     20  CB  TYR A   4       0.221   0.813  -8.392  1.00 92.00           C  
ATOM     21  CG  TYR A   4      -0.584  -0.298  -7.771  1.00 92.00           C  
ATOM     22  CD1 TYR A   4      -1.891  -0.081  -7.321  1.00 92.00           C  
ATOM     23  CD2 TYR A   4      -0.089  -1.575  -7.622  1.00 92.00           C  
ATOM     24  CE1 TYR A   4      -2.621  -1.097  -6.742  1.00 92.00           C  
ATOM     25  CE2 TYR A   4      -0.816  -2.595  -7.043  1.00 92.00           C  
ATOM     26  CZ  TYR A   4      -2.103  -2.351  -6.609  1.00 92.00           C  
ATOM     27  OH  TYR A   4      -2.826  -3.365  -6.031  1.00 92.00           O  
END
"""

    pdb_content_mutated = """HEADER    DEMO PROTEIN MUTATED                    30-JUN-25   DEMO
TITLE     DEMO ALPHAFOLD STRUCTURE - MUTATED (Y4F)
ATOM      1  N   ALA A   1      -8.901   4.127  -0.555  1.00 85.00           N  
ATOM      2  CA  ALA A   1      -8.608   3.135  -1.618  1.00 85.00           C  
ATOM      3  C   ALA A   1      -7.221   2.458  -1.897  1.00 85.00           C  
ATOM      4  O   ALA A   1      -6.632   1.846  -1.015  1.00 85.00           O  
ATOM      5  CB  ALA A   1      -9.025   3.712  -2.970  1.00 85.00           C  
ATOM      6  N   LEU A   2      -6.849   2.515  -3.137  1.00 90.00           N  
ATOM      7  CA  LEU A   2      -5.618   1.867  -3.612  1.00 90.00           C  
ATOM      8  C   LEU A   2      -4.872   2.707  -4.661  1.00 90.00           C  
ATOM      9  O   LEU A   2      -5.276   3.732  -5.219  1.00 90.00           O  
ATOM     10  CB  LEU A   2      -6.012   0.529  -4.273  1.00 90.00           C  
ATOM     11  N   VAL A   3      -3.678   2.321  -4.843  1.00 88.00           N  
ATOM     12  CA  VAL A   3      -2.851   2.983  -5.844  1.00 88.00           C  
ATOM     13  C   VAL A   3      -1.421   2.385  -6.021  1.00 88.00           C  
ATOM     14  O   VAL A   3      -0.892   1.734  -5.135  1.00 88.00           O  
ATOM     15  CB  VAL A   3      -3.489   3.058  -7.237  1.00 88.00           C  
ATOM     16  N   PHE A   4      -0.934   2.572  -7.223  1.00 92.00           N  
ATOM     17  CA  PHE A   4       0.421   2.051  -7.515  1.00 92.00           C  
ATOM     18  C   PHE A   4       1.452   2.991  -8.162  1.00 92.00           C  
ATOM     19  O   PHE A   4       1.142   4.081  -8.665  1.00 92.00           O  
ATOM     20  CB  PHE A   4       0.221   0.813  -8.392  1.00 92.00           C  
ATOM     21  CG  PHE A   4      -0.584  -0.298  -7.771  1.00 92.00           C  
ATOM     22  CD1 PHE A   4      -1.891  -0.081  -7.321  1.00 92.00           C  
ATOM     23  CD2 PHE A   4      -0.089  -1.575  -7.622  1.00 92.00           C  
ATOM     24  CE1 PHE A   4      -2.621  -1.097  -6.742  1.00 92.00           C  
ATOM     25  CE2 PHE A   4      -0.816  -2.595  -7.043  1.00 92.00           C  
ATOM     26  CZ  PHE A   4      -2.103  -2.351  -6.609  1.00 92.00           C  
END
"""
    
    # Crear archivos
    original_path = os.path.join(models_dir, "demo_original_model.pdb")
    mutated_path = os.path.join(models_dir, "demo_mutated_model.pdb")
    
    with open(original_path, 'w') as f:
        f.write(pdb_content_original)
    
    with open(mutated_path, 'w') as f:
        f.write(pdb_content_mutated)
    
    print(f"✅ Archivo original creado: {original_path}")
    print(f"✅ Archivo mutado creado: {mutated_path}")
    print(f"🔄 Diferencia: Tirosina (TYR) → Fenilalanina (PHE) en posición 4")
    
    # Crear archivo de información
    info_path = os.path.join(models_dir, "demo_info.txt")
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write("ARCHIVOS PDB DE DEMOSTRACIÓN\n")
        f.write("=" * 30 + "\n\n")
        f.write("Original: demo_original_model.pdb\n")
        f.write("Mutado:   demo_mutated_model.pdb\n\n")
        f.write("Mutacion: Y4F (Tirosina -> Fenilalanina en posicion 4)\n")
        f.write("Estructura: Helice alfa corta de 4 residuos\n")
        f.write("Confianza simulada: 90%\n\n")
        f.write("Para usar:\n")
        f.write("1. Ejecuta la aplicacion: python app.py\n")
        f.write("2. Ve a http://localhost:5000\n")
        f.write("3. Los archivos se pueden usar en el visualizador 3D\n")
    
    print(f"📄 Información: {info_path}")
    print("\n🎉 ¡Archivos de demostración creados exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Los archivos están listos para el visualizador NGL")
    print("2. Ejecuta la aplicación y crea una comparación con AlphaFold")
    print("3. Manually configura los paths en la base de datos si es necesario")

if __name__ == '__main__':
    create_simple_demo_pdb()
