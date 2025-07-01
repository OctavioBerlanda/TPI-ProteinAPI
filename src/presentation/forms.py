from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, EmailField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional

class SequenceComparisonForm(FlaskForm):
    """Formulario para comparar secuencias de proteínas"""
    
    # Información del usuario
    username = StringField('Nombre de Usuario', 
                          validators=[DataRequired(message="El nombre de usuario es obligatorio"),
                                    Length(min=3, max=80, message="El nombre debe tener entre 3 y 80 caracteres")])
    
    email = EmailField('Email', 
                      validators=[DataRequired(message="El email es obligatorio"),
                                Email(message="Formato de email inválido")])
    
    # Información de la comparación
    comparison_name = StringField('Nombre de la Comparación', 
                                validators=[Optional(),
                                          Length(max=200, message="El nombre no puede exceder 200 caracteres")])
    
    description = TextAreaField('Descripción (Opcional)', 
                               validators=[Optional(),
                                         Length(max=1000, message="La descripción no puede exceder 1000 caracteres")])
    
    # Secuencias
    original_sequence = TextAreaField('Secuencia Original', 
                                    validators=[DataRequired(message="La secuencia original es obligatoria"),
                                              Length(min=1, max=10000, message="La secuencia debe tener entre 1 y 10000 caracteres")],
                                    render_kw={'rows': 6, 'placeholder': 'Ingrese la secuencia de aminoácidos original (ej: MRKLLSLVLC...)'})
    
    mutated_sequence = TextAreaField('Secuencia Mutada', 
                                   validators=[DataRequired(message="La secuencia mutada es obligatoria"),
                                             Length(min=1, max=10000, message="La secuencia debe tener entre 1 y 10000 caracteres")],
                                   render_kw={'rows': 6, 'placeholder': 'Ingrese la secuencia de aminoácidos mutada (máximo 2 diferencias)'})
    
    alpha_fold = BooleanField('Incluir Predicción de AlphaFold')
    
    submit = SubmitField('Comparar Secuencias')

class UserSearchForm(FlaskForm):
    """Formulario para buscar comparaciones de un usuario"""
    
    username = StringField('Nombre de Usuario', 
                          validators=[DataRequired(message="El nombre de usuario es obligatorio")])
    
    submit = SubmitField('Buscar Comparaciones')
