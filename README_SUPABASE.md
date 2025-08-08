# Gateway de Pagamentos - Integração Supabase

## 🚀 Configuração Inicial

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Supabase

1. Crie um projeto no [Supabase](https://supabase.com)
2. Obtenha as credenciais:
   - URL do projeto
   - Chave anônima (anon key)
3. Configure as variáveis de ambiente:
   ```bash
   # Copie o arquivo env_example.txt para .env
   cp env_example.txt .env
   
   # Edite o arquivo .env com suas credenciais
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua-chave-anonima
   ```

### 3. Criar Tabelas no Supabase

Execute os seguintes comandos SQL no editor SQL do Supabase:

#### Tabela `usuarios`
```sql
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    nome_completo VARCHAR(255),
    telefone VARCHAR(20),
    tipo_conta VARCHAR(10), -- 'CPF' ou 'PJ'
    cpf VARCHAR(14),
    razao_social VARCHAR(255),
    cnpj VARCHAR(18),
    porte_juridico VARCHAR(50),
    tipo VARCHAR(20) DEFAULT 'seller', -- 'admin' ou 'seller'
    status VARCHAR(20) DEFAULT 'pendente_aprovacao',
    api_key VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabela `kyc`
```sql
CREATE TABLE kyc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    nome_responsavel VARCHAR(255),
    cpf_responsavel VARCHAR(14),
    nome_mae VARCHAR(255),
    data_nascimento DATE,
    setor_atividade TEXT,
    faturamento_mensal TEXT,
    tipo_entidade VARCHAR(10), -- 'PF' ou 'PJ'
    cnpj VARCHAR(18),
    razao_social VARCHAR(255),
    porte_juridico VARCHAR(50),
    documento_responsavel VARCHAR(255),
    contrato_social VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pendente_aprovacao',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabela `produtos`
```sql
CREATE TABLE produtos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10,2) NOT NULL,
    imagem VARCHAR(255),
    show_marketplace BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'ativo',
    views INTEGER DEFAULT 0,
    sales INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabela `transacoes`
```sql
CREATE TABLE transacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    payment_id VARCHAR(255),
    product_id UUID REFERENCES produtos(id),
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    merchant_reference_id VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabela `logs`
```sql
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    target_user_id UUID REFERENCES usuarios(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabela `taxas`
```sql
CREATE TABLE taxas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,
    valor DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Tabela `saques`
```sql
CREATE TABLE saques (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    valor DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente',
    data_solicitacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data_processamento TIMESTAMP WITH TIME ZONE
);
```

#### Tabela `metas`
```sql
CREATE TABLE metas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    valor_meta DECIMAL(10,2) NOT NULL,
    valor_atual DECIMAL(10,2) DEFAULT 0,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'ativa',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. Configurar RLS (Row Level Security)

Execute no editor SQL do Supabase:

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

-- Políticas para usuarios
CREATE POLICY "Users can view their own data" ON usuarios
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update their own data" ON usuarios
    FOR UPDATE USING (auth.uid()::text = id::text);

CREATE POLICY "Admins can view all users" ON usuarios
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM usuarios 
            WHERE id::text = auth.uid()::text 
            AND tipo = 'admin'
        )
    );

-- Políticas para produtos
CREATE POLICY "Users can view their own products" ON produtos
    FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can insert their own products" ON produtos
    FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY "Users can update their own products" ON produtos
    FOR UPDATE USING (user_id::text = auth.uid()::text);

CREATE POLICY "Anyone can view marketplace products" ON produtos
    FOR SELECT USING (show_marketplace = true AND status = 'ativo');

-- Políticas para transacoes
CREATE POLICY "Users can view their own transactions" ON transacoes
    FOR SELECT USING (user_id::text = auth.uid()::text);

CREATE POLICY "Users can insert their own transactions" ON transacoes
    FOR INSERT WITH CHECK (user_id::text = auth.uid()::text);

-- Políticas para logs (apenas admins)
CREATE POLICY "Admins can view all logs" ON logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM usuarios 
            WHERE id::text = auth.uid()::text 
            AND tipo = 'admin'
        )
    );

CREATE POLICY "Admins can insert logs" ON logs
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM usuarios 
            WHERE id::text = auth.uid()::text 
            AND tipo = 'admin'
        )
    );
```

### 5. Criar Usuário Admin Inicial

Execute no editor SQL do Supabase:

```sql
-- Inserir usuário admin padrão
INSERT INTO usuarios (
    id,
    username,
    email,
    nome_completo,
    tipo,
    status,
    api_key,
    created_at
) VALUES (
    gen_random_uuid(),
    'admin',
    'admin@gateway.com',
    'Administrador',
    'admin',
    'ativo',
    encode(gen_random_bytes(32), 'hex'),
    NOW()
);
```

## 🏃‍♂️ Executar Aplicação

```bash
python app.py
```

Acesse: http://localhost:5000

## 🔐 Credenciais Padrão

- **Admin**: admin@gateway.com / admin123
- **Seller**: seller@gateway.com / seller123

## 📁 Estrutura do Projeto

```
├── app.py                 # Aplicação principal
├── config/
│   └── supabase.py       # Configuração do Supabase
├── services/
│   ├── auth_service.py   # Serviço de autenticação
│   └── database_service.py # Serviço de banco de dados
├── lib/
│   └── decorators.py     # Decoradores de autenticação
├── templates/            # Templates HTML
├── uploads/             # Arquivos enviados
├── requirements.txt      # Dependências Python
└── env_example.txt      # Exemplo de variáveis de ambiente
```

## 🔧 Funcionalidades Implementadas

### ✅ Autenticação
- Login/Logout com Supabase Auth
- Registro de usuários
- Verificação de status (aprovado/pendente/rejeitado)
- Separação entre admin e seller

### ✅ Dashboard
- Dashboard do admin com estatísticas
- Dashboard do seller com produtos e transações
- Verificação de aprovação

### ✅ Produtos
- Criação de produtos
- Listagem de produtos por usuário
- Marketplace (produtos públicos)

### ✅ KYC
- Salvamento de dados KYC
- Busca de dados KYC existentes
- Aprovação manual pelo admin

### ✅ Admin
- Listagem de usuários pendentes
- Aprovação/rejeição de usuários
- Logs de ações

### ✅ PIX
- Geração de QR Code PIX
- Salvamento de transações

## 🐛 Correções Implementadas

### ✅ Login do Admin
- Autenticação correta com Supabase Auth
- Verificação de role de admin
- Rotas protegidas com decoradores
- Separação de login admin/seller

### ✅ Estrutura Organizada
- Separação em serviços (auth, database)
- Decoradores para autenticação
- Configuração centralizada
- Estrutura escalável

## 📝 Próximos Passos

1. **Configurar Supabase**: Adicione suas credenciais no arquivo `.env`
2. **Criar Tabelas**: Execute os comandos SQL no Supabase
3. **Testar Login**: Verifique se o admin consegue fazer login
4. **Personalizar**: Ajuste as configurações conforme necessário

## 🔍 Verificações

Para verificar se tudo está funcionando:

1. **Teste de Conexão**:
   ```python
   from config.supabase import supabase
   print("Conexão:", supabase.auth.get_user())
   ```

2. **Teste de Login Admin**:
   - Acesse: http://localhost:5000/admin-login
   - Use: admin@gateway.com / admin123

3. **Verificar Tabelas**:
   - Acesse o dashboard do Supabase
   - Verifique se as tabelas foram criadas
   - Confirme se o usuário admin existe

## ⚠️ Observações

- O sistema agora usa **Supabase Auth** em vez de JWT local
- As tabelas são criadas no **Supabase** em vez de SQLite
- A autenticação é mais segura e escalável
- O admin deve ser criado manualmente no Supabase
- Configure as variáveis de ambiente antes de executar

