# Comparador de Proteínas - Sistema de Análisis de Mutaciones

Sistema desarrollado en Python con arquitectura en 3 capas para comparar secuencias de proteínas y analizar mutaciones.

## 🎯 Características Principales

- **Validación rigurosa** de secuencias de aminoácidos
- **Análisis de mutaciones** (máximo 2 diferencias)
- **Almacenamiento en MySQL** con SQLAlchemy ORM
- **Interfaz web** moderna con Flask
- **Arquitectura en 3 capas** (Presentación, Negocio, Datos)
- **Tests completos** de reglas de negocio

## 🏗️ Arquitectura

```
src/
├── presentation/     # Capa de Presentación (Flask, Templates, Forms)
├── business/        # Capa de Negocio (Validaciones, Lógica)
└── data/           # Capa de Datos (Modelos, Repositorios)
```

## 📋 Requisitos

- Python 3.11+
- MySQL 8.0+
- Dependencias en `requirements.txt`

## 🚀 Instalación y Configuración

### 1. Clonar el proyecto

```bash
cd TPI-ProteinAPI
```

### 2. Crear entorno virtual

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

Editar el archivo `.env`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=protein_comparison_db
DB_USER=root
DB_PASSWORD=tu_password
```

### 5. Crear base de datos en MySQL

```sql
CREATE DATABASE protein_comparison_db;
```

### 6. Ejecutar tests (opcional pero recomendado)

```bash
python tests/run_tests.py
```

### 7. Ejecutar la aplicación

```bash
# Opción A: Script principal (RECOMENDADO)
python app.py

# Opción B: Script alternativo
python run_app.py
```

La aplicación estará disponible en: http://localhost:5000

## 🧪 Reglas de Negocio Implementadas

### ✅ Validaciones de Secuencias

- **RN-001**: Solo aminoácidos válidos (20 estándar)
- **RN-002**: Secuencias de igual longitud
- **RN-003**: Máximo 2 mutaciones
- **RN-004**: Mínimo 1 diferencia
- **RN-005**: Limpieza automática de secuencias

### ✅ Gestión de Datos

- **RN-006**: Creación automática de usuarios
- **RN-007**: Trazabilidad completa de comparaciones

## 🎮 Uso del Sistema

### 1. Página Principal

- Ingresa tus datos (usuario, email)
- Proporciona las dos secuencias de proteínas
- El sistema valida en tiempo real

### 2. Resultados

- Análisis detallado de mutaciones
- Visualización de diferencias
- Información de confianza

### 3. Búsqueda

- Busca comparaciones por usuario
- Historial completo de análisis

## 📊 Ejemplos de Uso

### Secuencias Válidas (1 mutación)

```
Original: ARNDCQEGHILKMFPSTWYV
Mutada:   GRNDCQEGHILKMFPSTWYV
Resultado: A1G (Alanina → Glicina en posición 1)
```

### Secuencias Válidas (2 mutaciones)

```
Original: ARNDCQ
Mutada:   GRNGCQ
Resultado: A1G, D4G
```

### Casos Inválidos

- Más de 2 diferencias ❌
- Diferentes longitudes ❌
- Caracteres inválidos (X, Z, etc.) ❌
- Secuencias idénticas ❌

## 🧪 Testing

Ejecutar todos los tests:

```bash
python tests/run_tests.py
```

Tests específicos:

```bash
python -m unittest tests.test_sequence_business_rules
python -m unittest tests.test_comparison_manager
```

## 📁 Estructura del Proyecto

```
TPI-ProteinAPI/
├── src/
│   ├── presentation/
│   │   ├── app.py              # Aplicación Flask principal
│   │   ├── routes.py           # Rutas y controladores
│   │   ├── forms.py            # Formularios WTF
│   │   └── templates/          # Plantillas HTML
│   ├── business/
│   │   ├── sequence_service.py # Lógica de validación
│   │   └── comparison_manager.py # Gestión de comparaciones
│   └── data/
│       ├── models.py           # Modelos SQLAlchemy
│       └── repositories.py     # Repositorios de datos
├── tests/
│   ├── test_sequence_business_rules.py
│   ├── test_comparison_manager.py
│   └── run_tests.py
├── config/
│   └── config.py               # Configuración de la app
├── docs/
│   └── MODELO_DOMINIO.md       # Documentación detallada
├── .env                        # Variables de entorno
└── requirements.txt            # Dependencias Python
```

## 🔮 Funcionalidades Futuras

- Integración con AlphaFold API para predicciones 3D
- Visualización 3D de estructuras proteicas
- Análisis de confianza pLDDT
- Exportación de resultados
- API REST completa

## 🐛 Resolución de Problemas

### Error de conexión a MySQL

- Verificar que MySQL esté ejecutándose
- Comprobar credenciales en `.env`
- Crear la base de datos manualmente

### Error de importación

- Verificar que el entorno virtual esté activado
- Reinstalar dependencias: `pip install -r requirements.txt`

### Tests fallan

- Verificar que no haya errores de sintaxis
- Comprobar que todas las dependencias estén instaladas

## 📝 Documentación Adicional

- [Modelo del Dominio](docs/MODELO_DOMINIO.md) - Documentación detallada de la arquitectura
- [Reglas de Negocio](docs/MODELO_DOMINIO.md#3-reglas-de-negocio) - Especificación completa

## 👨‍💻 Desarrollo

### Agregar nuevas validaciones

1. Editar `src/business/sequence_service.py`
2. Agregar tests en `tests/test_sequence_business_rules.py`
3. Ejecutar tests para verificar

### Agregar nuevas rutas

1. Editar `src/presentation/routes.py`
2. Crear templates en `src/presentation/templates/`
3. Actualizar formularios si es necesario

---

**Desarrollado como proyecto académico de Programación en Python con Arquitectura en Capas**  
_Fecha: Junio 2025_
