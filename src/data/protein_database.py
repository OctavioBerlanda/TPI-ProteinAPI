"""
Manejador de base de datos de proteínas conocidas
Carga y gestiona información de proteínas con estructuras en AlphaFold DB
"""
import json
import os
from typing import Dict, Optional, Tuple, List
from pathlib import Path

class ProteinDatabase:
    """Gestor de base de datos de proteínas conocidas"""
    
    def __init__(self, database_path: str = None):
        """
        Inicializa la base de datos de proteínas
        
        Args:
            database_path: Ruta opcional al archivo JSON de la base de datos
        """
        if database_path is None:
            # Usar ruta por defecto relativa al directorio del proyecto
            current_dir = Path(__file__).parent.parent.parent
            database_path = current_dir / "data" / "known_proteins" / "protein_database.json"
        
        self.database_path = Path(database_path)
        self.proteins = {}
        self._load_database()
    
    def _load_database(self):
        """Carga la base de datos desde el archivo JSON"""
        try:
            if self.database_path.exists():
                with open(self.database_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.proteins = data.get('proteins', {})
                print(f"✅ Base de datos de proteínas cargada: {len(self.proteins)} proteínas")
            else:
                print(f"⚠️ Archivo de base de datos no encontrado: {self.database_path}")
                print("📝 Usando base de datos en memoria reducida")
                self._load_fallback_database()
        except Exception as e:
            print(f"❌ Error cargando base de datos: {e}")
            print("📝 Usando base de datos en memoria reducida")
            self._load_fallback_database()
    
    def _load_fallback_database(self):
        """Carga una base de datos mínima en memoria como fallback"""
        self.proteins = {
            "P68871": {
                "name": "Hemoglobin subunit beta",
                "organism": "Homo sapiens",
                "function": "Oxygen transport",
                "sequence": "MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKVKAHGKKVLGAFSDGLAHLDNLKGTFATLSELHCDKLHVDPENFRLLGNVLVCVLAHHFGKEFTPPVQAAYQKVVAGVANALAHKYH",
                "length": 147,
                "confidence_score": 95
            },
            "P69905": {
                "name": "Hemoglobin subunit alpha", 
                "organism": "Homo sapiens",
                "function": "Oxygen transport",
                "sequence": "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHGSAQVKGHGKKVADALTNAVAHVDDMPNALSALSDLHAHKLRVDPVNFKLLSHCLLVTLAAHLPAEFTPAVHASLDKFLASVSTVLTSKYR",
                "length": 142,
                "confidence_score": 95
            },
            "P02100": {
                "name": "Hemoglobin subunit epsilon",
                "organism": "Homo sapiens",
                "function": "Embryonic oxygen transport", 
                "sequence": "MVHFTAEEKAAVTSLWSKMNVEEAGGEALGRLLVVYPWTQRFFDSFGNLSSPSAILGNPKVKAHGKKVLTSFGDAIKNMDNLKPAFAKLSELHCDKLHVDPENFKLLGNVMVIILATHFGKEFTPEVQAAWQKLVSAVAIALAHKYH",
                "length": 147,
                "confidence_score": 95
            }
        }
    
    def search_exact_match(self, sequence: str) -> Optional[Tuple[str, Dict]]:
        """
        Busca una coincidencia exacta de secuencia
        
        Args:
            sequence: Secuencia de aminoácidos a buscar
            
        Returns:
            Tupla (uniprot_id, protein_data) si se encuentra, None si no
        """
        for uniprot_id, protein_data in self.proteins.items():
            if protein_data['sequence'] == sequence:
                return uniprot_id, protein_data
        return None
    
    def search_similar_sequences(self, sequence: str, min_similarity: float = 0.95) -> List[Tuple[str, Dict, float]]:
        """
        Busca secuencias similares con similitud >= min_similarity
        
        Args:
            sequence: Secuencia de aminoácidos a buscar
            min_similarity: Similitud mínima requerida (0.0-1.0)
            
        Returns:
            Lista de tuplas (uniprot_id, protein_data, similarity) ordenadas por similitud
        """
        results = []
        
        for uniprot_id, protein_data in self.proteins.items():
            similarity = self._calculate_similarity(sequence, protein_data['sequence'])
            if similarity >= min_similarity:
                results.append((uniprot_id, protein_data, similarity))
        
        # Ordenar por similitud descendente
        results.sort(key=lambda x: x[2], reverse=True)
        return results
    
    def _calculate_similarity(self, seq1: str, seq2: str) -> float:
        """
        Calcula similitud entre dos secuencias
        
        Args:
            seq1: Primera secuencia
            seq2: Segunda secuencia
            
        Returns:
            Valor de similitud entre 0.0 y 1.0
        """
        if len(seq1) == 0 or len(seq2) == 0:
            return 0.0
        
        # Si las longitudes son muy diferentes, similitud baja
        if abs(len(seq1) - len(seq2)) / max(len(seq1), len(seq2)) > 0.1:
            return 0.0
        
        # Comparar posición por posición
        min_len = min(len(seq1), len(seq2))
        matches = sum(1 for i in range(min_len) if seq1[i] == seq2[i])
        
        return matches / min_len
    
    def get_protein_info(self, uniprot_id: str) -> Optional[Dict]:
        """
        Obtiene información de una proteína por UniProt ID
        
        Args:
            uniprot_id: ID de UniProt
            
        Returns:
            Diccionario con información de la proteína o None
        """
        return self.proteins.get(uniprot_id)
    
    def get_sequence_to_uniprot_mapping(self) -> Dict[str, str]:
        """
        Obtiene un mapeo de secuencia -> UniProt ID para compatibilidad
        
        Returns:
            Diccionario {secuencia: uniprot_id}
        """
        return {
            protein_data['sequence']: uniprot_id 
            for uniprot_id, protein_data in self.proteins.items()
        }
    
    def add_protein(self, uniprot_id: str, protein_data: Dict):
        """
        Añade una nueva proteína a la base de datos (solo en memoria)
        
        Args:
            uniprot_id: ID de UniProt
            protein_data: Datos de la proteína
        """
        self.proteins[uniprot_id] = protein_data
        print(f"➕ Proteína {uniprot_id} añadida a la base de datos")
    
    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas de la base de datos
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.proteins:
            return {}
        
        sequences = [p['sequence'] for p in self.proteins.values()]
        lengths = [len(seq) for seq in sequences]
        
        return {
            'total_proteins': len(self.proteins),
            'avg_length': sum(lengths) / len(lengths) if lengths else 0,
            'min_length': min(lengths) if lengths else 0,
            'max_length': max(lengths) if lengths else 0,
            'organisms': list(set(p.get('organism', 'Unknown') for p in self.proteins.values()))
        }
    
    def list_proteins(self) -> List[Tuple[str, str, int]]:
        """
        Lista todas las proteínas en la base de datos
        
        Returns:
            Lista de tuplas (uniprot_id, name, length)
        """
        return [
            (uniprot_id, protein_data.get('name', 'Unknown'), protein_data.get('length', 0))
            for uniprot_id, protein_data in self.proteins.items()
        ]
