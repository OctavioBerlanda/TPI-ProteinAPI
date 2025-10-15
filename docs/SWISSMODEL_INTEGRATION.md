# 🧬 Integración Swiss-Model + Modeller - Guía Técnica Avanzada

## 📋 Descripción General

El sistema **Comparador de Proteínas** implementa un flujo híbrido optimizado que combina:
- **Swiss-Model** para obtener modelos homólogos de la secuencia original
- **Modeller** para aplicar mutaciones con máxima precisión estructural
- **Algoritmos propios** para análisis fisicoquímico y estructural completo

## 🎯 Funcionalidades Implementadas

### ✅ Predicción Híbrida de Estructuras (Swiss-Model + Modeller)

**Flujo Optimizado:**
1. **Secuencia Original** → Swiss-Model (múltiples homólogos + consenso)
2. **Secuencia Mutada** → Modeller (mutación sobre consenso original)
3. **Análisis** → Algoritmos propios (ΔΔG, BLOSUM, Grantham, RMSD, SASA)

**Ventajas del enfoque híbrido:**
- ✅ **1 sola llamada a Swiss-Model** (solo para original) → Más rápido
- ✅ **Modeller para mutaciones** → Alta precisión con rotámeros optimizados
- ✅ **Sin dependencia de templates para mutadas** → Funciona siempre
- ✅ **Tiempo reducido:** 5-10 min vs 10-20 min del método anterior

### ✅ Predicción con Swiss-Model (Solo Original)

- **Predicción automática** usando Swiss-Model API **únicamente para secuencia original**
- **Flujo asíncrono de 3 pasos**: Envío → Polling → Descarga
- **Timeout dinámico** basado en longitud de secuencia (5-10 minutos)
- **Múltiples modelos homólogos** (3-5 plantillas PDB)
- **Archivos PDB/CIF descargables** para visualización externa
- **Métricas de calidad** (GMQE y QMEAN scores) integradas

### ✅ Mutación con Modeller (Solo Mutada)

**Nuevo componente: `ModellerMutator`**
- **Rotámeros optimizados** usando biblioteca Dunbrack
- **Minimización energética** con Conjugate Gradients
- **Dinámica molecular corta** (300 pasos a 300K) para refinamiento
- **Optimización local** alrededor de cada mutación (radio 10-12Å)
- **Métricas DOPE** para evaluación de calidad estructural
- **3 niveles de optimización**: low (rápido), medium (balanceado), high (máxima precisión)

**Requiere licencia académica GRATUITA:**
- Obtener en: https://salilab.org/modeller/registration.html
- Válida para estudiantes e investigadores de instituciones académicas
- Configurar en `.env`: `MODELLER_LICENSE_KEY=tu_clave`

### ✅ Algoritmos Propios de Análisis

#### 🤝 Mezcla de Plantillas Consenso

- **`ConsensusModelBuilder`** integra múltiples modelos homólogos ponderándolos por GMQE/QMEAN
- **Cálculo automático de cobertura** y SASA por residuo para alimentar análisis posteriores
- **Métricas de conservación ponderada** por residuo usando la alineación estructural
- **Alineamiento y superposición** usando Bio.PDB para asegurar geometría consistente

#### 🧮 Puntuación Fisicoquímica de Mutaciones

- **`MutationScorer`** combina BLOSUM62, distancia de Grantham y heurísticas de ΔΔG
- **Contexto ambiental** por residuo (SASA, conservación, estructura secundaria) incorporado en el puntaje
- **Clasificación automática** del impacto: estabilizante, neutro, levemente desestabilizante o desestabilizante

#### 📐 Métricas Estructurales Integradas

- **RMSD global y local** mediante superposición de átomos CA y vecindarios backbone
- **Cálculo de SASA** previo y posterior a mutaciones para medir efectos de exposición
- **Cobertura y solapamiento** cuantificados para detectar zonas no modeladas

