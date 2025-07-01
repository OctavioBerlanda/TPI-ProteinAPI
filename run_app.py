#!/usr/bin/env python3
"""
Script para ejecutar el Comparador de Proteínas
Configuración correcta de paths para evitar errores de importación
"""
import sys
import os

# Agregar el directorio raíz del proyecto al Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """Función principal para ejecutar la aplicación"""
    
    print("🧬 Comparador de Proteínas - Sistema de Análisis de Mutaciones")
    print("=" * 60)
    
    try:
        # Importar la aplicación Flask
        from src.presentation.app import create_app
        
        print("✅ Módulos importados correctamente")
        print("🚀 Iniciando servidor Flask...")
        print("📍 URL: http://localhost:5000")
        print("⏹️  Presiona Ctrl+C para detener el servidor")
        print("=" * 60)
        
        # Crear y ejecutar la aplicación
        app = create_app('development')
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("\nPosibles soluciones:")
        print("1. Verifica que las dependencias estén instaladas:")
        print("   pip install -r requirements.txt")
        print("2. Ejecuta desde el directorio raíz del proyecto")
        print("3. Usa el script de instalación: python install_simple.py")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error ejecutando la aplicación: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
