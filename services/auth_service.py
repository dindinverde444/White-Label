from config.supabase import supabase
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

class AuthService:
    def __init__(self):
        self.supabase = supabase
    
    def sign_up(self, email: str, password: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registra um novo usuário no Supabase Auth"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_data
                }
            })
            
            if response.user:
                # Salvar dados adicionais na tabela usuarios
                user_id = response.user.id
                self._save_user_data(user_id, user_data)
                
                return {
                    "success": True,
                    "user": response.user,
                    "message": "Usuário registrado com sucesso"
                }
            else:
                return {
                    "success": False,
                    "message": "Erro ao registrar usuário"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro: {str(e)}"
            }
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Faz login do usuário no Supabase Auth"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Buscar dados adicionais do usuário
                user_data = self._get_user_data(response.user.id)
                
                return {
                    "success": True,
                    "user": response.user,
                    "user_data": user_data,
                    "access_token": response.session.access_token
                }
            else:
                return {
                    "success": False,
                    "message": "Credenciais inválidas"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro: {str(e)}"
            }
    
    def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do usuário usando o token de acesso"""
        try:
            self.supabase.auth.set_session(access_token, None)
            user = self.supabase.auth.get_user()
            
            if user.user:
                user_data = self._get_user_data(user.user.id)
                return {
                    "user": user.user,
                    "user_data": user_data
                }
            return None
        except Exception:
            return None
    
    def sign_out(self, access_token: str) -> bool:
        """Faz logout do usuário"""
        try:
            self.supabase.auth.set_session(access_token, None)
            self.supabase.auth.sign_out()
            return True
        except Exception:
            return False
    
    def _save_user_data(self, user_id: str, user_data: Dict[str, Any]):
        """Salva dados adicionais do usuário na tabela usuarios"""
        try:
            self.supabase.table('usuarios').upsert({
                'id': user_id,
                'username': user_data.get('username'),
                'email': user_data.get('email'),
                'tipo': user_data.get('tipo', 'seller'),
                'status': user_data.get('status', 'pendente_aprovacao'),
                'api_key': user_data.get('api_key'),
                'created_at': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            print(f"Erro ao salvar dados do usuário: {e}")
    
    def _get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Busca dados adicionais do usuário"""
        try:
            response = self.supabase.table('usuarios').select('*').eq('id', user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Erro ao buscar dados do usuário: {e}")
            return None
    
    def is_admin(self, user_data: Dict[str, Any]) -> bool:
        """Verifica se o usuário é admin"""
        return user_data.get('tipo') == 'admin'
    
    def is_approved(self, user_data: Dict[str, Any]) -> bool:
        """Verifica se o usuário está aprovado"""
        return user_data.get('status') == 'ativo'

