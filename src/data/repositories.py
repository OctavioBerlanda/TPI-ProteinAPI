from typing import List, Optional
from src.data.models import db, ProteinComparison, User

class ProteinComparisonRepository:
    """Repositorio para operaciones de base de datos relacionadas con comparaciones de proteínas"""
    
    @staticmethod
    def create_comparison(user_id: int, original_sequence: str, mutated_sequence: str,
                         mutation_positions: List[int], mutations_description: str,
                         comparison_name: str = None, description: str = None) -> ProteinComparison:
        """Crea una nueva comparación de proteínas"""
        
        comparison = ProteinComparison(
            user_id=user_id,
            original_sequence=original_sequence,
            mutated_sequence=mutated_sequence,
            sequence_length=len(original_sequence),
            mutation_count=len(mutation_positions),
            mutation_positions=','.join(map(str, mutation_positions)),
            mutations_description=mutations_description,
            comparison_name=comparison_name,
            description=description
        )
        
        db.session.add(comparison)
        db.session.commit()
        return comparison
    
    @staticmethod
    def get_comparison_by_id(comparison_id: int) -> Optional[ProteinComparison]:
        """Obtiene una comparación por su ID"""
        return ProteinComparison.query.get(comparison_id)
    
    @staticmethod
    def get_comparisons_by_user(user_id: int) -> List[ProteinComparison]:
        """Obtiene todas las comparaciones de un usuario"""
        return ProteinComparison.query.filter_by(user_id=user_id).order_by(
            ProteinComparison.created_at.desc()
        ).all()
    
    @staticmethod
    def update_comparison_status(comparison_id: int, status: str, 
                               original_prediction_url: str = None,
                               mutated_prediction_url: str = None) -> bool:
        """Actualiza el estado y URLs de predicción de una comparación"""
        comparison = ProteinComparison.query.get(comparison_id)
        if comparison:
            comparison.status = status
            if original_prediction_url:
                comparison.original_prediction_url = original_prediction_url
            if mutated_prediction_url:
                comparison.mutated_prediction_url = mutated_prediction_url
            
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def delete_comparison(comparison_id: int) -> bool:
        """Elimina una comparación"""
        comparison = ProteinComparison.query.get(comparison_id)
        if comparison:
            db.session.delete(comparison)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_all_comparisons(limit: int = 100) -> List[ProteinComparison]:
        """Obtiene todas las comparaciones (para administración)"""
        return ProteinComparison.query.order_by(
            ProteinComparison.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def update_comparison(comparison_id: int, update_data: dict) -> bool:
        """
        Actualiza una comparación existente con nuevos datos
        
        Args:
            comparison_id: ID de la comparación a actualizar
            update_data: Diccionario con los campos a actualizar
            
        Returns:
            True si la actualización fue exitosa, False en caso contrario
        """
        try:
            comparison = db.session.query(ProteinComparison).filter_by(id=comparison_id).first()
            if not comparison:
                return False
            
            # Actualizar solo los campos proporcionados
            for field, value in update_data.items():
                if hasattr(comparison, field) and value is not None:
                    setattr(comparison, field, value)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error actualizando comparación {comparison_id}: {e}")
            return False

class UserRepository:
    """Repositorio para operaciones de base de datos relacionadas con usuarios"""
    
    @staticmethod
    def create_user(username: str, email: str) -> User:
        """Crea un nuevo usuario"""
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Obtiene un usuario por su ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Obtiene un usuario por su nombre de usuario"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Obtiene un usuario por su email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_or_create_user(username: str, email: str) -> User:
        """Obtiene un usuario existente o crea uno nuevo"""
        user = UserRepository.get_user_by_username(username)
        if not user:
            user = UserRepository.create_user(username, email)
        return user
