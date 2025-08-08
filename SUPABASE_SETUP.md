# 🔧 Configuração do Supabase - White Label Gateway

## 📋 Pré-requisitos

1. **Conta no Supabase**: [supabase.com](https://supabase.com)
2. **Projeto criado** no Supabase
3. **Credenciais** do projeto (URL e API Key)

## 🚀 Passo a Passo

### 1. Criar Projeto no Supabase

1. Acesse [supabase.com](https://supabase.com)
2. Faça login ou crie uma conta
3. Clique em "New Project"
4. Escolha sua organização
5. Digite um nome: `white-label-gateway`
6. Escolha uma senha para o banco de dados
7. Escolha uma região (recomendado: mais próxima)
8. Clique em "Create new project"

### 2. Obter Credenciais

1. No dashboard do projeto, vá em **Settings** → **API**
2. Copie a **Project URL**
3. Copie a **anon public** key
4. Configure no arquivo `.env`:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
```

### 3. Configurar Tabelas

Execute o seguinte SQL no **SQL Editor** do Supabase:

```sql
-- Tabela de usuários
CREATE TABLE usuarios (
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
CREATE TABLE kyc (
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
CREATE TABLE produtos (
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
CREATE TABLE transacoes (
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
CREATE TABLE logs (
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
CREATE TABLE taxas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    valor DECIMAL(5,2) NOT NULL,
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de saques
CREATE TABLE saques (
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
CREATE TABLE metas (
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
```

### 4. Habilitar RLS (Row Level Security)

Execute no SQL Editor:

```sql
-- Habilitar RLS em todas as tabelas
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE kyc ENABLE ROW LEVEL SECURITY;
ALTER TABLE produtos ENABLE ROW LEVEL SECURITY;
ALTER TABLE transacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE taxas ENABLE ROW LEVEL SECURITY;
ALTER TABLE saques ENABLE ROW LEVEL SECURITY;
ALTER TABLE metas ENABLE ROW LEVEL SECURITY;
```

### 5. Criar Políticas de Segurança

```sql
-- Política para usuários verem apenas seus próprios dados
CREATE POLICY "Usuários podem ver seus próprios dados" ON usuarios
    FOR SELECT USING (auth.uid() = id);

-- Política para admins verem todos os usuários
CREATE POLICY "Admins podem ver todos os usuários" ON usuarios
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM usuarios 
            WHERE id = auth.uid() AND tipo = 'admin'
        )
    );

-- Política para KYC
CREATE POLICY "Usuários podem ver seu próprio KYC" ON kyc
    FOR ALL USING (auth.uid() = user_id);

-- Política para produtos
CREATE POLICY "Usuários podem gerenciar seus produtos" ON produtos
    FOR ALL USING (auth.uid() = user_id);

-- Política para transações
CREATE POLICY "Usuários podem ver suas transações" ON transacoes
    FOR ALL USING (auth.uid() = user_id);

-- Política para logs (apenas admins)
CREATE POLICY "Admins podem ver logs" ON logs
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM usuarios 
            WHERE id = auth.uid() AND tipo = 'admin'
        )
    );

-- Política para taxas (leitura pública)
CREATE POLICY "Taxas são públicas" ON taxas
    FOR SELECT USING (true);

-- Política para saques
CREATE POLICY "Usuários podem ver seus saques" ON saques
    FOR ALL USING (auth.uid() = user_id);

-- Política para metas
CREATE POLICY "Usuários podem gerenciar suas metas" ON metas
    FOR ALL USING (auth.uid() = user_id);
```

### 6. Inserir Dados Iniciais

```sql
-- Inserir taxas padrão
INSERT INTO taxas (nome, tipo, valor) VALUES
('Taxa PIX', 'pix', 1.99),
('Taxa Cartão', 'cartao', 2.99),
('Taxa Boleto', 'boleto', 3.99);

-- Criar usuário administrador
INSERT INTO usuarios (id, username, email, nome_completo, tipo, status, api_key) VALUES
(gen_random_uuid(), 'admin', 'admin@whitelabel.com', 'Administrador', 'admin', 'ativo', 'admin_key_123');
```

### 7. Configurar Storage (Opcional)

Para upload de imagens:

1. Vá em **Storage** no dashboard
2. Crie um bucket chamado `uploads`
3. Configure as políticas:

```sql
-- Política para upload de arquivos
CREATE POLICY "Usuários podem fazer upload" ON storage.objects
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Política para visualizar arquivos
CREATE POLICY "Arquivos são públicos" ON storage.objects
    FOR SELECT USING (true);
```

## 🧪 Testar Configuração

### 1. Testar Conexão

Execute o script de configuração:

```bash
python setup_supabase.py
```

### 2. Testar Aplicação

```bash
python app.py
```

Acesse: http://localhost:5000

### 3. Credenciais de Teste

**Admin:**
- Email: admin@whitelabel.com
- Senha: admin123

## 🔒 Configurações de Segurança

### 1. Configurar Auth Settings

1. Vá em **Authentication** → **Settings**
2. Configure:
   - **Site URL**: http://localhost:5000
   - **Redirect URLs**: http://localhost:5000/callback
   - **Enable email confirmations**: Desabilitado (para desenvolvimento)

### 2. Configurar CORS

1. Vá em **Settings** → **API**
2. Adicione em **CORS Origins**:
   - http://localhost:5000
   - http://localhost:3000 (se usar React)

### 3. Configurar Email (Opcional)

1. Vá em **Authentication** → **Email Templates**
2. Personalize os templates de email

## 📊 Monitoramento

### 1. Logs

- **Database Logs**: Settings → Logs
- **Auth Logs**: Authentication → Logs
- **API Logs**: Settings → API

### 2. Analytics

- **Database**: Ver tabelas e consultas
- **Auth**: Ver usuários e sessões
- **Storage**: Ver uploads

## 🚨 Troubleshooting

### Problema: "Invalid API key"
- Verifique se a URL e chave estão corretas
- Certifique-se de usar a chave `anon public`

### Problema: "RLS policy violation"
- Verifique se as políticas foram criadas
- Teste com um usuário autenticado

### Problema: "Table doesn't exist"
- Execute o SQL de criação das tabelas
- Verifique se não há erros de sintaxe

### Problema: "CORS error"
- Configure as origens CORS no Supabase
- Verifique se a URL está correta

## 📞 Suporte

- **Documentação Supabase**: [supabase.com/docs](https://supabase.com/docs)
- **Issues**: [GitHub Issues](https://github.com/dindinverde444/White-Label/issues)
- **Comunidade**: [Discord Supabase](https://discord.supabase.com)

---

**✅ Configuração concluída!** Seu White Label Gateway está pronto para uso! 🚀
