# Documentación del Modelo del Dominio

## Comparador de Proteínas - Sistema de Análisis de Mutaciones

### 1. ARQUITECTURA DEL SISTEMA

El sistema implementa una **arquitectura en 3 capas**:

```
├── CAPA DE PRESENTACIÓN (src/presentation/)
│   ├── Interfaz web Flask
│   ├── Formularios de entrada
│   └── Visualización de resultados
│
├── CAPA DE NEGOCIO (src/business/)
│   ├── Reglas de validación de secuencias
│   ├── Lógica de comparación de proteínas
│   └── Gestión de comparaciones
│
└── CAPA DE DATOS (src/data/)
    ├── Modelos de base de datos
    ├── Repositorios
    └── Conexión a MySQL
```

---

### 2. MODELO DEL DOMINIO

#### 2.1. Entidades Principales

##### **Usuario (User)**

- **Propósito**: Representa a un investigador o usuario del sistema
- **Atributos**:
  - `id` (Integer): Identificador único
  - `username` (String): Nombre de usuario único
  - `email` (String): Correo electrónico único
  - `created_at` (DateTime): Fecha de registro

##### **Comparación de Proteínas (ProteinComparison)**

- **Propósito**: Representa una comparación entre dos secuencias de proteínas
- **Atributos**:
  - `id` (Integer): Identificador único
  - `user_id` (Integer): Referencia al usuario
  - `original_sequence` (Text): Secuencia original de aminoácidos
  - `mutated_sequence` (Text): Secuencia mutada de aminoácidos
  - `sequence_length` (Integer): Longitud de las secuencias
  - `mutation_count` (Integer): Número de mutaciones detectadas
  - `mutation_positions` (String): Posiciones de las mutaciones
  - `mutations_description` (Text): Descripción de las mutaciones (ej: "A12G, T45C")
  - `comparison_name` (String): Nombre descriptivo de la comparación
  - `description` (Text): Descripción opcional
  - `status` (String): Estado de la comparación (pending, completed, failed)
  - `created_at` (DateTime): Fecha de creación
  - `updated_at` (DateTime): Fecha de última modificación

#### 2.2. Relaciones del Modelo

```
User (1) -----> (N) ProteinComparison
```

- Un usuario puede tener múltiples comparaciones
- Cada comparación pertenece a un único usuario

---

### 3. REGLAS DE NEGOCIO

#### 3.1. Reglas de Validación de Secuencias

##### **RN-001: Validación de Aminoácidos**

- **Descripción**: Solo se permiten los 20 aminoácidos estándar
- **Aminoácidos válidos**: A, R, N, D, C, Q, E, G, H, I, L, K, M, F, P, S, T, W, Y, V
- **Implementación**: `SequenceValidator.validate_amino_acids()`
- **Test**: `test_validate_amino_acids_valid()`, `test_validate_amino_acids_invalid()`

##### **RN-002: Validación de Longitud**

- **Descripción**: Ambas secuencias deben tener exactamente la misma longitud
- **Justificación**: Las mutaciones puntuales no cambian la longitud total
- **Implementación**: `SequenceValidator.validate_sequence_length()`
- **Test**: `test_validate_sequence_length_equal()`, `test_validate_sequence_length_different()`

##### **RN-003: Límite de Mutaciones**

- **Descripción**: Se permiten máximo 2 mutaciones entre las secuencias
- **Justificación**: Mantener el foco en mutaciones puntuales específicas
- **Implementación**: `SequenceValidator.validate_mutation_count()`
- **Test**: `test_validate_mutation_count_valid()`, `test_validate_mutation_count_invalid()`

##### **RN-004: Diferencias Mínimas**

- **Descripción**: Debe existir al menos 1 diferencia entre las secuencias
- **Justificación**: No tiene sentido comparar secuencias idénticas
- **Implementación**: `SequenceValidator.find_differences()`
- **Test**: `test_find_differences_no_mutations()`

##### **RN-005: Limpieza de Secuencias**

- **Descripción**: Las secuencias se limpian automáticamente (espacios, mayúsculas)
- **Implementación**: `SequenceValidator.clean_sequence()`
- **Test**: `test_clean_sequence_valid()`, `test_whitespace_handling()`

#### 3.2. Reglas de Negocio de Gestión

##### **RN-006: Gestión de Usuarios**

- **Descripción**: Los usuarios se crean automáticamente si no existen
- **Implementación**: `UserRepository.get_or_create_user()`

##### **RN-007: Trazabilidad**

- **Descripción**: Todas las comparaciones quedan registradas con timestamp
- **Implementación**: Campos `created_at` y `updated_at` en `ProteinComparison`

---

### 4. SERVICIOS DEL DOMINIO

#### 4.1. SequenceValidator

