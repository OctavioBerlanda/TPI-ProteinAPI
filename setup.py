#!/usr/bin/env python3
"""
Script de inicialización para el Comparador de Proteínas
Verifica requisitos, configura la base de datos y ejecuta tests
"""

import os
import sys
import subprocess

def print_header(title):
    """Imprime un encabezado decorado"""
    print("\n" + "="*60)
    print(f"🧬 {title}")
    print("="*60)

def check_python_version():
    """Verifica la versión de Python"""
    print_header("VERIFICANDO VERSIÓN DE PYTHON")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Se requiere Python 3.11 o superior")
        print(f"   Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_requirements():
    """Instala las dependencias del requirements.txt"""
    print_header("INSTALANDO DEPENDENCIAS")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencias instaladas correctamente")
            return True
        else:
            print("❌ Error instalando dependencias:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando pip: {e}")
        return False

def check_env_file():
    """Verifica que existe el archivo .env"""
    print_header("VERIFICANDO CONFIGURACIÓN")
    
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        print("   Crea el archivo .env con la configuración de la base de datos")
        return False
    
    print("✅ Archivo .env encontrado")
    
    # Leer configuración
    config = {}
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value
    
    required_keys = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_keys = [key for key in required_keys if key not in config]
    
    if missing_keys:
        print(f"❌ Faltan configuraciones en .env: {', '.join(missing_keys)}")
        return False
    
    print("✅ Configuración .env completa")
    return True, config

def test_mysql_connection(config):
    """Prueba la conexión a MySQL"""
    print_header("VERIFICANDO CONEXIÓN A MYSQL")
    
    try:
        # Importar después de que las dependencias estén instaladas
        import mysql.connector
        from mysql.connector import Error
        
        connection = mysql.connector.connect(
            host=config['DB_HOST'],
            port=int(config['DB_PORT']),
            user=config['DB_USER'],
            password=config['DB_PASSWORD']
        )
        
        if connection.is_connected():
            print("✅ Conexión a MySQL exitosa")
            
            # Verificar si existe la base de datos
            cursor = connection.cursor()
            cursor.execute(f"SHOW DATABASES LIKE '{config['DB_NAME']}'")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Base de datos '{config['DB_NAME']}' existe")
            else:
                print(f"⚠️  Base de datos '{config['DB_NAME']}' no existe")
                print("   Creando base de datos...")
                cursor.execute(f"CREATE DATABASE {config['DB_NAME']}")
                print(f"✅ Base de datos '{config['DB_NAME']}' creada")
            
            cursor.close()
            connection.close()
            return True
            
    except ImportError:
        print("❌ mysql-connector-python no está instalado")
        print("   Ejecuta: pip install mysql-connector-python")
        return False
    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        print("\nVerifica que:")
        print("- MySQL esté ejecutándose")
        print("- Las credenciales en .env sean correctas")
        print("- El usuario tenga permisos para crear bases de datos")
        return False

def run_tests():
    """Ejecuta los tests del proyecto"""
    print_header("EJECUTANDO TESTS DE REGLAS DE NEGOCIO")
    
    try:
        result = subprocess.run([
            sys.executable, "tests/run_tests.py"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("✅ Todos los tests pasaron exitosamente")
            return True
        else:
            print("❌ Algunos tests fallaron")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando tests: {e}")
        return False

def create_database_tables():
    """Crea las tablas de la base de datos"""
    print_header("CREANDO TABLAS DE BASE DE DATOS")
    
    try:
        # Importar la aplicación para crear las tablas
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from presentation.app import create_app
        
        app = create_app('development')
        with app.app_context():
            from data.models import db
            db.create_all()
            print("✅ Tablas de base de datos creadas correctamente")
            return True
            
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def main():
    """Función principal de inicialización"""
    print_header("INICIALIZACIÓN DEL COMPARADOR DE PROTEÍNAS")
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Instalar dependencias
    if not install_requirements():
        sys.exit(1)
    
    # Verificar configuración
    env_result = check_env_file()
    if isinstance(env_result, tuple):
        env_ok, config = env_result
    else:
        sys.exit(1)
    
    # Verificar MySQL
    if not test_mysql_connection(config):
        sys.exit(1)
    
    # Crear tablas
    if not create_database_tables():
        sys.exit(1)
    
    # Ejecutar tests
    if not run_tests():
        print("\n⚠️  Los tests fallaron, pero el sistema puede funcionar")
        print("   Revisa los errores antes de usar en producción")
    
    # Mensaje final
    print_header("🎉 INICIALIZACIÓN COMPLETA")
    print("✅ Sistema listo para usar")
    print("\nPara ejecutar la aplicación:")
    print("   python src/presentation/app.py")
    print("\nLuego abre: http://localhost:5000")
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
