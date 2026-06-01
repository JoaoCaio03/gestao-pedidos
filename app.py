import os
import calendar
import pandas as pd
from io import BytesIO
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv() 

# Configuração do Flask para servir os arquivos estáticos (HTML/CSS/JS)
app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# Configuração do Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ==========================================
# ROTAS DO SISTEMA
# ==========================================

# Rota para abrir a tela de Login automaticamente ao acessar a URL raiz
@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"mensagem": "API rodando perfeitamente e conectada!"}), 200

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.json
    usuario = dados.get("usuario")
    senha = dados.get("senha")
    
    try:
        resposta = supabase.table("usuarios").select("*").eq("nome", usuario).eq("senha", senha).execute()
        
        if len(resposta.data) > 0:
            return jsonify({"sucesso": True}), 200
        else:
            return jsonify({"erro": "Usuário ou senha incorretos"}), 401
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/api/pedidos', methods=['POST'])
def criar_pedido():
    dados = request.json
    try:
        resposta = supabase.table("pedidos").insert({
            "telefone": dados.get("telefone"),
            "produto": dados.get("produto"),
            "quantidade": dados.get("quantidade"),
            "setor_destino": dados.get("setor_destino")
        }).execute()
        return jsonify({"sucesso": True, "dados": resposta.data}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/api/pedidos', methods=['GET'])
def listar_pedidos():
    try:
        filtro_data = request.args.get('data')
        filtro_mes = request.args.get('mes')   # <-- Recebe a nova variável do mês
        filtro_produto = request.args.get('produto')
        
        query = supabase.table("pedidos").select("*")
        
        if filtro_produto:
            query = query.eq("produto", filtro_produto)
            
        # LÓGICA INTELIGENTE: Se preencheu o MÊS, filtra o mês todo
        if filtro_mes:
            ano, mes = map(int, filtro_mes.split('-'))
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            inicio = f"{filtro_mes}-01T00:00:00"
            fim = f"{filtro_mes}-{ultimo_dia:02d}T23:59:59"
            query = query.gte("data_criacao", inicio).lte("data_criacao", fim)
            
        # Caso contrário, se preencheu só o DIA, filtra o dia exato
        elif filtro_data:
            inicio = f"{filtro_data}T00:00:00"
            fim = f"{filtro_data}T23:59:59"
            query = query.gte("data_criacao", inicio).lte("data_criacao", fim)
            
        resposta = query.order("data_criacao", desc=True).execute()
        return jsonify(resposta.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/api/exportar', methods=['GET'])
def exportar_excel():
    try:
        filtro_data = request.args.get('data')
        filtro_mes = request.args.get('mes')   # <-- Recebe a nova variável do mês
        filtro_produto = request.args.get('produto')
        
        query = supabase.table("pedidos").select("*")
        
        if filtro_produto:
            query = query.eq("produto", filtro_produto)
            
        # LÓGICA INTELIGENTE: Se preencheu o MÊS, filtra o mês todo
        if filtro_mes:
            ano, mes = map(int, filtro_mes.split('-'))
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            inicio = f"{filtro_mes}-01T00:00:00"
            fim = f"{filtro_mes}-{ultimo_dia:02d}T23:59:59"
            query = query.gte("data_criacao", inicio).lte("data_criacao", fim)
            
        # Caso contrário, se preencheu só o DIA, filtra o dia exato
        elif filtro_data:
            inicio = f"{filtro_data}T00:00:00"
            fim = f"{filtro_data}T23:59:59"
            query = query.gte("data_criacao", inicio).lte("data_criacao", fim)
            
        resposta = query.order("data_criacao", desc=True).execute()
        dados = resposta.data
        
        if not dados:
            return jsonify({"erro": "Nenhum dado encontrado para estes filtros"}), 404
            
        df = pd.DataFrame(dados)
        df = df.rename(columns={
            'id': 'ID', 'telefone': 'Telefone', 'produto': 'Produto',
            'quantidade': 'Quantidade', 'setor_destino': 'Setor Destino',
            'data_criacao': 'Data do Pedido'
        })
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Pedidos')
        
        output.seek(0)
        return send_file(output, download_name="relatorio_pedidos.xlsx", as_attachment=True)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400
    
@app.route('/api/dashboard', methods=['GET'])
def dashboard_metrics():
    try:
        resposta = supabase.table("pedidos").select("*").execute()
        dados = resposta.data
        
        total_pedidos = len(dados)
        mes_atual = datetime.now().strftime("%Y-%m")
        envios_mes = sum(1 for p in dados if p.get('data_criacao', '').startswith(mes_atual))
        
        produtos_contagem = {}
        for p in dados:
            prod = p.get('produto')
            qtd = p.get('quantidade', 0)
            if prod:
                produtos_contagem[prod] = produtos_contagem.get(prod, 0) + qtd
        
        maior_demanda = "Nenhum"
        if produtos_contagem:
            maior_demanda = max(produtos_contagem, key=produtos_contagem.get)
            
        return jsonify({
            "total": total_pedidos,
            "envios_mes": envios_mes,
            "maior_demanda": maior_demanda.capitalize()
        }), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
from supabase import create_client, Client
from dotenv import load_dotenv  # <-- 1. ADICIONE ISTO

# <-- 2. ADICIONE ISTO AQUI (Tem que ser antes de chamar as variáveis de ambiente)
load_dotenv() 

# Configuração do Flask para servir os arquivos estáticos (HTML/CSS/JS)
app = Flask(__name__, static_folder='public', static_url_path='')

# Configuração do Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ==========================================
# ROTAS DO SISTEMA
# ==========================================

# Rota para abrir a tela de Login automaticamente ao acessar a URL raiz
@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"mensagem": "API rodando perfeitamente e conectada!"}), 200

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.json
    usuario = dados.get("usuario")
    senha = dados.get("senha")
    
    try:
        resposta = supabase.table("usuarios").select("*").eq("nome", usuario).eq("senha", senha).execute()
        
        if len(resposta.data) > 0:
            return jsonify({"sucesso": True}), 200
        else:
            return jsonify({"erro": "Usuário ou senha incorretos"}), 401
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/api/pedidos', methods=['POST'])
def criar_pedido():
    dados = request.json
    try:
        resposta = supabase.table("pedidos").insert({
            "telefone": dados.get("telefone"),
            "produto": dados.get("produto"),
            "quantidade": dados.get("quantidade"),
            "setor_destino": dados.get("setor_destino")
        }).execute()
        return jsonify({"sucesso": True, "dados": resposta.data}), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/api/pedidos', methods=['GET'])
