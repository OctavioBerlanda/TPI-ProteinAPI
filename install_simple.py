#!/usr/bin/env python3
"""
Script simplificado de instalación para el Comparador de Proteínas
Soluciona problemas de instalación en Windows
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

def install_requirements_step_by_step():
    """Instala las dependencias paso a paso para evitar errores"""
    print_header("INSTALANDO DEPENDENCIAS ESENCIALES")
    
    # Lista de paquetes esenciales en orden de instalación
    essential_packages = [
        "python-dotenv==1.0.0",
        "Flask==2.3.3", 
        "WTForms==3.0.1",
        "Flask-WTF==1.1.1",
        "SQLAlchemy==2.0.21",
        "Flask-SQLAlchemy==3.0.5",
        "mysql-connector-python==8.1.0",
        "requests==2.31.0"
    ]
    
    failed_packages = []
    
    for package in essential_packages:
        print(f"\n📦 Instalando {package}...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--user", package
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ {package} instalado correctamente")
            else:
                print(f"❌ Error instalando {package}")
                print(f"   Error: {result.stderr}")
                failed_packages.append(package)
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout instalando {package}")
            failed_packages.append(package)
        except Exception as e:
            print(f"❌ Error inesperado instalando {package}: {e}")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️  Paquetes que fallaron: {', '.join(failed_packages)}")
        print("Puedes intentar instalarlos manualmente después.")
        return len(failed_packages) == 0
    else:
        print("\n✅ Todas las dependencias esenciales instaladas")
        return True

def check_env_file():
    """Verifica que existe el archivo .env"""
    print_header("VERIFICANDO CONFIGURACIÓN")
    
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        print("   Crea el archivo .env con la configuración de la base de datos")
        return False, {}
    
    print("✅ Archivo .env encontrado")
    
    # Leer configuración
    config = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    except Exception as e:
        print(f"❌ Error leyendo .env: {e}")
        return False, {}
    
    required_keys = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_keys = [key for key in required_keys if key not in config]
    
    if missing_keys:
        print(f"❌ Faltan configuraciones en .env: {', '.join(missing_keys)}")
        return False, {}
    
    print("✅ Configuración .env completa")
    return True, config

def run_basic_tests():
    """Ejecuta tests básicos sin dependencias problemáticas"""
    print_header("EJECUTANDO TESTS BÁSICOS")
    
    try:
        # Verificar que podemos importar nuestros módulos
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        from business.sequence_service import SequenceValidator, SequenceComparisonService
        print("✅ Módulos de negocio importados correctamente")
        
        # Test básico de validación
        validator = SequenceValidator()
        valid, invalid = validator.validate_amino_acids("ARNDCQ")
        
        if valid and len(invalid) == 0:
            print("✅ Validación de aminoácidos funcionando")
        else:
            print("❌ Error en validación de aminoácidos")
            return False
        
        # Test básico de comparación
        service = SequenceComparisonService()
        result = service.validate_and_compare_sequences("ARNDCQ", "GRNDCQ")
        
        if result['valid'] and result['mutations']['total_mutations'] == 1:
            print("✅ Comparación de secuencias funcionando")
        else:
            print("❌ Error en comparación de secuencias")
            return False
        
        print("✅ Todos los tests básicos pasaron")
        return True
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en tests: {e}")
        return False

def create_run_script():
    """Crea un script simple para ejecutar la aplicación"""
    print_header("CREANDO SCRIPT DE EJECUCIÓN")
    
    run_script_content = '''#!/usr/bin/env python3
"""
Script para ejecutar el Comparador de Proteínas
"""
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == '__main__':
    try:
        from presentation.app import create_app
        
        print("🚀 Iniciando Comparador de Proteínas...")
        print("📍 URL: http://localhost:5000")
        print("⏹️  Presiona Ctrl+C para detener")
        
        app = create_app('development')
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Error importando la aplicación: {e}")
        print("   Verifica que las dependencias estén instaladas")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error ejecutando la aplicación: {e}")
        sys.exit(1)
'''
    
    try:
        with open('run_app.py', 'w') as f:
            f.write(run_script_content)
        print("✅ Script 'run_app.py' creado")
        return True
    except Exception as e:
        print(f"❌ Error creando script: {e}")
        return False

def main():
    """Función principal simplificada"""
    print_header("INSTALACIÓN SIMPLIFICADA - COMPARADOR DE PROTEÍNAS")
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Instalar dependencias paso a paso
    if not install_requirements_step_by_step():
        print("\n⚠️  Algunas dependencias fallaron, pero puedes continuar")
        print("   Intenta instalar manualmente las que fallaron")
    
    # Verificar configuración
    env_ok, config = check_env_file()
    if not env_ok:
        print("\n⚠️  Configura el archivo .env antes de continuar")
    
    # Ejecutar tests básicos
    if run_basic_tests():
        print("✅ Sistema básico funcionando correctamente")
    else:
        print("⚠️  Algunos tests fallaron, revisa las dependencias")
    
    # Crear script de ejecución
    create_run_script()
    
    # Instrucciones finales
    print_header("🎉 INSTALACIÓN COMPLETADA")
    print("✅ Instalación básica completa")
    print("\nPara continuar:")
    print("1. Configura MySQL y crea la base de datos:")
    print("   CREATE DATABASE protein_comparison_db;")
    print("\n2. Ejecuta la aplicación:")
    print("   python app.py")
    print("\n3. Abre tu navegador en: http://localhost:5000")
    print("\n💡 Tip: Si hay errores de importación, ejecuta desde el directorio raíz")
    print("" + "="*60)

if __name__ == '__main__':
    main()
