"""
Script de instalación y verificación de Modeller.
Guía paso a paso para configurar Modeller en el proyecto.
"""

import os
import sys

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_modeller():
    """Verifica si Modeller está instalado."""
    try:
        import modeller
        return True, modeller.__version__
    except ImportError:
        return False, None

def check_license():
    """Verifica si la licencia está configurada."""
    from dotenv import load_dotenv
    load_dotenv()
    
    license_key = os.getenv('MODELLER_LICENSE_KEY', '')
    return bool(license_key and license_key != ''), license_key

def main():
    print_header("🔬 INSTALADOR DE MODELLER PARA TPI-ProteinAPI")
    
    print("Este script te guiará en la instalación y configuración de Modeller.\n")
    
    # Paso 1: Verificar instalación
    print("📦 Paso 1: Verificando instalación de Modeller...")
    modeller_installed, version = check_modeller()
    
    if modeller_installed:
        print(f"   ✅ Modeller {version} está instalado")
    else:
        print("   ❌ Modeller NO está instalado")
        print("\n📥 Para instalar Modeller:")
        print("   Opción A (Recomendado):")
        print("      conda install -c salilab modeller")
        print("\n   Opción B:")
        print("      Descargar desde: https://salilab.org/modeller/download_installation.html")
        print("\n⚠️  Después de instalar, ejecuta este script nuevamente.")
        return False
    
    # Paso 2: Verificar licencia
    print("\n🔑 Paso 2: Verificando licencia académica...")
    license_configured, license_key = check_license()
    
    if license_configured:
        print(f"   ✅ Licencia configurada: {license_key[:4]}...")
    else:
        print("   ❌ Licencia NO configurada en .env")
        print("\n📝 Para obtener una licencia académica GRATUITA:")
        print("   1. Ir a: https://salilab.org/modeller/registration.html")
        print("   2. Completar el formulario con tu email institucional @frro.utn.edu.ar")
        print("   3. Recibirás un email con tu clave (ej: MODELIRANJE)")
        print("   4. Agregar a .env:")
        print("      MODELLER_LICENSE_KEY=tu_clave_aqui")
        print("\n⚠️  Después de configurar la licencia, ejecuta este script nuevamente.")
        return False
    
    # Paso 3: Probar Modeller
    print("\n🧪 Paso 3: Probando Modeller...")
    try:
        from src.business.modeller_mutator import ModellerMutator
        from config.modeller_config import get_modeller_config
        
        config = get_modeller_config()
        mutator = ModellerMutator(
            license_key=config['license_key'],
            optimization_level='low'
        )
        
        print("   ✅ Modeller funciona correctamente")
        print(f"   ✅ Licencia válida")
        print(f"   ✅ Nivel de optimización: {config['default_optimization']}")
        
    except Exception as e:
        print(f"   ❌ Error al probar Modeller: {e}")
        print("\n⚠️  Verifica que:")
        print("   - La licencia sea correcta")
        print("   - Modeller esté instalado correctamente")
        print("   - No haya errores de importación")
        return False
    
    # Paso 4: Resumen
    print_header("✅ INSTALACIÓN COMPLETADA")
    print("Modeller está listo para usar en el proyecto.\n")
    print("📊 Configuración:")
    print(f"   - Modeller version: {version}")
    print(f"   - Licencia: {license_key[:4]}...")
    print(f"   - Optimización: {config['default_optimization']}")
    print("\n🚀 Próximos pasos:")
    print("   1. Inicia tu aplicación Flask: python app.py")
    print("   2. Las mutaciones se procesarán automáticamente con Modeller")
    print("   3. Revisa los logs para confirmar el uso de Modeller")
    print("\n📖 Documentación completa: docs/MODELLER_SETUP.md")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
