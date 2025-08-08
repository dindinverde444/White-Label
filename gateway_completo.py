#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gateway de Pagamentos White Label - Sistema Profissional
Com Admin e Seller, KYC, taxas, saques, gamificação e múltiplas adquirentes
"""

import os
import json
import hashlib
import jwt
import sqlite3
import hmac
import requests
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
import qrcode
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Configurações de upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max

# Criar pasta de uploads se não existir
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configuração do banco de dados
DATABASE = 'gateway_pagamentos.db'

class DatabaseManager:
    """Gerenciador do banco de dados"""
    
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Tabela de usuários (Admin e Seller)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'seller', -- 'admin' ou 'seller'
                status TEXT NOT NULL DEFAULT 'pendente', -- 'pendente', 'ativo', 'suspenso'
                api_key TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabela de KYC (Know Your Customer) - Expandida
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kyc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tipo_pessoa TEXT NOT NULL, -- 'PF' ou 'PJ'
                cpf_cnpj TEXT,
                nome_razao_social TEXT,
                porte_juridico TEXT, -- MEI, LTDA, etc
                data_nascimento TEXT,
                telefone TEXT,
                endereco TEXT,
                cidade TEXT,
                estado TEXT,
                cep TEXT,
                
                -- Dados do Responsável (PJ)
                nome_responsavel TEXT,
                cpf_responsavel TEXT,
                nome_mae TEXT,
                data_nascimento_responsavel TEXT,
                
                -- Dados de Atividade
                setor_atividade TEXT,
                faturamento_mensal TEXT,
                
                -- Documentos
                documento_responsavel TEXT, -- caminho do arquivo
                contrato_social TEXT, -- caminho do arquivo (PJ)
                documento_frente TEXT, -- caminho do arquivo
                documento_verso TEXT,
                comprovante_residencia TEXT,
                
                -- Status e Controle
                status TEXT DEFAULT 'pendente', -- 'pendente', 'aprovado', 'rejeitado', 'rascunho'
                observacoes TEXT,
                aprovado_por INTEGER,
                aprovado_em TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (id),
                FOREIGN KEY (aprovado_por) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabela de configurações de taxas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS taxas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tipo_pagamento TEXT NOT NULL, -- 'credito', 'debito', 'pix', 'boleto'
                taxa_percentual REAL DEFAULT 2.99,
                taxa_fixa REAL DEFAULT 0.00,
                ativo BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (id)
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
                payment_method TEXT NOT NULL, -- 'credito', 'debito', 'pix', 'boleto'
                status TEXT NOT NULL, -- 'pendente', 'aprovado', 'rejeitado', 'cancelado'
                customer_name TEXT,
                customer_email TEXT,
                merchant_reference_id TEXT,
                valor REAL NOT NULL,
                taxa_cobrada REAL NOT NULL,
                valor_liquido REAL NOT NULL,
                dados_pagamento TEXT, -- JSON com dados do pagamento
                adquirente TEXT, -- 'stripe', 'paypal', 'mercadopago', etc
                dados_retorno TEXT, -- JSON com retorno da adquirente
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                tipo TEXT NOT NULL, -- 'manual', 'automatico'
                status TEXT NOT NULL, -- 'pendente', 'processado', 'rejeitado'
                dados_pix TEXT, -- JSON com dados PIX
                observacoes TEXT,
                processado_por INTEGER,
                processado_em TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (id),
                FOREIGN KEY (processado_por) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabela de metas de venda
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                meta_valor REAL NOT NULL, -- 100k, 250k, 500k, 1M, 5M
                valor_atual REAL DEFAULT 0.0,
                data_inicio DATE,
                data_fim DATE,
                status TEXT DEFAULT 'ativa', -- 'ativa', 'concluida', 'cancelada'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                thank_page_type TEXT DEFAULT 'default', -- 'default' ou 'custom'
                thank_page_url TEXT,
                support_email TEXT,
                warranty_time INTEGER,
                warranty_unit TEXT,
                product_image TEXT, -- caminho da imagem
                product_banner TEXT,
                final_banner TEXT,
                show_marketplace BOOLEAN DEFAULT 1,
                status TEXT DEFAULT 'ativo', -- 'ativo', 'inativo', 'deletado'
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
        
        # Inserção idempotente para admin (segura contra reloader)
        admin_password = generate_password_hash('admin123')
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (username, email, password_hash, tipo, status, api_key)
            VALUES ('admin', 'admin@gateway.com', ?, 'admin', 'ativo', ?)
        ''', (admin_password, hashlib.sha256(uuid.uuid4().bytes).hexdigest()))

        # Inserção idempotente para seller (segura contra reloader)
        seller_password = generate_password_hash('seller123')
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (username, email, password_hash, tipo, status, api_key)
            VALUES ('seller', 'seller@gateway.com', ?, 'seller', 'ativo', ?)
        ''', (seller_password, hashlib.sha256(uuid.uuid4().bytes).hexdigest()))
        
        # Usuários de teste removidos para trabalhar apenas com dados reais
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Retorna conexão com o banco"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

class SecurityManager:
    """Gerenciador de segurança"""
    
    def __init__(self):
        # Usa segredo persistente para que os tokens continuem válidos após reload
        # Em produção, defina a variável de ambiente JWT_SECRET
        self.secret_key = os.environ.get('JWT_SECRET', 'dev-static-jwt-secret')
    
    def generate_token(self, user_id):
        """Gera token JWT"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        """Verifica token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['user_id']
        except:
            return None
    
    def generate_api_key(self):
        """Gera chave API única"""
        return hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    
    def log_activity(self, user_id, acao, detalhes, ip_address):
        """Registra atividade no log"""
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO logs (user_id, acao, detalhes, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, acao, detalhes, ip_address))
        
        conn.commit()
        conn.close()

