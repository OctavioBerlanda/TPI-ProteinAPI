#!/usr/bin/env python3
"""
Generador de secuencias de prueba que muestran claramente el impacto de las mutaciones
"""

def generate_test_sequences():
    """Genera pares de secuencias para mostrar diferencias claras"""
    
    print("🧬 SECUENCIAS DE PRUEBA PARA LA WEB")
    print("=" * 60)
    
    print("\n🎯 CASO 1: Hemoglobina con Mutación E6V (Anemia Falciforme)")
    print("-" * 60)
    print("📊 Resultado esperado: Original 95% vs Mutada ~62%")
    print("\n🔹 ORIGINAL:")
    original_hb = "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    print(original_hb)
    
    print("\n🔹 MUTADA (E6V):")
    mutated_hb = "MVHLTPVEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    print(mutated_hb)
    print(f"🔍 Cambio en posición 7: E → V")
    
    print("\n" + "=" * 60)
    print("\n🎯 CASO 2: Lisozima con Mutación Y134P (Sitio Activo)")
    print("-" * 60)
    print("📊 Resultado esperado: Original 95% vs Mutada ~62%")
    print("\n🔹 ORIGINAL:")
    original_ly = "MKALIVLGLVLLSVTVQGKVFERCELARTLKRLGMDGYRGISLANWMCLAKWESGYNTRATNYNAGDRSTDYGIFQINSRYWCNDGKTPGAVNACHLSCSALLQDNIADAVACAKRVVRDPQGIRAWVAWRNRCQNRDVRQYVQGCGV"
    print(original_ly)
    
    print("\n🔹 MUTADA (Y134P):")
    mutated_ly = "MKALIVLGLVLLSVTVQGKVFERCELARTLKRLGMDGYRGISLANWMCLAKWESGYNTRATNYNAGDRSTDYGIFQINSRYWCNDGKTPGAVNACHLSCSALLQDNIADAVACAKRVVRDPQGIRAWVAWRNRCQNRDVRQPVQGCGV"
    print(mutated_ly)
    print(f"🔍 Cambio en posición 134: Y → P")
    
    print("\n" + "=" * 60)
    print("\n🎯 CASO 3: Hemoglobina con Doble Mutación (Más Severa)")
    print("-" * 60)
    print("📊 Resultado esperado: Original 95% vs Mutada ~54%")
    print("\n🔹 ORIGINAL:")
    print(original_hb)
    
    print("\n🔹 MUTADA (E6V + H7P):")
    double_mutated = "MVHLTPVPKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH"
    print(double_mutated)
    print(f"🔍 Cambios: E6V (pos 7) + H7P (pos 8)")
    
    print("\n" + "=" * 60)
    print("💡 INSTRUCCIONES:")
    print("1. Ve a http://localhost:5000")
    print("2. ✅ Marca 'Habilitar AlphaFold'")
    print("3. Copia las secuencias de cualquier caso")
    print("4. Observa las diferencias claras en confianza")
    print("5. Revisa el análisis estructural detallado")
    print("=" * 60)

if __name__ == "__main__":
    generate_test_sequences()
