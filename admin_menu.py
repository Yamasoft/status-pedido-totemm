import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

DB_PATH = "totem.db"


def buscar_empresas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM empresas ORDER BY nome")
    empresas = cursor.fetchall()
    conn.close()
    return empresas


def zerar_senha_empresa(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE empresas SET proxima_senha = 1 WHERE id = ?", (empresa_id,))
    conn.commit()
    conn.close()


def buscar_vendas_do_dia(empresa_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.data_hora, p.valor_total
        FROM pedidos p
        WHERE p.empresa_id = ? AND DATE(p.data_hora) = DATE('now')
        ORDER BY p.data_hora
    """, (empresa_id,))
    vendas = cursor.fetchall()
    conn.close()
    return vendas


def abrir_menu_admin():
    root = tk.Tk()
    root.title("Menu Administrativo")
    root.geometry("700x500")

    tk.Label(root, text="Selecione a Empresa:", font=("Arial", 12)).pack(pady=10)
    combo_empresas = ttk.Combobox(root, state="readonly", width=50)
    combo_empresas.pack(pady=5)

    empresas = buscar_empresas()
    empresas_dict = {f"{nome} (ID {eid})": eid for eid, nome in empresas}
    combo_empresas["values"] = list(empresas_dict.keys())

    frame_botoes = tk.Frame(root)
    frame_botoes.pack(pady=10)

    def acao_zerar():
        selecionada = combo_empresas.get()
        if not selecionada:
            messagebox.showwarning("Aviso", "Selecione uma empresa.")
            return
        eid = empresas_dict[selecionada]
        if messagebox.askyesno("Confirmação", f"Deseja zerar a senha da empresa:\n{selecionada}?"):
            zerar_senha_empresa(eid)
            messagebox.showinfo("Sucesso", "Senha reiniciada com sucesso.")

    frame_resultados = tk.Frame(root)
    frame_resultados.pack(pady=10, fill="both", expand=True)

    def acao_vendas():
        for widget in frame_resultados.winfo_children():
            widget.destroy()

        selecionada = combo_empresas.get()
        if not selecionada:
            messagebox.showwarning("Aviso", "Selecione uma empresa.")
            return
        eid = empresas_dict[selecionada]
        vendas = buscar_vendas_do_dia(eid)

        tk.Label(frame_resultados, text="Vendas do dia:", font=("Arial", 12, "bold")).pack()
        texto = tk.Text(frame_resultados, height=15, width=80)
        texto.pack()

        total = 0
        for vid, data, valor in vendas:
            texto.insert(tk.END, f"Pedido #{vid} | {data} | R$ {valor:.2f}\n")
            total += valor

        texto.insert(tk.END, f"\nTotal vendido: R$ {total:.2f}")
        texto.config(state="disabled")

    tk.Button(frame_botoes, text="Zerar Senha", command=acao_zerar, bg="#f44336", fg="white", width=20).pack(side="left", padx=10)
    tk.Button(frame_botoes, text="Ver Vendas do Dia", command=acao_vendas, bg="#4CAF50", fg="white", width=20).pack(side="left", padx=10)

    root.mainloop()

if __name__ == "__main__":
    abrir_menu_admin()
