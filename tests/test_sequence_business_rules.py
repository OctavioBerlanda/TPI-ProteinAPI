import unittest
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.business.sequence_service import SequenceValidator, SequenceComparisonService, SequenceValidationError

class TestSequenceValidator(unittest.TestCase):
    """Tests para las reglas de negocio de validación de secuencias"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.validator = SequenceValidator()
    
    def test_clean_sequence_valid(self):
        """Test: Limpieza de secuencia válida"""
        # Arrange
        sequence_with_spaces = "A R N D C Q"
        sequence_with_newlines = "ARND\nCQ"
        sequence_lowercase = "arndcq"
        
        # Act
        cleaned_spaces = SequenceValidator.clean_sequence(sequence_with_spaces)
        cleaned_newlines = SequenceValidator.clean_sequence(sequence_with_newlines)
        cleaned_lowercase = SequenceValidator.clean_sequence(sequence_lowercase)
        
        # Assert
        self.assertEqual(cleaned_spaces, "ARNDCQ")
        self.assertEqual(cleaned_newlines, "ARNDCQ")
        self.assertEqual(cleaned_lowercase, "ARNDCQ")
    
    def test_clean_sequence_empty(self):
        """Test: Secuencia vacía debe lanzar excepción"""
        # Arrange & Act & Assert
        with self.assertRaises(SequenceValidationError):
            SequenceValidator.clean_sequence("")
        
        with self.assertRaises(SequenceValidationError):
            SequenceValidator.clean_sequence("   ")
    
    def test_validate_amino_acids_valid(self):
        """Test: Validación de aminoácidos válidos"""
        # Arrange
        valid_sequence = "ARNDCQEGHILKMFPSTWYV"
        
        # Act
        is_valid, invalid_chars = SequenceValidator.validate_amino_acids(valid_sequence)
        
        # Assert
        self.assertTrue(is_valid)
        self.assertEqual(len(invalid_chars), 0)
    
    def test_validate_amino_acids_invalid(self):
        """Test: Validación de aminoácidos inválidos"""
        # Arrange
        invalid_sequence = "ARNDXCQZGH"  # X y Z son inválidos
        
        # Act
        is_valid, invalid_chars = SequenceValidator.validate_amino_acids(invalid_sequence)
        
        # Assert
        self.assertFalse(is_valid)
        self.assertIn('X', invalid_chars)
        self.assertIn('Z', invalid_chars)
        self.assertEqual(len(invalid_chars), 2)
    
    def test_validate_sequence_length_equal(self):
        """Test: Secuencias de igual longitud"""
        # Arrange
        sequence1 = "ARNDCQ"
        sequence2 = "GHILKM"
        
        # Act
        result = SequenceValidator.validate_sequence_length(sequence1, sequence2)
        
        # Assert
        self.assertTrue(result)
    
    def test_validate_sequence_length_different(self):
        """Test: Secuencias de diferente longitud"""
        # Arrange
        sequence1 = "ARNDCQ"
        sequence2 = "GHILKMF"
        
        # Act
        result = SequenceValidator.validate_sequence_length(sequence1, sequence2)
        
        # Assert
        self.assertFalse(result)
    
    def test_find_differences_no_mutations(self):
        """Test: Secuencias idénticas (sin mutaciones)"""
        # Arrange
        original = "ARNDCQ"
        mutated = "ARNDCQ"
        
        # Act
        differences = SequenceValidator.find_differences(original, mutated)
        
        # Assert
        self.assertEqual(len(differences), 0)
    
    def test_find_differences_one_mutation(self):
        """Test: Una mutación"""
        # Arrange
        original = "ARNDCQ"
        mutated = "ARNGCQ"  # D -> G en posición 4
        
        # Act
        differences = SequenceValidator.find_differences(original, mutated)
        
        # Assert
        self.assertEqual(len(differences), 1)
        self.assertEqual(differences[0], (4, 'D', 'G'))
    
    def test_find_differences_two_mutations(self):
        """Test: Dos mutaciones"""
        # Arrange
        original = "ARNDCQ"
        mutated = "GRNGCQ"  # A -> G en pos 1, D -> G en pos 4
        
        # Act
        differences = SequenceValidator.find_differences(original, mutated)
        
        # Assert
        self.assertEqual(len(differences), 2)
        self.assertEqual(differences[0], (1, 'A', 'G'))
        self.assertEqual(differences[1], (4, 'D', 'G'))
    
    def test_validate_mutation_count_valid(self):
        """Test: Número válido de mutaciones (1-2)"""
        # Arrange
        one_mutation = [(1, 'A', 'G')]
        two_mutations = [(1, 'A', 'G'), (4, 'D', 'H')]
        
        # Act
        result_one = SequenceValidator.validate_mutation_count(one_mutation, 2)
        result_two = SequenceValidator.validate_mutation_count(two_mutations, 2)
        
        # Assert
        self.assertTrue(result_one)
        self.assertTrue(result_two)
    
    def test_validate_mutation_count_invalid(self):
        """Test: Número inválido de mutaciones (más de 2)"""
        # Arrange
        three_mutations = [(1, 'A', 'G'), (4, 'D', 'H'), (6, 'Q', 'K')]
        
        # Act
        result = SequenceValidator.validate_mutation_count(three_mutations, 2)
        
        # Assert
        self.assertFalse(result)
    
    def test_format_mutations_description(self):
        """Test: Formateo de descripción de mutaciones"""
        # Arrange
        differences = [(1, 'A', 'G'), (4, 'D', 'H')]
        
        # Act
        description = SequenceValidator.format_mutations_description(differences)
        
        # Assert
        self.assertEqual(description, "A1G, D4H")
    
    def test_get_mutation_summary(self):
        """Test: Resumen completo de mutaciones"""
        # Arrange
        differences = [(1, 'A', 'G'), (4, 'D', 'H')]
        
        # Act
        summary = SequenceValidator.get_mutation_summary(differences)
        
        # Assert
        self.assertEqual(summary['total_mutations'], 2)
        self.assertEqual(summary['positions'], [1, 4])
        self.assertEqual(summary['description'], "A1G, D4H")
        self.assertEqual(len(summary['mutations']), 2)
        
        # Verificar primer mutación
        mutation1 = summary['mutations'][0]
        self.assertEqual(mutation1['position'], 1)
        self.assertEqual(mutation1['original_amino_acid'], 'A')
        self.assertEqual(mutation1['mutated_amino_acid'], 'G')
        self.assertEqual(mutation1['mutation_notation'], 'A1G')

class TestSequenceComparisonService(unittest.TestCase):
    """Tests para el servicio de comparación de secuencias"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.service = SequenceComparisonService(max_mutations=2)
    
    def test_validate_and_compare_sequences_valid_one_mutation(self):
        """Test: Comparación válida con una mutación"""
        # Arrange
        original = "ARNDCQ"
        mutated = "GRNDCQ"  # A -> G en posición 1
        
        # Act
        result = self.service.validate_and_compare_sequences(original, mutated)
        
        # Assert
        self.assertTrue(result['valid'])
        self.assertEqual(result['sequence_length'], 6)
        self.assertEqual(result['mutations']['total_mutations'], 1)
        self.assertEqual(result['mutations']['description'], "A1G")
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_and_compare_sequences_valid_two_mutations(self):
        """Test: Comparación válida con dos mutaciones"""
        # Arrange
        original = "ARNDCQ"
        mutated = "GRNGCQ"  # A -> G en pos 1, D -> G en pos 4
        
        # Act
        result = self.service.validate_and_compare_sequences(original, mutated)
        
        # Assert
        self.assertTrue(result['valid'])
        self.assertEqual(result['mutations']['total_mutations'], 2)
        self.assertEqual(result['mutations']['description'], "A1G, D4G")
    
    def test_validate_and_compare_sequences_invalid_too_many_mutations(self):
        """Test: Demasiadas mutaciones (regla de negocio)"""
        # Arrange
        original = "ARNDCQ"
        mutated = "GRNGKQ"  # A -> G, D -> G, C -> K (3 mutaciones)
        
        # Act
        result = self.service.validate_and_compare_sequences(original, mutated)
        
        # Assert
        self.assertFalse(result['valid'])
        self.assertIn('Demasiadas mutaciones encontradas: 3', str(result['errors']))
    
    def test_validate_and_compare_sequences_invalid_different_lengths(self):
        """Test: Secuencias de diferente longitud (regla de negocio)"""
        # Arrange
        original = "ARNDCQ"
        mutated = "ARNDCQG"  # Una más larga
        
        # Act
        result = self.service.validate_and_compare_sequences(original, mutated)
        
        # Assert
        self.assertFalse(result['valid'])
        self.assertIn('diferentes longitudes', str(result['errors']))
    
    def test_validate_and_compare_sequences_invalid_characters(self):
        """Test: Caracteres inválidos (regla de negocio)"""
        # Arrange
        original = "ARNDCQ"
        mutated = "XRNDCQ"  # X es inválido
        
        # Act
        result = self.service.validate_and_compare_sequences(original, mutated)
        
        # Assert
        self.assertFalse(result['valid'])
        self.assertIn('caracteres inválidos', str(result['errors']))
    
    def test_validate_and_compare_sequences_no_differences(self):
        """Test: Secuencias idénticas (regla de negocio)"""
        # Arrange
        original = "ARNDCQ"
        mutated = "ARNDCQ"
        
        # Act
        result = self.service.validate_and_compare_sequences(original, mutated)
        
        # Assert
        self.assertFalse(result['valid'])
        self.assertIn('No se encontraron diferencias', str(result['errors']))
    
    def test_validate_and_compare_sequences_empty_sequences(self):
        """Test: Secuencias vacías"""
        # Arrange
        original = ""
        mutated = ""
        
        # Act
        result = self.service.validate_and_compare_sequences(original, mutated)
        
        # Assert
        self.assertFalse(result['valid'])
        self.assertIn('no puede estar vacía', str(result['errors']))
    
    def test_validate_and_compare_sequences_whitespace_handling(self):
        """Test: Manejo correcto de espacios en blanco"""
        # Arrange
        original = "A R N D C Q"
        mutated = "G R N D C Q"  # A -> G con espacios
        
        # Act
        result = self.service.validate_and_compare_sequences(original, mutated)
        
        # Assert
        self.assertTrue(result['valid'])
        self.assertEqual(result['original_sequence'], "ARNDCQ")
        self.assertEqual(result['mutated_sequence'], "GRNDCQ")
        self.assertEqual(result['mutations']['description'], "A1G")

if __name__ == '__main__':
    # Configurar y ejecutar los tests
    unittest.main(verbosity=2)
