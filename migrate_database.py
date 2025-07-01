#!/usr/bin/env python3
"""
Script de migración para añadir columnas de AlphaFold a la base de datos
"""
import sys
import os
import mysql.connector
from mysql.connector import Error

# Agregar el directorio raíz del proyecto al Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.config import Config

def migrate_database():
    """Migra la base de datos añadiendo las nuevas columnas de AlphaFold"""
    
    print("🔄" + "="*60)
    print("     MIGRACIÓN DE BASE DE DATOS - ALPHAFOLD")
    print("🔄" + "="*60)
    
    config = Config()
    
    # Conectar a la base de datos
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        
        cursor = connection.cursor()
        
        print(f"✅ Conectado a la base de datos: {config.DB_NAME}")
        
        # Lista de nuevas columnas para AlphaFold
        new_columns = [
            ("original_model_path", "VARCHAR(500) NULL COMMENT 'Ruta local del archivo PDB/CIF original'"),
            ("mutated_model_path", "VARCHAR(500) NULL COMMENT 'Ruta local del archivo PDB/CIF mutado'"),
            ("original_confidence_score", "FLOAT NULL COMMENT 'Puntuación de confianza promedio original'"),
            ("mutated_confidence_score", "FLOAT NULL COMMENT 'Puntuación de confianza promedio mutada'"),
            ("alphafold_job_id", "VARCHAR(100) NULL COMMENT 'ID del trabajo en AlphaFold'"),
            ("processing_time", "FLOAT NULL COMMENT 'Tiempo de procesamiento en segundos'"),
            ("structural_changes", "TEXT NULL COMMENT 'JSON con cambios estructurales detectados'"),
            ("rmsd_value", "FLOAT NULL COMMENT 'Root Mean Square Deviation entre estructuras'")
        ]
        
        print(f"\n📝 Añadiendo {len(new_columns)} nuevas columnas...")
        
        # Verificar qué columnas ya existen
        cursor.execute("DESCRIBE protein_comparisons")
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Columnas existentes: {len(existing_columns)}")
        
        # Añadir columnas que no existan
        added_count = 0
        skipped_count = 0
        
        for column_name, column_definition in new_columns:
            if column_name not in existing_columns:
                try:
                    alter_query = f"ALTER TABLE protein_comparisons ADD COLUMN {column_name} {column_definition}"
                    cursor.execute(alter_query)
                    print(f"✅ Añadida columna: {column_name}")
                    added_count += 1
                except Error as e:
                    print(f"❌ Error añadiendo {column_name}: {e}")
            else:
                print(f"⏭️  Columna ya existe: {column_name}")
                skipped_count += 1
        
        # Confirmar cambios
        connection.commit()
        
        print(f"\n📊 RESUMEN DE MIGRACIÓN:")
        print(f"   • Columnas añadidas: {added_count}")
        print(f"   • Columnas omitidas: {skipped_count}")
        print(f"   • Total de columnas nuevas: {len(new_columns)}")
        
        # Verificar la estructura final
        cursor.execute("DESCRIBE protein_comparisons")
        final_columns = cursor.fetchall()
        
        print(f"\n📋 ESTRUCTURA FINAL DE LA TABLA:")
        print("-" * 80)
        for column in final_columns:
            field_name = column[0]
            field_type = column[1]
            is_null = "NULL" if column[2] == "YES" else "NOT NULL"
            
            # Marcar las nuevas columnas
            marker = "🆕" if field_name in [col[0] for col in new_columns] else "  "
            print(f"{marker} {field_name:<25} {field_type:<20} {is_null}")
        
        print(f"\n✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print(f"🚀 La aplicación ahora puede usar todas las funcionalidades de AlphaFold")
        
    except Error as e:
        print(f"❌ Error de conexión a MySQL: {e}")
        print(f"\n🔧 Verifica:")
        print(f"   • Que MySQL esté ejecutándose")
        print(f"   • Que la base de datos '{config.DB_NAME}' exista")
        print(f"   • Que las credenciales en .env sean correctas")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print(f"🔌 Conexión cerrada")
    
    return True

def verify_migration():
    """Verifica que la migración se haya completado correctamente"""
    
    print(f"\n🔍 VERIFICANDO MIGRACIÓN...")
    
    config = Config()
    
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        
        cursor = connection.cursor()
        
        # Verificar que todas las columnas nuevas existan
        required_columns = [
            'original_model_path',
            'mutated_model_path', 
            'original_confidence_score',
            'mutated_confidence_score',
            'alphafold_job_id',
            'processing_time',
            'structural_changes',
            'rmsd_value'
        ]
        
        cursor.execute("DESCRIBE protein_comparisons")
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"❌ Faltan columnas: {missing_columns}")
            return False
        else:
            print(f"✅ Todas las columnas de AlphaFold están presentes")
            return True
            
    except Error as e:
        print(f"❌ Error verificando migración: {e}")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("🧬 MIGRACIÓN DE BASE DE DATOS PARA ALPHAFOLD\n")
    
    if migrate_database():
        if verify_migration():
            print(f"\n🎉 ¡MIGRACIÓN COMPLETAMENTE EXITOSA!")
            print(f"\n🚀 Ahora puedes:")
            print(f"   1. Ejecutar: python app.py")
            print(f"   2. Visitar: http://localhost:5000")
            print(f"   3. Usar AlphaFold marcando el checkbox correspondiente")
        else:
            print(f"\n⚠️ La migración tuvo problemas. Revisa los errores arriba.")
    else:
        print(f"\n❌ Migración fallida. Revisa la configuración de la base de datos.")
