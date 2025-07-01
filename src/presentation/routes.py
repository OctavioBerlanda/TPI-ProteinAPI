from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .forms import SequenceComparisonForm, UserSearchForm
from src.business.comparison_manager import ComparisonManager

# Crear blueprint para las rutas principales
main_bp = Blueprint('main', __name__)
comparison_manager = ComparisonManager()

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Página principal con formulario de comparación"""
    form = SequenceComparisonForm()
    
    if form.validate_on_submit():
        # Procesar la comparación
        result = comparison_manager.create_comparison(
            username=form.username.data,
            email=form.email.data,
            original_sequence=form.original_sequence.data,
            mutated_sequence=form.mutated_sequence.data,
            comparison_name=form.comparison_name.data,
            description=form.description.data
        )
        
        if result['success']:
            flash('¡Comparación creada exitosamente!', 'success')
            return redirect(url_for('main.comparison_result', comparison_id=result['comparison_id']))
        else:
            # Mostrar errores de validación
            for error in result['errors']:
                flash(error, 'error')
    
    return render_template('index.html', form=form)

@main_bp.route('/comparison/<int:comparison_id>')
def comparison_result(comparison_id):
    """Página que muestra los resultados de una comparación"""
    details = comparison_manager.get_comparison_details(comparison_id)
    
    if not details:
        flash('Comparación no encontrada', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('comparison_result.html', details=details)

@main_bp.route('/user_comparisons', methods=['GET', 'POST'])
def user_comparisons():
    """Página para buscar comparaciones de un usuario"""
    form = UserSearchForm()
    comparisons_data = None
    
    if form.validate_on_submit():
        comparisons_data = comparison_manager.get_user_comparisons(form.username.data)
        
        if not comparisons_data['success']:
            flash(comparisons_data['message'], 'error')
    
    return render_template('user_comparisons.html', form=form, data=comparisons_data)

@main_bp.route('/api/comparison/<int:comparison_id>')
def api_comparison_details(comparison_id):
    """API endpoint para obtener detalles de una comparación en JSON"""
    details = comparison_manager.get_comparison_details(comparison_id)
    
    if not details:
        return jsonify({'error': 'Comparación no encontrada'}), 404
    
    return jsonify(details)

@main_bp.route('/api/user/<username>/comparisons')
def api_user_comparisons(username):
    """API endpoint para obtener comparaciones de un usuario en JSON"""
    comparisons_data = comparison_manager.get_user_comparisons(username)
    return jsonify(comparisons_data)

# Manejo de errores
@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500
