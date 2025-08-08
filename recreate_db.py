#!/usr/bin/env python3
import os
import sqlite3

# Remover banco existente
if os.path.exists('gateway_pagamentos.db'):
    os.remove('gateway_pagamentos.db')
    print("Banco de dados removido")

# Recriar banco
conn = sqlite3.connect('gateway_pagamentos.db')
cursor = conn.cursor()

# Tabela de usuários
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        tipo TEXT NOT NULL DEFAULT 'seller',
        status TEXT NOT NULL DEFAULT 'pendente',
        api_key TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
''')

# Tabela de KYC
cursor.execute('''
    CREATE TABLE IF NOT EXISTS kyc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tipo_pessoa TEXT NOT NULL,
        cpf_cnpj TEXT,
        nome_razao_social TEXT,
        porte_juridico TEXT,
        data_nascimento TEXT,
        telefone TEXT,
        endereco TEXT,
        cidade TEXT,
        estado TEXT,
        cep TEXT,
        nome_responsavel TEXT,
        cpf_responsavel TEXT,
        nome_mae TEXT,
        data_nascimento_responsavel TEXT,
        setor_atividade TEXT,
        faturamento_mensal TEXT,
        documento_responsavel TEXT,
        contrato_social TEXT,
        documento_frente TEXT,
        documento_verso TEXT,
        comprovante_residencia TEXT,
        status TEXT DEFAULT 'pendente',
        observacoes TEXT,
        aprovado_por INTEGER,
        aprovado_em TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES usuarios (id),
        FOREIGN KEY (aprovado_por) REFERENCES usuarios (id)
    )
''')

# Tabela de transações
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id TEXT UNIQUE,
        transaction_id TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        product_id TEXT,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'BRL',
        payment_method TEXT NOT NULL,
        status TEXT NOT NULL,
        customer_name TEXT,
        customer_email TEXT,
        merchant_reference_id TEXT,
        valor REAL NOT NULL,
        taxa_cobrada REAL NOT NULL,
        valor_liquido REAL NOT NULL,
        dados_pagamento TEXT,
        adquirente TEXT,
        dados_retorno TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES usuarios (id)
    )
''')

# Tabela de produtos
cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        header TEXT NOT NULL,
        thank_page_type TEXT DEFAULT 'default',
        thank_page_url TEXT,
        support_email TEXT,
        warranty_time INTEGER,
        warranty_unit TEXT,
        product_image TEXT,
        product_banner TEXT,
        final_banner TEXT,
        show_marketplace BOOLEAN DEFAULT 1,
        status TEXT DEFAULT 'ativo',
        views INTEGER DEFAULT 0,
        sales INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES usuarios (id)
    )
''')

# Tabela de logs
cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        acao TEXT NOT NULL,
        detalhes TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES usuarios (id)
    )
''')

# Tabela de taxas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS taxas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tipo_pagamento TEXT NOT NULL,
        taxa_percentual REAL DEFAULT 2.99,
        taxa_fixa REAL DEFAULT 0.00,
        ativo BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES usuarios (id)
    )
''')

# Tabela de saques
cursor.execute('''
    CREATE TABLE IF NOT EXISTS saques (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        valor REAL NOT NULL,
        taxa_saque REAL NOT NULL,
        valor_liquido REAL NOT NULL,
        tipo TEXT NOT NULL,
        status TEXT NOT NULL,
        dados_pix TEXT,
        observacoes TEXT,
        processado_por INTEGER,
        processado_em TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES usuarios (id),
        FOREIGN KEY (processado_por) REFERENCES usuarios (id)
    )
''')

# Tabela de metas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        meta_valor REAL NOT NULL,
        valor_atual REAL DEFAULT 0.0,
        data_inicio DATE,
        data_fim DATE,
        status TEXT DEFAULT 'ativa',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES usuarios (id)
    )
''')

# Inserir admin padrão
cursor.execute('''
    INSERT OR IGNORE INTO usuarios (username, email, password_hash, tipo, status, api_key)
    VALUES (?, ?, ?, ?, ?, ?)
''', ('admin', 'admin@admin.com', 'pbkdf2:sha256:600000$admin123', 'admin', 'ativo', 'admin_key_123'))

conn.commit()
conn.close()

print("Banco de dados recriado com sucesso!")
