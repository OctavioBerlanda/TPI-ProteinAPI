#!/usr/bin/env python3
"""
Test de la nueva base de datos expandida de proteínas conocidas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.protein_database import ProteinDatabase
from src.business.alphafold_service import AlphaFoldService

def test_protein_database():
    """Test de la nueva base de datos de proteínas"""
    
    print("🧬 Probando la nueva base de datos expandida de proteínas")
    print("=" * 70)
    
    # Inicializar base de datos
    db = ProteinDatabase()
    
    # Mostrar estadísticas
    stats = db.get_statistics()
    print(f"📊 Estadísticas de la base de datos:")
    print(f"   • Total de proteínas: {stats['total_proteins']}")
    print(f"   • Longitud promedio: {stats['avg_length']:.1f} aa")
    print(f"   • Rango de longitud: {stats['min_length']} - {stats['max_length']} aa")
    print(f"   • Organismos: {', '.join(stats['organisms'])}")
    print()
    
    # Listar todas las proteínas
    print("📋 Proteínas disponibles:")
    proteins = db.list_proteins()
    for uniprot_id, name, length in proteins:
        print(f"   • {uniprot_id}: {name} ({length} aa)")
    print()
    
    # Probar búsquedas
    print("🔍 Probando búsquedas de secuencias:")
    
    # Test con hemoglobina beta (debería encontrar coincidencia exacta)
    hb_beta_seq = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    exact_match = db.search_exact_match(hb_beta_seq)
    if exact_match:
        uniprot_id, protein_data = exact_match
        print(f"✅ Coincidencia exacta: {protein_data['name']} ({uniprot_id})")
    else:
        print("❌ No se encontró coincidencia exacta para hemoglobina beta")
    
    # Test con mutación de hemoglobina (debería encontrar similitud alta)
    hb_beta_mutated = hb_beta_seq[:50] + "A" + hb_beta_seq[51:]  # Cambiar un aminoácido
    similar_matches = db.search_similar_sequences(hb_beta_mutated, min_similarity=0.95)
    if similar_matches:
        uniprot_id, protein_data, similarity = similar_matches[0]
        print(f"✅ Similitud alta: {protein_data['name']} ({uniprot_id}) - {similarity:.1%}")
    else:
        print("❌ No se encontró similitud alta para hemoglobina mutada")
    
    print()
    
    # Probar con el servicio AlphaFold
    print("🔬 Probando integración con AlphaFoldService:")
    
    config = {
        'ALPHAFOLD_API_ENDPOINT': 'https://alphafolddb.org/api',
        'COLABFOLD_ENDPOINT': 'http://localhost:8080',
        'MODELS_DIRECTORY': 'models/alphafold',
        'API_TIMEOUT': 300
    }
    
    service = AlphaFoldService(config)
    
    # Test con diferentes secuencias
    test_sequences = [
        {
            'name': 'Hemoglobina Beta (exacta)',
            'sequence': hb_beta_seq,
            'expected': 'Estructura real - 95% confianza'
        },
        {
            'name': 'Hemoglobina Epsilon (P02100)',
            'sequence': "MVHFTAEEKAAVTSLWSKMNVEEAGGEALGRLLVVYPWTQRFFDSFGNLSSPSAILGNPKVKAHGKKVLTSFGDAIKNMDNLKPAFAKLSELHCDKLHVDPENFKLLGNVMVIILATHFGKEFTPEVQAAWQKLVSAVAIALAHKYH",
            'expected': 'Estructura real - 95% confianza'
        },
        {
            'name': 'Mutación de Hemoglobina Beta',
            'sequence': hb_beta_mutated,
            'expected': 'Simulación mejorada - ~81% confianza'
        }
    ]
    
    for test in test_sequences:
        print(f"\n📝 Test: {test['name']}")
        print(f"   Esperado: {test['expected']}")
        
        try:
            result = service.predict_structure(test['sequence'], f"db_test_{test['name'].replace(' ', '_')}")
            confidence = result.get('confidence', 0)
            method = result.get('prediction_method', 'unknown')
            match_type = result.get('match_type', 'none')
            
            print(f"   ✅ Resultado:")
            print(f"      - Confianza: {confidence}%")
            print(f"      - Método: {method}")
            print(f"      - Tipo: {match_type}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print()
    print("=" * 70)
    print("🎉 Test de base de datos expandida completado")
    print()
    print("💡 Beneficios de la nueva estructura:")
    print("   • Base de datos extensible en JSON")
    print("   • Clase dedicada para gestión de proteínas")
    print("   • Fácil adición de nuevas proteínas")
    print("   • Mejor organización del código")
    print("   • Estadísticas y búsquedas optimizadas")

if __name__ == "__main__":
    test_protein_database()
