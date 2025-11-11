import sqlite3

DATABASE_FILE = 'monitoramento_rfid.db'
conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

# Tabela 1: Armazena os scans do LOTE ATUAL (ao vivo)
# Esta tabela é limpa a cada "Salvar Lote"
cursor.execute('''
CREATE TABLE IF NOT EXISTS scan_log_live (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    tag_uid TEXT NOT NULL
);
''')

# Tabela 2: Armazena os RESUMOS dos lotes passados
cursor.execute('''
CREATE TABLE IF NOT EXISTS lotes_arquivados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_fechamento DATETIME NOT NULL,
    contagem_bezerros INTEGER NOT NULL,
    contagem_vacas INTEGER NOT NULL,
    anotacao TEXT DEFAULT ''
);
''')

print("Banco de dados com tabelas 'scan_log_live' e 'lotes_arquivados' pronto.")
conn.commit()
conn.close()