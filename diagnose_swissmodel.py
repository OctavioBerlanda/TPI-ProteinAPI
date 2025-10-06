"""
Script de diagnóstico para verificar el proceso de SwissModel
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import get_config_dict
from src.business.swissmodel_service import SwissModelService
from src.business.comparison_manager import ComparisonManager
from src.data.repositories import ProteinComparisonRepository

def test_swissmodel_integration():
    """Prueba la integración completa con SwissModel"""
    print("="*60)
    print("🧪 Test de Diagnóstico - SwissModel Integration")
    print("="*60)
    
    # 1. Verificar configuración
    print("\n1️⃣ Verificando configuración...")
    config = get_config_dict()
    print(f"   📁 Directorio de modelos: {config.get('MODELS_DIRECTORY')}")
    print(f"   🔗 API Endpoint: {config.get('SWISSMODEL_API_ENDPOINT')}")
    print(f"   ⏱️ Timeout: {config.get('API_TIMEOUT')}s")
    print(f"   ✅ SwissModel habilitado: {config.get('ENABLE_SWISSMODEL')}")
    
    # 2. Verificar última comparación
    print("\n2️⃣ Verificando última comparación en BD...")
    try:
        comparison = ProteinComparisonRepository.get_comparison_by_id(3)
        if comparison:
            print(f"   ID: {comparison.id}")
            print(f"   Nombre: {comparison.comparison_name}")
            print(f"   Status: {comparison.status}")
            print(f"   Modelo original: {comparison.original_model_path or 'NULL'}")
            print(f"   Modelo mutado: {comparison.mutated_model_path or 'NULL'}")
            print(f"   SwissModel Job ID: {comparison.swissmodel_job_id or 'NULL'}")
            print(f"   RMSD: {comparison.rmsd_value or 'NULL'}")
            print(f"   Confianza original: {comparison.original_confidence_score or 'NULL'}")
            print(f"   Confianza mutada: {comparison.mutated_confidence_score or 'NULL'}")
        else:
            print("   ❌ No se encontró la comparación #3")
    except Exception as e:
        print(f"   ❌ Error al consultar BD: {e}")
    
    # 3. Listar archivos de modelos
    print("\n3️⃣ Verificando archivos de modelos generados...")
    models_dir = config.get('MODELS_DIRECTORY', 'models/swissmodel')
    if os.path.exists(models_dir):
        files = os.listdir(models_dir)
        if files:
            print(f"   📁 Archivos encontrados ({len(files)}):")
            for f in sorted(files):
                file_path = os.path.join(models_dir, f)
                size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                print(f"      - {f} ({size:,} bytes)")
        else:
            print(f"   ⚠️ Directorio vacío: {models_dir}")
    else:
        print(f"   ❌ Directorio no existe: {models_dir}")
    
    # 4. Verificar directorio de reportes
    print("\n4️⃣ Verificando reportes de mutación...")
    reports_dir = os.path.join(models_dir, 'reports')
    if os.path.exists(reports_dir):
        files = os.listdir(reports_dir)
        if files:
            print(f"   📁 Reportes encontrados ({len(files)}):")
            for f in sorted(files):
                print(f"      - {f}")
        else:
            print(f"   ⚠️ No hay reportes")
    else:
        print(f"   ℹ️ Directorio de reportes no existe")
    
    print("\n"+ "="*60)
    print("✅ Diagnóstico completado")
    print("="*60)

if __name__ == '__main__':
    test_swissmodel_integration()
