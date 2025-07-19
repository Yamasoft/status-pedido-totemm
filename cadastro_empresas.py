import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
import shutil

DB_PATH = "totem.db"


def abrir_interface(callback_voltar=None):
    root = tk.Tk()
    root.title("Cadastro de Empresas")
    root.geometry("1024x780")
    root.configure(bg="#ECEFF1")

    header = tk.Frame(root, bg="#263238", height=60)
    header.pack(fill="x")
    tk.Label(
        header, text="Cadastro de Empresas", font=("Arial", 22, "bold"), bg="#263238", fg="white"
    ).pack(pady=10)

    form_frame = tk.Frame(root, bg="white")
    form_frame.pack(padx=30, pady=10, fill="x")

    # Labels and input widgets
    labels = [
        "Nome da Empresa", "CNPJ", "Logo (imagem)",
        "Pix APP Key", "Pix Client ID", "Pix Client Secret", "Chave Pix",
        "Certificado (.pem)", "Chave (.key)", "Ambiente"
    ]
    entries = []

    for i, label in enumerate(labels):
        tk.Label(
            form_frame, text=label + ":", font=("Arial", 12), bg="white", fg="#37474F"
        ).grid(row=i, column=0, sticky="w", padx=10, pady=6)

        if i == 9:
            combo = ttk.Combobox(
                form_frame, font=("Arial", 12), values=["sandbox", "production"], state="readonly"
            )
            combo.grid(row=i, column=1, padx=10, pady=6)
            entries.append(combo)
        else:
            entry = tk.Entry(form_frame, font=("Arial", 12), width=50)
            entry.grid(row=i, column=1, padx=10, pady=6)
            entries.append(entry)

    # Buttons to select files
    def selecionar_logo():
        path = filedialog.askopenfilename(
            title="Selecionar Logo", filetypes=[("Imagens", "*.png *.jpg *.jpeg *.gif")]
        )
        if path:
            entries[2].delete(0, tk.END)
            entries[2].insert(0, path)

    def selecionar_cert():
        path = filedialog.askopenfilename(
            title="Selecionar Certificado", filetypes=[("Certificado", "*.pem")]
        )
        if path:
            entries[7].delete(0, tk.END)
            entries[7].insert(0, path)

    def selecionar_key():
        path = filedialog.askopenfilename(
            title="Selecionar Chave", filetypes=[("Chave", "*.key")]
        )
        if path:
            entries[8].delete(0, tk.END)
            entries[8].insert(0, path)

    tk.Button(form_frame, text="Selecionar", command=selecionar_logo).grid(row=2, column=2, padx=5)
    tk.Button(form_frame, text="Selecionar", command=selecionar_cert).grid(row=7, column=2, padx=5)
    tk.Button(form_frame, text="Selecionar", command=selecionar_key).grid(row=8, column=2, padx=5)

    # List of companies
    list_frame = tk.Frame(root, bg="white")
    list_frame.pack(padx=30, pady=10, fill="both", expand=True)
    tk.Label(
        list_frame, text="Empresas cadastradas:", font=("Arial", 14, "bold"), bg="white", fg="#37474F"
    ).pack(anchor="w", padx=10, pady=(10, 0))
    lista_empresas = tk.Listbox(list_frame, font=("Arial", 12), height=8)
    lista_empresas.pack(fill="both", expand=True, padx=10, pady=5)

    def carregar_empresas():
        lista_empresas.delete(0, tk.END)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM empresas WHERE ativa = 1 ORDER BY nome")
            for emp_id, emp_name in cursor.fetchall():
                lista_empresas.insert(tk.END, f"{emp_id} - {emp_name}")

    def selecionar_empresa(event=None):
        selection = lista_empresas.curselection()
        if not selection:
            return
        emp_id = int(lista_empresas.get(selection[0]).split(" - ")[0])
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nome, cnpj, logo, pix_app_key, pix_client_id, pix_client_secret, chave_pix, pix_cert_path, pix_key_path, pix_ambiente"
                " FROM empresas WHERE id = ?", (emp_id,)
            )
            row = cursor.fetchone()
        if row:
            for i, widget in enumerate(entries):
                val = row[i] if row[i] is not None else ""
                if isinstance(widget, ttk.Combobox):
                    widget.set(val)
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, val)

    lista_empresas.bind("<<ListboxSelect>>", selecionar_empresa)

    def salvar():
        dados = [w.get().strip() for w in entries]
        if not dados[0]:
            messagebox.showwarning("Atenção", "O nome da empresa é obrigatório!")
            return
        # Copiar logo para pasta local
        logo_src = dados[2]
        if logo_src and os.path.isfile(logo_src):
            dest_dir = os.path.join(os.path.dirname(__file__), "imagens", "logos_empresas")
            os.makedirs(dest_dir, exist_ok=True)
            filename = os.path.basename(logo_src)
            shutil.copy(logo_src, os.path.join(dest_dir, filename))
            dados[2] = filename
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO empresas (nome, cnpj, logo, pix_app_key, pix_client_id, pix_client_secret, chave_pix, pix_cert_path, pix_key_path, pix_ambiente, ativa)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                dados
            )
            conn.commit()
        messagebox.showinfo("Sucesso", "Empresa cadastrada com sucesso!")
        limpar_campos()
        carregar_empresas()

    def alterar():
        selection = lista_empresas.curselection()
        if not selection:
            messagebox.showwarning("Atenção", "Selecione uma empresa para alterar!")
            return
        emp_id = int(lista_empresas.get(selection[0]).split(" - ")[0])
        dados = [w.get().strip() for w in entries]
        logo_src = dados[2]
        if logo_src and os.path.isfile(logo_src):
            dest_dir = os.path.join(os.path.dirname(__file__), "imagens", "logos_empresas")
            os.makedirs(dest_dir, exist_ok=True)
            filename = os.path.basename(logo_src)
            shutil.copy(logo_src, os.path.join(dest_dir, filename))
            dados[2] = filename
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE empresas SET nome=?, cnpj=?, logo=?, pix_app_key=?, pix_client_id=?, pix_client_secret=?, chave_pix=?, pix_cert_path=?, pix_key_path=?, pix_ambiente=?"
                " WHERE id=?", (*dados, emp_id)
            )
            conn.commit()
        messagebox.showinfo("Sucesso", "Empresa alterada com sucesso!")
        limpar_campos()
        carregar_empresas()

    def deletar():
        selection = lista_empresas.curselection()
        if not selection:
            messagebox.showwarning("Atenção", "Selecione uma empresa para excluir!")
            return
        emp_id = int(lista_empresas.get(selection[0]).split(" - ")[0])
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir esta empresa?"):
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM empresas WHERE id = ?", (emp_id,))
                conn.commit()
            messagebox.showinfo("Sucesso", "Empresa excluída!")
            limpar_campos()
            carregar_empresas()

    def limpar_campos():
        for widget in entries:
            if isinstance(widget, ttk.Combobox):
                widget.set("")
            else:
                widget.delete(0, tk.END)
        lista_empresas.selection_clear(0, tk.END)

    # Action buttons
    btn_frame = tk.Frame(root, bg="#ECEFF1")
    btn_frame.pack(pady=15)
    tk.Button(btn_frame, text="Salvar", command=salvar, width=15,
              font=("Arial", 12, "bold"), bg="#388E3C", fg="white").pack(side="left", padx=6)
    tk.Button(btn_frame, text="Alterar", command=alterar, width=15,
              font=("Arial", 12, "bold"), bg="#0288D1", fg="white").pack(side="left", padx=6)
    tk.Button(btn_frame, text="Excluir", command=deletar, width=15,
              font=("Arial", 12), bg="#D32F2F", fg="white").pack(side="left", padx=6)
    tk.Button(btn_frame, text="Limpar", command=limpar_campos, width=15,
              font=("Arial", 12), bg="#757575", fg="white").pack(side="left", padx=6)

    if callback_voltar:
        def voltar():
            for i in range(3):
                root.attributes("-alpha", 1 - i * 0.3)
                root.update()
                root.after(50)
            root.destroy()
            callback_voltar()

        tk.Button(btn_frame, text="Voltar ao Menu", command=voltar, width=18,
                  font=("Arial", 12, "bold"), bg="#FF7043", fg="white").pack(side="left", padx=6)
    else:
        tk.Button(btn_frame, text="Sair", command=root.destroy, width=15,
                  font=("Arial", 12), bg="#455A64", fg="white").pack(side="left", padx=6)

    carregar_empresas()
    root.mainloop()


if __name__ == "__main__":
    def voltar_ao_menu():
        print("Retornando ao menu principal...")

    abrir_interface(callback_voltar=voltar_ao_menu)
