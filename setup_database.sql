-- Script para crear/recrear la base de datos y tablas
-- Ejecutar en MySQL como usuario root

-- Eliminar base de datos existente (CUIDADO: esto borra todos los datos)
DROP DATABASE IF EXISTS protein_comparison_db;

-- Crear base de datos
CREATE DATABASE protein_comparison_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Usar la base de datos
USE protein_comparison_db;

-- Tabla de usuarios
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de comparaciones de proteínas
CREATE TABLE protein_comparisons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    
    -- Secuencias
    original_sequence TEXT NOT NULL,
    mutated_sequence TEXT NOT NULL,
    sequence_length INT NOT NULL,
    
    -- Información de mutaciones
    mutation_count INT NOT NULL,
    mutation_positions VARCHAR(255) NOT NULL,
    mutations_description TEXT,
    
    -- Links de predicciones SwissModel
    original_prediction_url VARCHAR(500),
    mutated_prediction_url VARCHAR(500),
    original_model_path VARCHAR(500),
    mutated_model_path VARCHAR(500),
    
    -- Resultados de SwissModel
    original_confidence_score FLOAT,
    mutated_confidence_score FLOAT,
    swissmodel_job_id VARCHAR(100),
    processing_time FLOAT,
    
    -- Análisis estructural avanzado
    structural_changes TEXT,
    rmsd_value FLOAT,
    
    -- Análisis avanzados de mutaciones
    stability_change_score FLOAT,
    functional_impact_score FLOAT,
    dynamics_change_score FLOAT,
    thermal_stability_change FLOAT,
    folding_energy_change FLOAT,
    active_site_disruption BOOLEAN,
    
    -- Metadatos
    comparison_name VARCHAR(200),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertar usuario por defecto para pruebas
INSERT INTO users (username, email) 
VALUES ('admin', 'admin@protein.local')
ON DUPLICATE KEY UPDATE username=username;

-- Mostrar tablas creadas
SHOW TABLES;

-- Verificar estructura de la tabla protein_comparisons
DESCRIBE protein_comparisons;
