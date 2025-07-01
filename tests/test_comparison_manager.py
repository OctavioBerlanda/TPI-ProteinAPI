import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.business.comparison_manager import ComparisonManager

class TestComparisonManager(unittest.TestCase):
    """Tests para el gestor de comparaciones - Reglas de negocio de nivel superior"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.manager = ComparisonManager()
    
    @patch('src.business.comparison_manager.UserRepository')
    @patch('src.business.comparison_manager.ProteinComparisonRepository')
    def test_create_comparison_valid_business_rules(self, mock_protein_repo, mock_user_repo):
        """Test: Creación exitosa de comparación siguiendo todas las reglas de negocio"""
        # Arrange
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user_repo.get_or_create_user.return_value = mock_user
        
        mock_comparison = MagicMock()
        mock_comparison.id = 100
        mock_protein_repo.create_comparison.return_value = mock_comparison
        
        username = "test_user"
        email = "test@example.com"
        original_sequence = "ARNDCQ"
        mutated_sequence = "GRNDCQ"  # Una mutación válida
        
        # Act
        result = self.manager.create_comparison(
            username, email, original_sequence, mutated_sequence
        )
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['comparison_id'], 100)
        self.assertIsNotNone(result['validation_result'])
        self.assertTrue(result['validation_result']['valid'])
        
        # Verificar que se llamaron los métodos correctos
        mock_user_repo.get_or_create_user.assert_called_once_with(username, email)
        mock_protein_repo.create_comparison.assert_called_once()
    
    @patch('src.business.comparison_manager.UserRepository')
    @patch('src.business.comparison_manager.ProteinComparisonRepository')
    def test_create_comparison_violates_mutation_limit_business_rule(self, mock_protein_repo, mock_user_repo):
        """Test: Violación de regla de negocio - máximo 2 mutaciones"""
        # Arrange
        username = "test_user"
        email = "test@example.com"
        original_sequence = "ARNDCQ"
        mutated_sequence = "GRNGKQ"  # 3 mutaciones: A->G, D->G, C->K
        
        # Act
        result = self.manager.create_comparison(
            username, email, original_sequence, mutated_sequence
        )
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('Demasiadas mutaciones encontradas: 3', str(result['errors']))
        self.assertEqual(result['message'], "Las secuencias no son válidas")
        
        # Verificar que NO se creó la comparación en la base de datos
        mock_protein_repo.create_comparison.assert_not_called()
    
    @patch('src.business.comparison_manager.UserRepository')
    @patch('src.business.comparison_manager.ProteinComparisonRepository')
    def test_create_comparison_violates_length_business_rule(self, mock_protein_repo, mock_user_repo):
        """Test: Violación de regla de negocio - secuencias deben tener igual longitud"""
        # Arrange
        username = "test_user"
        email = "test@example.com"
        original_sequence = "ARNDCQ"
        mutated_sequence = "ARNDCQG"  # Diferente longitud
        
        # Act
        result = self.manager.create_comparison(
            username, email, original_sequence, mutated_sequence
        )
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('diferentes longitudes', str(result['errors']))
        
        # Verificar que NO se creó la comparación
        mock_protein_repo.create_comparison.assert_not_called()
    
    @patch('src.business.comparison_manager.UserRepository')
    @patch('src.business.comparison_manager.ProteinComparisonRepository')
    def test_create_comparison_violates_amino_acid_business_rule(self, mock_protein_repo, mock_user_repo):
        """Test: Violación de regla de negocio - solo aminoácidos válidos"""
        # Arrange
        username = "test_user"
        email = "test@example.com"
        original_sequence = "ARNDCQ"
        mutated_sequence = "XRNDCQ"  # X no es un aminoácido válido
        
        # Act
        result = self.manager.create_comparison(
            username, email, original_sequence, mutated_sequence
        )
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('caracteres inválidos', str(result['errors']))
        
        # Verificar que NO se creó la comparación
        mock_protein_repo.create_comparison.assert_not_called()
    
    @patch('src.business.comparison_manager.UserRepository')
    @patch('src.business.comparison_manager.ProteinComparisonRepository')
    def test_create_comparison_violates_no_differences_business_rule(self, mock_protein_repo, mock_user_repo):
        """Test: Violación de regla de negocio - debe haber al menos 1 diferencia"""
        # Arrange
        username = "test_user"
        email = "test@example.com"
        original_sequence = "ARNDCQ"
        mutated_sequence = "ARNDCQ"  # Secuencias idénticas
        
        # Act
        result = self.manager.create_comparison(
            username, email, original_sequence, mutated_sequence
        )
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('No se encontraron diferencias', str(result['errors']))
        
        # Verificar que NO se creó la comparación
        mock_protein_repo.create_comparison.assert_not_called()
    
    @patch('src.business.comparison_manager.UserRepository')
    @patch('src.business.comparison_manager.ProteinComparisonRepository')
    def test_create_comparison_handles_database_error(self, mock_protein_repo, mock_user_repo):
        """Test: Manejo de errores de base de datos"""
        # Arrange
        mock_user_repo.get_or_create_user.side_effect = Exception("Database connection error")
        
        username = "test_user"
        email = "test@example.com"
        original_sequence = "ARNDCQ"
        mutated_sequence = "GRNDCQ"
        
        # Act
        result = self.manager.create_comparison(
            username, email, original_sequence, mutated_sequence
        )
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('Error al crear la comparación', str(result['errors']))
        self.assertEqual(result['message'], "Error interno del servidor")
    
    @patch('src.business.comparison_manager.ProteinComparisonRepository')
    def test_get_comparison_details_valid(self, mock_protein_repo):
        """Test: Obtener detalles de comparación existente"""
        # Arrange
        mock_comparison = MagicMock()
        mock_comparison.id = 1
        mock_comparison.original_sequence = "ARNDCQ"
        mock_comparison.mutated_sequence = "GRNDCQ"
        mock_comparison.to_dict.return_value = {'id': 1, 'status': 'completed'}
        
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "test_user"
        mock_user.email = "test@example.com"
        mock_comparison.user = mock_user
        
        mock_protein_repo.get_comparison_by_id.return_value = mock_comparison
        
        # Act
        result = self.manager.get_comparison_details(1)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn('comparison', result)
        self.assertIn('mutations_analysis', result)
        self.assertIn('user', result)
        self.assertEqual(result['user']['username'], "test_user")
    
    @patch('src.business.comparison_manager.ProteinComparisonRepository')
    def test_get_comparison_details_not_found(self, mock_protein_repo):
        """Test: Comparación no encontrada"""
        # Arrange
        mock_protein_repo.get_comparison_by_id.return_value = None
        
        # Act
        result = self.manager.get_comparison_details(999)
        
        # Assert
        self.assertIsNone(result)
    
    @patch('src.business.comparison_manager.UserRepository')
    @patch('src.business.comparison_manager.ProteinComparisonRepository')
    def test_get_user_comparisons_valid(self, mock_protein_repo, mock_user_repo):
        """Test: Obtener comparaciones de usuario existente"""
        # Arrange
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "test_user"
        mock_user.email = "test@example.com"
        mock_user_repo.get_user_by_username.return_value = mock_user
        
        mock_comparison = MagicMock()
        mock_comparison.to_dict.return_value = {'id': 1, 'status': 'completed'}
        mock_protein_repo.get_comparisons_by_user.return_value = [mock_comparison]
        
        # Act
        result = self.manager.get_user_comparisons("test_user")
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(len(result['comparisons']), 1)
        self.assertEqual(result['user']['username'], "test_user")
    
    @patch('src.business.comparison_manager.UserRepository')
    def test_get_user_comparisons_user_not_found(self, mock_user_repo):
        """Test: Usuario no encontrado"""
        # Arrange
        mock_user_repo.get_user_by_username.return_value = None
        
        # Act
        result = self.manager.get_user_comparisons("nonexistent_user")
        
        # Assert
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'Usuario no encontrado')
        self.assertEqual(len(result['comparisons']), 0)

class TestBusinessRulesIntegration(unittest.TestCase):
    """Tests de integración para verificar todas las reglas de negocio"""
    
    def setUp(self):
        """Configuración inicial"""
        self.manager = ComparisonManager()
    
    def test_complete_business_rules_validation_workflow(self):
        """Test: Flujo completo de validación de reglas de negocio"""
        test_cases = [
            {
                'name': 'Caso válido: 1 mutación',
                'original': 'ARNDCQ',
                'mutated': 'GRNDCQ',
                'should_pass': True,
                'expected_mutations': 1
            },
            {
                'name': 'Caso válido: 2 mutaciones',
                'original': 'ARNDCQ',
                'mutated': 'GRNGCQ',
                'should_pass': True,
                'expected_mutations': 2
            },
            {
                'name': 'Caso inválido: 3 mutaciones',
                'original': 'ARNDCQ',
                'mutated': 'GRNGKQ',
                'should_pass': False,
                'error_contains': 'Demasiadas mutaciones'
            },
            {
                'name': 'Caso inválido: longitudes diferentes',
                'original': 'ARNDCQ',
                'mutated': 'ARNDCQG',
                'should_pass': False,
                'error_contains': 'diferentes longitudes'
            },
            {
                'name': 'Caso inválido: aminoácido inválido',
                'original': 'ARNDCQ',
                'mutated': 'XRNDCQ',
                'should_pass': False,
                'error_contains': 'caracteres inválidos'
            },
            {
                'name': 'Caso inválido: sin diferencias',
                'original': 'ARNDCQ',
                'mutated': 'ARNDCQ',
                'should_pass': False,
                'error_contains': 'No se encontraron diferencias'
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case['name']):
                # Act
                validation_result = self.manager.sequence_service.validate_and_compare_sequences(
                    case['original'], case['mutated']
                )
                
                # Assert
                if case['should_pass']:
                    self.assertTrue(validation_result['valid'], 
                                  f"Se esperaba que {case['name']} fuera válido")
                    if 'expected_mutations' in case:
                        self.assertEqual(
                            validation_result['mutations']['total_mutations'],
                            case['expected_mutations'],
                            f"Número incorrecto de mutaciones en {case['name']}"
                        )
                else:
                    self.assertFalse(validation_result['valid'], 
                                   f"Se esperaba que {case['name']} fuera inválido")
                    if 'error_contains' in case:
                        error_text = ' '.join(validation_result['errors'])
                        self.assertIn(case['error_contains'], error_text,
                                    f"Error esperado no encontrado en {case['name']}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
