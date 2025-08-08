#!/usr/bin/env python3
"""
Script de configuração do Supabase para o White Label Gateway
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

def setup_supabase():
    """Configura o Supabase com as tabelas necessárias"""
    
    # Verificar se as variáveis de ambiente estão configuradas
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Erro: Configure as variáveis SUPABASE_URL e SUPABASE_KEY no arquivo .env")
        print("Exemplo:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_KEY=your-anon-key")
        return False
    
    try:
        # Conectar ao Supabase
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Conectado ao Supabase com sucesso!")
        
        # SQL para criar as tabelas
        tables_sql = """
        -- Tabela de usuários
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

        -- Tabela de KYC
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

        -- Tabela de produtos
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

        -- Tabela de transações
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

        -- Tabela de logs
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

        -- Tabela de taxas
        CREATE TABLE IF NOT EXISTS taxas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome VARCHAR(100) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            valor DECIMAL(5,2) NOT NULL,
            ativo BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Tabela de saques
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

        -- Tabela de metas
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

        -- Habilitar RLS (Row Level Security)
        ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
        ALTER TABLE kyc ENABLE ROW LEVEL SECURITY;
        ALTER TABLE produtos ENABLE ROW LEVEL SECURITY;
        ALTER TABLE transacoes ENABLE ROW LEVEL SECURITY;
        ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
        ALTER TABLE taxas ENABLE ROW LEVEL SECURITY;
        ALTER TABLE saques ENABLE ROW LEVEL SECURITY;
        ALTER TABLE metas ENABLE ROW LEVEL SECURITY;

        -- Criar políticas RLS básicas
        -- Política para usuários verem apenas seus próprios dados
        CREATE POLICY IF NOT EXISTS "Usuários podem ver seus próprios dados" ON usuarios
            FOR SELECT USING (auth.uid() = id);

        -- Política para admins verem todos os usuários
        CREATE POLICY IF NOT EXISTS "Admins podem ver todos os usuários" ON usuarios
            FOR ALL USING (
                EXISTS (
                    SELECT 1 FROM usuarios 
                    WHERE id = auth.uid() AND tipo = 'admin'
                )
            );

        -- Política para KYC
        CREATE POLICY IF NOT EXISTS "Usuários podem ver seu próprio KYC" ON kyc
            FOR ALL USING (auth.uid() = user_id);

        -- Política para produtos
        CREATE POLICY IF NOT EXISTS "Usuários podem gerenciar seus produtos" ON produtos
            FOR ALL USING (auth.uid() = user_id);

        -- Política para transações
        CREATE POLICY IF NOT EXISTS "Usuários podem ver suas transações" ON transacoes
            FOR ALL USING (auth.uid() = user_id);

        -- Política para logs
        CREATE POLICY IF NOT EXISTS "Admins podem ver logs" ON logs
            FOR ALL USING (
                EXISTS (
                    SELECT 1 FROM usuarios 
                    WHERE id = auth.uid() AND tipo = 'admin'
                )
            );

        -- Inserir taxas padrão
        INSERT INTO taxas (nome, tipo, valor) VALUES
        ('Taxa PIX', 'pix', 1.99),
        ('Taxa Cartão', 'cartao', 2.99),
        ('Taxa Boleto', 'boleto', 3.99)
        ON CONFLICT DO NOTHING;

        """
        
        # Executar o SQL
        print("🔧 Criando tabelas no Supabase...")
        result = supabase.rpc('exec_sql', {'sql': tables_sql}).execute()
        print("✅ Tabelas criadas com sucesso!")
        
        # Testar a conexão
        print("🧪 Testando conexão...")
        test_result = supabase.table('usuarios').select('count').execute()
        print("✅ Conexão testada com sucesso!")
        
        print("\n🎉 Configuração do Supabase concluída!")
        print("📊 Tabelas criadas:")
        print("   - usuarios")
        print("   - kyc")
        print("   - produtos")
        print("   - transacoes")
        print("   - logs")
        print("   - taxas")
        print("   - saques")
        print("   - metas")
        print("\n🔒 RLS (Row Level Security) habilitado")
        print("📋 Políticas de segurança configuradas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar Supabase: {str(e)}")
        print("\n💡 Dicas:")
        print("1. Verifique se as credenciais do Supabase estão corretas")
        print("2. Certifique-se de que o projeto está ativo")
        print("3. Verifique se você tem permissões de administrador")
        return False

def create_admin_user():
    """Cria um usuário administrador padrão"""
    
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Configure as variáveis de ambiente primeiro")
            return False
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Dados do admin
        admin_data = {
            'username': 'admin',
            'email': 'admin@whitelabel.com',
            'nome_completo': 'Administrador',
            'tipo': 'admin',
            'status': 'ativo',
            'api_key': 'admin_key_123'
        }
        
        print("👤 Criando usuário administrador...")
        
        # Criar usuário no Auth
        auth_response = supabase.auth.sign_up({
            "email": admin_data['email'],
            "password": "admin123"
        })
        
        if auth_response.user:
            # Salvar dados adicionais
            admin_data['id'] = auth_response.user.id
            supabase.table('usuarios').upsert(admin_data).execute()
            
            print("✅ Usuário administrador criado!")
            print(f"📧 Email: {admin_data['email']}")
            print(f"🔑 Senha: admin123")
            return True
        else:
            print("❌ Erro ao criar usuário administrador")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar admin: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Configurando White Label Gateway...")
    print("=" * 50)
    
    # Configurar Supabase
    if setup_supabase():
        # Criar admin
        create_admin_user()
        
        print("\n" + "=" * 50)
        print("🎉 Configuração concluída!")
        print("🚀 Execute: python app.py")
        print("🌐 Acesse: http://localhost:5000")
    else:
        print("\n❌ Configuração falhou. Verifique os erros acima.")
