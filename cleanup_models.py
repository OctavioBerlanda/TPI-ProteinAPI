#!/usr/bin/env python3
"""
Script para limpiar manualmente archivos de modelos antiguos
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import get_config_dict
from src.business.swissmodel_service import SwissModelService

def main():
    """Ejecuta la limpieza manual de modelos"""
    print("🧹 INICIANDO LIMPIEZA MANUAL DE MODELOS")
    print("=" * 60)
    
    # Cargar configuración
    config = get_config_dict('development')
    swissmodel_service = SwissModelService(config)
    
    # Mostrar directorio de modelos
    print(f"📁 Directorio de modelos: {swissmodel_service.models_directory}")
    
    # Listar archivos actuales
    try:
        model_files = []
        if os.path.exists(swissmodel_service.models_directory):
            for file in os.listdir(swissmodel_service.models_directory):
                if file.endswith(('.pdb', '.cif')):
                    model_files.append(file)
        
        print(f"📊 Archivos de modelos encontrados: {len(model_files)}")
        if model_files:
            total_size = 0
            for file in model_files:
                file_path = os.path.join(swissmodel_service.models_directory, file)
                size = os.path.getsize(file_path)
                total_size += size
                print(f"   - {file} ({size/1024:.1f} KB)")
            print(f"💾 Tamaño total: {total_size/(1024*1024):.1f} MB")
        
    except Exception as e:
        print(f"⚠️ Error listando archivos: {e}")
    
    # Preguntar si proceder
    if model_files:
        print("\n🤔 Opciones de limpieza:")
        print("1. Limpiar todos los usuarios (mantener 2 comparaciones recientes por usuario)")
        print("2. Limpiar usuario específico")
        print("3. Cancelar")
        
        choice = input("\nSeleccione una opción (1-3): ").strip()
        
        if choice == "1":
            # Limpieza global
            print("\n🧹 Ejecutando limpieza global...")
            stats = swissmodel_service.cleanup_old_models(keep_recent=2)
            
        elif choice == "2":
            # Limpieza de usuario específico
            user_id = input("Ingrese el ID del usuario: ").strip()
            try:
                user_id = int(user_id)
                print(f"\n🧹 Ejecutando limpieza para usuario {user_id}...")
                stats = swissmodel_service.cleanup_old_models(user_id=user_id, keep_recent=2)
            except ValueError:
                print("❌ ID de usuario inválido")
                return
                
        elif choice == "3":
            print("❌ Limpieza cancelada")
            return
            
        else:
            print("❌ Opción inválida")
            return
        
        # Mostrar resultados
        print(f"\n✅ LIMPIEZA COMPLETADA")
        print(f"   📁 Archivos eliminados: {stats['files_deleted']}")
        print(f"   💾 Espacio liberado: {stats['space_freed_mb']:.1f} MB")
        if stats['errors']:
            print(f"   ⚠️ Errores: {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"      - {error}")
    
    else:
        print("✅ No hay archivos de modelos para limpiar")

if __name__ == "__main__":
    main()