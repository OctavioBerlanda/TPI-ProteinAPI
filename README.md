# 🧬 TPI-ProteinAPI

> **Sistema de Análisis y Comparación de Proteínas con Integración SwissModel**

Un sistema web completo para analizar mutaciones en proteínas y comparar sus estructuras 3D utilizando predicciones de SwissModel.

## 🚀 Características Principales

- ✅ **Análisis de Secuencias:** Validación y comparación de secuencias de aminoácidos
- ✅ **Integración SwissModel:** Predicción y comparación de estructuras 3D usando modelado homólogo
- ✅ **Predicción Avanzada de Mutaciones:** Algoritmos complejos de modelado molecular
  - 🔬 **Análisis Estructural:** RMSD local, cambios en contactos, superficie accesible
  - 🧬 **Estabilidad Proteica:** Cálculos de energía de plegamiento y estabilidad térmica
  - 🎯 **Impacto Funcional:** Análisis de sitios activos y interfaces de unión
  - 🌊 **Dinámica Molecular:** Predicción de cambios en flexibilidad y movimiento
- ✅ **Visualización 3D:** Viewer interactivo con NGL para modelos moleculares
- ✅ **Base de Datos:** Almacenamiento persistente de comparaciones y resultados avanzados
- ✅ **API REST:** Endpoints para integración programática
- ✅ **Interfaz Web:** Dashboard intuitivo para usuarios

## 🏗️ Arquitectura del Sistema

```
TPI-ProteinAPI/
├── src/
│   ├── business/          # Lógica de negocio
│   │   ├── swissmodel_service.py    # Servicio SwissModel
│   │   ├── comparison_manager.py   # Gestor de comparaciones
│   │   └── sequence_service.py     # Validación de secuencias
│   ├── data/             # Capa de datos
│   │   ├── models.py     # Modelos SQLAlchemy
│   │   └── repositories.py        # Repositorios de datos
│   └── presentation/     # Capa de presentación
│       ├── templates/    # Templates HTML
│       ├── static/       # CSS/JS
│       ├── routes.py     # Rutas Flask
│       └── forms.py      # Formularios WTF
├── config/               # Configuración
├── models/               # Modelos 3D generados
├── tests/                # Tests unitarios
└── docs/                 # Documentación
```

## 🛠️ Instalación

### Prerrequisitos

- Python 3.8+
- pip
- MySQL

### Configuración Rápida

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd TPI-ProteinAPI

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Inicializar base de datos
python -c "from src.data.models import init_db; init_db()"

# 4. Ejecutar aplicación
python -m src.main
```

### Acceso a la Aplicación

- **Web UI:** http://localhost:5000
- **API REST:** http://localhost:5000/api/
- **Debug Viewer:** debug_ngl_viewer.html

## 🔬 Funcionalidades Avanzadas de Predicción de Mutaciones

El sistema implementa algoritmos sofisticados de modelado molecular para analizar el impacto de mutaciones en proteínas:

### Análisis Estructural Avanzado

- **RMSD Local:** Calcula la desviación raíz cuadrática media en regiones específicas alrededor de mutaciones
- **Cambios en Contactos:** Detecta pérdidas y ganancias de interacciones intermoleculares
- **Superficie Accesible al Solvent:** Evalúa cambios en el área superficial hidrofóbica/hidrofílica
- **Análisis de Sitios de Mutación:** Caracteriza el entorno local de cada mutación

### Cálculos de Estabilidad Proteica

- **Energía de Plegamiento:** Modelos simplificados de cambio de energía libre de Gibbs
- **Estabilidad Térmica:** Predicción de cambios en temperatura de fusión (Tm)
- **Contribuciones por Mutación:** Análisis detallado del impacto energético de cada aminoácido cambiado
- **Factores Posicionales:** Penalizaciones por mutaciones en regiones críticas (terminales, núcleo hidrofóbico)

### Análisis Funcional

- **Impacto en Sitios Activos:** Detección de mutaciones que afectan residuos catalíticos
- **Interfaces de Unión:** Análisis de cambios en superficies de interacción proteína-proteína
- **Clasificación de Mutaciones:** Categorización por nivel de impacto (bajo, medio, alto)
- **Motivos Estructurales:** Detección de alteraciones en hélices α, láminas β y bucles

### Predicción de Dinámica Molecular

- **Cambios de Flexibilidad:** Análisis de rigidez en diferentes regiones de la proteína
- **Entropía Conformacional:** Estimación de cambios en el espacio conformacional
- **Análisis de Modos Normales Simplificado:** Predicción de movimientos colectivos
- **Regiones Afectadas:** Identificación de segmentos con cambios dinámicos significativos

### Sistema de Confianza Mejorado

- **Penalización Inteligente:** Ajuste de confianza basado en análisis multi-paramétrico
- **Puntuaciones Derivadas:** Métricas específicas para estabilidad, funcionalidad y dinámica
- **Validación Cruzada:** Combinación de múltiples algoritmos para mayor robustez

## 🔗 Endpoints API Principales

```
GET  /api/comparison/{id}/structural-analysis
GET  /api/comparison/{id}/model/{type}/view.pdb
GET  /api/comparison/{id}/model/{type}/view.cif
POST /api/comparisons
GET  /api/user/{username}/comparisons
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una branch para tu feature
3. Commit tus cambios
4. Push a la branch
5. Crea un Pull Request