#### 🎯 Calibración Dinámica de Confianza

- Penalización final basada en ΔΔG agregados, RMSD, cobertura y picos locales
- **Curvas de penalización** ajustadas para priorizar modelos con soporte estructural sólido
- **Reporte detallado** que acompaña cada resultado con métricas intermedias para auditoría

### ✅ Sistema de Confianza Mejorado

- **Penalización Multi-paramétrica:** Ajuste basado en ΔΔG, RMSD, SASA y DOPE scores
- **Puntuaciones Derivadas:** Métricas específicas para cada tipo de análisis
- **Validación Cruzada:** Combinación de algoritmos para mayor robustez
- **Métricas de Modeller:** DOPE scores integrados en la evaluación final

## 🏗️ Arquitectura del Sistema

### Capa de Negocio

```
src/business/swissmodel_service.py
├── SwissModelService
│   ├── predict_structure()                      # Predicción 3D con Swiss-Model (SOLO ORIGINAL)
│   ├── predict_mutated_with_modeller()         # 🔥 NUEVA: Mutación con Modeller (SOLO MUTADA)
│   ├── _predict_with_swiss_model()             # Implementa flujo Swiss-Model
│   ├── _download_swiss_model_file()            # Descarga modelos PDB/CIF
│   ├── compare_structures()                    # Compara estructuras
│   ├── _compute_structural_metrics()            # Métricas RMSD/SASA
│   ├── _collect_ca_atoms() / _collect_local_atoms() # Utilidades geométricas
│   ├── _derive_confidence_penalty()             # Ajuste de confianza final
│   └── cleanup_old_models()                     # Gestión de archivos

src/business/modeller_mutator.py [NUEVO]
├── ModellerMutator
│   ├── mutate_structure()                       # Aplica mutaciones con Modeller
│   ├── _setup_environment()                     # Configura entorno Modeller
│   ├── _load_structure()                        # Carga PDB
│   ├── _apply_single_mutation()                 # Mutación puntual + rotámeros
│   ├── _optimize_low/medium/high()              # 3 niveles de optimización
│   ├── _assess_quality()                        # Calcula DOPE scores
│   └── _aa_to_modeller()                        # Conversión códigos aminoácidos

src/business/consensus_model.py
├── ConsensusModelBuilder
│   ├── build()                                  # Fusiona plantillas y calcula SASA
│   ├── _collect_alignment_atoms()               # Selecciona átomos guía
│   └── _compute_sasa()                          # Ejecuta Shrake-Rupley por residuo

src/business/mutation_scoring.py
├── MutationScorer
│   ├── score_mutations()                        # Puntajes y agregados por mutación
│   ├── _estimate_ddg()                          # Heurística ΔΔG con propiedades
│   └── classify_ddg()                           # Etiquetas de impacto

config/modeller_config.py [NUEVO]
└── Configuración de Modeller (licencia, optimización, umbrales)
```

### Comparación Manager (actualizado)

```python
ComparisonManager._process_swissmodel_predictions()
├── Paso 1: SwissModel para ORIGINAL
│   ├── predict_structure(original_sequence, return_all_models=True)
│   └── ConsensusModelBuilder.build() → Modelo consenso
│
├── Paso 2: Modeller para MUTADA (NUEVO FLUJO)
│   ├── predict_mutated_with_modeller()
│   │   ├── MutationScorer.score_mutations()      # Análisis fisicoquímico
│   │   ├── ModellerMutator.mutate_structure()    # Mutación física
│   │   ├── _compute_structural_metrics()         # RMSD, SASA
│   │   ├── _derive_confidence_penalty()          # Ajuste confianza
│   │   └── build_mutation_report()               # Reporte HTML
│   └── ❌ NO llama a Swiss-Model para mutada
│
└── Paso 3: Comparación estructural
    └── compare_structures() → Análisis comparativo final
```

### Algoritmos Implementados

#### 🔬 Mutación con Modeller (NUEVO)

