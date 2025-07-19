import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os


DB_PATH = "totem.db"

# --- Funções de acesso ao banco de dados ---

def buscar_empresas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM empresas WHERE ativa = 1")
    empresas = cursor.fetchall()
    conn.close()
    return empresas


def buscar_grupos_da_empresa(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM grupos WHERE empresa_id = ?", (empresa_id,))
    grupos = cursor.fetchall()
    conn.close()
    return grupos


def buscar_produtos_por_grupo(grupo_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, preco, foto, esgotado, promocao FROM produtos WHERE grupo_id = ?",
        (grupo_id,)
    )
    produtos = cursor.fetchall()
    conn.close()
    return produtos


def cadastrar_produto(nome, preco, grupo_id, foto, promocao):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, preco, grupo_id, foto, esgotado, promocao) VALUES (?, ?, ?, ?, 0, ?)",
        (nome, preco, grupo_id, foto, promocao)
    )
    conn.commit()
    conn.close()


def atualizar_produto(produto_id, nome, preco, grupo_id, foto, esgotado, promocao):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE produtos SET nome=?, preco=?, grupo_id=?, foto=?, esgotado=?, promocao=? WHERE id=?",
        (nome, preco, grupo_id, foto, esgotado, promocao, produto_id)
    )
    conn.commit()
    conn.close()


