from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """Modelo para usuarios del sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con comparaciones
    comparisons = db.relationship('ProteinComparison', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class ProteinComparison(db.Model):
    """Modelo para almacenar comparaciones de proteínas"""
    __tablename__ = 'protein_comparisons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Secuencias
    original_sequence = db.Column(db.Text, nullable=False)
    mutated_sequence = db.Column(db.Text, nullable=False)
    sequence_length = db.Column(db.Integer, nullable=False)
    
    # Información de mutaciones
    mutation_count = db.Column(db.Integer, nullable=False)
    mutation_positions = db.Column(db.String(255), nullable=False)  # Formato: "12,45" para posiciones
    mutations_description = db.Column(db.Text)  # Formato: "A12G,T45C"
    
    # Links de predicciones SwissModel
    original_prediction_url = db.Column(db.String(500))
    mutated_prediction_url = db.Column(db.String(500))
    original_model_path = db.Column(db.String(500))  # Ruta local del archivo PDB/CIF
    mutated_model_path = db.Column(db.String(500))   # Ruta local del archivo PDB/CIF
    
    # Resultados de SwissModel
    original_confidence_score = db.Column(db.Float)  # Puntuación de confianza promedio
    mutated_confidence_score = db.Column(db.Float)   # Puntuación de confianza promedio
    original_confidence_source = db.Column(db.String(50))  # Fuente del score (GMQE, QMEAN, B-factor)
    mutated_confidence_source = db.Column(db.String(50))   # Fuente del score (GMQE, QMEAN, B-factor)
    swissmodel_job_id = db.Column(db.String(100))     # ID del trabajo en SwissModel
    processing_time = db.Column(db.Float)            # Tiempo de procesamiento en segundos
    
    # Análisis estructural
    structural_changes = db.Column(db.Text)          # JSON con cambios estructurales detectados
    rmsd_value = db.Column(db.Float)                 # Valor RMSD entre estructuras
    
    # Análisis de calidad local (GMQE por residuo)
    original_quality_analysis = db.Column(db.Text)   # JSON con análisis detallado de calidad original
    mutated_quality_analysis = db.Column(db.Text)    # JSON con análisis detallado de calidad mutada
    
    # Análisis avanzados de mutaciones
    stability_change_score = db.Column(db.Float)     # Cambio en estabilidad proteica
    functional_impact_score = db.Column(db.Float)    # Impacto funcional de las mutaciones
    dynamics_change_score = db.Column(db.Float)      # Cambio en dinámica molecular
    thermal_stability_change = db.Column(db.Float)   # Cambio en estabilidad térmica (°C)
    folding_energy_change = db.Column(db.Float)      # Cambio en energía de plegamiento (kcal/mol)
    active_site_disruption = db.Column(db.Boolean)   # Si se afecta sitio activo
    
    # Metadatos
    comparison_name = db.Column(db.String(200))
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProteinComparison {self.id}: {self.comparison_name}>'
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'original_sequence': self.original_sequence,
            'mutated_sequence': self.mutated_sequence,
            'sequence_length': self.sequence_length,
            'mutation_count': self.mutation_count,
            'mutation_positions': self.mutation_positions,
            'mutations_description': self.mutations_description,
            'comparison_name': self.comparison_name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Campos de SwissModel
            'original_prediction_url': self.original_prediction_url,
            'mutated_prediction_url': self.mutated_prediction_url,
            'original_model_path': self.original_model_path,
            'mutated_model_path': self.mutated_model_path,
            'original_confidence_score': self.original_confidence_score,
            'mutated_confidence_score': self.mutated_confidence_score,
            'original_confidence_source': self.original_confidence_source,
            'mutated_confidence_source': self.mutated_confidence_source,
            'swissmodel_job_id': self.swissmodel_job_id,
            'processing_time': self.processing_time,
            'structural_changes': self.structural_changes,
            'rmsd_value': self.rmsd_value,
            # Análisis de calidad local
            'original_quality_analysis': self.original_quality_analysis,
            'mutated_quality_analysis': self.mutated_quality_analysis,
            # Campos avanzados
            'stability_change_score': self.stability_change_score,
            'functional_impact_score': self.functional_impact_score,
            'dynamics_change_score': self.dynamics_change_score,
            'thermal_stability_change': self.thermal_stability_change,
            'folding_energy_change': self.folding_energy_change,
            'active_site_disruption': self.active_site_disruption
        }
