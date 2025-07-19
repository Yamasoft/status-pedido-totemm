import sqlite3
import datetime
import win32print
import socket  # ✅ necessário para descobrir o IP local

# ✅ Função para descobrir o IP local real
def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Conecta a um IP público apenas para descobrir a interface usada
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


DB_PATH = "totem.db"
ESC = b"\x1B"
GS = b"\x1D"
CUT = GS + b"V" + b"\x42" + b"\x00"

def imprimir(pedido_id: int, senha: int, txid: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Buscar dados do pedido e da empresa
    cursor.execute("""
        SELECT e.nome, p.data_hora, p.valor_total
        FROM pedidos p
        JOIN empresas e ON p.empresa_id = e.id
        WHERE p.id = ?
    """, (pedido_id,))
    pedido = cursor.fetchone()

    if not pedido:
        print("Pedido não encontrado")
        return

    empresa_nome, data_hora, total = pedido

    # Buscar itens do pedido
    cursor.execute("""
        SELECT pr.nome, i.quantidade, i.preco_unitario
        FROM pedido_itens i
        JOIN produtos pr ON pr.id = i.produto_id
        WHERE i.pedido_id = ?
    """, (pedido_id,))
    itens = cursor.fetchall()

    conn.close()

    # Montagem do texto
    buf = ESC + b"@"                 # Reset
    buf += ESC + b"a" + b"\x01"      # Centralizar

    # Nome da empresa (fonte dupla)
    buf += ESC + b"!" + b"\x30"
    buf += f"{empresa_nome}\r\n".encode("cp850")

    # Reset fonte
    buf += ESC + b"!" + b"\x00"
    buf += b"==============================\r\n"

    # SENHA em destaque
    buf += ESC + b"!" + b"\x30"      # Fonte dupla (largura e altura)
    buf += f"     SENHA: {senha:04}\r\n".encode("cp850")
    buf += ESC + b"!" + b"\x00"
    buf += b"==============================\r\n"

    # Data e Hora
    buf += f"{datetime.datetime.strptime(data_hora, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')}\r\n".encode("cp850")
    buf += b"\r\nItens:\r\n"

    # Itens
    for nome, quantidade, preco in itens:
        subtotal = quantidade * preco
        linha = f"{quantidade}x {nome.ljust(15)[:15]} R$ {subtotal:6.2f}\r\n"
        buf += linha.encode("cp850")

    buf += b"------------------------------\r\n"
    buf += f"TOTAL................R$ {total:6.2f}\r\n".encode("cp850")
    buf += b"\r\n"

    # Dados do Pix
    buf += f"TXID: {txid}\r\n".encode("cp850")
    buf += b"STATUS: PAGO\r\n"
    buf += b"==============================\r\n"

    # ✅ IP local detectado automaticamente
    ip_servidor = obter_ip_local()
    url_status = f"http://{ip_servidor}:5000/status_pedido/{senha}"
    url_bytes = url_status.encode("utf-8")

    # 📌 Instruções ESC/POS para imprimir QR Code com o link do pedido
    qr_store = b'\x1D\x28\x6B' + bytes([
        (len(url_bytes) + 3) % 256,
        (len(url_bytes) + 3) // 256
    ]) + b'\x31\x50\x30' + url_bytes

    qr_print = b'\x1D\x28\x6B\x03\x00\x31\x51\x30'

    # adiciona ao buffer
    buf += b"\nEscaneie para acompanhar seu pedido:\n"
    buf += qr_store
    buf += qr_print

    # Mensagem final
    buf += ESC + b"a" + b"\x01"      # Centralizar
    buf += b"Obrigado! Aguarde atendimento\r\n\r\n\r\n"
    buf += CUT

    # Impressão
    printer_name = win32print.GetDefaultPrinter()
    h = win32print.OpenPrinter(printer_name)
    try:
        win32print.StartDocPrinter(h, 1, ("Comprovante Pix", None, "RAW"))
        win32print.StartPagePrinter(h)
        win32print.WritePrinter(h, buf)
        win32print.EndPagePrinter(h)
        win32print.EndDocPrinter(h)
    finally:
        win32print.ClosePrinter(h)

    print("✅ Comprovante impresso com sucesso.")


def salvar_e_imprimir(empresa_id: int, carrinho_itens: list, txid: str) -> int:
    """
    Insere o pedido e seus itens no banco, chama a impressão
    e retorna a 'senha' (usamos o pedido_id como senha).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Corrigido: aceita tanto 'preco' quanto 'valor'
    total = sum((item.get('preco') or item.get('valor') or 0) * item['quantidade'] for item in carrinho_itens)

    cursor.execute(
        "INSERT INTO pedidos (empresa_id, data_hora, valor_total) VALUES (?, ?, ?)",
        (empresa_id, agora, total)
    )
    pedido_id = cursor.lastrowid

    cursor.executemany(
        "INSERT INTO pedido_itens (pedido_id, produto_id, quantidade, preco_unitario) "
        "VALUES (?, ?, ?, ?)",
        [
            (
                pedido_id,
                item['id'],
                item['quantidade'],
                item.get('preco') or item.get('valor') or 0
            )
            for item in carrinho_itens
        ]
    )

    conn.commit()
    conn.close()

    senha = pedido_id

    # Chama impressão
    imprimir(pedido_id, senha, txid)

    return senha