class PaymentGateway:
    """Gateway de pagamentos com múltiplas adquirentes"""
    
    def __init__(self):
        self.adquirentes = {
            'stripe': {'taxa': 2.9, 'taxa_fixa': 0.30},
            'paypal': {'taxa': 3.5, 'taxa_fixa': 0.35},
            'mercadopago': {'taxa': 2.99, 'taxa_fixa': 0.00},
            'pix': {'taxa': 0.99, 'taxa_fixa': 0.00}
        }
    
    def processar_pagamento(self, dados, user_id):
        """Processa pagamento com adquirente"""
        try:
            # Simular processamento com adquirente
            adquirente = dados.get('adquirente', 'stripe')
            valor = dados.get('valor', 0.0)
            
            # Calcular taxas
            taxa_config = self.adquirentes.get(adquirente, self.adquirentes['stripe'])
            taxa_valor = (valor * taxa_config['taxa'] / 100) + taxa_config['taxa_fixa']
            valor_liquido = valor - taxa_valor
            
            # Simular resposta da adquirente
            transaction_id = str(uuid.uuid4())
            
            return {
                'status': 'sucesso',
                'transaction_id': transaction_id,
                'valor': valor,
                'taxa_cobrada': taxa_valor,
                'valor_liquido': valor_liquido,
                'adquirente': adquirente,
                'status_pagamento': 'aprovado'
            }
        except Exception as e:
            return {'erro': f'Erro no processamento: {str(e)}'}
    
    def gerar_qr_code_pix(self, dados_pix):
        """Gera QR Code para PIX"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(dados_pix)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            return None

class RapydPayments:
    """Integração com Rapyd Payments API"""
    
    def __init__(self, access_key=None, secret_key=None, sandbox=True):
        self.access_key = access_key or "rak_test_12345"  # Chave de teste padrão
        self.secret_key = secret_key or "rsk_test_67890"  # Chave secreta de teste padrão
        self.base_url = "https://sandboxapi.rapyd.net" if sandbox else "https://api.rapyd.net"
        self.sandbox = sandbox
    
    def _generate_signature(self, method, url_path, salt, timestamp, body=""):
        """Gera assinatura para autenticação Rapyd"""
        try:
            to_sign = method + url_path + salt + str(timestamp) + self.access_key + self.secret_key + body
            signature = base64.b64encode(hmac.new(
                self.secret_key.encode('utf-8'),
                to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()).decode('utf-8')
            return signature
        except Exception as e:
            print(f"Erro ao gerar assinatura: {str(e)}")
            return None
    
    def _make_request(self, method, endpoint, data=None):
        """Faz requisição para API Rapyd"""
        try:
            salt = str(uuid.uuid4())
            timestamp = int(time.time())
            url_path = f"/v1/{endpoint}"
            body = json.dumps(data) if data else ""
            
            signature = self._generate_signature(method, url_path, salt, timestamp, body)
            if not signature:
                return {"success": False, "error": "Erro ao gerar assinatura"}
            
            headers = {
                'Content-Type': 'application/json',
                'access_key': self.access_key,
                'signature': signature,
                'salt': salt,
                'timestamp': str(timestamp)
            }
            
            url = f"{self.base_url}{url_path}"
            
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, data=body)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, data=body)
            else:
                return {"success": False, "error": "Método HTTP não suportado"}
            
            return response.json()
            
        except Exception as e:
            return {"success": False, "error": f"Erro na requisição: {str(e)}"}
    
    def create_pix_payment(self, payment_data):
        """Cria pagamento PIX via Rapyd"""
        try:
            # Dados necessários para PIX
            pix_data = {
                "amount": payment_data.get('amount'),
                "currency": "BRL",
                "payment_method": {
                    "type": "br_pix"
                },
                "customer": {
                    "name": payment_data.get('customer_name'),
                    "email": payment_data.get('customer_email'),
                    "phone_number": payment_data.get('customer_phone', ''),
                    "country": "BR"
                },
                "merchant_reference_id": payment_data.get('merchant_reference_id'),
                "description": payment_data.get('description', 'Pagamento PIX'),
                "complete_payment_url": payment_data.get('complete_payment_url'),
                "cancel_payment_url": payment_data.get('cancel_payment_url')
            }
            
            result = self._make_request('POST', 'payments', pix_data)
            
            if result.get('status', {}).get('status') == 'SUCCESS':
                payment_data = result.get('data', {})
                return {
                    'success': True,
                    'payment_id': payment_data.get('id'),
                    'qr_code': payment_data.get('payment_method_data', {}).get('qr_code'),
                    'qr_code_image': payment_data.get('payment_method_data', {}).get('qr_code_image'),
                    'pix_code': payment_data.get('payment_method_data', {}).get('pix_code'),
                    'status': payment_data.get('status'),
                    'amount': payment_data.get('amount'),
                    'currency': payment_data.get('currency')
                }
            else:
                return {
                    'success': False,
                    'error': result.get('status', {}).get('message', 'Erro desconhecido')
                }
                
        except Exception as e:
            return {"success": False, "error": f"Erro ao criar PIX: {str(e)}"}
    
    def get_payment_status(self, payment_id):
        """Obtém status de um pagamento"""
        return self._make_request('GET', f'payments/{payment_id}')
    
    def get_payment_methods(self, country='BR', currency='BRL'):
        """Lista métodos de pagamento disponíveis"""
        params = {
            'country': country,
            'currency': currency
        }
        return self._make_request('GET', 'payment_methods', params)
    
    def create_customer(self, customer_data):
        """Cria um cliente"""
        return self._make_request('POST', 'customers', customer_data)
    
    def get_countries(self):
        """Lista países suportados"""
        return self._make_request('GET', 'data/countries')
    
    def get_currencies(self):
        """Lista moedas suportadas"""
        return self._make_request('GET', 'data/currencies')

class RapdynPayments:
    """Integração com Rapdyn Payments API"""
    
    def __init__(self, token=None):
        self.token = token or "your_rapdyn_token_here"  # Token padrão
        self.base_url = "https://app.rapdyn.io/api"
    
    def _make_request(self, method, endpoint, data=None):
        """Faz requisição para API Rapdyn"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token}'
            }
            
            url = f"{self.base_url}/{endpoint}"
            
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                return {"success": False, "error": "Método HTTP não suportado"}
            
            # Verificar se a resposta é válida
            if response.status_code == 200:
                try:
                    return {"success": True, "data": response.json()}
                except:
                    return {"success": True, "data": response.text}
            else:
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
            
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Erro de conexão: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Erro na requisição: {str(e)}"}
    
    def test_connection(self):
        """Testa conexão com API Rapdyn"""
        return self._make_request('GET', 'health')
    
    def get_payment_methods(self):
        """Lista métodos de pagamento disponíveis"""
        return self._make_request('GET', 'payment-methods')
    
    def create_payment(self, payment_data):
        """Cria um pagamento"""
        return self._make_request('POST', 'payments', payment_data)
    
    def get_payment(self, payment_id):
        """Obtém detalhes de um pagamento"""
        return self._make_request('GET', f'payments/{payment_id}')
    
    def list_payments(self, filters=None):
        """Lista pagamentos com filtros opcionais"""
        return self._make_request('GET', 'payments', filters)
    
    def cancel_payment(self, payment_id):
        """Cancela um pagamento"""
        return self._make_request('DELETE', f'payments/{payment_id}')
    
    def create_customer(self, customer_data):
        """Cria um cliente"""
        return self._make_request('POST', 'customers', customer_data)
    
    def get_customer(self, customer_id):
        """Obtém dados de um cliente"""
        return self._make_request('GET', f'customers/{customer_id}')
    
    def update_customer(self, customer_id, customer_data):
        """Atualiza dados de um cliente"""
        return self._make_request('PUT', f'customers/{customer_id}', customer_data)
    
    def get_webhook_config(self):
        """Obtém configuração do webhook"""
        return self._make_request('GET', 'webhooks')
    
    def set_webhook_config(self, webhook_data):
        """Configura webhook"""
        return self._make_request('POST', 'webhooks', webhook_data)

