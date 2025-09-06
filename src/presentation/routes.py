from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file, make_response
from .forms import SequenceComparisonForm, UserSearchForm
from src.business.comparison_manager import ComparisonManager
from config.config import get_config_dict

# Crear blueprint para las rutas principales
main_bp = Blueprint('main', __name__)
config = get_config_dict()
comparison_manager = ComparisonManager(config)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Página principal con formulario de comparación"""
    form = SequenceComparisonForm()
    
    if form.validate_on_submit():
        # Verificar si se debe usar AlphaFold
        enable_alphafold = form.alpha_fold.data
        
        if enable_alphafold:
            # Usar el método con AlphaFold
            result = comparison_manager.create_comparison_with_alphafold(
                username=form.username.data,
                email=form.email.data,
                original_sequence=form.original_sequence.data,
                mutated_sequence=form.mutated_sequence.data,
                comparison_name=form.comparison_name.data,
                description=form.description.data,
                enable_alphafold=True
            )
        else:
            # Usar el método tradicional
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

@main_bp.route('/comparison/<int:comparison_id>/alphafold')
def alphafold_results(comparison_id):
    """Página que muestra los resultados detallados de AlphaFold"""
    details = comparison_manager.get_comparison_details(comparison_id)
    
    if not details:
        flash('Comparación no encontrada', 'error')
        return redirect(url_for('main.index'))
    
    # Verificar que la comparación tiene datos de AlphaFold
    comparison_data = details.get('comparison', {})
    if not comparison_data.get('original_model_path') and not comparison_data.get('original_prediction_url'):
        flash('Esta comparación no incluye predicciones de AlphaFold', 'warning')
        return redirect(url_for('main.comparison_result', comparison_id=comparison_id))
    
    return render_template('alphafold_results.html', 
                         comparison=details,
                         comparison_id=comparison_id)

@main_bp.route('/api/comparison/<int:comparison_id>/model/<model_type>')
def get_model_file(comparison_id, model_type):
    """API endpoint para servir archivos de modelos 3D"""
    import os
    from flask import send_file, abort
    
    details = comparison_manager.get_comparison_details(comparison_id)
    if not details:
        abort(404)
    
    comparison_data = details.get('comparison', {})
    model_path = None
    if model_type == 'original':
        model_path = comparison_data.get('original_model_path')
    elif model_type == 'mutated':
        model_path = comparison_data.get('mutated_model_path')
    
    if not model_path:
        abort(404)
    
    # Resolver ruta absoluta si la ruta es relativa
    if not os.path.isabs(model_path):
        # La ruta es relativa al directorio raíz del proyecto
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        model_path = os.path.join(project_root, model_path)
    
    if not os.path.exists(model_path):
        abort(404)
    
    return send_file(model_path, as_attachment=True)

@main_bp.route('/api/comparison/<int:comparison_id>/model/<model_type>/view.cif', methods=['GET', 'OPTIONS'])
def get_model_file_for_viewer(comparison_id, model_type):
    """API endpoint para servir archivos de modelos 3D para visualización (con CORS)"""
    import os
    from flask import request, abort
    
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    details = comparison_manager.get_comparison_details(comparison_id)
    if not details:
        abort(404)
    
    comparison_data = details.get('comparison', {})
    model_path = None
    if model_type == 'original':
        model_path = comparison_data.get('original_model_path')
    elif model_type == 'mutated':
        model_path = comparison_data.get('mutated_model_path')
    
    if not model_path:
        abort(404)
    
    # --- USAMOS TU LÓGICA DE RUTAS QUE YA FUNCIONA ---
    if not os.path.isabs(model_path):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        model_path = os.path.join(project_root, model_path)
    # --- FIN DE TU LÓGICA ---
    
    if not os.path.exists(model_path):
        print(f"❌ Archivo no encontrado: {model_path}", flush=True)
        abort(404)
    
    print(f"✅ Sirviendo archivo para visualización (con CORS): {model_path}", flush=True)

    # --- LA SOLUCIÓN DE CORS MEJORADA ---
    # 1. Creamos la respuesta a partir de send_file
    response = make_response(send_file(model_path, as_attachment=False, mimetype='chemical/x-cif'))
    
    # 2. Añadimos todos los encabezados CORS necesarios
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Length, Content-Type'
    # --- FIN DE LA SOLUCIÓN ---

    return response
@main_bp.route('/api/comparison/<int:comparison_id>/structural-analysis')
def get_structural_analysis(comparison_id):
    """API endpoint para obtener análisis estructural en formato JSON"""
    details = comparison_manager.get_comparison_details(comparison_id)
    
    if not details:
        return jsonify({'error': 'Comparación no encontrada'}), 404
    
    analysis = {
        'comparison_id': comparison_id,
        'sequence_analysis': {
            'original_sequence': details.get('original_sequence'),
            'mutated_sequence': details.get('mutated_sequence'),
            'mutations': details.get('mutations_description'),
            'mutation_count': details.get('mutation_count')
        },
        'structural_analysis': {
            'original_confidence': details.get('original_confidence_score'),
            'mutated_confidence': details.get('mutated_confidence_score'),
            'rmsd_value': details.get('rmsd_value'),
            'structural_changes': details.get('structural_changes'),
            'processing_time': details.get('processing_time')
        },
        'models': {
            'original_available': bool(details.get('original_model_path')),
            'mutated_available': bool(details.get('mutated_model_path')),
            'original_url': details.get('original_prediction_url'),
            'mutated_url': details.get('mutated_prediction_url')
        }
    }
    
    return jsonify(analysis)

@main_bp.route('/test/simple.cif')
def serve_simple_test_cif():
    """Endpoint para servir un archivo CIF de prueba súper simple"""
    import os
    from flask import send_file, abort
    
    test_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'test_simple.cif')
    
    if not os.path.exists(test_file):
        abort(404)
    
    print(f"✅ Sirviendo archivo CIF de prueba: {test_file}", flush=True)
    
    response = make_response(send_file(test_file, as_attachment=False, mimetype='chemical/x-cif'))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response

@main_bp.route('/test/simple.pdb')
def serve_simple_test_pdb():
    """Endpoint para servir un archivo PDB de prueba súper simple"""
    import os
    from flask import send_file, abort
    
    test_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'test_simple.pdb')
    
    if not os.path.exists(test_file):
        abort(404)
    
    print(f"✅ Sirviendo archivo PDB de prueba: {test_file}", flush=True)
    
    response = make_response(send_file(test_file, as_attachment=False, mimetype='chemical/x-pdb'))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response

@main_bp.route('/models/alphafold/<path:filename>')
def serve_alphafold_models(filename):
    """Endpoint para servir archivos de modelos AlphaFold directamente"""
    import os
    from flask import send_file, abort
    
    # Construir ruta al archivo
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(project_root, 'models', 'alphafold', filename)
    
    if not os.path.exists(file_path):
        abort(404)
    
    print(f"✅ Sirviendo archivo AlphaFold: {file_path}", flush=True)
    
    response = make_response(send_file(file_path, as_attachment=False, mimetype='chemical/x-cif'))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response

@main_bp.route('/api/comparison/<int:comparison_id>/model/<model_type>/view.pdb')
def get_model_file_as_pdb(comparison_id, model_type):
    """API endpoint para servir archivos de modelos convertidos a PDB para mejor compatibilidad con NGL"""
    import os
    from flask import request, abort
    
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    details = comparison_manager.get_comparison_details(comparison_id)
    if not details:
        abort(404)
    
    comparison_data = details.get('comparison', {})
    model_path = None
    if model_type == 'original':
        model_path = comparison_data.get('original_model_path')
    elif model_type == 'mutated':
        model_path = comparison_data.get('mutated_model_path')
    
    if not model_path:
        abort(404)
    
    # Resolver ruta absoluta
    if not os.path.isabs(model_path):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        model_path = os.path.join(project_root, model_path)
    
    if not os.path.exists(model_path):
        print(f"❌ Archivo no encontrado: {model_path}", flush=True)
        abort(404)
    
    print(f"🔄 Preparando archivo para visualización: {model_path}", flush=True)
    
    try:
        # Detectar el formato del archivo basado en la extensión
        file_extension = os.path.splitext(model_path)[1].lower()
        
        if file_extension == '.pdb':
            # Si ya es PDB, servirlo directamente
            print(f"✅ Archivo ya es PDB, sirviendo directamente", flush=True)
            
            response = make_response(send_file(model_path, as_attachment=False, mimetype='chemical/x-pdb'))
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
            
        elif file_extension == '.cif':
            # Si es CIF, convertir a PDB
            print(f"🔄 Convirtiendo CIF a PDB", flush=True)
            from Bio.PDB import MMCIFParser, PDBIO
            import tempfile
            
            # Parsear CIF
            parser = MMCIFParser(QUIET=True)
            structure = parser.get_structure('temp', model_path)
            
            # Crear archivo PDB temporal
            pdb_io = PDBIO()
            pdb_io.set_structure(structure)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pdb', delete=False) as temp_pdb:
                pdb_io.save(temp_pdb.name)
                
                print(f"✅ CIF convertido a PDB exitosamente", flush=True)
                
                response = make_response(send_file(temp_pdb.name, as_attachment=False, mimetype='chemical/x-pdb'))
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                
                # Limpiar archivo temporal después del envío
                @response.call_on_close
                def cleanup():
                    try:
                        os.unlink(temp_pdb.name)
                    except:
                        pass
                
                return response
        else:
            # Formato no soportado
            print(f"❌ Formato de archivo no soportado: {file_extension}", flush=True)
            abort(400)
            
    except Exception as e:
        print(f"❌ Error procesando archivo de modelo: {e}", flush=True)
        abort(500)

# Manejo de errores
@main_bp.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500
