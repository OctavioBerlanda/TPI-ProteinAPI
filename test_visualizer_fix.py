#!/usr/bin/env python3
"""
Test rápido para verificar que el sistema está mostrando correctamente las diferencias en el visualizador
"""

print("🧪 TEST RÁPIDO - Verificación del Visualizador")
print("=" * 60)

print("""
🎯 CASO DE PRUEBA RECOMENDADO:

📋 Datos del formulario:
   - Usuario: TestUser
   - Email: test@example.com
   - Nombre: Prueba Hemoglobina E6V
   - ✅ Marcar "Habilitar AlphaFold"

🔹 SECUENCIA ORIGINAL:
MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH

🔹 SECUENCIA MUTADA:
MVHLTPVEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH

📊 RESULTADOS ESPERADOS EN EL VISUALIZADOR:

✅ Secuencia Original:
   - Badge: "📡 AlphaFold DB Real" (verde)
   - Confianza: 95.0%
   - Alerta: "Estructura Real: Obtenida de AlphaFold DB con máxima confianza"

⚠️ Secuencia Mutada:
   - Badge: "📡 AlphaFold DB Real (Mutada)" (amarillo/warning)
   - Confianza: ~77%
   - Alerta: "Estructura Real Mutada: Basada en AlphaFold DB pero con confianza reducida"

📈 Análisis Comparativo:
   - Cambio de Confianza: -18.0 puntos (aprox)
   - RMSD: ~1.3 Å
   - Impacto Predicho: "❌ Perjudicial"

🔬 Mutaciones Detectadas:
   - Total: 1 mutación
   - Posición: 7
   - Cambio: E → V (Ácido Glutámico → Valina)

💡 CÓMO VERIFICAR:
1. Ve a http://localhost:5000
2. Llena el formulario con los datos arriba
3. Envía la comparación
4. Clic en "Ver Análisis Estructural"
5. Verifica que los badges y confianzas coincidan con lo esperado

🎯 SI TODO FUNCIONA CORRECTAMENTE:
- Verás badges diferentes (verde vs amarillo)
- Confianzas diferentes (~95% vs ~77%)
- Alertas explicativas distintas
- Visualización 3D de ambas estructuras
""")

print("=" * 60)
print("✅ Copia las secuencias y prueba en http://localhost:5000")
print("📊 El visualizador ahora debería mostrar las diferencias claramente")
print("=" * 60)