```
ModellerMutator.mutate_structure()
├── _setup_environment()              # Configura Modeller (topología, parámetros)
├── _load_structure()                 # Carga PDB consenso original
├── Para cada mutación:
│   ├── _apply_single_mutation()
│   │   ├── Seleccionar residuo
│   │   ├── Mutar con rotámeros Dunbrack
│   │   ├── Optimizar localmente (radio 10-12Å)
│   │   └── Minimización Conjugate Gradients (200 iter)
│   └── ...
├── _optimize_high()                  # Optimización global
│   ├── Conjugate Gradients (500 iter)
│   ├── Molecular Dynamics (300 pasos a 300K)
│   └── Refinamiento final (200 iter)
└── _assess_quality()                 # DOPE scores
```

#### 🤝 Generación de Consenso Estructural

```
ConsensusModelBuilder.build()
├── _collect_alignment_atoms()     # Selección de átomos para alineamiento
├── _superimpose_templates()       # Superposición múltiple
├── _compute_sasa()                # Cálculo Shrake-Rupley por residuo
└── _export_consensus_structure()  # Escritura PDB final
```

#### � Puntuación Fisicoquímica de Mutaciones

```
MutationScorer.score_mutations()
├── _get_blosum_score()            # Consulta BLOSUM62
├── _get_grantham_distance()       # Distancia fisicoquímica
├── _estimate_ddg()                # Heurística ΔΔG con SASA y conservación
└── classify_ddg()                 # Etiquetado del impacto
```

#### 📐 Métricas Estructurales Automatizadas

```
SwissModelService._compute_structural_metrics()
├── _collect_ca_atoms()            # Listas pareadas de CA
├── _collect_local_atoms()         # Ventanas backbone alrededor de mutaciones
├── _sum_residue_sasa()            # Integración de SASA por residuo
└── _derive_confidence_penalty()   # Penalización dinámica de confianza
```

### 🗂️ Reportes Interactivos de Mutaciones

```
build_mutation_report()
├── Genera HTML responsivo con métricas por residuo
├── Integra conservación, SASA y puntajes fisicoquímicos
└── Produce resumen de confianza antes/después del ajuste
```

### Flujo Swiss-Model (3 Pasos)

```
1. ENVÍO (POST /automodel)
   ├── Envía secuencia y título del proyecto
   ├── Obtiene project_id
   └── Configura headers de autenticación

2. POLLING (GET /project/{id}/models/summary/)
   ├── Verifica estado cada 10 segundos
   ├── Estados válidos: PENDING, RUNNING, QUEUED, INITIALISED
   ├── Timeout dinámico según longitud de secuencia
   └── Espera hasta estado COMPLETED

3. DESCARGA (GET coordinates_url)
   ├── Extrae URL del mejor modelo
   ├── Descarga archivo PDB/CIF
   ├── Extrae métricas GMQE y QMEAN
   └── Calcula confianza final
```

### Capa de Datos

```
src/data/models.py (actualizado)
├── ProteinComparison
│   ├── original_model_path
│   ├── mutated_model_path
│   ├── original_confidence_score
│   ├── mutated_confidence_score
│   ├── rmsd_value
│   └── structural_changes
```

### Capa de Presentación

```
src/presentation/
├── routes.py (rutas SwissModel)
├── forms.py (checkbox swiss_model)
└── templates/
    └── swissmodel_results.html
```

## 🚀 Uso del Sistema

### 1. Configuración

#### Paso 1.1: Variables de Entorno

```env
# .env

# SwissModel (para secuencia original)
ENABLE_SWISSMODEL=true
SWISSMODEL_API_ENDPOINT=https://swissmodel.expasy.org/
SWISS_MODEL_TOKEN=tu_token_swissmodel_aqui
SWISSMODEL_CONSENSUS_TEMPLATES=3
MODELS_DIRECTORY=models/swissmodel
API_TIMEOUT=600

# Modeller (para mutaciones) - NUEVO
MODELLER_LICENSE_KEY=MODELIRANJE  # Tu clave académica
MODELLER_OPTIMIZATION_LEVEL=high   # low, medium, high
```

