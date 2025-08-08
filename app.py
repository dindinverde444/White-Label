from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
from datetime import datetime
import uuid
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import qrcode
import base64
from io import BytesIO

# Importações dos serviços
from services.auth_service import AuthService
from services.database_service import DatabaseService
from lib.decorators import require_auth, require_admin, require_approved_user, get_current_user_id

# Configurações
app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

# Garantir que a pasta uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar serviços
auth_service = AuthService()
db_service = DatabaseService()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Rotas de autenticação
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email e senha são obrigatórios"}), 400
    
    result = auth_service.sign_in(email, password)
    
    if result['success']:
        return jsonify({
            "success": True,
            "token": result['access_token'],
            "user": {
                "id": result['user'].id,
                "email": result['user'].email,
                "tipo": result['user_data'].get('tipo'),
                "status": result['user_data'].get('status')
            }
        })
    else:
        return jsonify({"error": result['message']}), 401

@app.route('/api/registrar', methods=['POST'])
def registrar():
    data = request.get_json()
    
    # Validações básicas
    required_fields = ['email', 'password', 'username', 'nome_completo', 'telefone', 'tipo_conta']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Campo {field} é obrigatório"}), 400
    
    # Validações específicas por tipo de conta
    if data['tipo_conta'] == 'CPF':
        if not data.get('cpf'):
            return jsonify({"error": "CPF é obrigatório para pessoa física"}), 400
    elif data['tipo_conta'] == 'PJ':
        required_pj_fields = ['razao_social', 'cnpj', 'porte_juridico']
        for field in required_pj_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo {field} é obrigatório para pessoa jurídica"}), 400
    
    # Preparar dados do usuário
    user_data = {
        'username': data['username'],
        'email': data['email'],
        'nome_completo': data['nome_completo'],
        'telefone': data['telefone'],
        'tipo_conta': data['tipo_conta'],
        'tipo': 'seller',
        'status': 'pendente_aprovacao',
        'api_key': hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    }
    
    # Adicionar campos específicos
    if data['tipo_conta'] == 'CPF':
        user_data['cpf'] = data['cpf']
    else:
        user_data.update({
            'razao_social': data['razao_social'],
            'cnpj': data['cnpj'],
            'porte_juridico': data['porte_juridico']
        })
    
    # Registrar no Supabase Auth
    result = auth_service.sign_up(data['email'], data['password'], user_data)
    
    if result['success']:
        return jsonify({
            "success": True,
            "message": "Usuário registrado com sucesso. Aguarde aprovação do administrador."
        })
    else:
        return jsonify({"error": result['message']}), 400

@app.route('/api/logout', methods=['POST'])
@require_auth
def logout():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    
    if auth_service.sign_out(token):
        return jsonify({"success": True, "message": "Logout realizado com sucesso"})
    else:
        return jsonify({"error": "Erro ao fazer logout"}), 500

