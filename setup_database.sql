-- ==================================================
-- CONFIGURAÇÃO DO BANCO DE DADOS - WHITE LABEL GATEWAY
-- ==================================================
-- Execute este SQL no SQL Editor do Supabase

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

-- ==================================================
-- HABILITAR RLS (ROW LEVEL SECURITY)
-- ==================================================

ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE kyc ENABLE ROW LEVEL SECURITY;
ALTER TABLE produtos ENABLE ROW LEVEL SECURITY;
ALTER TABLE transacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE taxas ENABLE ROW LEVEL SECURITY;
ALTER TABLE saques ENABLE ROW LEVEL SECURITY;
ALTER TABLE metas ENABLE ROW LEVEL SECURITY;

-- ==================================================
-- CRIAR POLÍTICAS DE SEGURANÇA
-- ==================================================

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

-- Política para logs (apenas admins)
CREATE POLICY IF NOT EXISTS "Admins podem ver logs" ON logs
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM usuarios 
            WHERE id = auth.uid() AND tipo = 'admin'
        )
    );

-- Política para taxas (leitura pública)
CREATE POLICY IF NOT EXISTS "Taxas são públicas" ON taxas
    FOR SELECT USING (true);

-- Política para saques
CREATE POLICY IF NOT EXISTS "Usuários podem ver seus saques" ON saques
    FOR ALL USING (auth.uid() = user_id);

-- Política para metas
CREATE POLICY IF NOT EXISTS "Usuários podem gerenciar suas metas" ON metas
    FOR ALL USING (auth.uid() = user_id);

-- ==================================================
-- INSERIR DADOS INICIAIS
-- ==================================================

-- Inserir taxas padrão
INSERT INTO taxas (nome, tipo, valor) VALUES
('Taxa PIX', 'pix', 1.99),
('Taxa Cartão', 'cartao', 2.99),
('Taxa Boleto', 'boleto', 3.99)
ON CONFLICT DO NOTHING;

-- Criar usuário administrador
INSERT INTO usuarios (id, username, email, nome_completo, tipo, status, api_key) VALUES
(gen_random_uuid(), 'admin', 'admin@whitelabel.com', 'Administrador', 'admin', 'ativo', 'admin_key_123')
ON CONFLICT DO NOTHING;

-- ==================================================
-- CONFIGURAÇÃO DE STORAGE (OPCIONAL)
-- ==================================================

-- Política para upload de arquivos
CREATE POLICY IF NOT EXISTS "Usuários podem fazer upload" ON storage.objects
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Política para visualizar arquivos
CREATE POLICY IF NOT EXISTS "Arquivos são públicos" ON storage.objects
    FOR SELECT USING (true);

-- ==================================================
-- MENSAGEM DE CONFIRMAÇÃO
-- ==================================================

-- Verificar se as tabelas foram criadas
SELECT 
    'Tabelas criadas com sucesso!' as status,
    COUNT(*) as total_tabelas
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('usuarios', 'kyc', 'produtos', 'transacoes', 'logs', 'taxas', 'saques', 'metas');
