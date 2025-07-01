#!/usr/bin/env python3
"""
Script para solucionar problemas de compatibilidad de dependencias
Específicamente para el error de Werkzeug/Flask
"""

import subprocess
import sys

def print_header(title):
    """Imprime un encabezado decorado"""
    print("\n" + "="*60)
    print(f"🔧 {title}")
    print("="*60)

def fix_flask_werkzeug_compatibility():
    """Soluciona el problema de compatibilidad Flask/Werkzeug"""
    print_header("SOLUCIONANDO COMPATIBILIDAD FLASK/WERKZEUG")
    
    # Lista de comandos para solucionar el problema
    commands = [
        # Desinstalar versiones problemáticas
        [sys.executable, "-m", "pip", "uninstall", "-y", "Flask", "Werkzeug", "Flask-WTF", "WTForms"],
        
        # Instalar versiones específicas compatibles
        [sys.executable, "-m", "pip", "install", "--user", "Flask==2.2.5"],
        [sys.executable, "-m", "pip", "install", "--user", "Werkzeug==2.2.3"],
        [sys.executable, "-m", "pip", "install", "--user", "Flask-WTF==1.1.1"],
        [sys.executable, "-m", "pip", "install", "--user", "WTForms==3.0.1"],
        
        # Instalar dependencias de base de datos
        [sys.executable, "-m", "pip", "install", "--user", "mysql-connector-python==8.1.0"],
        [sys.executable, "-m", "pip", "install", "--user", "SQLAlchemy==1.4.53"],
        [sys.executable, "-m", "pip", "install", "--user", "Flask-SQLAlchemy==3.0.5"],
        
        # Dependencias adicionales
        [sys.executable, "-m", "pip", "install", "--user", "python-dotenv==1.0.0"],
        [sys.executable, "-m", "pip", "install", "--user", "requests==2.31.0"]
    ]
    
    for i, cmd in enumerate(commands, 1):
        package_name = cmd[-1] if len(cmd) > 4 else "dependencias"
        print(f"\n📦 Paso {i}/{len(commands)}: {package_name}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ Completado: {package_name}")
            else:
                print(f"⚠️  Advertencia en {package_name}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout en {package_name}")
        except Exception as e:
            print(f"❌ Error en {package_name}: {e}")
    
    print("\n✅ Proceso de compatibilidad completado")

def test_imports():
    """Prueba que las importaciones funcionen"""
    print_header("PROBANDO IMPORTACIONES")
    
    try:
        import flask
        print(f"✅ Flask {flask.__version__} importado correctamente")
        
        import werkzeug
        print(f"✅ Werkzeug {werkzeug.__version__} importado correctamente")
        
        from flask import Flask
        print("✅ Flask.Flask importado correctamente")
        
        from flask_wtf import FlaskForm
        print("✅ Flask-WTF importado correctamente")
        
        print("\n🎉 Todas las importaciones funcionan correctamente")
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_app_startup():
    """Prueba que la aplicación pueda iniciarse"""
    print_header("PROBANDO INICIO DE APLICACIÓN")
    
    try:
        import sys
        import os
        
        # Agregar path del proyecto
        project_root = os.getcwd()
        sys.path.insert(0, project_root)
        
        # Importar configuración
        from config.config import config
        print("✅ Configuración importada")
        
        # Importar modelos
        from src.data.models import db
        print("✅ Modelos importados")
        
        # Importar aplicación
        from src.presentation.app import create_app
        print("✅ Aplicación importada")
        
        # Crear aplicación de prueba
        app = create_app('development')
        print("✅ Aplicación creada exitosamente")
        
        print("\n🎉 La aplicación está lista para ejecutarse")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print_header("SOLUCIONADOR DE COMPATIBILIDAD - COMPARADOR DE PROTEÍNAS")
    
    # Solucionar compatibilidad
    fix_flask_werkzeug_compatibility()
    
    # Probar importaciones
    if test_imports():
        print("✅ Importaciones OK")
    else:
        print("❌ Problemas con importaciones")
        return
    
    # Probar aplicación
    if test_app_startup():
        print("✅ Aplicación OK")
    else:
        print("❌ Problemas con la aplicación")
        return
    
    # Instrucciones finales
    print_header("🎉 PROBLEMA SOLUCIONADO")
    print("✅ Compatibilidad de dependencias corregida")
    print("✅ Aplicación lista para ejecutar")
    print("\nAhora puedes ejecutar:")
    print("   python app.py")
    print("\nO:")
    print("   python run_app.py")
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
