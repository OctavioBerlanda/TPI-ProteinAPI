import re
from typing import List, Tuple, Dict, Any

class SequenceValidationError(Exception):
    """Excepción personalizada para errores de validación de secuencias"""
    pass

class SequenceValidator:
    """Clase para validar secuencias de proteínas"""
    
    # Los 20 aminoácidos estándar
    VALID_AMINO_ACIDS = {
        'A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I',
        'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y', 'V'
    }
    
    # Nombres completos de aminoácidos para mensajes más descriptivos
    AMINO_ACID_NAMES = {
        'A': 'Alanina', 'R': 'Arginina', 'N': 'Asparagina', 'D': 'Ácido aspártico',
        'C': 'Cisteína', 'Q': 'Glutamina', 'E': 'Ácido glutámico', 'G': 'Glicina',
        'H': 'Histidina', 'I': 'Isoleucina', 'L': 'Leucina', 'K': 'Lisina',
        'M': 'Metionina', 'F': 'Fenilalanina', 'P': 'Prolina', 'S': 'Serina',
        'T': 'Treonina', 'W': 'Triptófano', 'Y': 'Tirosina', 'V': 'Valina'
    }
    
    @classmethod
    def clean_sequence(cls, sequence: str) -> str:
        """Limpia la secuencia removiendo espacios y convirtiendo a mayúsculas"""
        if not sequence:
            raise SequenceValidationError("La secuencia no puede estar vacía")
        
        # Remover espacios, saltos de línea y convertir a mayúsculas
        cleaned = re.sub(r'\s+', '', sequence.upper())
        
        # Validar que después de limpiar no quede vacía
        if not cleaned:
            raise SequenceValidationError("La secuencia no puede estar vacía")
        
        return cleaned
    
    @classmethod
    def validate_amino_acids(cls, sequence: str) -> Tuple[bool, List[str]]:
        """
        Valida que la secuencia contenga solo aminoácidos válidos
        
        Returns:
            Tuple[bool, List[str]]: (es_válida, lista_de_caracteres_inválidos)
        """
        invalid_chars = []
        for char in sequence:
            if char not in cls.VALID_AMINO_ACIDS:
                if char not in invalid_chars:
                    invalid_chars.append(char)
        
        return len(invalid_chars) == 0, invalid_chars
    
    @classmethod
    def validate_sequence_length(cls, original: str, mutated: str) -> bool:
        """Valida que ambas secuencias tengan la misma longitud"""
        return len(original) == len(mutated)
    
    @classmethod
    def find_differences(cls, original: str, mutated: str) -> List[Tuple[int, str, str]]:
        """
        Encuentra las diferencias entre dos secuencias
        
        Returns:
            List[Tuple[int, str, str]]: Lista de (posición, amino_original, amino_mutado)
        """
        differences = []
        for i, (orig_aa, mut_aa) in enumerate(zip(original, mutated)):
            if orig_aa != mut_aa:
                differences.append((i + 1, orig_aa, mut_aa))  # Posición 1-indexed
        
        return differences
    
    @classmethod
    def validate_mutation_count(cls, differences: List[Tuple[int, str, str]], 
                              max_mutations: int = 2) -> bool:
        """Valida que el número de mutaciones no exceda el máximo permitido"""
        return len(differences) <= max_mutations
    
    @classmethod
    def format_mutations_description(cls, differences: List[Tuple[int, str, str]]) -> str:
        """
        Formatea las mutaciones en una descripción legible
        
        Args:
            differences: Lista de (posición, amino_original, amino_mutado)
            
        Returns:
            str: Descripción formateada (ej: "A12G, T45C")
        """
        mutations = []
        for pos, orig, mut in differences:
            mutations.append(f"{orig}{pos}{mut}")
        
        return ", ".join(mutations)
    
    @classmethod
    def get_mutation_summary(cls, differences: List[Tuple[int, str, str]]) -> Dict[str, Any]:
        """
        Genera un resumen detallado de las mutaciones
        
        Returns:
            Dict con información detallada de las mutaciones
        """
        summary = {
            'total_mutations': len(differences),
            'positions': [pos for pos, _, _ in differences],
            'mutations': [],
            'description': cls.format_mutations_description(differences)
        }
        
        for pos, orig, mut in differences:
            mutation_info = {
                'position': pos,
                'original_amino_acid': orig,
                'mutated_amino_acid': mut,
                'original_name': cls.AMINO_ACID_NAMES.get(orig, orig),
                'mutated_name': cls.AMINO_ACID_NAMES.get(mut, mut),
                'mutation_notation': f"{orig}{pos}{mut}"
            }
            summary['mutations'].append(mutation_info)
        
        return summary