- **Responsabilidad**: Validación de secuencias de aminoácidos
- **Métodos principales**:
  - `clean_sequence()`: Limpia y normaliza secuencias
  - `validate_amino_acids()`: Valida caracteres permitidos
  - `find_differences()`: Encuentra mutaciones entre secuencias
  - `format_mutations_description()`: Genera descripción de mutaciones

#### 4.2. SequenceComparisonService

- **Responsabilidad**: Orquestación de la comparación completa
- **Método principal**: `validate_and_compare_sequences()`
- **Flujo**:
  1. Limpia las secuencias
  2. Valida aminoácidos
  3. Valida longitudes
  4. Encuentra diferencias
  5. Valida número de mutaciones
  6. Genera resumen completo

#### 4.3. ComparisonManager

- **Responsabilidad**: Gestión de alto nivel de comparaciones
- **Métodos principales**:
  - `create_comparison()`: Crea nueva comparación en BD
  - `get_comparison_details()`: Recupera detalles de comparación
  - `get_user_comparisons()`: Lista comparaciones de usuario
  - `create_comparison_with_alphafold()`: Crea comparación con predicción 3D

#### 4.4. AlphaFoldService

- **Responsabilidad**: Integración con Swiss-Model y AlphaFold Database
- **Métodos principales**:
  - `predict_structure()`: Coordina predicción de estructura 3D
  - `_predict_with_swiss_model()`: Implementa flujo asíncrono Swiss-Model
  - `_download_swiss_model_file()`: Descarga modelos PDB/CIF
  - `compare_structures()`: Compara estructuras original vs mutada
  - `cleanup_old_models()`: Gestión de archivos de modelos
- **Características**:
  - Timeout dinámico basado en longitud de secuencia
  - Manejo de estados asíncronos (PENDING, RUNNING, COMPLETED)
  - Extracción de métricas de calidad (GMQE, QMEAN)
  - Integración con base de datos AlphaFold para información adicional

---

### 5. REPOSITORIOS

#### 5.1. UserRepository

- **Responsabilidad**: Operaciones de persistencia de usuarios
- **Métodos**:
  - `create_user()`, `get_user_by_id()`, `get_user_by_username()`
  - `get_or_create_user()`: Implementa la lógica de negocio RN-006

#### 5.2. ProteinComparisonRepository

- **Responsabilidad**: Operaciones de persistencia de comparaciones
- **Métodos**:
  - `create_comparison()`, `get_comparison_by_id()`
  - `get_comparisons_by_user()`, `update_comparison_status()`

---

### 6. CASOS DE USO

#### 6.1. Crear Nueva Comparación

1. **Actor**: Usuario/Investigador
2. **Flujo**:
   - Usuario ingresa datos personales y secuencias
   - Sistema valida reglas de negocio (RN-001 a RN-005)
   - Sistema crea/obtiene usuario (RN-006)
   - Sistema almacena comparación con trazabilidad (RN-007)
   - Sistema muestra resultados de mutaciones

#### 6.2. Crear Comparación con Predicción 3D

1. **Actor**: Usuario/Investigador
2. **Precondición**: Usuario marca checkbox "Incluir Predicción de AlphaFold"
3. **Flujo**:
   - Sistema ejecuta flujo de comparación estándar
   - Sistema inicia predicción Swiss-Model para secuencia original
   - Sistema inicia predicción Swiss-Model para secuencia mutada
   - Sistema aplica timeout dinámico según longitud (RN-009)
   - Sistema descarga modelos 3D y extrae métricas de calidad
   - Sistema almacena rutas de archivos y puntuaciones
   - Sistema muestra resultados con enlace a análisis estructural
4. **Postcondición**: Modelos 3D disponibles para descarga y visualización

#### 6.3. Consultar Comparaciones de Usuario

1. **Actor**: Usuario/Investigador
2. **Flujo**:
   - Usuario ingresa nombre de usuario
   - Sistema busca usuario en BD
   - Sistema retorna lista de comparaciones históricas

#### 6.4. Ver Detalles de Comparación

1. **Actor**: Usuario/Investigador
2. **Flujo**:
   - Usuario selecciona comparación específica
   - Sistema recupera datos completos
   - Sistema muestra análisis detallado de mutaciones

#### 6.5. Analizar Estructuras 3D

1. **Actor**: Usuario/Investigador
2. **Precondición**: Comparación con predicción 3D completada
3. **Flujo**:
   - Usuario hace clic en "Ver Análisis Estructural"
   - Sistema recupera modelos 3D y métricas de calidad
   - Sistema calcula RMSD entre estructuras
   - Sistema muestra impacto predicted de las mutaciones
   - Usuario puede descargar modelos PDB/CIF para análisis externo

---

### 7. VALIDACIÓN Y TESTING

#### 7.1. Tests de Reglas de Negocio