#### Paso 1.2: Obtener Licencia de Modeller (GRATUITA)

1. **Ir a:** https://salilab.org/modeller/registration.html
2. **Completar formulario** con tu email institucional `@frro.utn.edu.ar`
3. **Recibir email** con tu clave de licencia
4. **Copiar clave** al `.env`

#### Paso 1.3: Instalar Modeller

```powershell
# Opción A: Con conda (RECOMENDADO)
conda install -c salilab modeller

# Opción B: Descarga manual
# https://salilab.org/modeller/download_installation.html
```

#### Paso 1.4: Verificar Instalación

```powershell
# Ejecutar script de verificación
python setup_modeller.py
```

**Salida esperada:**
```
🔬 INSTALADOR DE MODELLER PARA TPI-ProteinAPI
📦 Paso 1: Verificando instalación de Modeller...
   ✅ Modeller 10.5 está instalado
🔑 Paso 2: Verificando licencia académica...
   ✅ Licencia configurada: MODE...
🧪 Paso 3: Probando Modeller...
   ✅ Modeller funciona correctamente
✅ INSTALACIÓN COMPLETADA
```

### 2. Interfaz Web

1. Accede a `http://localhost:5000`
2. Completa el formulario de comparación
3. **Marca el checkbox "Incluir Predicción de SwissModel"**
4. Envía las secuencias
5. **Espera 5-10 minutos** según longitud de secuencia
6. Ve los resultados en la página de resultados
7. Haz clic en **"Ver Análisis Estructural"** para detalles completos

### 3. API Programática

```python
# Ejemplo de uso completo con el nuevo flujo
from src.business.comparison_manager import ComparisonManager
from config.config import get_config

manager = ComparisonManager(get_config())

# Crear comparación con predicción híbrida
result = manager.create_comparison_with_swissmodel(
    username="usuario",
    email="email@frro.utn.edu.ar",
    original_sequence="MKLLSLVCLASFA",
    mutated_sequence="MKLMSLVCLASFA",  # L→M en posición 4
    enable_swissmodel=True  # Activa predicción híbrida
)

# Ver resultados
if result['success']:
    swissmodel = result['swissmodel_results']
    
    # Original (Swiss-Model)
    original = swissmodel['original']
    print(f"Original: {original['confidence']}% confianza")
    print(f"Método: {original.get('prediction_method')}")
    
    # Mutada (Modeller)
    mutated = swissmodel['mutated']
    print(f"Mutada: {mutated['confidence']}% confianza")
    print(f"Método: {mutated['prediction_method']}")  # → 'modeller_mutation_on_consensus'
    print(f"DOPE: {mutated['modeller_quality']['dope_score']}")
    
    # Comparación
    comparison = swissmodel['comparison']
    print(f"RMSD: {comparison['rmsd_value']} Å")
```

**Logs del nuevo flujo:**
```
➡️  Paso 1: Obteniendo estructura de referencia para la secuencia original...
   📊 Resultado original: 3 modelos disponibles
   🏆 Mejor modelo: GMQE=0.75, Confianza=75.0%
   🤝 Modelo consenso generado (3 plantillas, cobertura 0.98)

➡️  Paso 2: Generando estructura mutada desde modelos originales con Modeller...
   🔄 Mutaciones detectadas: [(4, 'L', 'M')]
   🧬 Aplicando 1 mutación(es) con Modeller...
   🔬 Iniciando mutación con Modeller (nivel: high)
      🧬 Mutación 1/1: L4M
      ⚙️ Optimizando geometría (nivel high)...
      📊 Evaluando calidad del modelo...
   ✅ Mutación completada: mutated_modeller.pdb
   📈 DOPE score: -8234.56
   📈 DOPE normalizado: -0.041
   📊 Calculando métricas estructurales (RMSD, SASA)...
   🎯 Confianza base: 75.0%
   🎯 Penalización: -2.5%
   🎯 Confianza ajustada: 72.5%

✅ Predicción con Modeller completada en 45.3s
```

