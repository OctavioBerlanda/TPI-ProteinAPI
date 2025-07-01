#!/usr/bin/env python3
"""
Script para crear más mutaciones de hemoglobina para testing
"""

import sys
import os
import sqlite3

# Agregar el directorio raíz del proyecto al path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.business.alphafold_service import AlphaFoldService
from src.business.uniprot_service import UniProtService

def create_hemoglobin_mutations():
    """Crear varias mutaciones interesantes de hemoglobina"""
    
    alphafold_service = AlphaFoldService()
    uniprot_service = UniProtService()
    
    # Definir mutaciones interesantes
    mutations = [
        {
            "name": "Hemoglobina Beta S (Anemia Falciforme)",
            "original_aa": "E",
            "position": 6,
            "mutated_aa": "S",
            "description": "La mutación más famosa - causa anemia falciforme"
        },
        {
            "name": "Hemoglobina Beta C",
            "original_aa": "E",
            "position": 6,
            "mutated_aa": "K",
            "description": "Otra variante común en la posición 6"
        },
        {
            "name": "Hemoglobina Beta E",
            "original_aa": "E",
            "position": 26,
            "mutated_aa": "K",
            "description": "Mutación muy común en el sudeste asiático"
        },
        {
            "name": "Hemoglobina Beta Lepore",
            "original_aa": "G",
            "position": 16,
            "mutated_aa": "S",
            "description": "Mutación que afecta la estabilidad"
        },
        {
            "name": "Hemoglobina Beta Köln",
            "original_aa": "V",
            "position": 98,
            "mutated_aa": "M",
            "description": "Causa inestabilidad térmica"
        },
        {
            "name": "Hemoglobina Beta Zurich",
            "original_aa": "H",
            "position": 63,
            "mutated_aa": "R",
            "description": "Hemoglobina inestable"
        },
        {
            "name": "Hemoglobina Beta Santa Ana",
            "original_aa": "L",
            "position": 88,
            "mutated_aa": "P",
            "description": "Hemoglobina con alta afinidad por oxígeno"
        },
        {
            "name": "Hemoglobina Beta Chesapeake",
            "original_aa": "L",
            "position": 92,
            "mutated_aa": "R",
            "description": "Alta afinidad por oxígeno"
        },
        {
            "name": "Hemoglobina Beta Kansas",
            "original_aa": "N",
            "position": 102,
            "mutated_aa": "T",
            "description": "Baja afinidad por oxígeno"
        },
        {
            "name": "Hemoglobina Beta M Boston",
            "original_aa": "H",
            "position": 58,
            "mutated_aa": "Y",
            "description": "Causa metahemoglobinemia"
        }
    ]
    
    print("🧬 Creando mutaciones de hemoglobina...")
    print("=" * 60)
    
    uniprot_id = "P68871"  # Hemoglobina beta humana
    
    # Obtener la secuencia original
    print(f"📥 Obteniendo datos de UniProt para {uniprot_id}...")
    protein_data = uniprot_service.get_protein_data(uniprot_id)
    
    if not protein_data or 'sequence' not in protein_data:
        print("❌ Error: No se pudo obtener la secuencia de UniProt")
        return
    
    original_sequence = protein_data['sequence']
    print(f"✅ Secuencia original obtenida: {len(original_sequence)} aminoácidos")
    print(f"🔤 Primeros 50 aa: {original_sequence[:50]}...")
    
    successful_mutations = []
    
    for i, mutation in enumerate(mutations, 1):
        print(f"\n🧪 Procesando mutación {i}/{len(mutations)}: {mutation['name']}")
        print(f"   {mutation['original_aa']}{mutation['position']}{mutation['mutated_aa']}")
        
        try:
            # Verificar que la posición es válida
            if mutation['position'] > len(original_sequence):
                print(f"   ⚠️  Posición {mutation['position']} fuera de rango (secuencia tiene {len(original_sequence)} aa)")
                continue
            
            # Verificar que el aminoácido original coincide
            actual_aa = original_sequence[mutation['position'] - 1]  # Posición 1-indexada
            if actual_aa != mutation['original_aa']:
                print(f"   ⚠️  Aminoácido original no coincide: esperado {mutation['original_aa']}, encontrado {actual_aa}")
                continue
            
            # Crear la secuencia mutada
            mutated_sequence = (
                original_sequence[:mutation['position'] - 1] + 
                mutation['mutated_aa'] + 
                original_sequence[mutation['position']:]
            )
            
            print(f"   🔄 Secuencia mutada creada")
            print(f"   📍 Posición {mutation['position']}: {actual_aa} → {mutation['mutated_aa']}")
            
            # Generar estructura con AlphaFold
            print("   🤖 Generando estructura con AlphaFold...")
            
            result = alphafold_service.generate_structure_with_alphafold(
                original_sequence=original_sequence,
                mutated_sequence=mutated_sequence,
                original_name=f"{mutation['name']} Original",
                mutated_name=f"{mutation['name']} Mutada",
                protein_name=mutation['name'],
                description=mutation['description']
            )
            
            if result['success']:
                print(f"   ✅ Estructura generada exitosamente!")
                print(f"   📁 ID de comparación: {result['comparison_id']}")
                print(f"   📄 Archivos: {result['original_file']} | {result['mutated_file']}")
                
                successful_mutations.append({
                    'name': mutation['name'],
                    'mutation': f"{mutation['original_aa']}{mutation['position']}{mutation['mutated_aa']}",
                    'comparison_id': result['comparison_id'],
                    'description': mutation['description']
                })
            else:
                print(f"   ❌ Error generando estructura: {result['error']}")
                
        except Exception as e:
            print(f"   ❌ Error procesando mutación: {str(e)}")
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE MUTACIONES CREADAS")
    print("=" * 60)
    
    if successful_mutations:
        print(f"✅ {len(successful_mutations)} mutaciones creadas exitosamente:")
        print()
        
        for mut in successful_mutations:
            print(f"🧬 {mut['name']}")
            print(f"   Mutación: {mut['mutation']}")
            print(f"   ID: {mut['comparison_id']}")
            print(f"   Descripción: {mut['description']}")
            print(f"   URL: http://localhost:5000/comparison/{mut['comparison_id']}")
            print()
        
        print("🔗 URLs para testing rápido:")
        for mut in successful_mutations:
            print(f"http://localhost:5000/comparison/{mut['comparison_id']}")
    
    else:
        print("❌ No se pudieron crear mutaciones")
    
    print("\n🎉 ¡Proceso completado!")

if __name__ == "__main__":
    create_hemoglobin_mutations()
