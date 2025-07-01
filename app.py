#!/usr/bin/env python3
"""
Punto de entrada principal para el Comparador de Proteínas
Este script debe ejecutarse desde la raíz del proyecto
"""
import os
import sys

# Verificar que estamos en el directorio correcto
current_dir = os.getcwd()
if not os.path.exists('src') or not os.path.exists('config'):
    print("❌ Error: Ejecuta este script desde el directorio raíz del proyecto")
    print(f"   Directorio actual: {current_dir}")
    print("   Debe contener las carpetas 'src' y 'config'")
    sys.exit(1)

# Agregar el directorio actual al Python path
sys.path.insert(0, os.getcwd())

def main():
    """Función principal"""
    print("🧬 Comparador de Proteínas - Sistema de Análisis de Mutaciones")
    print("=" * 60)
    
    try:
        # Verificar que podemos importar la configuración
        from config.config import config
        print("✅ Configuración cargada")
        
        # Verificar que podemos importar los modelos
        from src.data.models import db
        print("✅ Modelos de datos cargados")
        
        # Importar y crear la aplicación Flask
        from src.presentation.app import create_app
        print("✅ Aplicación Flask configurada")
        
        print("\n🚀 Iniciando servidor...")
        print("📍 URL: http://localhost:5000")
        print("⏹️  Presiona Ctrl+C para detener")
        print("=" * 60)
        
        # Crear y ejecutar la aplicación
        app = create_app('development')
        app.run(debug=True, host='localhost', port=5000)
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("\n🔧 Soluciones:")
        print("1. Verifica que las dependencias estén instaladas:")
        print("   pip install -r requirements.txt")
        print("2. O usa la instalación simplificada:")
        print("   python install_simple.py")
        print("3. Verifica que MySQL esté ejecutándose")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Verifica:")
        print("- Que MySQL esté ejecutándose")
        print("- Que el archivo .env esté configurado correctamente")
        print("- Que la base de datos exista")
        sys.exit(1)

if __name__ == '__main__':
    main()