**Nota importante:** ❌ NO verás llamadas a Swiss-Model para la secuencia mutada.

### 4. Endpoints API REST

```http
GET /api/comparison/{id}/structural-analysis
GET /api/comparison/{id}/model/original
GET /api/comparison/{id}/model/mutated
GET /api/comparison/{id}/mutation-report  # Nuevo: Reporte HTML detallado
```

## 📊 Datos Estructurales Disponibles

### Información de Swiss-Model (Solo Original)

- **GMQE scores**: Global Model Quality Estimation (0-1, preferido)
- **QMEAN scores**: Qualitative Model Energy Analysis (Z-score)
- **Confianza final**: Principalmente calculada desde GMQE (× 100%)
- **Clasificación**: Alta (>70%), Media (40-70%), Baja (<40%)
- **Templates usados**: 3-5 estructuras homólogas del PDB
- **Cobertura consenso**: Porcentaje de la secuencia cubierta

### Información de Modeller (Solo Mutada) - NUEVO

#### **DOPE Score (Discrete Optimized Protein Energy)**
- **Métrica principal** de calidad estructural de Modeller
- **Valores negativos = mejor calidad**
- **Interpretación:**
  - `< -15000`: Excelente
  - `-15000 to 0`: Bueno
  - `0 to +10000`: Aceptable
  - `> +10000`: Revisar

#### **DOPE Normalizado (por residuo)**
- **Normalizado** por número de residuos para comparar proteínas de diferente tamaño
- **Interpretación:**
  - `< -0.03`: Excelente ✅
  - `-0.03 to 0.0`: Bueno
  - `0.0 to 0.05`: Aceptable
  - `> 0.05`: Pobre (revisar mutación)

#### **Nivel de Optimización**
- `low`: Rápido (~10-20s), precisión básica
- `medium`: Balanceado (~30-60s), buena precisión
- `high`: Máxima precisión (~1-3min), minimización + MD ⭐

#### **Método de Predicción**
- `modeller_mutation_on_consensus`: Modeller aplicado sobre consenso de Swiss-Model

### Análisis Comparativo (Algoritmos Propios)

- **RMSD**: Root Mean Square Deviation entre estructuras
- **Cambio de confianza**: Diferencia en puntuaciones GMQE/QMEAN
- **Impacto predicho**: Evaluación del efecto de la mutación
- **Regiones afectadas**: Identificación de áreas de cambio

### Archivos Generados

- **Modelos PDB/CIF**: Archivos de estructura 3D descargables
- **Metadatos JSON**: Información detallada del análisis
- **Logs de procesamiento**: Tiempos y métodos utilizados

## 🔬 Interpretación de Resultados

### Puntuaciones de Confianza Swiss-Model

#### **GMQE (Global Model Quality Estimation)**

- **0.8-1.0**: Muy alta confianza (estructura muy fiable)
- **0.6-0.8**: Confianza alta (estructura generalmente correcta)
- **0.4-0.6**: Confianza moderada (estructura posiblemente correcta)
- **<0.4**: Baja confianza (estructura poco fiable)

#### **QMEAN (Z-score)**

- **>-1**: Excelente calidad del modelo
- **-1 to -2**: Buena calidad
- **-2 to -3**: Calidad moderada
- **<-3**: Baja calidad (señal de alerta)

### Valores RMSD

- **<1.0 Å**: Cambio estructural mínimo
- **1.0-2.0 Å**: Cambio moderado, probablemente tolerable
- **2.0-5.0 Å**: Cambio significativo, posible impacto funcional
- **>5.0 Å**: Cambio dramático, probable pérdida de función

