import sqlite3

DB_PATH = "totem.db"

def adicionar_coluna_retirado_em():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verifica se a coluna já existe
    cursor.execute("PRAGMA table_info(pedidos)")
    colunas = [linha[1] for linha in cursor.fetchall()]
    if "retirado_em" in colunas:
        print("✔ A coluna 'retirado_em' já existe.")
    else:
        cursor.execute("ALTER TABLE pedidos ADD COLUMN retirado_em TEXT")
        conn.commit()
        print("✅ Coluna 'retirado_em' adicionada com sucesso.")

    conn.close()

if __name__ == "__main__":
    adicionar_coluna_retirado_em()