# Rotas do dashboard
@app.route('/api/dashboard/admin')
@require_admin
def dashboard_admin():
    try:
        # Estatísticas básicas
        pending_users = db_service.get_pending_users()
        archived_users = db_service.get_archived_users()
        
        return jsonify({
            "success": True,
            "stats": {
                "pending_users": len(pending_users),
                "archived_users": len(archived_users)
            }
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao carregar dashboard: {str(e)}"}), 500

@app.route('/api/dashboard/seller')
@require_auth
def dashboard_seller():
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # Buscar dados do usuário
        user_data = db_service.get_user_by_id(user_id)
        if not user_data:
            return jsonify({"error": "Usuário não encontrado"}), 404
        
        # Buscar produtos do usuário
        products = db_service.get_products_by_user(user_id)
        
        # Buscar transações do usuário
        transactions = db_service.get_transactions_by_user(user_id)
        
        return jsonify({
            "success": True,
            "user": user_data,
            "products": products,
            "transactions": transactions
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao carregar dashboard: {str(e)}"}), 500

# Rotas de status do usuário
@app.route('/api/user/status')
@require_auth
def user_status():
    try:
        user_data = request.user_data
        user_info = user_data.get('user_data', {})
        
        return jsonify({
            "success": True,
            "is_approved": auth_service.is_approved(user_info),
            "is_pending": user_info.get('status') == 'pendente_aprovacao',
            "is_rejected": user_info.get('status') == 'rejeitado',
            "is_admin": auth_service.is_admin(user_info)
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao verificar status: {str(e)}"}), 500

# Rotas de produtos
@app.route('/api/products', methods=['GET'])
@require_auth
def list_products():
    try:
        user_id = get_current_user_id()
        products = db_service.get_products_by_user(user_id)
        
        return jsonify({
            "success": True,
            "products": products
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao listar produtos: {str(e)}"}), 500

@app.route('/api/products', methods=['POST'])
@require_approved_user
def create_product():
    try:
        data = request.get_json()
        user_id = get_current_user_id()
        
        # Adicionar user_id aos dados do produto
        data['user_id'] = user_id
        
        result = db_service.create_product(data)
        
        if result['success']:
            return jsonify({
                "success": True,
                "product": result['data']
            })
        else:
            return jsonify({"error": result['error']}), 400
    except Exception as e:
        return jsonify({"error": f"Erro ao criar produto: {str(e)}"}), 500

# Rotas de KYC
@app.route('/api/kyc/save', methods=['POST'])
@require_auth
def save_kyc():
    try:
        data = request.get_json()
        user_id = get_current_user_id()
        
        # Salvar KYC
        if db_service.save_kyc(user_id, data):
            return jsonify({
                "success": True,
                "message": "Dados KYC salvos com sucesso"
            })
        else:
            return jsonify({"error": "Erro ao salvar dados KYC"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro ao salvar KYC: {str(e)}"}), 500

@app.route('/api/kyc/complete')
@require_auth
def get_kyc_complete():
    try:
        user_id = get_current_user_id()
        kyc_data = db_service.get_kyc_by_user_id(user_id)
        
        return jsonify({
            "success": True,
            "kyc": kyc_data
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar KYC: {str(e)}"}), 500

# Rotas de admin
@app.route('/api/admin/pending-users')
@require_admin
def get_pending_users():
    try:
        pending_users = db_service.get_pending_users()
        
        return jsonify({
            "success": True,
            "users": pending_users
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar usuários pendentes: {str(e)}"}), 500

@app.route('/api/admin/approve-user/<user_id>', methods=['POST'])
@require_admin
def approve_user(user_id):
    try:
        # Atualizar status do usuário
        if db_service.update_user(user_id, {'status': 'ativo'}):
            # Criar log
            admin_user_id = get_current_user_id()
            db_service.create_log({
                'user_id': admin_user_id,
                'action': 'approve_user',
                'target_user_id': user_id,
                'description': 'Usuário aprovado'
            })
            
            return jsonify({
                "success": True,
                "message": "Usuário aprovado com sucesso"
            })
        else:
            return jsonify({"error": "Erro ao aprovar usuário"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro ao aprovar usuário: {str(e)}"}), 500

@app.route('/api/admin/reject-user/<user_id>', methods=['POST'])
@require_admin
def reject_user(user_id):
    try:
        # Atualizar status do usuário
        if db_service.update_user(user_id, {'status': 'rejeitado'}):
            # Criar log
            admin_user_id = get_current_user_id()
            db_service.create_log({
                'user_id': admin_user_id,
                'action': 'reject_user',
                'target_user_id': user_id,
                'description': 'Usuário rejeitado'
            })
            
            return jsonify({
                "success": True,
                "message": "Usuário rejeitado com sucesso"
            })
        else:
            return jsonify({"error": "Erro ao rejeitar usuário"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro ao rejeitar usuário: {str(e)}"}), 500

# Rotas de páginas
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/admin-login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/seller')
def seller_page():
    return render_template('seller.html')

@app.route('/registro')
def registro_page():
    return render_template('registro.html')

# Simulação de PIX (mantida do código original)
def create_local_pix_payment(amount, description):
    payment_id = str(uuid.uuid4())
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"PIX:{payment_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    
    return {
        'payment_id': payment_id,
        'qr_code': img_str,
        'amount': amount,
        'description': description,
        'status': 'pending'
    }

@app.route('/api/pix/create', methods=['POST'])
@require_approved_user
def create_pix():
    try:
        data = request.get_json()
        amount = data.get('amount')
        description = data.get('description', 'Pagamento PIX')
        
        if not amount:
            return jsonify({"error": "Valor é obrigatório"}), 400
        
        # Criar pagamento PIX local
        pix_data = create_local_pix_payment(amount, description)
        
        # Salvar transação
        user_id = get_current_user_id()
        transaction_data = {
            'user_id': user_id,
            'payment_id': pix_data['payment_id'],
            'amount': amount,
            'description': description,
            'status': 'pending',
            'payment_method': 'pix'
        }
        
        db_service.create_transaction(transaction_data)
        
        return jsonify({
            "success": True,
            "pix": pix_data
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar PIX: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Iniciando Gateway de Pagamentos com Supabase...")
    print("📊 Banco de dados: Supabase")
    print("🔐 Segurança: Supabase Auth")
    print("👥 Usuários: Admin e Seller")
    print("💳 Pagamentos: Cartão, PIX, Boleto")
    print("🎯 Gamificação: Metas e Premiações")
    print("🌐 Interface: Web Dashboard Responsivo")
    print("📱 Acesse: http://localhost:5000")
    print("👨‍💼 Admin: admin / admin123")
    print("👤 Seller: seller / seller123")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

