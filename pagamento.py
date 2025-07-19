# pagamento.py
import sqlite3
import datetime

DB_PATH = "totem.db"

def registrar_pedido(empresa_id: int, carrinho: list, total: float, txid: str) -> tuple:
    data_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pedidos (empresa_id, data_hora, valor_total, status, txid)
        VALUES (?, ?, ?, 'pago', ?)
    """, (empresa_id, data_hora, total, txid))
    pedido_id = cursor.lastrowid

    for item in carrinho:
        cursor.execute("""
            INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario)
            VALUES (?, ?, ?, ?)
        """, (pedido_id, item['id'], item['quantidade'], item['valor']))

    cursor.execute("SELECT proxima_senha FROM empresas WHERE id = ?", (empresa_id,))
    resultado = cursor.fetchone()
    proxima = resultado[0] if resultado and resultado[0] else 1

    cursor.execute("UPDATE empresas SET proxima_senha = proxima_senha + 1 WHERE id = ?", (empresa_id,))
    cursor.execute("""
        INSERT INTO senhas (empresa_id, numero, pedido_id, data_hora)
        VALUES (?, ?, ?, ?)
    """, (empresa_id, proxima, pedido_id, data_hora))

    conn.commit()
    conn.close()

    print(f"✅ Pedido {pedido_id} registrado com senha {proxima}")
    return pedido_id, proxima
