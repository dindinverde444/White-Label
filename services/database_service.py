from config.supabase import supabase, TABLES
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class DatabaseService:
    def __init__(self):
        self.supabase = supabase
    
    # Métodos para usuários
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um novo usuário"""
        try:
            user_data['id'] = str(uuid.uuid4())
            user_data['created_at'] = datetime.now().isoformat()
            
            response = self.supabase.table(TABLES['usuarios']).insert(user_data).execute()
            return {"success": True, "data": response.data[0] if response.data else None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por ID"""
        try:
            response = self.supabase.table(TABLES['usuarios']).select('*').eq('id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar usuário: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por email"""
        try:
            response = self.supabase.table(TABLES['usuarios']).select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar usuário por email: {e}")
            return None
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Atualiza dados do usuário"""
        try:
            user_data['updated_at'] = datetime.now().isoformat()
            self.supabase.table(TABLES['usuarios']).update(user_data).eq('id', user_id).execute()
            return True
        except Exception as e:
            print(f"Erro ao atualizar usuário: {e}")
            return False
    
    def get_pending_users(self) -> List[Dict[str, Any]]:
        """Busca usuários pendentes de aprovação"""
        try:
            response = self.supabase.table(TABLES['usuarios']).select('*').eq('status', 'pendente_aprovacao').execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar usuários pendentes: {e}")
            return []
    
    def get_archived_users(self) -> List[Dict[str, Any]]:
        """Busca usuários arquivados"""
        try:
            response = self.supabase.table(TABLES['usuarios']).select('*').eq('status', 'rejeitado').execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar usuários arquivados: {e}")
            return []
    
    # Métodos para KYC
    def save_kyc(self, user_id: str, kyc_data: Dict[str, Any]) -> bool:
        """Salva dados KYC"""
        try:
            kyc_data['user_id'] = user_id
            kyc_data['created_at'] = datetime.now().isoformat()
            
            # Verificar se já existe KYC para este usuário
            existing = self.supabase.table(TABLES['kyc']).select('*').eq('user_id', user_id).execute()
            
            if existing.data:
                # Atualizar KYC existente
                kyc_data['updated_at'] = datetime.now().isoformat()
                self.supabase.table(TABLES['kyc']).update(kyc_data).eq('user_id', user_id).execute()
            else:
                # Criar novo KYC
                self.supabase.table(TABLES['kyc']).insert(kyc_data).execute()
            
            return True
        except Exception as e:
            print(f"Erro ao salvar KYC: {e}")
            return False
    
    def get_kyc_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca KYC por user_id"""
        try:
            response = self.supabase.table(TABLES['kyc']).select('*').eq('user_id', user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao buscar KYC: {e}")
            return None
    
    def get_pending_kyc(self) -> List[Dict[str, Any]]:
        """Busca KYC pendentes"""
        try:
            response = self.supabase.table(TABLES['kyc']).select('*').eq('status', 'pendente_aprovacao').execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar KYC pendentes: {e}")
            return []
    
    # Métodos para produtos
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um novo produto"""
        try:
            product_data['id'] = str(uuid.uuid4())
            product_data['created_at'] = datetime.now().isoformat()
            
            response = self.supabase.table(TABLES['produtos']).insert(product_data).execute()
            return {"success": True, "data": response.data[0] if response.data else None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_products_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Busca produtos de um usuário"""
        try:
            response = self.supabase.table(TABLES['produtos']).select('*').eq('user_id', user_id).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar produtos: {e}")
            return []
    
    def get_marketplace_products(self) -> List[Dict[str, Any]]:
        """Busca produtos do marketplace"""
        try:
            response = self.supabase.table(TABLES['produtos']).select('*').eq('show_marketplace', True).eq('status', 'ativo').execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar produtos do marketplace: {e}")
            return []
    
    # Métodos para transações
    def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma nova transação"""
        try:
            transaction_data['id'] = str(uuid.uuid4())
            transaction_data['created_at'] = datetime.now().isoformat()
            
            response = self.supabase.table(TABLES['transacoes']).insert(transaction_data).execute()
            return {"success": True, "data": response.data[0] if response.data else None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_transactions_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Busca transações de um usuário"""
        try:
            response = self.supabase.table(TABLES['transacoes']).select('*').eq('user_id', user_id).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar transações: {e}")
            return []
    
    # Métodos para logs
    def create_log(self, log_data: Dict[str, Any]) -> bool:
        """Cria um novo log"""
        try:
            log_data['id'] = str(uuid.uuid4())
            log_data['created_at'] = datetime.now().isoformat()
            
            self.supabase.table(TABLES['logs']).insert(log_data).execute()
            return True
        except Exception as e:
            print(f"Erro ao criar log: {e}")
            return False
    
    def get_logs_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Busca logs de um usuário"""
        try:
            response = self.supabase.table(TABLES['logs']).select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao buscar logs: {e}")
            return []

