# 🚀 White Label - Gateway de Pagamentos

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![Supabase](https://img.shields.io/badge/Supabase-2.0.2-purple.svg)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Descrição

**White Label** é um sistema completo de gateway de pagamentos desenvolvido em Python/Flask com integração ao Supabase. O projeto oferece uma solução white label para processamento de pagamentos, incluindo autenticação, dashboard administrativo, KYC, e suporte a múltiplos métodos de pagamento.

## ✨ Funcionalidades

### 🔐 Autenticação e Autorização
- **Supabase Auth** para autenticação segura
- **Sistema de roles**: Admin e Seller
- **Aprovação de usuários** com workflow completo
- **JWT tokens** para sessões seguras

### 💳 Métodos de Pagamento
- **PIX** - Geração de QR Code e pagamentos instantâneos
- **Cartão de Crédito** - Processamento via gateways
- **Boleto Bancário** - Geração e controle de boletos
- **Múltiplos gateways** de pagamento

### 👥 Gestão de Usuários
- **Dashboard Admin** - Aprovação de sellers, relatórios
- **Dashboard Seller** - Gestão de produtos e transações
- **Sistema KYC** - Know Your Customer completo
- **Perfis diferenciados** - CPF e Pessoa Jurídica

### 📊 Analytics e Relatórios
- **Estatísticas em tempo real**
- **Logs de transações**
- **Relatórios de performance**
- **Métricas de conversão**

### 🛡️ Segurança
- **RLS (Row Level Security)** no Supabase
- **Validação de dados** robusta
- **Sanitização de inputs**
- **Rate limiting** e proteção contra ataques

## 🏗️ Arquitetura

```
White Label Gateway/
├── app.py                 # Aplicação principal Flask
├── config/
│   └── supabase.py       # Configuração Supabase
├── services/
│   ├── auth_service.py   # Serviço de autenticação
│   └── database_service.py # Serviço de banco de dados
├── lib/
│   └── decorators.py     # Decoradores de autorização
├── templates/            # Templates HTML
├── uploads/             # Upload de arquivos
└── seller-panel/        # Painel do vendedor (React)
```

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- Node.js 16+ (para o seller-panel)
- Conta no Supabase

### 1. Clone o repositório
```bash
git clone https://github.com/dindinverde444/White-Label.git
cd White-Label
```

### 2. Instale as dependências Python
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
```bash
cp env_example.txt .env
```

Edite o arquivo `.env` com suas credenciais do Supabase:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
FLASK_ENV=development
FLASK_DEBUG=True
```

### 4. Configure o Supabase

#### Criar projeto no Supabase
1. Acesse [supabase.com](https://supabase.com)
2. Crie um novo projeto
3. Copie as credenciais para o arquivo `.env`

#### Configurar tabelas
Execute os seguintes comandos SQL no Supabase SQL Editor:

```sql
-- Tabela de usuários
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    tipo VARCHAR(50) DEFAULT 'seller',
    status VARCHAR(50) DEFAULT 'pendente_aprovacao',
    api_key VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de KYC
CREATE TABLE kyc (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id),
    documento_tipo VARCHAR(50),
    documento_numero VARCHAR(255),
    endereco TEXT,
    status VARCHAR(50) DEFAULT 'pendente',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de produtos
CREATE TABLE produtos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id),
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10,2),
    imagem_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'ativo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de transações
CREATE TABLE transacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id),
    payment_id VARCHAR(255),
    amount DECIMAL(10,2),
    description TEXT,
    status VARCHAR(50),
    payment_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de logs
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES usuarios(id),
    action VARCHAR(100),
    target_user_id UUID,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habilitar RLS
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE kyc ENABLE ROW LEVEL SECURITY;
ALTER TABLE produtos ENABLE ROW LEVEL SECURITY;
ALTER TABLE transacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
```

### 5. Execute a aplicação
```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

## 🔧 Configuração do Seller Panel

### Instalar dependências
```bash
cd seller-panel
npm install
```

### Configurar variáveis de ambiente
Crie um arquivo `.env` na pasta `seller-panel`:
```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
```

### Executar o painel
```bash
npm start
```

## 📚 API Endpoints

### Autenticação
- `POST /api/login` - Login de usuário
- `POST /api/registrar` - Registro de novo usuário
- `POST /api/logout` - Logout

### Dashboard
- `GET /api/dashboard/admin` - Dashboard administrativo
- `GET /api/dashboard/seller` - Dashboard do vendedor

### Produtos
- `GET /api/products` - Listar produtos
- `POST /api/products` - Criar produto

### Pagamentos
- `POST /api/pix/create` - Criar pagamento PIX

### KYC
- `POST /api/kyc/save` - Salvar dados KYC
- `GET /api/kyc/complete` - Buscar dados KYC

### Admin
- `GET /api/admin/pending-users` - Usuários pendentes
- `POST /api/admin/approve-user/<id>` - Aprovar usuário
- `POST /api/admin/reject-user/<id>` - Rejeitar usuário

## 🎯 Casos de Uso

### Para Administradores
1. **Aprovação de Sellers**: Gerenciar solicitações de novos vendedores
2. **Monitoramento**: Acompanhar transações e performance
3. **Relatórios**: Gerar relatórios de vendas e conversão
4. **Configuração**: Definir taxas e configurações do sistema

### Para Vendedores
1. **Cadastro**: Registro com validação KYC
2. **Gestão de Produtos**: Cadastro e edição de produtos
3. **Pagamentos**: Geração de links e QR codes PIX
4. **Dashboard**: Acompanhamento de vendas e receitas

## 🔒 Segurança

- **Autenticação JWT** via Supabase Auth
- **Row Level Security** no banco de dados
- **Validação de inputs** em todas as rotas
- **Rate limiting** para proteção contra ataques
- **Sanitização de dados** antes do processamento

## 🧪 Testes

### Testes Manuais
```bash
# Testar login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Testar criação de PIX
curl -X POST http://localhost:5000/api/pix/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"amount":100.00,"description":"Teste PIX"}'
```

## 📈 Roadmap

- [ ] **Integração com mais gateways** de pagamento
- [ ] **Webhook system** para notificações
- [ ] **Sistema de comissões** automático
- [ ] **API REST** completa para integração
- [ ] **Mobile app** para vendedores
- [ ] **Sistema de notificações** push
- [ ] **Analytics avançados** com gráficos
- [ ] **Multi-tenancy** para white label

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📞 Suporte

- **Email**: suporte@whitelabel.com
- **Documentação**: [docs.whitelabel.com](https://docs.whitelabel.com)
- **Issues**: [GitHub Issues](https://github.com/dindinverde444/White-Label/issues)

## 🙏 Agradecimentos

- [Supabase](https://supabase.com) pela infraestrutura
- [Flask](https://flask.palletsprojects.com/) pelo framework web
- [React](https://reactjs.org/) pelo frontend
- Comunidade open source

---

**White Label Gateway** - Transformando ideias em soluções de pagamento! 💳✨