class GatewayPagamentos:
    """Gateway principal com todas as funcionalidades"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.security = SecurityManager()
        self.payment = PaymentGateway()
        self.rapdyn = RapdynPayments()  # Integração Rapdyn
    
    def registrar_usuario(self, username, email, password, tipo='seller'):
        """Registra novo usuário"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(password)
            api_key = self.security.generate_api_key()
            
            cursor.execute('''
                INSERT INTO usuarios (username, email, password_hash, tipo, api_key)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, tipo, api_key))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'status': 'sucesso',
                'user_id': user_id,
                'api_key': api_key,
                'mensagem': 'Usuário registrado com sucesso'
            }
        except sqlite3.IntegrityError:
            return {'erro': 'Usuário ou email já existe'}
        except Exception as e:
            return {'erro': f'Erro ao registrar: {str(e)}'}
    
    def autenticar_usuario(self, username, password):
        """Autentica usuário"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password_hash, api_key, tipo, status
                FROM usuarios WHERE username = ? AND is_active = 1
            ''', (username,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user and check_password_hash(user[2], password):  # user[2] = password_hash
                if user[5] != 'ativo':  # user[5] = status
                    return {'erro': 'Conta não está ativa'}
                
                token = self.security.generate_token(user[0])  # user[0] = id
                return {
                    'status': 'sucesso',
                    'token': token,
                    'user_id': user[0],
                    'username': user[1],
                    'tipo': user[4],
                    'api_key': user[3]
                }
            else:
                return {'erro': 'Credenciais inválidas'}
        except Exception as e:
            return {'erro': f'Erro na autenticação: {str(e)}'}
    
    def processar_pagamento(self, dados, user_id, ip_address):
        """Processa pagamento"""
        try:
            # Validar dados
            if not dados or 'valor' not in dados or 'tipo_pagamento' not in dados:
                return {'erro': 'Dados inválidos'}
            
            # Processar pagamento
            resultado = self.payment.processar_pagamento(dados, user_id)
            
            if resultado.get('status') == 'sucesso':
                # Registrar transação
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO transacoes (transaction_id, user_id, tipo_pagamento, valor, 
                    taxa_cobrada, valor_liquido, status, dados_pagamento, adquirente, dados_retorno)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    resultado['transaction_id'],
                    user_id,
                    dados['tipo_pagamento'],
                    resultado['valor'],
                    resultado['taxa_cobrada'],
                    resultado['valor_liquido'],
                    'aprovado',
                    json.dumps(dados),
                    resultado['adquirente'],
                    json.dumps(resultado)
                ))
                
                conn.commit()
                conn.close()
                
                # Log da atividade
                self.security.log_activity(
                    user_id, 
                    'pagamento_processado', 
                    f'Valor: R$ {resultado["valor"]:.2f}, Tipo: {dados["tipo_pagamento"]}',
                    ip_address
                )
            
            return resultado
            
        except Exception as e:
            return {'erro': f'Erro interno: {str(e)}'}
    
    def obter_dashboard_seller(self, user_id):
        """Obtém dados do dashboard do seller"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Vendas do dia
            hoje = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) as total, SUM(valor) as valor_total
                FROM transacoes 
                WHERE user_id = ? AND DATE(created_at) = ? AND status = 'aprovado'
            ''', (user_id, hoje))
            vendas_dia = cursor.fetchone()
            
            # Vendas do mês
            mes_atual = datetime.now().strftime('%Y-%m')
            cursor.execute('''
                SELECT COUNT(*) as total, SUM(valor) as valor_total
                FROM transacoes 
                WHERE user_id = ? AND strftime('%Y-%m', created_at) = ? AND status = 'aprovado'
            ''', (user_id, mes_atual))
            vendas_mes = cursor.fetchone()
            
            # Saldo atual
            cursor.execute('''
                SELECT COALESCE(SUM(valor_liquido), 0) as saldo
                FROM transacoes 
                WHERE user_id = ? AND status = 'aprovado'
            ''', (user_id,))
            saldo = cursor.fetchone()
            
            # Últimas transações
            cursor.execute('''
                SELECT * FROM transacoes 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 10
            ''', (user_id,))
            transacoes = cursor.fetchall()
            
            # Metas ativas
            cursor.execute('''
                SELECT * FROM metas 
                WHERE user_id = ? AND status = 'ativa'
                ORDER BY meta_valor ASC
            ''', (user_id,))
            metas = cursor.fetchall()
            
            conn.close()
            
            return {
                'vendas_dia': {
                    'total': vendas_dia[0] or 0,
                    'valor': vendas_dia[1] or 0.0
                },
                'vendas_mes': {
                    'total': vendas_mes[0] or 0,
                    'valor': vendas_mes[1] or 0.0
                },
                'saldo_atual': saldo[0] or 0.0,
                'transacoes': [dict(zip([col[0] for col in cursor.description], t)) for t in transacoes],
                'metas': [dict(zip([col[0] for col in cursor.description], m)) for m in metas]
            }
        except Exception as e:
            return {'erro': f'Erro ao obter dashboard: {str(e)}'}
    
    def obter_dashboard_admin(self):
        """Obtém dados do dashboard do admin"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Total de sellers
            cursor.execute('SELECT COUNT(*) as total FROM usuarios WHERE tipo = "seller"')
            total_sellers = cursor.fetchone()
            
            # Sellers pendentes
            cursor.execute('SELECT COUNT(*) as total FROM usuarios WHERE tipo = "seller" AND status = "pendente"')
            sellers_pendentes = cursor.fetchone()
            
            # KYC pendentes
            cursor.execute('SELECT COUNT(*) as total FROM kyc WHERE status = "pendente"')
            kyc_pendentes = cursor.fetchone()
            
            # Transações hoje
            hoje = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) as total, SUM(valor) as valor_total
                FROM transacoes 
                WHERE DATE(created_at) = ? AND status = 'aprovado'
            ''', (hoje,))
            transacoes_hoje = cursor.fetchone()
            
            # Saques pendentes
            cursor.execute('SELECT COUNT(*) as total FROM saques WHERE status = "pendente"')
            saques_pendentes = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_sellers': total_sellers[0] or 0,
                'sellers_pendentes': sellers_pendentes[0] or 0,
                'kyc_pendentes': kyc_pendentes[0] or 0,
                'transacoes_hoje': {
                    'total': transacoes_hoje[0] or 0,
                    'valor': transacoes_hoje[1] or 0.0
                },
                'saques_pendentes': saques_pendentes[0] or 0
            }
        except Exception as e:
            return {'erro': f'Erro ao obter dashboard admin: {str(e)}'}

# Instância global
gateway = GatewayPagamentos()

# Middleware de autenticação
def require_auth(f):
    """Decorator para autenticação"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401
        
        user_id = gateway.security.verify_token(token.replace('Bearer ', ''))
        if not user_id:
            return jsonify({'erro': 'Token inválido'}), 401
        
        request.user_id = user_id
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Middleware para admin
def require_admin(f):
    """Decorator para verificar se é admin"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'erro': 'Token não fornecido'}), 401
        
        user_id = gateway.security.verify_token(token.replace('Bearer ', ''))
        if not user_id:
            return jsonify({'erro': 'Token inválido'}), 401
        
        # Verificar se é admin
        conn = gateway.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT tipo FROM usuarios WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or user[0] != 'admin':
            return jsonify({'erro': 'Acesso negado'}), 403
        
        request.user_id = user_id
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Funções auxiliares para PIX local
def create_local_pix_payment(payment_data):
    """Cria pagamento PIX local para demonstração"""
    try:
        # Gerar dados PIX simulados
        payment_id = f"pix_{uuid.uuid4().hex[:8]}"
        qr_code = f"00020126580014br.gov.bcb.pix0136{payment_id}520400005303986540510.005802BR5913Teste Empresa6008Brasilia62070503***6304"
        
        # Gerar QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code)
        qr.make(fit=True)
        
        # Criar imagem do QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_image = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'success': True,
            'payment_id': payment_id,
            'qr_code': qr_code,
            'qr_code_image': f"data:image/png;base64,{qr_code_image}",
            'pix_code': qr_code,
            'status': 'pending',
            'amount': payment_data.get('amount'),
            'currency': 'BRL'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Erro ao criar PIX local: {str(e)}'
        }

def get_local_pix_status(payment_id):
    """Obtém status do PIX local"""
    try:
        # Simular verificação de status
        return {
            'success': True,
            'status': {
                'status': 'SUCCESS'
            },
            'data': {
                'id': payment_id,
                'status': 'pending',
                'amount': 0,
                'currency': 'BRL'
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Erro ao verificar status: {str(e)}'
        }

# Funções auxiliares para upload
def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, prefix=''):
    """Salva arquivo enviado e retorna o caminho"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Adicionar timestamp para evitar conflitos
        timestamp = str(int(datetime.now().timestamp()))
        name, ext = os.path.splitext(filename)
        new_filename = f"{prefix}_{timestamp}_{name}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        file.save(file_path)
        return new_filename
    return None

# Rotas da API
@app.route('/api/registrar', methods=['POST'])
def registrar():
    """Registra novo usuário com dados KYC iniciais"""
    try:
        dados = request.json
        
        # Validar campos obrigatórios
        required_fields = ['username', 'email', 'password', 'nome_completo', 'telefone', 'tipo_conta']
        for field in required_fields:
            if not dados.get(field):
                return jsonify({'success': False, 'message': f'Campo obrigatório não informado: {field}'}), 400
        
        # Validar tipo de conta
        if dados.get('tipo_conta') not in ['PF', 'PJ']:
            return jsonify({'success': False, 'message': 'Tipo de conta deve ser PF ou PJ'}), 400
        
        # Validar campos específicos por tipo
        if dados.get('tipo_conta') == 'PF':
            if not dados.get('cpf'):
                return jsonify({'success': False, 'message': 'CPF é obrigatório para pessoa física'}), 400
        else:  # PJ
            if not dados.get('razao_social') or not dados.get('cnpj') or not dados.get('porte_juridico'):
                return jsonify({'success': False, 'message': 'Razão Social, CNPJ e Porte Jurídico são obrigatórios para pessoa jurídica'}), 400
        
        # Registrar usuário
        resultado = gateway.registrar_usuario(
            dados.get('username'),
            dados.get('email'),
            dados.get('password'),
            'seller'
        )
        
        if resultado.get('status') == 'sucesso':
            # Criar registro KYC inicial
            conn = DatabaseManager().get_connection()
            cursor = conn.cursor()
            
            kyc_data = {
                'user_id': resultado.get('user_id'),
                'tipo_pessoa': dados.get('tipo_conta'),
                'nome_razao_social': dados.get('nome_completo') if dados.get('tipo_conta') == 'PF' else dados.get('razao_social'),
                'cpf_cnpj': dados.get('cpf') if dados.get('tipo_conta') == 'PF' else dados.get('cnpj'),
                'porte_juridico': dados.get('porte_juridico') if dados.get('tipo_conta') == 'PJ' else None,
                'telefone': dados.get('telefone'),
                'status': 'pendente_aprovacao'
            }
            
            cursor.execute('''
                INSERT INTO kyc (
                    user_id, tipo_pessoa, nome_razao_social, cpf_cnpj, 
                    porte_juridico, telefone, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                kyc_data['user_id'],
                kyc_data['tipo_pessoa'],
                kyc_data['nome_razao_social'],
                kyc_data['cpf_cnpj'],
                kyc_data['porte_juridico'],
                kyc_data['telefone'],
                kyc_data['status']
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Usuário registrado com sucesso. Complete seu cadastro KYC.',
                'user_id': resultado.get('user_id'),
                'kyc_status': 'pendente_aprovacao'
            })
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao registrar: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Autentica usuário"""
    dados = request.json
    resultado = gateway.autenticar_usuario(
        dados.get('username'),
        dados.get('password')
    )
    return jsonify(resultado)

@app.route('/api/pagamento', methods=['POST'])
@require_auth
def processar_pagamento():
    """Processa pagamento"""
    dados = request.json
    resultado = gateway.processar_pagamento(
        dados, 
        request.user_id,
        request.remote_addr
    )
    return jsonify(resultado)

@app.route('/api/pix/create', methods=['POST'])
def create_pix_payment():
    """Cria pagamento PIX via Rapyd"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['amount', 'customer_name', 'customer_email', 'product_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'error': f'Campo obrigatório não informado: {field}'
                }), 400
        
        # Gerar ID único para referência
        merchant_reference_id = f"pix_{uuid.uuid4().hex[:8]}"
        
        # Preparar dados para Rapyd
        payment_data = {
            'amount': data.get('amount'),
            'customer_name': data.get('customer_name'),
            'customer_email': data.get('customer_email'),
            'customer_phone': data.get('customer_phone', ''),
            'merchant_reference_id': merchant_reference_id,
            'description': f"Pagamento PIX - {data.get('product_name', 'Produto')}",
            'complete_payment_url': f"{request.host_url}payment/success",
            'cancel_payment_url': f"{request.host_url}payment/cancel"
        }
        
        # Criar pagamento PIX local
        result = create_local_pix_payment(payment_data)
        
        if result.get('success'):
            # Salvar transação no banco
            conn = gateway.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transacoes (
                    payment_id, transaction_id, user_id, product_id, amount, currency, 
                    payment_method, status, customer_name, customer_email,
                    merchant_reference_id, valor, taxa_cobrada, valor_liquido,
                    dados_pagamento, adquirente, dados_retorno, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.get('payment_id'),
                merchant_reference_id,  # transaction_id
                data.get('user_id', 1),  # Default seller
                data.get('product_id'),
                result.get('amount'),
                result.get('currency', 'BRL'),
                'pix',
                result.get('status', 'pending'),
                data.get('customer_name'),
                data.get('customer_email'),
                merchant_reference_id,
                result.get('amount'),
                0.0,  # taxa_cobrada
                result.get('amount'),  # valor_liquido
                json.dumps(data),
                'local',
                json.dumps(result),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'payment_id': result.get('payment_id'),
                'qr_code': result.get('qr_code'),
                'qr_code_image': result.get('qr_code_image'),
                'pix_code': result.get('pix_code'),
                'status': result.get('status'),
                'amount': result.get('amount'),
                'currency': result.get('currency'),
                'merchant_reference_id': merchant_reference_id
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erro desconhecido ao criar PIX')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/api/pix/status/<payment_id>', methods=['GET'])
def get_pix_status(payment_id):
    """Verifica status do pagamento PIX"""
    try:
        # Verificar no banco de dados primeiro
        conn = gateway.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, amount, currency, customer_name, created_at 
            FROM transacoes 
            WHERE payment_id = ?
        ''', (payment_id,))
        
        transaction = cursor.fetchone()
        conn.close()
        
        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Pagamento não encontrado'
            }), 404
        
        # Verificar status atualizado localmente
        local_status = get_local_pix_status(payment_id)
        
        if local_status.get('status', {}).get('status') == 'SUCCESS':
            payment_data = local_status.get('data', {})
            current_status = payment_data.get('status', 'pending')
            
            # Atualizar status no banco se mudou
            if current_status != transaction[0]:
                conn = gateway.db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE transacoes 
                    SET status = ? 
                    WHERE payment_id = ?
                ''', (current_status, payment_id))
                conn.commit()
                conn.close()
            
            return jsonify({
                'success': True,
                'payment_id': payment_id,
                'status': current_status,
                'amount': transaction[1],
                'currency': transaction[2],
                'customer_name': transaction[3],
                'created_at': transaction[4],
                'is_paid': current_status == 'CLOSED'
            })
        else:
            return jsonify({
                'success': True,
                'payment_id': payment_id,
                'status': transaction[0],
                'amount': transaction[1],
                'currency': transaction[2],
                'customer_name': transaction[3],
                'created_at': transaction[4],
                'is_paid': transaction[0] == 'CLOSED'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao verificar status: {str(e)}'
        }), 500