- **TestSequenceValidator**: Valida todas las reglas RN-001 a RN-005
- **TestSequenceComparisonService**: Valida orquestación de validaciones
- **TestComparisonManager**: Valida lógica de negocio de alto nivel
- **TestBusinessRulesIntegration**: Tests de integración end-to-end

#### 7.2. Cobertura de Tests

- ✅ Validación de aminoácidos válidos e inválidos
- ✅ Validación de longitudes iguales y diferentes
- ✅ Validación de límites de mutaciones (1-2)
- ✅ Validación de diferencias mínimas
- ✅ Manejo de errores y casos edge
- ✅ Limpieza y normalización de datos

---

### 8. TECNOLOGÍAS UTILIZADAS

- **Backend**: Python 3.11+, Flask
- **ORM**: SQLAlchemy
- **Base de Datos**: MySQL 8.0+
- **Frontend**: HTML5, Bootstrap 5, JavaScript (mínimo)
- **Testing**: unittest (Python estándar)
- **Validación**: WTForms, Flask-WTF
- **APIs Externas**:
  - **Swiss-Model API**: Predicción de estructuras 3D por homología
  - **AlphaFold Database**: Consulta de datos de proteínas conocidas
- **Formatos de Archivo**: PDB, CIF para modelos 3D
- **Bibliotecas Científicas**:
  - **BioPython**: Manejo de secuencias y estructuras
  - **Requests**: Comunicación HTTP con APIs
  - **NumPy**: Cálculos numéricos y análisis estructural

---

### 9. INTEGRACIÓN SWISS-MODEL Y ALPHAFOLD

#### 9.1. Swiss-Model para Predicción 3D

El sistema ahora incluye integración completa con **Swiss-Model** para predicción de estructuras 3D:

##### **Flujo de Predicción 3D**

1. **Envío del trabajo**: Secuencia enviada a Swiss-Model API
2. **Polling asíncrono**: Verificación periódica del estado (cada 10 segundos)
3. **Descarga del modelo**: Archivo PDB/CIF descargado automáticamente

##### **Timeout Dinámico por Longitud de Secuencia**

- **Secuencias ≤200 residuos**: Timeout de 5 minutos (30 intentos × 10s)
- **Secuencias >200 residuos**: Timeout de 10 minutos (60 intentos × 10s)
- **Estados válidos**: `PENDING`, `RUNNING`, `QUEUED`, `INITIALISED`, `COMPLETED`

##### **Métricas de Calidad**

- **GMQE Score**: Global Model Quality Estimation (0-1, preferido)
- **QMEAN Score**: Qualitative Model Energy Analysis (Z-score)
- **Confianza**: Calculada principalmente desde GMQE (× 100%)

#### 9.2. AlphaFold para Datos Informativos

**AlphaFold** se utiliza para obtener información de proteínas conocidas:

- **UniProt ID**: Identificador de la proteína
- **Nombre de proteína**: Descripción funcional
- **Organismo**: Especie de origen
- **Versión AlphaFold**: Versión de la base de datos

#### 9.3. Reglas de Negocio de Integración

##### **RN-008: Predicción 3D Opcional**

- **Descripción**: La predicción 3D es opcional via checkbox en el formulario
- **Implementación**: Campo `enable_alphafold` en comparaciones
- **Duración**: Variable según longitud de secuencia (5-10 minutos)

##### **RN-009: Gestión de Timeouts**

- **Descripción**: Timeout dinámico basado en complejidad de la secuencia
- **Criterio**: Secuencias >200 residuos reciben 10 minutos vs 5 minutos
- **Justificación**: Secuencias largas requieren más tiempo de modelado

##### **RN-010: Calidad de Modelos**

- **Descripción**: Solo se aceptan modelos con métricas de calidad válidas
- **GMQE mínimo**: >0.0 (preferido para confianza)
- **QMEAN válido**: Z-score dentro de rangos aceptables
- **Fallback**: Si GMQE no disponible, usar QMEAN normalizado

### 10. EXTENSIBILIDAD FUTURA

El modelo está diseñado para futuras extensiones:

- **✅ Integración Swiss-Model**: Completamente implementada
- **✅ Visualización 3D**: Archivos PDB/CIF descargables
- **✅ Análisis Estructural**: Métricas GMQE y QMEAN integradas
- **🔄 Visualizador 3D Web**: NGL Viewer o PyMol.js en desarrollo
- **🔄 Comparación Estructural**: Cálculo de RMSD entre modelos
- **🔄 Análisis de Dominios**: Identificación de regiones estructurales

---

_Documentación actualizada para el proyecto de Comparador de Proteínas_  
_Fecha: 14 de Septiembre, 2025_  
_Incluye integración Swiss-Model y mejoras de timeout dinámico_
