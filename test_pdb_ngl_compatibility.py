#!/usr/bin/env python3
"""
Test para verificar la descarga y formato de archivos PDB de SWISS-MODEL
para uso con NGL Viewer
"""

import sys
import os
import time

# Añadir los directorios necesarios al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))
sys.path.insert(0, current_dir)

from business.alphafold_service import AlphaFoldService, AlphaFoldIntegrationError
from config.config import get_config

def test_pdb_format_for_ngl():
    """
    Test específico para verificar que los archivos PDB descargados
    sean compatibles con NGL Viewer
    """
    print("🧪 === TEST DE FORMATO PDB PARA NGL VIEWER ===")
    print()
    
    # Configuración
    config_class = get_config('development')
    config = {
        'SWISS_MODEL_TOKEN': config_class.SWISS_MODEL_TOKEN,
        'MODELS_DIRECTORY': config_class.MODELS_DIRECTORY,
        'API_TIMEOUT': config_class.API_TIMEOUT
    }
    
    alphafold_service = AlphaFoldService(config)
    
    # Secuencia de test más corta para rapidez
    test_sequence = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    
    print(f"📋 Secuencia de test: {len(test_sequence)} residuos")
    print(f"🔬 Prediciendo estructura con SWISS-MODEL...")
    print()
    
    try:
        # Predecir estructura
        result = alphafold_service.predict_structure(
            sequence=test_sequence,
            job_name="ngl_test"
        )
        
        # Verificar archivo descargado
        model_path = result.get('model_path')
        if not model_path or not os.path.exists(model_path):
            print("❌ No se descargó el archivo del modelo")
            return False
        
        print(f"✅ Archivo descargado: {os.path.basename(model_path)}")
        print(f"📊 Tamaño: {os.path.getsize(model_path)} bytes")
        
        # Verificar contenido del archivo
        print("\n🔍 Verificando contenido del archivo PDB:")
        with open(model_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print(f"   📄 Total de líneas: {len(lines)}")
        
        # Mostrar primeras líneas
        print("   🔤 Primeras 10 líneas:")
        for i, line in enumerate(lines[:10]):
            print(f"      {i+1:2d}: {line.strip()}")
        
        # Verificar estructuras esperadas en PDB
        header_found = any(line.startswith('HEADER') for line in lines)
        title_found = any(line.startswith('TITLE') for line in lines)
        atom_found = any(line.startswith('ATOM') or line.startswith('HETATM') for line in lines)
        end_found = any(line.startswith('END') for line in lines)
        
        print(f"\n📋 Verificación de formato PDB:")
        print(f"   HEADER encontrado: {'✅' if header_found else '❌'}")
        print(f"   TITLE encontrado: {'✅' if title_found else '❌'}")
        print(f"   Registros ATOM encontrados: {'✅' if atom_found else '❌'}")
        print(f"   END encontrado: {'✅' if end_found else '❌'}")
        
        # Contar átomos
        atom_count = sum(1 for line in lines if line.startswith('ATOM'))
        hetatm_count = sum(1 for line in lines if line.startswith('HETATM'))
        
        print(f"   📊 Total ATOM records: {atom_count}")
        print(f"   📊 Total HETATM records: {hetatm_count}")
        
        # Verificar si es compatible con NGL (más flexible)
        ngl_compatible = (header_found or title_found) and atom_found and atom_count > 0
        
        print(f"\n🎯 Compatibilidad con NGL Viewer: {'✅ COMPATIBLE' if ngl_compatible else '❌ NO COMPATIBLE'}")
        
        if ngl_compatible:
            print(f"✅ El archivo PDB está listo para visualización en NGL!")
            print(f"📁 Ruta del archivo: {model_path}")
            
            # Información adicional del modelo
            print(f"\n📊 Información del modelo:")
            print(f"   🆔 Job ID: {result.get('job_id')}")
            print(f"   📊 Confianza: {result.get('confidence')}%")
            print(f"   ⏱️ Tiempo de procesamiento: {result.get('processing_time', 0):.1f}s")
            print(f"   🔗 URL original: {result.get('model_url')}")
        
        return ngl_compatible
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_existing_files():
    """
    Verifica archivos PDB existentes para compatibilidad con NGL
    """
    print("\n🔍 === VERIFICANDO ARCHIVOS EXISTENTES ===")
    
    models_dir = "models/alphafold"
    if not os.path.exists(models_dir):
        print(f"❌ Directorio {models_dir} no encontrado")
        return
    
    pdb_files = [f for f in os.listdir(models_dir) if f.endswith('.pdb')]
    pdb_files.sort(key=lambda x: os.path.getmtime(os.path.join(models_dir, x)), reverse=True)
    
    print(f"📁 Archivos PDB encontrados: {len(pdb_files)}")
    
    if pdb_files:
        latest_file = os.path.join(models_dir, pdb_files[0])
        print(f"📄 Verificando archivo más reciente: {pdb_files[0]}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"   📊 Tamaño: {len(content)} caracteres")
            
            # Verificar si es texto legible
            if content.strip():
                lines = content.split('\n')
                print(f"   📄 Líneas: {len(lines)}")
                print("   🔤 Primeras 5 líneas:")
                for i, line in enumerate(lines[:5]):
                    if line.strip():
                        print(f"      {i+1}: {line.strip()[:80]}")
                        
                # Verificar formato PDB básico
                has_atoms = any(line.startswith('ATOM') for line in lines)
                print(f"   ⚛️ Contiene átomos: {'✅' if has_atoms else '❌'}")
                
            else:
                print("   ❌ Archivo vacío")
                
        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando test de compatibilidad PDB con NGL Viewer")
    print("=" * 60)
    
    # Verificar archivos existentes primero
    verify_existing_files()
    
    # Crear nuevo archivo de test
    success = test_pdb_format_for_ngl()
    
    if success:
        print("\n🎉 ¡Test exitoso! Los archivos PDB son compatibles con NGL Viewer")
    else:
        print("\n❌ Test falló. Revisar implementación")
        sys.exit(1)