### Clasificación de Impacto (ΔΔG)

**Basado en análisis fisicoquímico (BLOSUM, Grantham, ΔΔG):**
- **Estabilizante**: ΔΔG < -0.5 kcal/mol (mejora estructura)
- **Neutro**: -0.5 ≤ ΔΔG < 0.5 kcal/mol (sin cambio significativo)
- **Levemente desestabilizante**: 0.5 ≤ ΔΔG < 2.0 kcal/mol (cambio tolerable)
- **Desestabilizante**: ΔΔG ≥ 2.0 kcal/mol (impacto significativo)

### Tiempos de Procesamiento

**Con el nuevo flujo híbrido:**
- **Secuencia original (Swiss-Model)**: 2-5 min (≤200 aa) o 5-10 min (>200 aa)
- **Secuencia mutada (Modeller)**: 30s-3min según nivel de optimización
- **Total estimado**: 3-13 minutos (vs 10-20 min del método anterior)

**Niveles de optimización Modeller:**
- `low`: ~10-20 segundos
- `medium`: ~30-60 segundos
- `high`: ~1-3 minutos ⭐ (recomendado)

## 🧪 Testing y Validación

### Tests Automatizados

```bash
# Verificar sintaxis
python -m compileall src

# Verificar instalación de Modeller
python setup_modeller.py

# Test de integración (si existe)
python test_swissmodel_debug.py
```

## 🛠️ Instalación y Configuración

### Dependencias Base

```bash
# Instalar dependencias Python
pip install -r requirements.txt
```

### Instalación de Modeller (NUEVO - Requerido)

```bash
# Opción A: Con conda (RECOMENDADO)
conda install -c salilab modeller

# Opción B: Descarga manual
# https://salilab.org/modeller/download_installation.html
```

### Obtener Licencia Académica (GRATUITA)

1. Ir a: https://salilab.org/modeller/registration.html
2. Completar con email institucional `@frro.utn.edu.ar`
3. Recibir clave por email
4. Agregar a `.env`: `MODELLER_LICENSE_KEY=tu_clave`

### Configuración de Directorio

```bash
mkdir -p models/swissmodel
```

### Variables de Entorno

Copiar y ajustar el archivo `.env` con las configuraciones de SwissModel.

## 📈 Métricas y Monitoreo

### Rendimiento del Sistema Híbrido

**Tiempos de procesamiento:**
- **Original (Swiss-Model)**: 2-10 min según longitud
  - ≤200 residuos: 2-5 minutos
  - >200 residuos: 5-10 minutos
- **Mutada (Modeller)**: 30s-3min según optimización
  - `low`: ~10-20 segundos
  - `medium`: ~30-60 segundos  
  - `high`: ~1-3 minutos
- **Total**: 3-13 minutos (50% más rápido que antes)

**Uso de recursos:**
- **Disco**: ~1-5 MB por modelo PDB
- **RAM**: ~500MB-2GB durante optimización Modeller
- **CPU**: Intensivo durante MD (Molecular Dynamics)

### Precisión y Confiabilidad

**Original (Swiss-Model):**
- Depende de homología (GMQE > 0.6 = alta confianza)
- Requiere templates en PDB

**Mutada (Modeller):**
- Alta precisión para mutaciones puntuales
- DOPE < -0.03 por residuo = excelente calidad
- No depende de templates adicionales ✅

### Limitaciones

**Swiss-Model (solo original):**
- Longitud máxima: 2000 aminoácidos
- Requiere proteínas homólogas conocidas
- API rate limits aplicables

**Modeller (solo mutada):**
- Requiere licencia académica (gratuita)
- Intensivo en CPU para nivel `high`
- Solo mutaciones puntuales (no inserciones/deleciones grandes)

## 🔮 Próximas Funcionalidades

### En Desarrollo

