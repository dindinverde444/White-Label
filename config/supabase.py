import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'your-anon-key')

# Cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configurações de tabelas
TABLES = {
    'usuarios': 'usuarios',
    'kyc': 'kyc',
    'produtos': 'produtos',
    'transacoes': 'transacoes',
    'logs': 'logs',
    'taxas': 'taxas',
    'saques': 'saques',
    'metas': 'metas'
}
