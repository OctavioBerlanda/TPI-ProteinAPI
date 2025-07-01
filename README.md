# 🧬 TPI-ProteinAPI

> **Sistema de Análisis y Comparación de Proteínas con Integración AlphaFold**

Un sistema web completo para analizar mutaciones en proteínas y comparar sus estructuras 3D utilizando predicciones de AlphaFold.

## 🚀 Características Principales

- ✅ **Análisis de Secuencias:** Validación y comparación de secuencias de aminoácidos
- ✅ **Integración AlphaFold:** Predicción y comparación de estructuras 3D
- ✅ **Visualización 3D:** Viewer interactivo con NGL para modelos moleculares
- ✅ **Base de Datos:** Almacenamiento persistente de comparaciones y resultados
- ✅ **API REST:** Endpoints para integración programática
- ✅ **Interfaz Web:** Dashboard intuitivo para usuarios

## 🏗️ Arquitectura del Sistema

```
TPI-ProteinAPI/
├── src/
│   ├── business/          # Lógica de negocio
│   │   ├── alphafold_service.py    # Servicio AlphaFold
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
- SQLite (incluido con Python)

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

## 🧬 Uso del Sistema

### 1. Análisis de Mutaciones

1. Ingresa la secuencia original de aminoácidos
2. Ingresa la secuencia mutada
3. Marca "Usar AlphaFold" para análisis 3D
4. Revisa los resultados de comparación

### 2. Visualización 3D

- **Modelos individuales:** Ver estructuras por separado
- **Comparación lado a lado:** Visualizar diferencias
- **Superposición:** Analizar cambios estructurales

### 3. API Programática

```python
# Ejemplo de uso de la API
import requests

# Crear comparación
response = requests.post('/api/comparisons', json={
    'original_sequence': 'MVHLTPEEKS...',
    'mutated_sequence': 'MVHLTPVEKS...',
    'enable_alphafold': True
})

# Obtener resultados
comparison_id = response.json()['comparison_id']
results = requests.get(f'/api/comparison/{comparison_id}/structural-analysis')
```

## 📊 Proteínas Soportadas

El sistema puede analizar cualquier proteína, con soporte optimizado para:

- 🩸 **Hemoglobina** (variantes patológicas)
- 💉 **Insulina** (diabetes y trastornos metabólicos)
- 🧠 **p53** (supresión tumoral)
- 🔬 **Lisozima** (función antimicrobiana)
- 🧪 **Hormona de crecimiento** (trastornos del desarrollo)

## 🔗 Endpoints API Principales

```
GET  /api/comparison/{id}/structural-analysis
GET  /api/comparison/{id}/model/{type}/view.pdb
GET  /api/comparison/{id}/model/{type}/view.cif
POST /api/comparisons
GET  /api/user/{username}/comparisons
```

## 🧪 Testing y Debugging

- **Tests:** `python -m pytest tests/`
- **Debug Viewer:** Archivo `debug_ngl_viewer.html` para testing de NGL
- **Mutaciones de ejemplo:** Ver `MUTACIONES_PARA_PROBAR.md`

## 📁 Archivos Importantes

- `src/main.py` - Punto de entrada principal
- `requirements.txt` - Dependencias Python
- `MUTACIONES_PARA_PROBAR.md` - Ejemplos de mutaciones
- `debug_ngl_viewer.html` - Herramienta de debugging
- `.gitignore` - Archivos ignorados por Git

## 🤝 Contribución

1. Fork el proyecto
2. Crea una branch para tu feature
3. Commit tus cambios
4. Push a la branch
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT.

## 🆘 Soporte

Para problemas o preguntas:

- Revisa la documentación en `docs/`
- Usa el debug viewer para problemas de visualización 3D
- Consulta los ejemplos en `MUTACIONES_PARA_PROBAR.md`