def excluir_produto(produto_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()

# --- Interface Tkinter ---

def abrir_interface(callback_voltar=None):
    root = tk.Tk()
    root.title("Cadastro de Produtos")
    root.geometry("800x700")
    root.configure(bg="#f4f4f4")

    header = tk.Label(
        root, text="Cadastro de Produtos", bg="#3949AB", fg="white",
        font=("Arial", 22, "bold")
    )
    header.pack(fill="x")

    frame_empresa = tk.Frame(root, bg="#f4f4f4")
    frame_empresa.pack(padx=20, pady=10, fill="x")
    tk.Label(frame_empresa, text="Empresa:", bg="#f4f4f4", font=("Arial", 12)).pack(side="left")
    empresas = buscar_empresas()
    empresas_dict = {nome: eid for eid, nome in empresas}
    combo_empresa = ttk.Combobox(
        frame_empresa, state="readonly", values=list(empresas_dict.keys()),
        font=("Arial", 12), width=30
    )
    combo_empresa.pack(side="left", padx=5)

    tk.Label(frame_empresa, text="Grupo:", bg="#f4f4f4", font=("Arial", 12)).pack(side="left", padx=(20,0))
    combo_grupo = ttk.Combobox(
        frame_empresa, state="readonly", font=("Arial", 12), width=30
    )
    combo_grupo.pack(side="left", padx=5)

    frame_lista = tk.Frame(root, bg="white")
    frame_lista.pack(fill="both", expand=True, padx=20, pady=(0,10))
    tk.Label(
        frame_lista, text="Produtos:", bg="white", font=("Arial", 14, "bold")
    ).pack(anchor="w", padx=5, pady=5)
    lista_produtos = tk.Listbox(frame_lista, font=("Arial", 12))
    lista_produtos.pack(fill="both", expand=True, padx=5, pady=5)

    frame_form = tk.Frame(root, bg="white")
    frame_form.pack(fill="x", padx=20, pady=10)
    tk.Label(frame_form, text="Nome:", bg="white").grid(row=0, column=0, sticky="w")
    nome_var = tk.StringVar()
    entry_nome = tk.Entry(
        frame_form, textvariable=nome_var, font=("Arial", 12), width=30
    )
    entry_nome.grid(row=0, column=1, padx=5, pady=2)

    tk.Label(frame_form, text="Preço (R$):", bg="white").grid(row=1, column=0, sticky="w")
    entry_preco = tk.Entry(frame_form, font=("Arial", 12), width=15)
    entry_preco.grid(row=1, column=1, padx=5, pady=2, sticky="w")

    tk.Label(frame_form, text="Foto:", bg="white").grid(row=2, column=0, sticky="w")
    entry_foto = tk.Entry(frame_form, font=("Arial", 12), width=30)
    entry_foto.grid(row=2, column=1, padx=5, pady=2)
    tk.Button(
        frame_form, text="Selecionar", command=lambda: selecionar_foto(entry_foto)
    ).grid(row=2, column=2, padx=5)

    esg_var = tk.IntVar()
    tk.Checkbutton(
        frame_form, text="Esgotado", variable=esg_var, bg="white"
    ).grid(row=3, column=1, sticky="w")
    prom_var = tk.IntVar()
    tk.Checkbutton(
        frame_form, text="Promoção", variable=prom_var, bg="white"
    ).grid(row=4, column=1, sticky="w")

    frame_botoes = tk.Frame(root, bg="white")
    frame_botoes.pack(fill="x", padx=20, pady=(0,20))
    btn_salvar = tk.Button(
        frame_botoes, text="Salvar", bg="#4CAF50", fg="white",
        command=lambda: salvar(), width=12, font=("Arial", 12, "bold")
    )
    btn_alterar = tk.Button(
        frame_botoes, text="Alterar", bg="#2196F3", fg="white",
        command=lambda: alterar(), width=12, font=("Arial", 12, "bold")
    )
    btn_excluir = tk.Button(
        frame_botoes, text="Excluir", bg="#f44336", fg="white",
        command=lambda: excluir(), width=12, font=("Arial", 12, "bold")
    )
    btn_limpar = tk.Button(
        frame_botoes, text="Limpar", bg="#9E9E9E", fg="white",
        command=lambda: limpar_form(), width=12, font=("Arial", 12)
    )
    btn_salvar.pack(side="left", padx=5)
    btn_alterar.pack(side="left", padx=5)
    btn_excluir.pack(side="left", padx=5)
    btn_limpar.pack(side="left", padx=5)

    current_empresa = None
    current_produto_id = None

    def on_empresa_selected(event=None):
        nonlocal current_empresa
        nome = combo_empresa.get()
        current_empresa = empresas_dict.get(nome)
        grupos = buscar_grupos_da_empresa(current_empresa)
        combo_grupo['values'] = [nome for _, nome in grupos]
        combo_grupo.grupo_dict = {nome: gid for gid, nome in grupos}
        lista_produtos.delete(0, tk.END)
        limpar_form()

    def on_grupo_selected(event=None):
        gid = combo_grupo.grupo_dict.get(combo_grupo.get())
        lista_produtos.delete(0, tk.END)
        if gid:
            for pid, nome, preco, foto, esg, prom in buscar_produtos_por_grupo(gid):
                status = 'ESGOTADO' if esg else ('PROMOÇÃO' if prom else 'Disponível')
                lista_produtos.insert(
                    tk.END, f"{pid} - {nome} | R$ {preco:.2f} | {status}"
                )

    def on_produto_selected(event=None):
        nonlocal current_produto_id
        sel = lista_produtos.curselection()
        if not sel:
            return
        pid = int(lista_produtos.get(sel[0]).split(' - ')[0])
        current_produto_id = pid
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT nome, preco, foto, esgotado, promocao, grupo_id FROM produtos WHERE id = ?", (pid,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            nome_var.set(row[0])
            entry_preco.delete(0, tk.END); entry_preco.insert(0, str(row[1]))
            entry_foto.delete(0, tk.END); entry_foto.insert(0, row[2])
            esg_var.set(row[3]); prom_var.set(row[4])
            for nome, gid in combo_grupo.grupo_dict.items():
                if gid == row[5]:
                    combo_grupo.set(nome)
                    break

    def salvar():
        nome = nome_var.get().strip()
        preco_str = entry_preco.get().strip().replace(',', '.')
        gid = combo_grupo.grupo_dict.get(combo_grupo.get())
        foto = entry_foto.get().strip()
        esg = esg_var.get(); prom = prom_var.get()
        if current_produto_id:
            messagebox.showwarning("Atenção", "Use o botão Alterar para editar o produto.")
            return
        if not (nome and preco_str and gid):
            messagebox.showwarning("Atenção", "Preencha todos os campos obrigatórios.")
            return
        try:
            preco = float(preco_str)
        except ValueError:
            messagebox.showwarning("Atenção", "Preço inválido.")
            return
        cadastrar_produto(nome, preco, gid, foto, prom)
        messagebox.showinfo("Sucesso", "Produto cadastrado.")
        on_grupo_selected()
        limpar_form()

    def alterar():
        nonlocal current_produto_id
        if current_produto_id is None:
            messagebox.showwarning("Atenção", "Selecione um produto para alterar.")
            return
        nome = nome_var.get().strip()
        preco_str = entry_preco.get().strip().replace(',', '.')
        gid = combo_grupo.grupo_dict.get(combo_grupo.get())
        foto = entry_foto.get().strip()
        esg = esg_var.get(); prom = prom_var.get()
        if not (nome and preco_str and gid):
            messagebox.showwarning("Atenção", "Preencha todos os campos obrigatórios.")
            return
        try:
            preco = float(preco_str)
        except ValueError:
            messagebox.showwarning("Atenção", "Preço inválido.")
            return
        atualizar_produto(current_produto_id, nome, preco, gid, foto, esg, prom)
        messagebox.showinfo("Sucesso", "Produto atualizado.")
        on_grupo_selected()
        limpar_form()

    def excluir():
        nonlocal current_produto_id
        if current_produto_id is None:
            messagebox.showwarning("Atenção", "Selecione um produto para excluir.")
            return
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir este produto?"):
            excluir_produto(current_produto_id)
            messagebox.showinfo("Sucesso", "Produto excluído.")
            on_grupo_selected()
            limpar_form()

    def limpar_form():
        nonlocal current_produto_id
        nome_var.set("")
        entry_preco.delete(0, tk.END)
        entry_foto.delete(0, tk.END)
        esg_var.set(0); prom_var.set(0)
        current_produto_id = None
        lista_produtos.selection_clear(0, tk.END)
        entry_nome.focus_set()

    def selecionar_foto(entry):
        path = filedialog.askopenfilename(
            title="Selecionar Imagem", filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")]
        )
        if path:
            nome_arquivo = os.path.basename(path)
            destino = os.path.join("static", "imagens", nome_arquivo)
            try:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                with open(path, "rb") as src, open(destino, "wb") as dst:
                    dst.write(src.read())
                entry.delete(0, tk.END)
                entry.insert(0, nome_arquivo)
                messagebox.showinfo("Imagem Copiada", f"A imagem foi salva em static/imagens/{nome_arquivo}")
            except Exception as e:
                messagebox.showerror("Erro ao copiar imagem", str(e))

    combo_empresa.bind("<<ComboboxSelected>>", on_empresa_selected)
    combo_grupo.bind("<<ComboboxSelected>>", on_grupo_selected)
    lista_produtos.bind("<<ListboxSelect>>", on_produto_selected)

    root.mainloop()

if __name__ == "__main__":
    abrir_interface()
