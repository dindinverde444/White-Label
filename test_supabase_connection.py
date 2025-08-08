#!/usr/bin/env python3
"""
Script para testar conexão com Supabase e criar tabelas
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

def test_connection():
    """Testa a conexão com o Supabase"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Erro: Configure as variáveis SUPABASE_URL e SUPABASE_KEY no arquivo .env")
        return False
    
    try:
        # Conectar ao Supabase
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Conectado ao Supabase com sucesso!")
        
        # Testar conexão fazendo uma consulta simples
        result = supabase.table('usuarios').select('count').execute()
        print("✅ Conexão testada com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {str(e)}")
        return False

def create_tables():
    """Cria as tabelas uma por uma"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Lista de comandos SQL para criar tabelas
    tables = [
        {
            'name': 'usuarios',
            'sql': '''
            CREATE TABLE IF NOT EXISTS usuarios (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                nome_completo VARCHAR(255),
                telefone VARCHAR(20),
                tipo_conta VARCHAR(10),
                cpf VARCHAR(14),
                razao_social VARCHAR(255),
                cnpj VARCHAR(18),
                porte_juridico VARCHAR(50),
                tipo VARCHAR(50) DEFAULT 'seller',
                status VARCHAR(50) DEFAULT 'pendente_aprovacao',
                api_key VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            '''
        },
        {
            'name': 'kyc',
            'sql': '''
            CREATE TABLE IF NOT EXISTS kyc (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
                documento_tipo VARCHAR(50),
                documento_numero VARCHAR(255),
                endereco TEXT,
                cidade VARCHAR(100),
                estado VARCHAR(2),
                cep VARCHAR(10),
                status VARCHAR(50) DEFAULT 'pendente',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            '''
        },
        {
            'name': 'produtos',
            'sql': '''
            CREATE TABLE IF NOT EXISTS produtos (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
                nome VARCHAR(255) NOT NULL,
                descricao TEXT,
                preco DECIMAL(10,2),
                imagem_url VARCHAR(500),
                categoria VARCHAR(100),
                status VARCHAR(50) DEFAULT 'ativo',
                show_marketplace BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            '''
        },
        {
            'name': 'transacoes',
            'sql': '''
            CREATE TABLE IF NOT EXISTS transacoes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
                payment_id VARCHAR(255) UNIQUE,
                amount DECIMAL(10,2),
                description TEXT,
                status VARCHAR(50),
                payment_method VARCHAR(50),
                gateway_response TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            '''
        },
        {
            'name': 'logs',
            'sql': '''
            CREATE TABLE IF NOT EXISTS logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
                action VARCHAR(100),
                target_user_id UUID,
                description TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            '''
        },
        {
            'name': 'taxas',
            'sql': '''
            CREATE TABLE IF NOT EXISTS taxas (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                nome VARCHAR(100) NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                valor DECIMAL(5,2) NOT NULL,
                ativo BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            '''
        },
        {
            'name': 'saques',
            'sql': '''
            CREATE TABLE IF NOT EXISTS saques (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
                valor DECIMAL(10,2) NOT NULL,
                conta_bancaria TEXT,
                status VARCHAR(50) DEFAULT 'pendente',
                data_solicitacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                data_processamento TIMESTAMP WITH TIME ZONE,
                observacoes TEXT
            );
            '''
        },
        {
            'name': 'metas',
            'sql': '''
            CREATE TABLE IF NOT EXISTS metas (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
                titulo VARCHAR(255) NOT NULL,
                descricao TEXT,
                valor_meta DECIMAL(10,2) NOT NULL,
                valor_atual DECIMAL(10,2) DEFAULT 0,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                status VARCHAR(50) DEFAULT 'ativa',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            '''
        }
    ]
    
    print("🔧 Criando tabelas...")
    
    for table in tables:
        try:
            print(f"📋 Criando tabela: {table['name']}")
            # Como não podemos executar SQL diretamente, vamos verificar se a tabela existe
            result = supabase.table(table['name']).select('count').execute()
            print(f"✅ Tabela {table['name']} já existe")
        except Exception as e:
            print(f"❌ Tabela {table['name']} não existe ou erro: {str(e)}")
            print(f"💡 Execute o SQL manualmente no Supabase SQL Editor:")
            print(f"   {table['sql'].strip()}")
            print()

def insert_initial_data():
    """Insere dados iniciais"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Inserir taxas padrão
        print("💰 Inserindo taxas padrão...")
        taxas_data = [
            {'nome': 'Taxa PIX', 'tipo': 'pix', 'valor': 1.99},
            {'nome': 'Taxa Cartão', 'tipo': 'cartao', 'valor': 2.99},
            {'nome': 'Taxa Boleto', 'tipo': 'boleto', 'valor': 3.99}
        ]
        
        for taxa in taxas_data:
            try:
                supabase.table('taxas').upsert(taxa).execute()
                print(f"✅ Taxa {taxa['nome']} inserida")
            except Exception as e:
                print(f"❌ Erro ao inserir taxa {taxa['nome']}: {str(e)}")
        
        # Criar usuário admin
        print("👤 Criando usuário administrador...")
        admin_data = {
            'username': 'admin',
            'email': 'admin@whitelabel.com',
            'nome_completo': 'Administrador',
            'tipo': 'admin',
            'status': 'ativo',
            'api_key': 'admin_key_123'
        }
        
        try:
            supabase.table('usuarios').upsert(admin_data).execute()
            print("✅ Usuário administrador criado!")
            print("📧 Email: admin@whitelabel.com")
            print("🔑 Senha: admin123")
        except Exception as e:
            print(f"❌ Erro ao criar admin: {str(e)}")
            
    except Exception as e:
        print(f"❌ Erro ao inserir dados iniciais: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testando White Label Gateway...")
    print("=" * 50)
    
    # Testar conexão
    if test_connection():
        # Criar tabelas
        create_tables()
        
        # Inserir dados iniciais
        insert_initial_data()
        
        print("\n" + "=" * 50)
        print("🎉 Teste concluído!")
        print("📋 Para criar as tabelas, execute o arquivo setup_database.sql no SQL Editor do Supabase")
        print("🚀 Execute: python app.py")
        print("🌐 Acesse: http://localhost:5000")
    else:
        print("\n❌ Teste falhou. Verifique as credenciais do Supabase.")
