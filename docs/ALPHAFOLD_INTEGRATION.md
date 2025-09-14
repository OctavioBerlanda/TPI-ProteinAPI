# 🧬 Integración Swiss-Model y AlphaFold - Guía Técnica

## 📋 Descripción General

El sistema **Comparador de Proteínas** incluye integración completa con **Swiss-Model** para predicción de estructuras 3D y **AlphaFold Database** para información de proteínas conocidas.

## 🎯 Funcionalidades Implementadas

### ✅ Predicción de Estructuras 3D con Swiss-Model

- **Predicción automática** usando Swiss-Model API para secuencias original y mutada
- **Flujo asíncrono de 3 pasos**: Envío → Polling → Descarga
- **Timeout dinámico** basado en longitud de secuencia (5-10 minutos)
- **Archivos PDB/CIF descargables** para visualización externa
- **Métricas de calidad** (GMQE y QMEAN scores) integradas

### ✅ Consulta de Datos AlphaFold

- **Información de proteínas** conocidas desde AlphaFold Database
- **UniProt ID, nombre y organismo** automáticamente identificados
- **Complemento informativo** sin predicción estructural adicional

### ✅ Análisis Estructural Comparativo

- **Cálculo de RMSD** entre estructuras original y mutada
- **Análisis de impacto** de mutaciones en la estabilidad
- **Evaluación de cambios** de confianza entre estructuras
- **Clasificación del efecto** (beneficioso, neutral, perjudicial)

### ✅ Interfaz Web Integrada

- **Checkbox opcional** para habilitar predicción 3D en el formulario
- **Página especializada** para mostrar resultados estructurales
- **API endpoints** para acceso programático a los datos
- **Descarga directa** de modelos 3D en formato PDB/CIF

## 🏗️ Arquitectura del Sistema

### Capa de Negocio

```
src/business/alphafold_service.py
├── AlphaFoldService
│   ├── predict_structure()           # Coordina predicción 3D
│   ├── _predict_with_swiss_model()   # Implementa flujo Swiss-Model
│   ├── _download_swiss_model_file()  # Descarga modelos PDB/CIF
│   ├── compare_structures()          # Compara estructuras
│   └── cleanup_old_models()          # Gestión de archivos
└── ComparisonManager (actualizado)
    └── create_comparison_with_alphafold()
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
├── routes.py (rutas AlphaFold)
├── forms.py (checkbox alpha_fold)
└── templates/
    └── alphafold_results.html
```

## 🚀 Uso del Sistema

### 1. Configuración

```env
# .env
ENABLE_ALPHAFOLD=true
ALPHAFOLD_API_ENDPOINT=https://alphafolddb.org/api
COLABFOLD_ENDPOINT=http://localhost:8080
MODELS_DIRECTORY=models/alphafold
API_TIMEOUT=300
```

### 2. Interfaz Web

1. Accede a `http://localhost:5000`
2. Completa el formulario de comparación
3. **Marca el checkbox "Incluir Predicción de AlphaFold"**
4. Envía las secuencias
5. **Espera 5-10 minutos** según longitud de secuencia
6. Ve los resultados en la página de resultados
7. Haz clic en **"Ver Análisis Estructural"** para detalles completos

### 3. API Programática

```python
# Ejemplo de uso directo
from src.business.comparison_manager import ComparisonManager
from config.config import get_config

manager = ComparisonManager(get_config())
result = manager.create_comparison_with_alphafold(
    username="usuario",
    email="email@ejemplo.com",
    original_sequence="MKLLSLVCLASFA",
    mutated_sequence="MKLMSLVCLASFA",
    enable_alphafold=True  # Activa Swiss-Model + AlphaFold Data
)
```

### 4. Endpoints API REST

```http
GET /api/comparison/{id}/structural-analysis
GET /api/comparison/{id}/model/original
GET /api/comparison/{id}/model/mutated
```

## 📊 Datos Estructurales Disponibles

### Información de Confianza Swiss-Model

- **GMQE scores**: Global Model Quality Estimation (0-1, preferido)
- **QMEAN scores**: Qualitative Model Energy Analysis (Z-score)
- **Confianza final**: Principalmente calculada desde GMQE (× 100%)
- **Clasificación**: Alta (>70%), Media (40-70%), Baja (<40%)

### Información AlphaFold Database

- **UniProt ID**: Identificador único de la proteína
- **Nombre proteína**: Descripción funcional
- **Organismo**: Especie de origen
- **Versión AlphaFold**: Versión de la base de datos

