import tkinter as tk
from tkinter import ttk, messagebox
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


def cadastrar_grupo(nome, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO grupos (nome, empresa_id) VALUES (?, ?)", (nome, empresa_id))
    conn.commit()
    conn.close()


def atualizar_grupo(grupo_id, nome, empresa_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE grupos SET nome = ? WHERE id = ? AND empresa_id = ?",
        (nome, grupo_id, empresa_id)
    )
    conn.commit()
    conn.close()


def excluir_grupo(grupo_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grupos WHERE id = ?", (grupo_id,))
    conn.commit()
    conn.close()

# --- Interface Tkinter ---

def abrir_interface(callback_voltar=None):
    root = tk.Tk()
    root.title("Cadastro de Grupos (Categorias)")
    root.geometry("700x550")
    root.configure(bg="#f4f4f4")

    # Estado atual do grupo selecionado
    current_grupo_id = None

    # Cabeçalho
    header_frame = tk.Frame(root, bg="#3949AB", height=60)
    header_frame.pack(fill="x")
    header_label = tk.Label(
        header_frame, text="Cadastro de Grupos", font=("Arial", 20, "bold"),
        bg="#3949AB", fg="white"
    )
    header_label.pack(pady=10)

    # Seleção de Empresa
    select_empresa_frame = tk.Frame(root, bg="#f4f4f4")
    select_empresa_frame.pack(padx=20, pady=10, fill="x")
    tk.Label(select_empresa_frame, text="Selecione a Empresa:", font=("Arial", 12), bg="#f4f4f4", fg="#333").pack(side="left", padx=5)
    empresas = buscar_empresas()
    empresas_dict = {nome: eid for eid, nome in empresas}
    combo_empresa = ttk.Combobox(select_empresa_frame, state="readonly", font=("Arial", 12), width=30)
    combo_empresa["values"] = list(empresas_dict.keys())
    combo_empresa.pack(side="left", padx=5)

    empresa_selecionada_label = tk.Label(
        root, text="Empresa: [Nenhuma Selecionada]", font=("Arial", 16, "bold"), bg="#f4f4f4", fg="#3949AB"
    )
    empresa_selecionada_label.pack(pady=5)

    # Container para grupos
    container = tk.Frame(root, bg="white", bd=2, relief="groove")
    container.pack(fill="both", expand=True, padx=20, pady=10)

    # Formulário
    form_frame = tk.Frame(container, bg="white")
    form_frame.pack(padx=10, pady=10, fill="x")
    tk.Label(form_frame, text="Nome do Grupo:", font=("Arial", 12), bg="white", fg="#333").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    entry_nome = tk.Entry(form_frame, font=("Arial", 12), width=40)
    entry_nome.grid(row=0, column=1, padx=5, pady=5)

    # Ações
    frame_botoes = tk.Frame(container, bg="white")
    frame_botoes.pack(pady=5)
    btn_salvar = tk.Button(frame_botoes, text="Salvar / Inserir", width=12, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white")
    btn_alterar = tk.Button(frame_botoes, text="Alterar", width=12, font=("Arial", 12, "bold"), bg="#2196F3", fg="white")
    btn_excluir = tk.Button(frame_botoes, text="Excluir", width=12, font=("Arial", 12, "bold"), bg="#f44336", fg="white")
    btn_limpar = tk.Button(frame_botoes, text="Limpar", width=12, font=("Arial", 12), bg="#9E9E9E", fg="white")
    btn_salvar.pack(side="left", padx=5)
    btn_alterar.pack(side="left", padx=5)
    btn_excluir.pack(side="left", padx=5)
    btn_limpar.pack(side="left", padx=5)

    # Lista de grupos
    frame_lista = tk.Frame(container, bg="white")
    frame_lista.pack(padx=10, pady=10, fill="both", expand=True)
    tk.Label(frame_lista, text="Grupos Cadastrados:", font=("Arial", 14, "bold"), bg="white", fg="#333").pack(anchor="w", padx=5, pady=5)
    lista_grupos = tk.Listbox(frame_lista, font=("Arial", 12), height=8)
    lista_grupos.pack(fill="both", expand=True, padx=5, pady=5)

    # Membros da lógica
    selected_empresa_id = tk.IntVar(value=0)

    def carregar_grupos():
        lista_grupos.delete(0, tk.END)
        for gid, nome in buscar_grupos_da_empresa(selected_empresa_id.get()):
            lista_grupos.insert(tk.END, f"{gid} - {nome}")

    def limpar():
        nonlocal current_grupo_id
        entry_nome.delete(0, tk.END)
        lista_grupos.selection_clear(0, tk.END)
        current_grupo_id = None

    def ao_selecionar_grupo(event=None):
        nonlocal current_grupo_id
        sel = lista_grupos.curselection()
        if not sel:
            return
        gid = int(lista_grupos.get(sel[0]).split(" - ")[0])
        current_grupo_id = gid
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT nome FROM grupos WHERE id = ? AND empresa_id = ?", (gid, selected_empresa_id.get()))
        row = cur.fetchone()
        conn.close()
        if row:
            entry_nome.delete(0, tk.END)
            entry_nome.insert(0, row[0])

    def salvar():
        nome_val = entry_nome.get().strip()
        if selected_empresa_id.get() == 0:
            messagebox.showwarning("Atenção", "Selecione uma empresa.")
            return
        if not nome_val:
            messagebox.showwarning("Atenção", "Preencha o nome do grupo.")
            return
        cadastrar_grupo(nome_val, selected_empresa_id.get())
        messagebox.showinfo("Sucesso", "Grupo cadastrado.")
        limpar()
        carregar_grupos()

    def alterar():
        if current_grupo_id is None:
            messagebox.showwarning("Atenção", "Selecione um grupo para alterar.")
            return
        nome_val = entry_nome.get().strip()
        if not nome_val:
            messagebox.showwarning("Atenção", "Preencha o nome do grupo.")
            return
        atualizar_grupo(current_grupo_id, nome_val, selected_empresa_id.get())
        messagebox.showinfo("Sucesso", "Grupo atualizado.")
        limpar()
        carregar_grupos()

    def deletar():
        if current_grupo_id is None:
            messagebox.showwarning("Atenção", "Selecione um grupo para excluir.")
            return
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir este grupo?"):
            excluir_grupo(current_grupo_id)
            messagebox.showinfo("Sucesso", "Grupo excluído.")
            limpar()
            carregar_grupos()

    def atualizar_empresa_selecionada(event=None):
        nome = combo_empresa.get()
        eid = empresas_dict.get(nome, 0)
        selected_empresa_id.set(eid)
        empresa_selecionada_label.config(text=f"Empresa: {nome.upper()}")
        limpar()
        carregar_grupos()

    # Binds
    combo_empresa.bind("<<ComboboxSelected>>", atualizar_empresa_selecionada)
    lista_grupos.bind("<<ListboxSelect>>", ao_selecionar_grupo)
    btn_salvar.config(command=salvar)
    btn_alterar.config(command=alterar)
    btn_excluir.config(command=deletar)
    btn_limpar.config(command=limpar)

    root.mainloop()

if __name__ == "__main__":
    abrir_interface()
