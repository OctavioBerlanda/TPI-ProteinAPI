#!/usr/bin/env python3
"""
Script para crear archivos CIF de demostración para el visualizador 3D
"""
import os
import sys

# Agregar el directorio actual al Python path
sys.path.insert(0, os.getcwd())

def create_demo_cif_files():
    """Crear archivos CIF de demostración"""
    print("🧬 Creando archivos CIF de demostración para NGL Viewer")
    print("=" * 60)
    
    # Crear directorio
    models_dir = "models/alphafold"
    os.makedirs(models_dir, exist_ok=True)
    
    # Secuencias de demostración
    sequences = {
        "original": "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG",
        "mutated": "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGFVLAGG"  # Y->F en pos 60
    }
    
    print(f"📁 Directorio: {models_dir}")
    print(f"🔄 Mutación: Y->F en posición 60")
    print()
    
    for seq_type, sequence in sequences.items():
        print(f"⚗️  Creando archivo CIF {seq_type}...")
        
        # Contenido CIF básico
        cif_content = f"""data_demo_{seq_type}
#
_entry.id   demo_{seq_type}
_entry.title   "Demo protein structure - {seq_type}"
#
_entity.id   1
_entity.type   polymer
_entity.pdbx_description   "Demo protein {seq_type}"
#
_entity_poly.entity_id   1
_entity_poly.type   "polypeptide(L)"
_entity_poly.pdbx_seq_one_letter_code   "{sequence}"
#
_struct.entry_id   demo_{seq_type}
_struct.title   "AlphaFold prediction demo - {seq_type}"
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_entity_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.pdbx_formal_charge
_atom_site.auth_seq_id
_atom_site.auth_comp_id
_atom_site.auth_asym_id
_atom_site.auth_atom_id
_atom_site.pdbx_PDB_model_num
"""
        
        # Mapeo de aminoácidos
        aa_map = {
            'A': 'ALA', 'R': 'ARG', 'N': 'ASN', 'D': 'ASP', 'C': 'CYS',
            'Q': 'GLN', 'E': 'GLU', 'G': 'GLY', 'H': 'HIS', 'I': 'ILE',
            'L': 'LEU', 'K': 'LYS', 'M': 'MET', 'F': 'PHE', 'P': 'PRO',
            'S': 'SER', 'T': 'THR', 'W': 'TRP', 'Y': 'TYR', 'V': 'VAL'
        }
        
        # Generar coordenadas para una hélice alfa
        atom_id = 1
        for i, aa in enumerate(sequence[:20]):  # Solo primeros 20 para demo
            aa_code = aa_map.get(aa, 'ALA')
            
            # Coordenadas de hélice alfa
            angle = i * 100.0 * 3.14159 / 180.0  # 100 grados por residuo
            radius = 2.3
            rise = 1.5
            
            x = radius * (angle * 0.1)
            y = radius * (angle * 0.1) * 0.8
            z = i * rise
            
            # Agregar pequeña variación para la mutación
            if seq_type == "mutated" and i == 19:  # Posición de mutación
                x += 0.5
                y += 0.3
            
            # Línea CIF para CA
            cif_line = f"ATOM {atom_id:6d} C CA . {aa_code} A 1 {i+1:4d} ? {x:8.3f} {y:8.3f} {z:8.3f} 1.00 85.00 ? {i+1:4d} {aa_code} A CA 1"
            cif_content += cif_line + "\n"
            atom_id += 1
        
        cif_content += "#\n"
        
        # Guardar archivo
        file_path = os.path.join(models_dir, f"demo_{seq_type}_model.cif")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cif_content)
        
        print(f"   ✅ Creado: {file_path}")
        print(f"   📊 Átomos: {len(sequence[:20])} CA atoms")
    
    # Crear archivo de información
    info_path = os.path.join(models_dir, "demo_cif_info.txt")
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write("ARCHIVOS CIF DE DEMOSTRACIÓN\n")
        f.write("=" * 30 + "\n\n")
        f.write("Original: demo_original_model.cif\n")
        f.write("Mutado:   demo_mutated_model.cif\n\n")
        f.write("Formato: mmCIF (Crystal Information File)\n")
        f.write("Compatible con: NGL Viewer, PyMOL, ChimeraX\n")
        f.write("Estructura: Hélice alfa de 20 residuos\n")
        f.write("Mutación: Y->F en posición 19\n\n")
        f.write("URLs para testing:\n")
        f.write("Original: /api/comparison/1/model/original/view\n")
        f.write("Mutado:   /api/comparison/1/model/mutated/view\n")
    
    print(f"\n📄 Info: {info_path}")
    print("\n🎉 ¡Archivos CIF de demostración creados!")
    print("\n🔗 NGL Viewer ahora puede cargar estos archivos .cif")
    print("📋 Los archivos están optimizados para visualización web")

if __name__ == '__main__':
    create_demo_cif_files()