@app.route('/api/dashboard/seller')
@require_auth
def dashboard_seller():
    """Dashboard do seller"""
    resultado = gateway.obter_dashboard_seller(request.user_id)
    return jsonify(resultado)

@app.route('/api/dashboard/admin')
@require_admin
def dashboard_admin():
    """Dashboard do admin"""
    resultado = gateway.obter_dashboard_admin()
    return jsonify(resultado)

@app.route('/api/adquirentes')
def adquirentes():
    """Lista adquirentes disponíveis"""
    return jsonify(gateway.payment.adquirentes)

@app.route('/api/products', methods=['POST'])
@require_auth
def create_product():
    """Cria novo produto"""
    try:
        # Gerar ID único do produto
        product_id = f"prod_{uuid.uuid4().hex[:8]}"
        
        # Processar uploads de imagens
        product_image = None
        product_banner = None
        final_banner = None
        
        if 'product_image' in request.files:
            product_image = save_uploaded_file(request.files['product_image'], 'product')
        
        if 'product_banner' in request.files:
            product_banner = save_uploaded_file(request.files['product_banner'], 'banner')
            
        if 'final_banner' in request.files:
            final_banner = save_uploaded_file(request.files['final_banner'], 'final')
        
        # Validar campos obrigatórios
        name = request.form.get('name')
        price = request.form.get('price')
        header = request.form.get('header')
        
        if not all([name, price, header]):
            return jsonify({'success': False, 'message': 'Campos obrigatórios: nome, preço e cabeçalho'}), 400
        
        if not product_image:
            return jsonify({'success': False, 'message': 'Imagem do produto é obrigatória'}), 400
        
        # Salvar no banco de dados
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO produtos (
                product_id, user_id, name, price, header, thank_page_type, 
                thank_page_url, support_email, warranty_time, warranty_unit,
                product_image, product_banner, final_banner, show_marketplace
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_id,
            request.user_id,
            name,
            float(price),
            header,
            request.form.get('thank_page_type', 'default'),
            request.form.get('thank_page_url'),
            request.form.get('support_email'),
            int(request.form.get('warranty_time', 0)) if request.form.get('warranty_time') else None,
            request.form.get('warranty_unit'),
            product_image,
            product_banner,
            final_banner,
            request.form.get('show_marketplace') == 'true'
        ))
        
        conn.commit()
        conn.close()
        
        # Log da ação (implementar depois se necessário)
        # gateway.adicionar_log(request.user_id, f"Produto criado: {name}", request.remote_addr)
        
        checkout_url = f"{request.host_url}checkout/{product_id}"
        
        return jsonify({
            'success': True,
            'message': 'Produto criado com sucesso',
            'product_id': product_id,
            'checkout_url': checkout_url
        })
        
    except Exception as e:
        print(f"Erro ao criar produto: {str(e)}")  # Log para debug
        return jsonify({'success': False, 'message': f'Erro ao criar produto: {str(e)}'}), 500

