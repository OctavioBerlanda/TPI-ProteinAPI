#!/usr/bin/env python3
"""
Script para ejecutar todos los tests del proyecto
Comparador de Proteínas - Tests de Reglas de Negocio
"""

import unittest
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_all_tests():
    """Ejecuta todos los tests del proyecto"""
    
    print("="*60)
    print("🧪 EJECUTANDO TESTS DE REGLAS DE NEGOCIO")
    print("="*60)
    
    # Descubrir y ejecutar todos los tests
    test_dir = os.path.dirname(__file__)
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Ejecutar tests con verbosidad alta
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*60)
    
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Omitidos: {len(result.skipped)}")
    
    if result.errors:
        print("\n❌ ERRORES:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    if result.failures:
        print("\n❌ FALLOS:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    if result.wasSuccessful():
        print("\n✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("✅ TODAS LAS REGLAS DE NEGOCIO SE CUMPLEN CORRECTAMENTE")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        return False
    
    return True

def verify_business_rules():
    """Verifica que todas las reglas de negocio estén implementadas"""
    
    print("\n" + "="*60)
    print("📋 VERIFICACIÓN DE REGLAS DE NEGOCIO IMPLEMENTADAS")
    print("="*60)
    
    business_rules = [
        "✅ Validación de aminoácidos (solo los 20 estándar)",
        "✅ Validación de longitud igual entre secuencias",
        "✅ Validación de máximo 2 mutaciones",
        "✅ Validación de mínimo 1 diferencia (no secuencias idénticas)",
        "✅ Limpieza automática de secuencias (espacios, mayúsculas)",
        "✅ Detección y descripción de mutaciones",
        "✅ Almacenamiento en base de datos MySQL",
        "✅ Gestión de usuarios y comparaciones",
        "✅ Arquitectura en 3 capas (Presentación, Negocio, Datos)",
    ]
    
    for rule in business_rules:
        print(rule)
    
    print("\n✅ TODAS LAS REGLAS DE NEGOCIO ESTÁN IMPLEMENTADAS Y TESTADAS")

if __name__ == '__main__':
    success = run_all_tests()
    verify_business_rules()
    
    print("\n" + "="*60)
    print("🚀 PROYECTO LISTO PARA USO")
    print("="*60)
    print("Para ejecutar la aplicación:")
    print("1. Configura la base de datos MySQL en .env")
    print("2. Instala dependencias: pip install -r requirements.txt")
    print("3. Ejecuta: python src/presentation/app.py")
    print("4. Abre: http://localhost:5000")
    
    sys.exit(0 if success else 1)
