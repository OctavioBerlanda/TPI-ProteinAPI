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
    
    # Links de predicciones AlphaFold
    original_prediction_url = db.Column(db.String(500))
    mutated_prediction_url = db.Column(db.String(500))
    original_model_path = db.Column(db.String(500))  # Ruta local del archivo PDB/CIF
    mutated_model_path = db.Column(db.String(500))   # Ruta local del archivo PDB/CIF
    
    # Resultados de AlphaFold
    original_confidence_score = db.Column(db.Float)  # Puntuación de confianza promedio
    mutated_confidence_score = db.Column(db.Float)   # Puntuación de confianza promedio
    alphafold_job_id = db.Column(db.String(100))     # ID del trabajo en AlphaFold
    processing_time = db.Column(db.Float)            # Tiempo de procesamiento en segundos
    
    # Análisis estructural
    structural_changes = db.Column(db.Text)          # JSON con cambios estructurales detectados
    rmsd_value = db.Column(db.Float)                 # Root Mean Square Deviation entre estructuras
    
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
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
