"""
API de Validação de Licenças para Vercel
Usando Flask + PostgreSQL (Vercel Postgres)
"""

from flask import Flask, request, jsonify
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from functools import wraps

app = Flask(__name__)

# API Key para endpoints protegidos
API_KEY = os.environ.get('API_KEY', 'seu-token-secreto-aqui')

def require_api_key(f):
    """Decorator para proteger endpoints com API Key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar API Key no header
        provided_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')
        
        # Remover "Bearer " se presente
        if provided_key and provided_key.startswith('Bearer '):
            provided_key = provided_key[7:]
        
        if not provided_key:
            return jsonify({
                "success": False,
                "message": "API Key não fornecida. Use header: X-API-Key ou Authorization"
            }), 401
        
        if provided_key != API_KEY:
            return jsonify({
                "success": False,
                "message": "API Key inválida"
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

# Configuração do banco de dados (Vercel Postgres)
def get_db_connection():
    """Cria conexão com o banco de dados"""
    try:
        # Vercel fornece a URL completa do banco
        database_url = os.environ.get('POSTGRES_URL')
        
        if database_url:
            conn = psycopg2.connect(database_url, sslmode='require')
        else:
            # Fallback para variáveis individuais
            conn = psycopg2.connect(
                host=os.environ.get('POSTGRES_HOST'),
                database=os.environ.get('POSTGRES_DATABASE'),
                user=os.environ.get('POSTGRES_USER'),
                password=os.environ.get('POSTGRES_PASSWORD'),
                port=os.environ.get('POSTGRES_PORT', '5432'),
                sslmode='require'
            )
        return conn
    except Exception as e:
        print(f"Erro ao conectar no banco: {e}")
        return None


@app.route('/', methods=['GET'])
def index():
    """Rota principal"""
    return jsonify({
        "service": "License Server API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "validate": "/api/licenca?key=XXX&uuid=XXX&disk=XXX (GET)",
            "add": "/api/licenca/add (POST)",
            "info": "/api/licenca/info?key=XXX (GET)",
            "deactivate": "/api/licenca/deactivate (POST)",
            "health": "/health (GET)",
            "setup": "/setup (GET)"
        }
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    if conn:
        conn.close()
    
    return jsonify({
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "service": "License Server",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/token/verify', methods=['GET'])
@require_api_key
def verify_token():
    """Endpoint para verificar se o token é válido"""
    return jsonify({
        "valid": True,
        "message": "Token válido"
    })


@app.route('/api/licenca', methods=['GET'])
def validate_license():
    """
    Endpoint de validação de licença
    
    Parâmetros GET:
    - key: Chave de licença
    - uuid: UUID da máquina
    - disk: Serial do disco
    """
    
    license_key = request.args.get('key', '').strip()
    machine_uuid = request.args.get('uuid', '').strip()
    disk_serial = request.args.get('disk', '').strip()
    
    if not license_key:
        return jsonify({
            "valid": False,
            "message": "Chave de licença não fornecida"
        }), 400
    
    if not machine_uuid or not disk_serial:
        return jsonify({
            "valid": False,
            "message": "Informações de hardware incompletas"
        }), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "valid": False,
            "message": "Erro ao conectar no banco de dados"
        }), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Buscar licença
        cur.execute("""
            SELECT id, license_key, owner, email, expires_on, 
                   max_activations, is_active, created_at
            FROM licenses
            WHERE license_key = %s
        """, (license_key,))
        
        license_data = cur.fetchone()
        
        if not license_data:
            return jsonify({
                "valid": False,
                "message": "Chave de licença inválida"
            }), 404
        
        if not license_data['is_active']:
            return jsonify({
                "valid": False,
                "message": "Licença desativada"
            }), 403
        
        if license_data['expires_on']:
            if datetime.now().date() > license_data['expires_on']:
                return jsonify({
                    "valid": False,
                    "message": f"Licença expirada em {license_data['expires_on']}"
                }), 403
        
        hardware_signature = f"{machine_uuid}_{disk_serial}"
        
        # Verificar se já está ativado
        cur.execute("""
            SELECT id FROM activations
            WHERE license_id = %s AND hardware_signature = %s
        """, (license_data['id'], hardware_signature))
        
        existing_activation = cur.fetchone()
        
        if existing_activation:
            return jsonify({
                "valid": True,
                "message": "Licença válida (já ativada neste hardware)",
                "owner": license_data['owner'],
                "expires": str(license_data['expires_on']) if license_data['expires_on'] else None
            })
        
        # Contar ativações
        cur.execute("""
            SELECT COUNT(*) as count FROM activations
            WHERE license_id = %s
        """, (license_data['id'],))
        
        activations_count = cur.fetchone()['count']
        
        if activations_count >= license_data['max_activations']:
            return jsonify({
                "valid": False,
                "message": f"Limite de ativações atingido ({license_data['max_activations']})"
            }), 403
        
        # Adicionar nova ativação
        cur.execute("""
            INSERT INTO activations (license_id, hardware_signature)
            VALUES (%s, %s)
        """, (license_data['id'], hardware_signature))
        
        conn.commit()
        
        return jsonify({
            "valid": True,
            "message": "Licença ativada com sucesso!",
            "owner": license_data['owner'],
            "expires": str(license_data['expires_on']) if license_data['expires_on'] else None,
            "activations_used": activations_count + 1,
            "activations_max": license_data['max_activations']
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({
            "valid": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
        
    finally:
        cur.close()
        conn.close()


@app.route('/api/licenca/info', methods=['GET'])
def license_info():
    """Endpoint para obter informações sobre uma licença"""
    license_key = request.args.get('key', '').strip()
    
    if not license_key:
        return jsonify({
            "found": False,
            "message": "Chave não fornecida"
        }), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "found": False,
            "message": "Erro ao conectar no banco de dados"
        }), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, license_key, owner, email, expires_on, 
                   max_activations, is_active, created_at
            FROM licenses
            WHERE license_key = %s
        """, (license_key,))
        
        license_data = cur.fetchone()
        
        if not license_data:
            return jsonify({
                "found": False,
                "message": "Licença não encontrada"
            }), 404
        
        cur.execute("""
            SELECT COUNT(*) as count FROM activations
            WHERE license_id = %s
        """, (license_data['id'],))
        
        activations_count = cur.fetchone()['count']
        
        return jsonify({
            "found": True,
            "active": license_data['is_active'],
            "owner": license_data['owner'],
            "email": license_data['email'],
            "expires": str(license_data['expires_on']) if license_data['expires_on'] else None,
            "activations_used": activations_count,
            "activations_max": license_data['max_activations'],
            "created_at": str(license_data['created_at'])
        })
        
    except Exception as e:
        return jsonify({
            "found": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
        
    finally:
        cur.close()
        conn.close()


@app.route('/api/licenca/add', methods=['POST'])
@require_api_key
def add_license():
    """
    Endpoint para adicionar nova licença
    
    JSON esperado:
    {
        "license_key": "NOVA-CHAVE-AQUI",
        "owner": "Nome do Cliente",
        "email": "email@cliente.com",
        "expires_on": "2026-12-31",  (opcional)
        "max_activations": 1,         (opcional, padrão: 1)
        "is_active": true             (opcional, padrão: true)
    }
    """
    data = request.get_json()
    
    license_key = data.get('license_key', '').strip()
    owner = data.get('owner', '').strip()
    email = data.get('email', '').strip()
    expires_on = data.get('expires_on')
    max_activations = data.get('max_activations', 1)
    is_active = data.get('is_active', True)
    
    if not license_key or not owner or not email:
        return jsonify({
            "success": False,
            "message": "Dados obrigatórios faltando (license_key, owner, email)"
        }), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "success": False,
            "message": "Erro ao conectar no banco de dados"
        }), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            INSERT INTO licenses (license_key, owner, email, expires_on, max_activations, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, license_key, owner, email, expires_on, max_activations, is_active, created_at
        """, (license_key, owner, email, expires_on, max_activations, is_active))
        
        new_license = cur.fetchone()
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Licença criada com sucesso!",
            "license": {
                "id": new_license['id'],
                "license_key": new_license['license_key'],
                "owner": new_license['owner'],
                "email": new_license['email'],
                "expires_on": str(new_license['expires_on']) if new_license['expires_on'] else None,
                "max_activations": new_license['max_activations'],
                "is_active": new_license['is_active'],
                "created_at": str(new_license['created_at'])
            }
        }), 201
        
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": "Chave de licença já existe"
        }), 409
        
    except Exception as e:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
        
    finally:
        cur.close()
        conn.close()


@app.route('/api/licenca/deactivate', methods=['POST'])
@require_api_key
def deactivate_license():
    """Endpoint para desativar licença de um hardware"""
    data = request.get_json()
    
    license_key = data.get('key', '').strip()
    machine_uuid = data.get('uuid', '').strip()
    disk_serial = data.get('disk', '').strip()
    
    if not license_key or not machine_uuid or not disk_serial:
        return jsonify({
            "success": False,
            "message": "Dados incompletos"
        }), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "success": False,
            "message": "Erro ao conectar no banco de dados"
        }), 500
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id FROM licenses WHERE license_key = %s
        """, (license_key,))
        
        license_data = cur.fetchone()
        
        if not license_data:
            return jsonify({
                "success": False,
                "message": "Licença não encontrada"
            }), 404
        
        hardware_signature = f"{machine_uuid}_{disk_serial}"
        
        cur.execute("""
            DELETE FROM activations
            WHERE license_id = %s AND hardware_signature = %s
        """, (license_data['id'], hardware_signature))
        
        if cur.rowcount > 0:
            conn.commit()
            return jsonify({
                "success": True,
                "message": "Licença desativada deste hardware"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Hardware não encontrado nas ativações"
            }), 404
            
    except Exception as e:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": f"Erro interno: {str(e)}"
        }), 500
        
    finally:
        cur.close()
        conn.close()


