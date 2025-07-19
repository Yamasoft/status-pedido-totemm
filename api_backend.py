from flask import Flask, jsonify, request, render_template, redirect, send_from_directory
from flask_socketio import SocketIO
import sqlite3, os, time, random, socket, webbrowser
from api import criar_cobranca, status_cobranca
from impressao_recibo import salvar_e_imprimir
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['SECRET_KEY'] = 'chave-secreta'
socketio = SocketIO(app, cors_allowed_origins="*")

DB_PATH = "totem.db"

# ─── HELPERS ─────────────────────────────────────────────
def q(sql, args=(), one=False):
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory = sqlite3.Row
        cur = c.execute(sql, args)
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows

def calcular_total(carrinho):
    return sum(item.get("preco", 0) * item.get("quantidade", 0) for item in carrinho)

# ─── API JSON ────────────────────────────────────────────
@app.route("/empresas")
def api_empresas():
    rows = q("SELECT id, nome, logo FROM empresas WHERE ativa=1 ORDER BY nome")
    out = []
    for r in rows:
        raw = r["logo"] or ""
        if raw.startswith("/static"):
            url = raw
        elif os.path.isabs(raw):
            url = "/static/logo/" + os.path.basename(raw)
        else:
            url = "/static/logo/" + raw
        out.append({"id": r["id"], "nome": r["nome"], "logo": url})
    return jsonify(out)

@app.route("/status_pedido/<senha>")
def status_pedido(senha):
    row = q("""
        SELECT e.nome AS empresa_nome
        FROM pedidos p
        JOIN empresas e ON e.id = p.empresa_id
        WHERE p.id = ?
    """, (senha,), one=True)
    nome_empresa = row["empresa_nome"] if row else "Empresa"
    return render_template("status_pedido.html", senha=senha, nome_empresa=nome_empresa)

@app.route("/status_atual/<senha>")
def status_atual(senha):
    row = q("SELECT pronto FROM pedidos WHERE id=?", (senha,), one=True)
    if row:
        if row["pronto"] == 1:
            return jsonify({"status": "pronto"})
        elif row["pronto"] == 2:
            return jsonify({"status": "retirado"})
    return jsonify({"status": "preparando"})

@app.route("/categorias/<int:eid>")
def api_categorias(eid):
    rows = q("SELECT id,nome FROM grupos WHERE empresa_id=? ORDER BY nome", (eid,))
    return jsonify([dict(r) for r in rows])

@app.route("/produtos/<int:gid>")
def api_produtos(gid):
    rows = q("SELECT id,nome,preco,foto FROM produtos WHERE grupo_id=?", (gid,))
    prods = []
    for r in rows:
        raw = r["foto"] or ""
        if raw.startswith("/static"):
            url = raw
        elif os.path.isabs(raw):
            url = "/static/imagens/" + os.path.basename(raw)
        else:
            url = "/static/imagens/" + raw
        prods.append({"id": r["id"], "nome": r["nome"], "preco": r["preco"], "foto": url})
    return jsonify(prods)

# ─── PÁGINAS HTML ────────────────────────────────────────
@app.route("/")
def home():
    return render_template("menu_principal.html")

@app.route("/empresas_web")
def empresas_web():
    return render_template("empresas.html")

@app.route("/pedido")
def pedido():
    eid = request.args.get("empresa_id", type=int)
    if not eid:
        return jsonify({"erro": "Parametro empresa_id ausente"}), 400
    return render_template("index.html", empresa_id=eid)

# ─── PIX ────────────────────────────────────────────────
pagamentos = {}

@app.route("/pix", methods=["POST"])
def gerar_pix():
    data = request.get_json(silent=True) or {}
    try:
        carrinho = data["carrinho"]
        empresa = data["empresa_id"]
    except KeyError as e:
        return jsonify(erro=f"Campo obrigatório faltando: {e}"), 400

    valor = calcular_total(carrinho)
    row = q("SELECT chave_pix FROM empresas WHERE id=?", (empresa,), one=True)
    if not row or not row["chave_pix"]:
        return jsonify({"erro": "Chave Pix não cadastrada"}), 400

    resp = criar_cobranca(valor, row["chave_pix"])
    if not resp or "txid" not in resp or "pixCopiaECola" not in resp:
        return jsonify({"erro": f"Falha ao criar cobrança PIX. Resposta: {resp}"}), 500

    txid = resp["txid"]
    pagamentos[txid] = time.time()
    return jsonify({"txid": txid, "pixCopiaECola": resp["pixCopiaECola"]})