- **Visualizador 3D integrado** usando PyMol.js o NGL Viewer
- **Análisis de bolsillos** y sitios activos
- **Comparación con estructuras experimentales** (PDB)
- **Predicción de efectos alostéricos**
- **Optimización paralela** de múltiples mutaciones

### Planificado

- **Integración con ChimeraX** para visualización avanzada
- **Análisis de dinámicas moleculares** extendidas con Modeller
- **Predicción de interacciones** proteína-proteína
- **Export a formatos** adicionales (mmCIF, mol2)
- **Machine Learning** para predecir impacto de mutaciones

## 📞 Soporte y Solución de Problemas

### Problemas Comunes con Swiss-Model

1. **"Swiss-Model service not available"**: Verificar token y configuración API
2. **"Model file not found"**: Comprobar permisos del directorio de modelos
3. **"Timeout exceeded (5/10 minutes)"**: Secuencia muy larga o Swiss-Model sobrecargado
4. **"No homologous templates found"**: Swiss-Model no encontró proteínas similares
5. **"GMQE score too low"**: Baja confianza en el modelo generado

### Problemas Comunes con Modeller (NUEVO)

1. **"Modeller no está instalado"**
   - Solución: `conda install -c salilab modeller`
   
2. **"Invalid license key"**
   - Verifica `.env`: `MODELLER_LICENSE_KEY=tu_clave`
   - Sin espacios extra ni comillas
   
3. **"Import modeller could not be resolved"**
   - Reinstalar: `conda install -c salilab modeller --force-reinstall`
   - Verificar PATH de Python
   
4. **"Residue not found at position X"**
   - El PDB puede tener numeración diferente
   - Verifica que las posiciones sean 1-based
   
5. **"DOPE score muy alto (>10000)"**
   - La mutación puede ser muy drástica
   - Revisar BLOSUM/Grantham scores
   - Considerar nivel `high` de optimización

### Configuración Requerida

```env
# .env

# Swiss-Model (para original)
SWISS_MODEL_TOKEN=your_swiss_model_api_token
SWISSMODEL_API_ENDPOINT=https://swissmodel.expasy.org/
MODELS_DIRECTORY=models/swissmodel
API_TIMEOUT=600

# Modeller (para mutada) - NUEVO
MODELLER_LICENSE_KEY=tu_clave_academica
MODELLER_OPTIMIZATION_LEVEL=high
```

### Logs de Debug

**Verifica que el flujo sea correcto:**
```
✅ Correcto (nuevo flujo):
   ➡️  Paso 1: Obteniendo estructura [...] secuencia original...
   ➡️  Paso 2: Generando estructura mutada [...] con Modeller...
   🔬 Aplicando mutaciones con Modeller...
   
❌ Incorrecto (flujo antiguo):
   ➡️  Paso 2: Generando estructura mutada desde modelos originales...
   🔬 Aplicando mutaciones usando algoritmos avanzados...
   [llamada a Swiss-Model para mutada]
```

### Recursos Útiles

**Swiss-Model:**
- Manual: https://swissmodel.expasy.org/docs/
- FAQ: https://swissmodel.expasy.org/docs/faq

**Modeller:**
- Manual: https://salilab.org/modeller/manual/
- Tutorial: https://salilab.org/modeller/tutorial/
- Licencia: https://salilab.org/modeller/registration.html
- Soporte: https://salilab.org/modeller/contact.html

### Contacto

Para problemas específicos del proyecto, consultar la documentación interna o contactar al equipo de desarrollo.

---

**✅ Sistema híbrido Swiss-Model + Modeller completamente implementado y optimizado.**

**🎯 Ventajas del nuevo flujo:**
- ⚡ 50% más rápido (3-13 min vs 10-20 min)
- 🎓 Alta precisión con Modeller académico
- 💰 1 sola llamada a Swiss-Model (ahorro API)
- 🔧 Sin dependencia de templates para mutadas
- 📊 Métricas DOPE adicionales de calidad