class SequenceComparisonService:
    """Servicio principal para comparar secuencias de proteínas"""
    
    def __init__(self, max_mutations: int = 2):
        self.max_mutations = max_mutations
    
    def validate_and_compare_sequences(self, original_sequence: str, 
                                     mutated_sequence: str) -> Dict[str, Any]:
        """
        Valida y compara dos secuencias de proteínas
        
        Args:
            original_sequence: Secuencia original de la proteína
            mutated_sequence: Secuencia mutada de la proteína
            
        Returns:
            Dict con el resultado de la validación y comparación
            
        Raises:
            SequenceValidationError: Si las secuencias no son válidas
        """
        result = {
            'valid': False,
            'original_sequence': '',
            'mutated_sequence': '',
            'sequence_length': 0,
            'mutations': {},
            'errors': []
        }
        
        try:
            # Limpiar secuencias
            clean_original = SequenceValidator.clean_sequence(original_sequence)
            clean_mutated = SequenceValidator.clean_sequence(mutated_sequence)
            
            result['original_sequence'] = clean_original
            result['mutated_sequence'] = clean_mutated
            
            # Validar caracteres válidos en secuencia original
            valid_orig, invalid_orig = SequenceValidator.validate_amino_acids(clean_original)
            if not valid_orig:
                result['errors'].append(
                    f"La secuencia original contiene caracteres inválidos: {', '.join(invalid_orig)}"
                )
            
            # Validar caracteres válidos en secuencia mutada
            valid_mut, invalid_mut = SequenceValidator.validate_amino_acids(clean_mutated)
            if not valid_mut:
                result['errors'].append(
                    f"La secuencia mutada contiene caracteres inválidos: {', '.join(invalid_mut)}"
                )
            
            # Si hay caracteres inválidos, no continuar
            if not (valid_orig and valid_mut):
                return result
            
            # Validar longitud
            if not SequenceValidator.validate_sequence_length(clean_original, clean_mutated):
                result['errors'].append(
                    f"Las secuencias tienen diferentes longitudes: original={len(clean_original)}, "
                    f"mutada={len(clean_mutated)}"
                )
                return result
            
            result['sequence_length'] = len(clean_original)
            
            # Encontrar diferencias
            differences = SequenceValidator.find_differences(clean_original, clean_mutated)
            
            # Validar número de mutaciones
            if not SequenceValidator.validate_mutation_count(differences, self.max_mutations):
                result['errors'].append(
                    f"Demasiadas mutaciones encontradas: {len(differences)}. "
                    f"Máximo permitido: {self.max_mutations}"
                )
                return result
            
            # Si no hay mutaciones
            if len(differences) == 0:
                result['errors'].append("No se encontraron diferencias entre las secuencias")
                return result
            
            # Generar resumen de mutaciones
            result['mutations'] = SequenceValidator.get_mutation_summary(differences)
            result['valid'] = True
            
        except SequenceValidationError as e:
            result['errors'].append(str(e))
        except Exception as e:
            result['errors'].append(f"Error inesperado durante la validación: {str(e)}")
        
        return result
