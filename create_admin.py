#!/usr/bin/env python3
"""
Script para criar usuário admin no Supabase
"""

import os
import uuid
import hashlib
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def create_admin_user():
    """Cria usuário admin no Supabase"""
    try:
        from config.supabase import supabase
        from services.database_service import DatabaseService
        
        print("👨‍💼 Criando usuário admin...")
        
        # Dados do admin
        admin_data = {
            'username': 'admin',
            'email': 'admin@gateway.com',
            'nome_completo': 'Administrador',
            'tipo': 'admin',
            'status': 'ativo',
            'api_key': hashlib.sha256(uuid.uuid4().bytes).hexdigest()
        }
        
        # Criar usuário no Supabase Auth
        print("🔐 Criando conta no Supabase Auth...")
        
        auth_response = supabase.auth.sign_up({
            "email": admin_data['email'],
            "password": "admin123",
            "options": {
                "data": admin_data
            }
        })
        
        if auth_response.user:
            print("✅ Usuário criado no Supabase Auth")
            
            # Salvar dados adicionais na tabela usuarios
            db_service = DatabaseService()
            user_id = auth_response.user.id
            
            # Verificar se já existe
            existing_user = db_service.get_user_by_email(admin_data['email'])
            if existing_user:
                print("⚠️ Usuário admin já existe")
                return
            
            # Criar na tabela usuarios
            result = db_service.create_user({
                'id': user_id,
                **admin_data
            })
            
            if result['success']:
                print("✅ Dados salvos na tabela usuarios")
                print(f"🆔 ID: {user_id}")
                print(f"📧 Email: {admin_data['email']}")
                print(f"🔑 Senha: admin123")
                print("\n🎉 Usuário admin criado com sucesso!")
            else:
                print(f"❌ Erro ao salvar dados: {result['error']}")
        else:
            print("❌ Erro ao criar usuário no Supabase Auth")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("💡 Verifique suas credenciais do Supabase")

def main():
    """Função principal"""
    print("🚀 Criador de Usuário Admin")
    print("=" * 30)
    
    create_admin_user()
    
    print("\n" + "=" * 30)
    print("📋 Próximos passos:")
    print("1. Execute: python app.py")
    print("2. Acesse: http://localhost:5000/admin-login")
    print("3. Faça login com: admin@gateway.com / admin123")

if __name__ == "__main__":
    main()