@app.route("/verificar_pagamento/<txid>")
def verificar_pagamento(txid):
    try:
        st = status_cobranca(txid)
    except Exception:
        st = "PENDENTE"

    if st == "CONCLUIDA":
        senha = random.randint(1000, 9999)
        return jsonify({"status": "CONCLUIDO", "senha": senha})
    return jsonify({"status": st})

@app.route("/finalizar_pagamento", methods=["POST"])
def finalizar_pagamento():
    data = request.get_json(silent=True) or {}
    try:
        empresa_id = data["empresa_id"]
        carrinho = data["carrinho"]
        txid = data["txid"]
    except KeyError as e:
        return jsonify(erro=f"Campo obrigatório faltando: {e}"), 400

    try:
        senha = salvar_e_imprimir(empresa_id, carrinho, txid)
        return jsonify({"status": "ok", "senha": senha})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ─── PAINEL DE PEDIDOS ───────────────────────────────────
@app.route("/painel")
def painel():
    empresa_id = request.args.get("empresa_id", type=int)
    if not empresa_id:
        return render_template("painel_empresas.html")
    return render_template("painel.html", empresa_id=empresa_id)

@app.route("/pedidos_em_aberto")
def pedidos_em_aberto():
    empresa_id = request.args.get("empresa_id", type=int)
    if not empresa_id:
        return jsonify([])

    rows = q("""
        SELECT p.id, p.valor_total, p.pronto, e.nome AS empresa_nome
        FROM pedidos p
        JOIN empresas e ON e.id = p.empresa_id
        WHERE p.empresa_id = ?
        AND (
            p.pronto != 2 OR
            (p.retirado_em IS NOT NULL AND julianday('now') - julianday(p.retirado_em) < 0.0014)
        )
        ORDER BY p.id DESC
    """, (empresa_id,))
    return jsonify([dict(r) for r in rows])

@app.route("/atualizar_status/<int:pedido_id>/<int:novo_status>", methods=["GET"])
def atualizar_status(pedido_id, novo_status):
    with sqlite3.connect(DB_PATH) as conn:
        if novo_status == 2:
            conn.execute("UPDATE pedidos SET pronto=?, retirado_em=? WHERE id=?",
                         (novo_status, datetime.now(), pedido_id))
        else:
            conn.execute("UPDATE pedidos SET pronto=? WHERE id=?", (novo_status, pedido_id))
        conn.commit()

    socketio.emit("status_atualizado", {"pedido_id": pedido_id, "novo_status": novo_status})
    return jsonify({"status": "ok"})

# ─── OUTRAS ROTAS ────────────────────────────────────────
@app.route("/static/imagens/<path:fname>")
def imagens(fname):
    return send_from_directory(os.path.join(app.static_folder, "imagens"), fname)

@app.route("/"
           "/<int:pedido_id>")
def produtos_pedido(pedido_id):
    rows = q("""
        SELECT i.quantidade, pr.nome
        FROM itens_pedido i
        JOIN produtos pr ON pr.id = i.produto_id
        WHERE i.pedido_id = ?
    """, (pedido_id,))
    return jsonify([dict(r) for r in rows])

@app.route("/pagamento")
def pagamento():
    empresa_id = request.args.get("empresa_id", type=int)
    total = request.args.get("total", type=float)

    if not empresa_id:
        return redirect("/empresas_web")

    if total is None or total <= 0:
        return redirect(f"/pedido?empresa_id={empresa_id}")

    return render_template("pagamento.html", empresa_id=empresa_id)

# ─── EXECUÇÃO ────────────────────────────────────────────
if __name__ == "__main__":
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\nServidor iniciado: http://{local_ip}:5000/\n")

    # webbrowser.open(f"http://{local_ip}:5000/")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)