# Rota para inicializar o banco (executar uma vez)
@app.route('/setup', methods=['GET'])
def setup_database():
    """Criar tabelas no banco (executar apenas uma vez)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "success": False,
            "message": "Erro ao conectar no banco"
        }), 500
    
    try:
        cur = conn.cursor()
        
        # Criar tabelas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id SERIAL PRIMARY KEY,
                license_key VARCHAR(255) UNIQUE NOT NULL,
                owner VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                expires_on DATE,
                max_activations INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activations (
                id SERIAL PRIMARY KEY,
                license_id INTEGER NOT NULL,
                hardware_signature VARCHAR(255) NOT NULL,
                activated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (license_id) REFERENCES licenses (id) ON DELETE CASCADE,
                UNIQUE (license_id, hardware_signature)
            );
        """)
        
        # Inserir dados de exemplo
        cur.execute("""
            INSERT INTO licenses (license_key, owner, email, expires_on, max_activations, is_active) 
            VALUES
            ('DEMO-1234-5678-ABCD', 'Cliente Teste', 'teste@email.com', '2025-12-31', 1, TRUE),
            ('PROD-9876-5432-ZYXW', 'Cliente Premium', 'premium@email.com', '2026-12-31', 3, TRUE),
            ('EXPIRED-LITE-LICENSE', 'Cliente Expirado', 'expired@email.com', '2020-01-01', 1, TRUE)
            ON CONFLICT (license_key) DO NOTHING;
        """)
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Banco de dados configurado com sucesso!"
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({
            "success": False,
            "message": f"Erro: {str(e)}"
        }), 500
        
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
