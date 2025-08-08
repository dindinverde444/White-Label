# 🚀 Configuração Rápida - Gateway Supabase

## ⚡ Passos Rápidos

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Supabase
1. Crie um projeto no [Supabase](https://supabase.com)
2. Copie as credenciais:
   - **URL**: https://seu-projeto.supabase.co
   - **Anon Key**: sua-chave-anonima

### 3. Configurar Variáveis de Ambiente
```bash
# Copie o arquivo de exemplo
cp env_example.txt .env

# Edite o arquivo .env com suas credenciais
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anonima
```

### 4. Testar Conexão
```bash
python test_supabase.py
```

### 5. Criar Tabelas no Supabase
Execute no **SQL Editor** do Supabase:

```sql
-- Tabela usuarios
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
    tipo VARCHAR(20) DEFAULT 'seller',
    status VARCHAR(20) DEFAULT 'pendente_aprovacao',
    api_key VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela kyc
CREATE TABLE kyc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    nome_responsavel VARCHAR(255),
    cpf_responsavel VARCHAR(14),
    nome_mae VARCHAR(255),
    data_nascimento DATE,
    setor_atividade TEXT,
    faturamento_mensal TEXT,
    tipo_entidade VARCHAR(10),
    cnpj VARCHAR(18),
    razao_social VARCHAR(255),
    porte_juridico VARCHAR(50),
    documento_responsavel VARCHAR(255),
    contrato_social VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pendente_aprovacao',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela produtos
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

-- Tabela transacoes
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

-- Tabela logs
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    target_user_id UUID REFERENCES usuarios(id),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 6. Criar Usuário Admin
```bash
python create_admin.py
```

### 7. Executar Aplicação
```bash
python app.py
```

### 8. Acessar
- **Admin**: http://localhost:5000/admin-login
- **Seller**: http://localhost:5000/login

## 🔐 Credenciais Padrão
- **Admin**: admin@gateway.com / admin123
- **Seller**: seller@gateway.com / seller123

## ✅ Verificações

### Teste de Conexão
```bash
python test_supabase.py
```

### Teste de Login Admin
1. Acesse: http://localhost:5000/admin-login
2. Use: admin@gateway.com / admin123
3. Deve redirecionar para: http://localhost:5000/admin

## 🐛 Problemas Comuns

### Erro: "Module not found"
```bash
pip install -r requirements.txt
```

### Erro: "Invalid API key"
- Verifique o arquivo `.env`
- Confirme as credenciais do Supabase

### Erro: "Table does not exist"
- Execute os comandos SQL no Supabase
- Verifique se as tabelas foram criadas

### Admin não consegue fazer login
- Execute: `python create_admin.py`
- Verifique se o usuário foi criado no Supabase

## 📞 Suporte
- Verifique o arquivo `README_SUPABASE.md` para documentação completa
- Execute `python test_supabase.py` para diagnóstico