@app.route('/api/products', methods=['GET'])
@require_auth
def list_products():
    """Lista produtos do usuário"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT product_id, name, price, header, status, show_marketplace, 
                   views, sales, created_at
            FROM produtos 
            WHERE user_id = ? AND status != 'deletado'
            ORDER BY created_at DESC
        ''', (request.user_id,))
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'product_id': row[0],
                'name': row[1],
                'price': row[2],
                'header': row[3],
                'status': row[4],
                'show_marketplace': bool(row[5]),
                'views': row[6],
                'sales': row[7],
                'created_at': row[8],
                'checkout_url': f"{request.host_url}checkout/{row[0]}"
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'products': products
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao listar produtos: {str(e)}'}), 500

@app.route('/api/marketplace', methods=['GET'])
def marketplace():
    """Lista produtos do marketplace"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.product_id, p.name, p.price, p.header, p.product_image,
                   p.views, p.sales, p.created_at, u.username as seller_name
            FROM produtos p
            JOIN usuarios u ON p.user_id = u.id
            WHERE p.show_marketplace = 1 AND p.status = 'ativo'
            ORDER BY p.created_at DESC
        ''')
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'product_id': row[0],
                'name': row[1],
                'price': row[2],
                'header': row[3],
                'product_image': row[4],
                'views': row[5],
                'sales': row[6],
                'seller_name': row[8],
                'created_at': row[7],
                'checkout_url': f"{request.host_url}checkout/{row[0]}"
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'products': products
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao carregar marketplace: {str(e)}'}), 500

# APIs do Admin
@app.route('/api/admin/pending-users', methods=['GET'])
@require_auth
@require_admin
def get_pending_users():
    """Lista usuários pendentes de aprovação"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, tipo, created_at, status 
            FROM usuarios 
            WHERE status IN ('pendente', 'pendente_aprovacao')
            ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'tipo': row[3],
                'created_at': row[4],
                'status': row[5]
            })
        
        conn.close()
        return jsonify({'success': True, 'users': users})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar usuários: {str(e)}'}), 500

@app.route('/api/admin/approve-user', methods=['POST'])
@require_auth
@require_admin
def approve_user():
    """Aprova um usuário pendente"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'ID do usuário é obrigatório'}), 400
        
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Verificar se o usuário existe e está pendente
        cursor.execute('SELECT username, email, tipo FROM usuarios WHERE id = ? AND status IN ("pendente", "pendente_aprovacao")', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado ou já aprovado'}), 404
        
        # Aprovar usuário
        cursor.execute('UPDATE usuarios SET status = "ativo" WHERE id = ?', (user_id,))
        
        # Registrar log de aprovação
        cursor.execute('''
            INSERT INTO logs (user_id, acao, detalhes, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (request.user_id, 'aprovar_usuario', f'Aprovou usuário {user[0]} (ID: {user_id})', request.remote_addr))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Usuário {user[0]} aprovado com sucesso',
            'user': {
                'username': user[0],
                'email': user[1],
                'tipo': user[2]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao aprovar usuário: {str(e)}'}), 500

@app.route('/api/admin/reject-user', methods=['POST'])
@require_auth
@require_admin
def reject_user():
    """Rejeita um usuário pendente"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'ID do usuário é obrigatório'}), 400
        
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Verificar se o usuário existe e está pendente
        cursor.execute('SELECT username FROM usuarios WHERE id = ? AND status IN ("pendente", "pendente_aprovacao")', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado ou já processado'}), 404
        
        # Rejeitar usuário
        cursor.execute('UPDATE usuarios SET status = "rejeitado" WHERE id = ?', (user_id,))
        
        # Registrar log de rejeição
        cursor.execute('''
            INSERT INTO logs (user_id, acao, detalhes, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (request.user_id, 'rejeitar_usuario', f'Rejeitou usuário {user[0]} (ID: {user_id})', request.remote_addr))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Usuário {user[0]} rejeitado'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao rejeitar usuário: {str(e)}'}), 500

@app.route('/api/admin/archived-users', methods=['GET'])
@require_auth
@require_admin
def get_archived_users():
    """Lista usuários arquivados (rejeitados)"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, tipo, created_at, status 
            FROM usuarios 
            WHERE status = 'rejeitado'
            ORDER BY created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'tipo': row[3],
                'created_at': row[4],
                'status': row[5]
            })
        
        conn.close()
        return jsonify({'success': True, 'users': users})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar usuários arquivados: {str(e)}'}), 500

