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

#### 6.2. Consultar Comparaciones de Usuario

1. **Actor**: Usuario/Investigador
2. **Flujo**:
   - Usuario ingresa nombre de usuario
   - Sistema busca usuario en BD
   - Sistema retorna lista de comparaciones históricas

#### 6.3. Ver Detalles de Comparación

1. **Actor**: Usuario/Investigador
2. **Flujo**:
   - Usuario selecciona comparación específica
   - Sistema recupera datos completos
   - Sistema muestra análisis detallado de mutaciones

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

---

### 9. EXTENSIBILIDAD FUTURA

El modelo está diseñado para futuras extensiones:

- **Integración AlphaFold**: Campos preparados para URLs de predicciones
- **Visualización 3D**: Estructura base para almacenar datos de estructuras
- **Análisis Avanzado**: Extensión para métricas de confianza (pLDDT)
- **API REST**: Endpoints ya implementados para integración externa

---

_Documentación generada para el proyecto de Comparador de Proteínas_  
_Fecha: 30 de Junio, 2025_