def listar_pedidos():
    try:
        filtro_data = request.args.get('data')
        filtro_produto = request.args.get('produto')
        
        query = supabase.table("pedidos").select("*")
        
        if filtro_produto:
            query = query.eq("produto", filtro_produto)
            
        if filtro_data:
            inicio = f"{filtro_data}T00:00:00"
            fim = f"{filtro_data}T23:59:59"
            query = query.gte("data_criacao", inicio).lte("data_criacao", fim)
            
        resposta = query.order("data_criacao", desc=True).execute()
        return jsonify(resposta.data), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/api/exportar', methods=['GET'])
def exportar_excel():
    try:
        filtro_data = request.args.get('data')
        filtro_produto = request.args.get('produto')
        
        query = supabase.table("pedidos").select("*")
        
        if filtro_produto:
            query = query.eq("produto", filtro_produto)
            
        if filtro_data:
            inicio = f"{filtro_data}T00:00:00"
            fim = f"{filtro_data}T23:59:59"
            query = query.gte("data_criacao", inicio).lte("data_criacao", fim)
            
        resposta = query.order("data_criacao", desc=True).execute()
        dados = resposta.data
        
        if not dados:
            return jsonify({"erro": "Nenhum dado encontrado para estes filtros"}), 404
            
        df = pd.DataFrame(dados)
        df = df.rename(columns={
            'id': 'ID', 'telefone': 'Telefone', 'produto': 'Produto',
            'quantidade': 'Quantidade', 'setor_destino': 'Setor Destino',
            'data_criacao': 'Data do Pedido'
        })
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Pedidos')
        
        output.seek(0)
        return send_file(output, download_name="relatorio_pedidos.xlsx", as_attachment=True)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400
    
@app.route('/api/dashboard', methods=['GET'])
def dashboard_metrics():
    try:
        resposta = supabase.table("pedidos").select("*").execute()
        dados = resposta.data
        
        total_pedidos = len(dados)
        mes_atual = datetime.now().strftime("%Y-%m")
        envios_mes = sum(1 for p in dados if p.get('data_criacao', '').startswith(mes_atual))
        
        produtos_contagem = {}
        for p in dados:
            prod = p.get('produto')
            qtd = p.get('quantidade', 0)
            if prod:
                produtos_contagem[prod] = produtos_contagem.get(prod, 0) + qtd
        
        maior_demanda = "Nenhum"
        if produtos_contagem:
            maior_demanda = max(produtos_contagem, key=produtos_contagem.get)
            
        return jsonify({
            "total": total_pedidos,
            "envios_mes": envios_mes,
            "maior_demanda": maior_demanda.capitalize()
        }), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)