@app.route('/api/admin/delete-user', methods=['POST'])
@require_auth
@require_admin
def delete_user():
    """Exclui definitivamente um usuário arquivado"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'ID do usuário é obrigatório'}), 400
        
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Verificar se o usuário existe e está rejeitado
        cursor.execute('SELECT username FROM usuarios WHERE id = ? AND status = "rejeitado"', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado ou não está arquivado'}), 404
        
        # Excluir usuário e dados relacionados
        cursor.execute('DELETE FROM kyc WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM logs WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
        
        # Registrar log de exclusão
        cursor.execute('''
            INSERT INTO logs (user_id, acao, detalhes, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (request.user_id, 'excluir_usuario', f'Excluiu usuário {user[0]} (ID: {user_id})', request.remote_addr))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Usuário {user[0]} excluído definitivamente'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao excluir usuário: {str(e)}'}), 500

@app.route('/api/admin/user-details/<int:user_id>', methods=['GET'])
@require_auth
@require_admin
def get_user_details(user_id):
    """Obtém detalhes completos de um usuário para aprovação"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Dados do usuário
        cursor.execute('''
            SELECT id, username, email, tipo, status, created_at
            FROM usuarios 
            WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
        
        # Dados do KYC
        cursor.execute('''
            SELECT *
            FROM kyc 
            WHERE user_id = ?
        ''', (user_id,))
        
        kyc = cursor.fetchone()
        
        # Logs do usuário
        cursor.execute('''
            SELECT acao, detalhes, created_at
            FROM logs 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (user_id,))
        
        logs = cursor.fetchall()
        
        conn.close()
        
        user_details = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'tipo': user[3],
            'status': user[4],
            'created_at': user[5],
            'kyc': kyc,
            'logs': [{'acao': log[0], 'detalhes': log[1], 'created_at': log[2]} for log in logs]
        }
        
        return jsonify({
            'success': True,
            'user': user_details
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao obter detalhes: {str(e)}'}), 500

# APIs para Gerenciamento de Empresas e KYC
@app.route('/api/admin/empresas', methods=['GET'])
@require_auth
@require_admin
def get_empresas():
    """Lista todas as empresas cadastradas"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                u.id,
                u.username,
                u.email,
                u.status,
                u.created_at,
                COALESCE(k.tipo_pessoa, 'Não informado') as tipo_pessoa,
                COALESCE(k.nome_razao_social, 'Não informado') as nome_razao_social,
                COALESCE(k.cpf_cnpj, 'Não informado') as cpf_cnpj,
                COALESCE(k.porte_juridico, 'Não aplicável') as porte_juridico,
                COALESCE(k.setor_atividade, 'Não informado') as setor_atividade,
                COALESCE(k.faturamento_mensal, 'Não informado') as faturamento_mensal,
                COALESCE(k.status, 'pendente') as kyc_status,
                COALESCE(k.created_at, u.created_at) as kyc_created_at,
                CASE 
                    WHEN k.status = 'aprovado' THEN 'Aprovado'
                    WHEN k.status = 'rejeitado' THEN 'Rejeitado'
                    WHEN k.status = 'rascunho' THEN 'Rascunho'
                    WHEN k.status = 'pendente' THEN 'Pendente'
                    ELSE 'Pendente'
                END as status_kyc_display
            FROM usuarios u
            LEFT JOIN kyc k ON u.id = k.user_id
            WHERE u.tipo = 'seller'
            ORDER BY u.created_at DESC
        ''')
        
        empresas = []
        for row in cursor.fetchall():
            empresas.append({
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'status': row[3],
                'created_at': row[4],
                'tipo_pessoa': row[5],
                'nome_razao_social': row[6],
                'cpf_cnpj': row[7],
                'porte_juridico': row[8],
                'setor_atividade': row[9],
                'faturamento_mensal': row[10],
                'kyc_status': row[11],
                'kyc_created_at': row[12],
                'status_kyc_display': row[13]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'empresas': empresas,
            'total': len(empresas)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao listar empresas: {str(e)}'}), 500

@app.route('/api/admin/empresa/<int:user_id>', methods=['GET'])
@require_auth
@require_admin
def get_empresa_detalhes(user_id):
    """Obtém detalhes completos de uma empresa"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Dados do usuário
        cursor.execute('''
            SELECT id, username, email, status, created_at
            FROM usuarios 
            WHERE id = ? AND tipo = 'seller'
        ''', (user_id,))
        
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        
        # Dados do KYC
        cursor.execute('''
            SELECT *
            FROM kyc 
            WHERE user_id = ?
        ''', (user_id,))
        
        kyc = cursor.fetchone()
        
        conn.close()
        
        empresa = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'status': user[3],
            'created_at': user[4],
            'kyc': kyc
        }
        
        return jsonify({
            'success': True,
            'empresa': empresa
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao obter detalhes: {str(e)}'}), 500

@app.route('/api/kyc/save', methods=['POST'])
@require_auth
def save_kyc():
    """Salva dados KYC (rascunho ou final)"""
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios baseado no tipo de pessoa
        if data.get('tipo_pessoa') == 'PF':
            required_fields = ['nome_responsavel', 'cpf_responsavel', 'nome_mae', 'data_nascimento_responsavel']
        else:  # PJ
            required_fields = ['nome_responsavel', 'cpf_responsavel', 'nome_mae', 'data_nascimento_responsavel', 'setor_atividade', 'faturamento_mensal']
            
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Campo obrigatório não informado: {field}'}), 400
        
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Verificar se já existe KYC para este usuário
        cursor.execute('SELECT id FROM kyc WHERE user_id = ?', (request.user_id,))
        existing_kyc = cursor.fetchone()
        
        if existing_kyc:
            # Atualizar KYC existente
            cursor.execute('''
                UPDATE kyc SET
                    nome_responsavel = ?,
                    cpf_responsavel = ?,
                    nome_mae = ?,
                    data_nascimento_responsavel = ?,
                    setor_atividade = ?,
                    faturamento_mensal = ?,
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                data.get('nome_responsavel'),
                data.get('cpf_responsavel'),
                data.get('nome_mae'),
                data.get('data_nascimento_responsavel'),
                data.get('setor_atividade'),
                data.get('faturamento_mensal'),
                                           data.get('status', 'pendente_aprovacao'),
                request.user_id
            ))
        else:
            # Criar novo KYC
            cursor.execute('''
                INSERT INTO kyc (
                    user_id, tipo_pessoa, cpf_cnpj, nome_razao_social, porte_juridico,
                    nome_responsavel, cpf_responsavel, nome_mae, data_nascimento_responsavel,
                    setor_atividade, faturamento_mensal, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.user_id,
                data.get('tipo_pessoa'),
                data.get('cpf_cnpj'),
                data.get('nome_razao_social'),
                data.get('porte_juridico'),
                data.get('nome_responsavel'),
                data.get('cpf_responsavel'),
                data.get('nome_mae'),
                data.get('data_nascimento_responsavel'),
                data.get('setor_atividade'),
                data.get('faturamento_mensal'),
                                     data.get('status', 'pendente_aprovacao')
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Dados KYC salvos com sucesso'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao salvar KYC: {str(e)}'}), 500

@app.route('/api/kyc/complete', methods=['GET'])
@require_auth
def get_kyc_complete():
    """Obtém dados KYC para completar cadastro"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT tipo_pessoa, nome_razao_social, cpf_cnpj, porte_juridico,
                   nome_responsavel, cpf_responsavel, nome_mae, data_nascimento_responsavel,
                   setor_atividade, faturamento_mensal, status
            FROM kyc 
            WHERE user_id = ?
        ''', (request.user_id,))
        
        kyc = cursor.fetchone()
        conn.close()
        
        if kyc:
            return jsonify({
                'success': True,
                'kyc': {
                    'tipo_pessoa': kyc[0],
                    'nome_razao_social': kyc[1],
                    'cpf_cnpj': kyc[2],
                    'porte_juridico': kyc[3],
                    'nome_responsavel': kyc[4],
                    'cpf_responsavel': kyc[5],
                    'nome_mae': kyc[6],
                    'data_nascimento_responsavel': kyc[7],
                    'setor_atividade': kyc[8],
                    'faturamento_mensal': kyc[9],
                    'status': kyc[10]
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Dados KYC não encontrados'
            }), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao obter dados KYC: {str(e)}'}), 500

@app.route('/api/kyc/upload', methods=['POST'])
@require_auth
def upload_kyc_document():
    """Upload de documentos KYC"""
    try:
        if 'document' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['document']
        document_type = request.form.get('document_type')  # 'responsavel', 'contrato_social', etc.
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        if file and allowed_file(file.filename):
            filename = save_uploaded_file(file, f'kyc_{document_type}')
            
            # Atualizar banco de dados
            conn = DatabaseManager().get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f'''
                UPDATE kyc 
                SET {document_type} = ?
                WHERE user_id = ?
            ''', (filename, request.user_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Documento enviado com sucesso',
                'filename': filename
            })
        else:
            return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao enviar documento: {str(e)}'}), 500

@app.route('/api/user/status', methods=['GET'])
@require_auth
def get_user_status():
    """Obtém status do usuário para controle de acesso"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, tipo
            FROM usuarios 
            WHERE id = ?
        ''', (request.user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'success': True,
                'status': user[0],
                'tipo': user[1],
                'is_approved': user[0] == 'ativo',
                'is_pending': user[0] in ['pendente', 'pendente_aprovacao'],
                'is_rejected': user[0] == 'rejeitado'
            })
        else:
            return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao obter status: {str(e)}'}), 500

@app.route('/api/kyc/status', methods=['GET'])
@require_auth
def get_kyc_status():
    """Obtém status do KYC do usuário"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, tipo_pessoa, nome_razao_social, cpf_cnpj, 
                   nome_responsavel, cpf_responsavel, nome_mae, data_nascimento_responsavel,
                   setor_atividade, faturamento_mensal, porte_juridico,
                   documento_responsavel, contrato_social
            FROM kyc 
            WHERE user_id = ?
        ''', (request.user_id,))
        
        kyc = cursor.fetchone()
        conn.close()
        
        if kyc:
            return jsonify({
                'success': True,
                'kyc': {
                    'status': kyc[0],
                    'tipo_pessoa': kyc[1],
                    'nome_razao_social': kyc[2],
                    'cpf_cnpj': kyc[3],
                    'nome_responsavel': kyc[4],
                    'cpf_responsavel': kyc[5],
                    'nome_mae': kyc[6],
                    'data_nascimento_responsavel': kyc[7],
                    'setor_atividade': kyc[8],
                    'faturamento_mensal': kyc[9],
                    'porte_juridico': kyc[10],
                    'documento_responsavel': kyc[11],
                    'contrato_social': kyc[12]
                }
            })
        else:
            return jsonify({
                'success': True,
                'kyc': None
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao obter status KYC: {str(e)}'}), 500

# APIs para Aprovação de KYC
@app.route('/api/admin/kyc/pending', methods=['GET'])
@require_auth
@require_admin
def get_pending_kyc():
    """Lista KYC pendentes de aprovação"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                k.id,
                k.user_id,
                u.username,
                u.email,
                k.tipo_pessoa,
                k.nome_razao_social,
                k.cpf_cnpj,
                k.porte_juridico,
                k.nome_responsavel,
                k.cpf_responsavel,
                k.nome_mae,
                k.data_nascimento_responsavel,
                k.setor_atividade,
                k.faturamento_mensal,
                k.documento_responsavel,
                k.contrato_social,
                k.status,
                k.created_at,
                k.updated_at
            FROM kyc k
            JOIN usuarios u ON k.user_id = u.id
            WHERE k.status IN ('pendente', 'rascunho')
            ORDER BY k.created_at ASC
        ''')
        
        pending_kyc = []
        for row in cursor.fetchall():
            pending_kyc.append({
                'id': row[0],
                'user_id': row[1],
                'username': row[2],
                'email': row[3],
                'tipo_pessoa': row[4],
                'nome_razao_social': row[5],
                'cpf_cnpj': row[6],
                'porte_juridico': row[7],
                'nome_responsavel': row[8],
                'cpf_responsavel': row[9],
                'nome_mae': row[10],
                'data_nascimento_responsavel': row[11],
                'setor_atividade': row[12],
                'faturamento_mensal': row[13],
                'documento_responsavel': row[14],
                'contrato_social': row[15],
                'status': row[16],
                'created_at': row[17],
                'updated_at': row[18]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'pending_kyc': pending_kyc,
            'total': len(pending_kyc)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao listar KYC pendentes: {str(e)}'}), 500

@app.route('/api/admin/kyc/approve', methods=['POST'])
@require_auth
@require_admin
def approve_kyc():
    """Aprova KYC de um usuário"""
    try:
        data = request.get_json()
        kyc_id = data.get('kyc_id')
        observacoes = data.get('observacoes', '')
        
        if not kyc_id:
            return jsonify({'success': False, 'message': 'ID do KYC é obrigatório'}), 400
        
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Atualizar status do KYC
        cursor.execute('''
            UPDATE kyc 
            SET status = 'aprovado', 
                aprovado_por = ?, 
                aprovado_em = CURRENT_TIMESTAMP,
                observacoes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (request.user_id, observacoes, kyc_id))
        
        # Atualizar status do usuário
        cursor.execute('''
            UPDATE usuarios 
            SET status = 'ativo'
            WHERE id = (SELECT user_id FROM kyc WHERE id = ?)
        ''', (kyc_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'KYC aprovado com sucesso'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao aprovar KYC: {str(e)}'}), 500

@app.route('/api/admin/kyc/reject', methods=['POST'])
@require_auth
@require_admin
def reject_kyc():
    """Rejeita KYC de um usuário"""
    try:
        data = request.get_json()
        kyc_id = data.get('kyc_id')
        observacoes = data.get('observacoes', '')
        
        if not kyc_id:
            return jsonify({'success': False, 'message': 'ID do KYC é obrigatório'}), 400
        
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Atualizar status do KYC
        cursor.execute('''
            UPDATE kyc 
            SET status = 'rejeitado', 
                aprovado_por = ?, 
                aprovado_em = CURRENT_TIMESTAMP,
                observacoes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (request.user_id, observacoes, kyc_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'KYC rejeitado'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao rejeitar KYC: {str(e)}'}), 500

@app.route('/api/admin/kyc/document/<filename>', methods=['GET'])
@require_auth
@require_admin
def get_kyc_document(filename):
    """Obtém documento KYC para visualização"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'Documento não encontrado'}), 404
        
        # Verificar se é um arquivo PDF
        if filename.endswith('.pdf'):
            return send_file(file_path, mimetype='application/pdf')
        else:
            return send_file(file_path)
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao obter documento: {str(e)}'}), 500

# APIs Rapdyn para Adquirentes
@app.route('/api/admin/rapdyn/payment-methods', methods=['GET'])
@require_auth
@require_admin
def get_rapdyn_payment_methods():
    """Lista métodos de pagamento Rapdyn"""
    try:
        result = gateway.rapdyn.get_payment_methods()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar métodos de pagamento: {str(e)}'}), 500

@app.route('/api/admin/rapdyn/test-connection', methods=['POST'])
@require_auth
@require_admin
def test_rapdyn_connection():
    """Testa conexão com API Rapdyn"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'success': False, 'message': 'Token é obrigatório'}), 400
        
        # Criar instância temporária para teste
        test_rapdyn = RapdynPayments(token)
        result = test_rapdyn.test_connection()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': 'Conexão com Rapdyn realizada com sucesso',
                'data': result.get('data')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Falha na conexão com Rapdyn',
                'error': result.get('error', 'Erro desconhecido')
            })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao testar conexão: {str(e)}'}), 500

@app.route('/api/admin/rapdyn/configure', methods=['POST'])
@require_auth
@require_admin
def configure_rapdyn():
    """Configura token Rapdyn"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'success': False, 'message': 'Token é obrigatório'}), 400
        
        # Atualizar instância global do Rapdyn
        gateway.rapdyn = RapdynPayments(token)
        
        # TODO: Salvar configurações no banco de dados de forma segura
        
        return jsonify({
            'success': True,
            'message': 'Configurações Rapdyn atualizadas com sucesso'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao configurar Rapdyn: {str(e)}'}), 500

@app.route('/api/admin/rapdyn/payments', methods=['GET'])
@require_auth
@require_admin
def get_rapdyn_payments():
    """Lista pagamentos Rapdyn"""
    try:
        filters = request.args.to_dict()
        result = gateway.rapdyn.list_payments(filters)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar pagamentos: {str(e)}'}), 500

@app.route('/api/admin/rapdyn/webhook', methods=['GET'])
@require_auth
@require_admin
def get_rapdyn_webhook():
    """Obtém configuração do webhook Rapdyn"""
    try:
        result = gateway.rapdyn.get_webhook_config()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao buscar webhook: {str(e)}'}), 500

@app.route('/api/admin/rapdyn/webhook', methods=['POST'])
@require_auth
@require_admin
def set_rapdyn_webhook():
    """Configura webhook Rapdyn"""
    try:
        data = request.get_json()
        result = gateway.rapdyn.set_webhook_config(data)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao configurar webhook: {str(e)}'}), 500

# Rotas da interface web
@app.route('/')
def home():
    """Página principal"""
    return render_template('dashboard.html')

@app.route('/login')
def login_page():
    """Página de login"""
    return render_template('login.html')

@app.route('/registro')
def registro_page():
    """Página de registro"""
    return render_template('registro.html')

@app.route('/admin')
def admin_page():
    """Página do admin"""
    return render_template('admin.html')

@app.route('/admin-login')
def admin_login_page():
    """Página de login exclusiva do admin"""
    return render_template('admin_login.html')

@app.route('/seller')
def seller_page():
    """Página do seller"""
    return render_template('seller.html')

@app.route('/checkout/<product_id>')
def checkout_page(product_id):
    """Página de checkout do produto"""
    try:
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Buscar dados do produto
        cursor.execute('''
            SELECT p.*, u.username as seller_name, u.email as seller_email
            FROM produtos p
            JOIN usuarios u ON p.user_id = u.id
            WHERE p.product_id = ? AND p.status = 'ativo'
        ''', (product_id,))
        
        product = cursor.fetchone()
        
        if not product:
            conn.close()
            return render_template('404.html'), 404
        
        # Incrementar visualizações
        cursor.execute('''
            UPDATE produtos SET views = views + 1 
            WHERE product_id = ?
        ''', (product_id,))
        
        conn.commit()
        conn.close()
        
        # Converter para dict para template
        product_data = dict(product)
        
        return render_template('checkout.html', product=product_data)
        
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve arquivos de upload"""
    return app.send_static_file(f'../uploads/{filename}')

@app.route('/payment/success')
def payment_success():
    """Página de sucesso do pagamento"""
    return render_template('payment_success.html')

@app.route('/payment/cancel')
def payment_cancel():
    """Página de cancelamento do pagamento"""
    return render_template('payment_cancel.html')

if __name__ == '__main__':
    gateway = GatewayPagamentos()
    print("🚀 Iniciando Gateway de Pagamentos White Label...")
    print("📊 Banco de dados: SQLite")
    print("🔐 Segurança: JWT + Hash")
    print("👥 Usuários: Admin e Seller")
    print("💳 Pagamentos: Cartão, PIX, Boleto")
    print("🎯 Gamificação: Metas e Premiações")
    print("🌐 Interface: Web Dashboard Responsivo")
    print("📱 Acesse: http://localhost:5000")
    print("👨‍💼 Admin: admin / admin123")
    print("👤 Seller: seller / seller123")
    app.run(debug=True, host='0.0.0.0', port=5000)
