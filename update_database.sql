-- Script para agregar columnas faltantes a tablas existentes
-- Ejecutar SOLO si ya tienes datos que quieres conservar

USE protein_comparison_db;

-- Agregar columnas faltantes a protein_comparisons si no existen
ALTER TABLE protein_comparisons 
ADD COLUMN IF NOT EXISTS swissmodel_job_id VARCHAR(100) AFTER mutated_confidence_score,
ADD COLUMN IF NOT EXISTS processing_time FLOAT AFTER swissmodel_job_id,
ADD COLUMN IF NOT EXISTS structural_changes TEXT AFTER processing_time,
ADD COLUMN IF NOT EXISTS rmsd_value FLOAT AFTER structural_changes,
ADD COLUMN IF NOT EXISTS stability_change_score FLOAT AFTER rmsd_value,
ADD COLUMN IF NOT EXISTS functional_impact_score FLOAT AFTER stability_change_score,
ADD COLUMN IF NOT EXISTS dynamics_change_score FLOAT AFTER functional_impact_score,
ADD COLUMN IF NOT EXISTS thermal_stability_change FLOAT AFTER dynamics_change_score,
ADD COLUMN IF NOT EXISTS folding_energy_change FLOAT AFTER thermal_stability_change,
ADD COLUMN IF NOT EXISTS active_site_disruption BOOLEAN AFTER folding_energy_change;

-- Verificar estructura actualizada
DESCRIBE protein_comparisons;