### Análisis Comparativo

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

### Clasificación de Impacto

- **Beneficioso**: Aumento de confianza >10 puntos GMQE
- **Neutral**: Cambio de confianza ±10 puntos GMQE
- **Perjudicial**: Disminución de confianza >10 puntos GMQE

### Timeouts por Longitud de Secuencia

- **≤200 residuos**: Timeout de 5 minutos (secuencias cortas/medianas)
- **>200 residuos**: Timeout de 10 minutos (secuencias largas y complejas)
- **Justificación**: Secuencias largas requieren más tiempo de modelado homólogo

## 🧪 Testing y Validación

### Tests Automatizados

```bash
# Ejecutar todos los tests incluyendo Swiss-Model
python tests/run_tests.py

# Tests específicos de integración
python -m pytest tests/test_alphafold_integration.py

# Tests de la nueva lógica Swiss-Model
python test_swiss_model_new_logic.py
```

### Demostración

```bash
# Ejecutar demostración Swiss-Model
python test_swiss_model.py

# Test completo de la nueva lógica
python test_swiss_model_new_logic.py
```

## 🛠️ Instalación y Configuración

### Dependencias

```bash
pip install -r requirements.txt
```

### Configuración de Directorio

```bash
mkdir -p models/alphafold
```

### Variables de Entorno

Copiar y ajustar el archivo `.env` con las configuraciones de AlphaFold.

## 📈 Métricas y Monitoreo

### Rendimiento

- **Tiempo de predicción**: 5-10 minutos según longitud de secuencia
- **Secuencias ≤200 residuos**: Típicamente 2-5 minutos
- **Secuencias >200 residuos**: Típicamente 5-10 minutos
- **Uso de disco**: ~1-5 MB por modelo PDB/CIF generado
- **Precisión**: Dependiente de homología y calidad de templates

### Limitaciones Actuales

- **Longitud máxima**: 2000 aminoácidos (límite Swiss-Model)
- **Tiempo de espera**: 5-10 minutos dinámico según secuencia
- **Dependencia de templates**: Requiere proteínas homólogas conocidas
- **API rate limits**: Límites de Swiss-Model API aplicables

### Configuración de Timeouts

```python
# Lógica implementada en AlphaFoldService
if sequence_length > 200:
    max_attempts = 60  # 10 minutos
    print(f"Secuencia larga ({sequence_length} residuos). Timeout: 10 min")
else:
    max_attempts = 30  # 5 minutos
    print(f"Timeout: 5 minutos")
```

## 🔮 Próximas Funcionalidades

### En Desarrollo

- **Visualizador 3D integrado** usando PyMol.js o NGL Viewer
- **Análisis de bolsillos** y sitios activos
- **Comparación con estructuras experimentales** (PDB)
- **Predicción de efectos alostéricos**

### Planificado

- **Integración con ChimeraX** para visualización avanzada
- **Análisis de dinámicas moleculares** básicas
- **Predicción de interacciones** proteína-proteína
- **Export a formatos** adicionales (mmCIF, mol2)

## 📞 Soporte y Solución de Problemas

### Problemas Comunes

1. **"Swiss-Model service not available"**: Verificar token y configuración API
2. **"Model file not found"**: Comprobar permisos del directorio de modelos
3. **"Timeout exceeded (5/10 minutes)"**: Secuencia muy larga o Swiss-Model sobrecargado
4. **"No homologous templates found"**: Swiss-Model no encontró proteínas similares
5. **"GMQE score too low"**: Baja confianza en el modelo generado

### Configuración Requerida

```env
# .env
SWISS_MODEL_TOKEN=your_swiss_model_api_token
MODELS_DIRECTORY=models/alphafold
API_TIMEOUT=600  # 10 minutos máximo
ALPHAFOLD_API_ENDPOINT=https://alphafolddb.org/api
```

### Logs de Debug

Los logs detallados se encuentran en la consola durante la ejecución.

### Contacto

Para problemas específicos de AlphaFold, consultar la documentación del proyecto.

---

**✅ La integración Swiss-Model está completamente implementada y optimizada para secuencias de diferentes longitudes.**

**🔧 Optimizaciones incluidas:**

- Timeout dinámico basado en longitud de secuencia
- Manejo mejorado de estados asíncronos
- Extracción automática de métricas de calidad GMQE/QMEAN
- Integración con AlphaFold Database para información complementaria
