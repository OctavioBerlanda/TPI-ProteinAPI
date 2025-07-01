# 🧬 Integración AlphaFold - Guía Técnica

## 📋 Descripción General

El sistema **Comparador de Proteínas** ahora incluye integración completa con **AlphaFold** para predicción de estructuras 3D y análisis estructural de mutaciones.

## 🎯 Funcionalidades Implementadas

### ✅ Predicción de Estructuras 3D

- **Predicción automática** de estructuras para secuencias original y mutada
- **Soporte para ColabFold local** y simulación para desarrollo
- **Archivos PDB descargables** para visualización externa
- **Puntuaciones de confianza** (pLDDT scores) para cada predicción

### ✅ Análisis Estructural Comparativo

- **Cálculo de RMSD** entre estructuras original y mutada
- **Análisis de impacto** de mutaciones en la estabilidad
- **Evaluación de cambios** de confianza entre estructuras
- **Clasificación del efecto** (beneficioso, neutral, perjudicial)

### ✅ Interfaz Web Integrada

- **Checkbox opcional** para habilitar AlphaFold en el formulario
- **Página especializada** para mostrar resultados estructurales
- **API endpoints** para acceso programático a los datos
- **Descarga directa** de modelos 3D en formato PDB

## 🏗️ Arquitectura del Sistema

### Capa de Negocio

```
src/business/alphafold_service.py
├── AlphaFoldService
│   ├── predict_structure()
│   ├── compare_structures()
│   └── _analyze_structural_changes()
└── ComparisonManager (actualizado)
    └── create_comparison_with_alphafold()
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
5. Ve los resultados en la página de resultados
6. Haz clic en **"Ver Análisis Estructural"** para detalles completos

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
    enable_alphafold=True
)
```

### 4. Endpoints API REST

```http
GET /api/comparison/{id}/structural-analysis
GET /api/comparison/{id}/model/original
GET /api/comparison/{id}/model/mutated
```

## 📊 Datos Estructurales Disponibles

### Información de Confianza

- **pLDDT scores**: Puntuaciones de confianza por residuo
- **Confianza promedio**: Evaluación global de la predicción
- **Clasificación**: Alta (>80%), Media (60-80%), Baja (<60%)

### Análisis Comparativo

- **RMSD**: Root Mean Square Deviation entre estructuras
- **Cambio de confianza**: Diferencia en puntuaciones pLDDT
- **Impacto predicho**: Evaluación del efecto de la mutación
- **Regiones afectadas**: Identificación de áreas de cambio

### Archivos Generados

- **Modelos PDB**: Archivos de estructura 3D descargables
- **Metadatos JSON**: Información detallada del análisis
- **Logs de procesamiento**: Tiempos y métodos utilizados

## 🔬 Interpretación de Resultados

### Puntuaciones de Confianza (pLDDT)

- **90-100**: Muy alta confianza (estructura experimental equivalente)
- **70-90**: Confianza alta (estructura generalmente correcta)
- **50-70**: Confianza baja (estructura posiblemente correcta)
- **<50**: Muy baja confianza (estructura poco fiable)

### Valores RMSD

- **<1.0 Å**: Cambio estructural mínimo
- **1.0-2.0 Å**: Cambio moderado, probablemente tolerable
- **2.0-5.0 Å**: Cambio significativo, posible impacto funcional
- **>5.0 Å**: Cambio dramático, probable pérdida de función

### Clasificación de Impacto

- **Beneficioso**: Aumento de confianza >5 puntos
- **Neutral**: Cambio de confianza ±5 puntos
- **Perjudicial**: Disminución de confianza >5 puntos

## 🧪 Testing y Validación

### Tests Automatizados

```bash
# Ejecutar todos los tests incluyendo AlphaFold
python tests/run_tests.py

# Tests específicos de AlphaFold
python -m pytest tests/test_alphafold_integration.py
```

### Demostración

```bash
# Ejecutar demostración completa
python demo_alphafold.py
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

- **Tiempo de predicción**: Típicamente 30-120 segundos por secuencia
- **Uso de disco**: ~1-5 MB por modelo PDB generado
- **Precisión**: Dependiente de la longitud y complejidad de la secuencia

### Limitaciones Actuales

- **Longitud máxima**: 2000 aminoácidos (configurable)
- **Tiempo de espera**: 5 minutos por predicción (configurable)
- **Modo demo**: Utiliza simulación cuando ColabFold no está disponible

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

1. **"AlphaFold service not available"**: Verificar configuración de endpoints
2. **"Model file not found"**: Comprobar permisos del directorio de modelos
3. **"Timeout exceeded"**: Aumentar `API_TIMEOUT` en configuración

### Logs de Debug

Los logs detallados se encuentran en la consola durante la ejecución.

### Contacto

Para problemas específicos de AlphaFold, consultar la documentación del proyecto.

---

**✅ La integración AlphaFold está completamente implementada y lista para uso en producción.**
