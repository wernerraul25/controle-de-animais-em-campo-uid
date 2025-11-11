import sqlite3
from flask import Flask, jsonify, render_template, request
from datetime import datetime
import pytz 

app = Flask(__name__)
DATABASE = 'monitoramento_rfid.db'
BR_TIMEZONE = pytz.timezone("America/Sao_Paulo") 

# --- MAPEAMENTO DE ANIMAIS ---
BEZERROS_UIDS = ['219085403461']
VACAS_UIDS = ['703695879170']
# --- FIM DO MAPEAMENTO ---


def get_db_connection():
    """Cria uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Rota 1: Servir o Dashboard
@app.route('/')
def index():
    """Serve a página principal 'index.html'."""
    return render_template('index.html')

# Rota 2: API para ler o log e as contagens
@app.route('/api/status', methods=['GET'])
def get_status():
    """
    Busca o log do lote atual, o histórico de lotes,
    e calcula as contagens TOTAIS (não-únicas) do lote atual.
    """
    conn = get_db_connection()
    
    # 1. Pega o log do LOTE ATUAL
    log_live_cursor = conn.execute(
        'SELECT id, timestamp, tag_uid FROM scan_log_live ORDER BY timestamp DESC'
    ).fetchall()
    log_live = [dict(entrada) for entrada in log_live_cursor]

    # 2. Pega o HISTÓRICO de lotes salvos
    historico_cursor = conn.execute(
        'SELECT id, data_fechamento, contagem_bezerros, contagem_vacas, anotacao FROM lotes_arquivados ORDER BY data_fechamento DESC'
    ).fetchall()
    historico = [dict(lote) for lote in historico_cursor]

    # 3. Calcula as contagens TOTAIS (não-únicas)
    # Esta lógica agora conta cada LINHA no log_live,
    # que é controlado pelo cooldown do sensor.py.
    counts = {"bezerros": 0, "vacas": 0}
    for entrada in log_live: 
        uid = entrada['tag_uid']
        if uid in BEZERROS_UIDS:
            counts["bezerros"] += 1
        elif uid in VACAS_UIDS:
            counts["vacas"] += 1
    
    conn.close()
    
    # 4. Retorna TUDO para o dashboard
    return jsonify({
        "log_live": log_live,
        "live_counts": counts,
        "history": historico
    })

# Rota 3: API para a Pi registrar um novo scan
@app.route('/api/scan', methods=['POST'])
def registrar_scan():
    """Salva um novo scan na tabela 'scan_log_live'."""
    data = request.json
    tag_uid = data.get('uid')

    if not tag_uid:
        return jsonify({"erro": "UID da tag não fornecido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    data_agora = datetime.now(BR_TIMEZONE)

    # Insere na tabela do LOTE ATUAL
    cursor.execute(
        'INSERT INTO scan_log_live (timestamp, tag_uid) VALUES (?, ?)',
        (data_agora, tag_uid)
    )
    
    conn.commit()
    conn.close()
    
    print(f"API: Novo scan ao vivo registrado. UID: {tag_uid}")
    return jsonify({"sucesso": True})

# Rota 4: API para "Salvar Lote"
@app.route('/api/salvar_lote', methods=['POST'])
def salvar_lote():
    """
    Calcula o resumo TOTAL (não-único) do lote atual, salva no histórico,
    e limpa o log ao vivo.
    """
    data = request.json
    anotacao = data.get('anotacao', '') 

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Calcula as contagens TOTAIS (não-únicas)
    counts = {"bezerros": 0, "vacas": 0}
    all_uids_cursor = cursor.execute(
        'SELECT tag_uid FROM scan_log_live' # Pega todos, não apenas os distintos
    ).fetchall()
    
    for row in all_uids_cursor:
        uid = row['tag_uid']
        if uid in BEZERROS_UIDS:
            counts["bezerros"] += 1
        elif uid in VACAS_UIDS:
            counts["vacas"] += 1
            
    # 2. Salva o resumo na tabela 'lotes_arquivados'
    data_agora = datetime.now(BR_TIMEZONE)
    if (counts["bezerros"] + counts["vacas"]) > 0: 
        cursor.execute(
            'INSERT INTO lotes_arquivados (data_fechamento, contagem_bezerros, contagem_vacas, anotacao) VALUES (?, ?, ?, ?)',
            (data_agora, counts["bezerros"], counts["vacas"], anotacao)
        )
        print(f"API: Lote salvo no histórico. Bezerros: {counts['bezerros']}, Vacas: {counts['vacas']}")
    else:
        print("API: Lote vazio, nada para salvar.")

    # 3. Limpa o log do LOTE ATUAL
    cursor.execute('DELETE FROM scan_log_live')
    
    conn.commit()
    conn.close()
    
    return jsonify({"sucesso": True})

# Rota 5: API para EXCLUIR um lote do HISTÓRICO
@app.route('/api/historico/<int:id_lote>', methods=['DELETE'])
def excluir_lote(id_lote):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lotes_arquivados WHERE id = ?', (id_lote,))
    conn.commit()
    conn.close()
    print(f"API: Lote arquivado ID {id_lote} excluído.")
    return jsonify({"sucesso": True})

# Rota 6: API para ATUALIZAR anotação de um lote do HISTÓRICO
@app.route('/api/historico/<int:id_lote>', methods=['PUT'])
def atualizar_anotacao(id_lote):
    data = request.json
    nova_anotacao = data.get('anotacao')

    if nova_anotacao is None:
        return jsonify({"erro": "Anotação não fornecida"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE lotes_arquivados SET anotacao = ? WHERE id = ?', (nova_anotacao, id_lote))
    conn.commit()
    conn.close()
    print(f"API: Anotação do lote {id_lote} atualizada.")
    return jsonify({"sucesso": True})

if __name__ == '__main__':
    try:
        get_db_connection().close()
        print("Conexão com o banco de dados 'monitoramento_rfid.db' OK.")
        print(f"Fuso horário configurado para: {BR_TIMEZONE}")
        print("Mapeamento de Tags:")
        print(f"  Bezerros: {BEZERROS_UIDS}")
        print(f"  Vacas: {VACAS_UIDS}")
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        
    app.run(debug=True, host='0.0.0.0', port=5000)