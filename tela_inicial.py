import tkinter as tk
from PIL import Image, ImageTk
import sqlite3
import os
import math

# Configurações de UI
db_path = os.path.join(os.path.dirname(__file__), "totem.db")
COLORS = ["#FF7A00", "#0096A7", "#0079C2", "#C4278C"]
FONTE_H1 = ("Arial", 40, "bold")
FONTE_BTN = ("Arial", 18, "bold")  # compatibilidade com main.py


def buscar_empresas_ativas():
    """
    Retorna lista de tuplas (id, nome, logo) de empresas ativas.
    """
    with sqlite3.connect(db_path) as conn:
        return conn.execute(
            "SELECT id, nome, logo FROM empresas WHERE ativa=1"
        ).fetchall()


class TelaInicial(tk.Frame):
    """
    Tela de seleção de empresa para iniciar o totem.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#F5F5F5")
        self.controller = controller

        # Cabeçalho
        header = tk.Frame(self, bg=COLORS[0], height=120)
        header.pack(fill="x")
        tk.Label(
            header,
            text="SELECIONE UMA EMPRESA",
            font=FONTE_H1,
            fg="white",
            bg=COLORS[0]
        ).pack(pady=30)

        # Grid de botões
        grid = tk.Frame(self, bg="#F5F5F5")
        grid.pack(expand=True, fill="both", padx=40, pady=20)

        empresas = buscar_empresas_ativas()
        if not empresas:
            tk.Label(
                grid,
                text="Nenhuma empresa cadastrada",
                font=FONTE_BTN,
                fg="gray",
                bg="#F5F5F5"
            ).pack(pady=50)
            return

        cols = 2
        for c in range(cols):
            grid.grid_columnconfigure(c, weight=1)
        rows = math.ceil(len(empresas) / cols)
        for r in range(rows):
            grid.grid_rowconfigure(r, weight=1)

        for idx, (eid, nome, logo) in enumerate(empresas):
            r, c = divmod(idx, cols)

            # define cores
            card_bg = "#FFFFFF"
            card_border = "#DDDDDD"
            card_hover = "#F5F5F5"
            nome_bg = "#1976D2"  # azul destaque

            logo_path = None
            if logo:
                candidate = os.path.join(
                    os.path.dirname(__file__),
                    "imagens", "logos_empresas",
                    logo
                )
                if os.path.exists(candidate):
                    logo_path = candidate
                elif os.path.isabs(logo) and os.path.exists(logo):
                    logo_path = logo

            logo_img = None
            if logo_path:
                img = Image.open(logo_path).resize((160, 160), Image.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)

            empresa_frame = tk.Frame(
                grid,
                bg=card_bg,
                highlightbackground=card_border,
                highlightthickness=2,
                bd=0,
                relief="raised",
                cursor="hand2"
            )
            empresa_frame.grid(row=r, column=c, padx=30, pady=30, sticky="nsew")
            empresa_frame.configure(borderwidth=2, relief="groove")

            # logo
            if logo_img:
                lbl_logo = tk.Label(empresa_frame, image=logo_img, bg=card_bg)
                lbl_logo.image = logo_img
                lbl_logo.pack(padx=10, pady=(15, 10))

            lbl_nome = tk.Label(
                empresa_frame,
                text=nome.title(),  # maiúscula só a inicial de cada palavra
                font=("Segoe UI", 16, "bold"),  # fonte moderna e menor
                fg="#333333",  # cinza escuro, elegante
                bg=card_bg,
                wraplength=220,
                justify="center"
            )
            lbl_nome.pack(padx=10, pady=(0, 20))

            # clique
            empresa_frame.bind("<Button-1>", lambda e, eid_=eid: self.selecionar(eid_))
            lbl_nome.bind("<Button-1>", lambda e, eid_=eid: self.selecionar(eid_))
            if logo_img:
                lbl_logo.bind("<Button-1>", lambda e, eid_=eid: self.selecionar(eid_))

            # efeito hover
            def on_enter(ev, frame=empresa_frame):
                frame.configure(bg=card_hover)

            def on_leave(ev, frame=empresa_frame):
                frame.configure(bg=card_bg)

            empresa_frame.bind("<Enter>", on_enter)
            empresa_frame.bind("<Leave>", on_leave)

    def selecionar(self, empresa_id: int):
        # Remove tela de vendas antiga
        antigo = self.controller.frames.get("TelaVendas")
        if antigo:
            antigo.destroy()
        # Cria nova tela de vendas
        from tela_vendas import TelaVendas  # evita loop de imports
        nova = TelaVendas(parent=self.controller.frames["TelaMenu"].master, controller=self.controller)
        self.controller.frames["TelaVendas"] = nova
        nova.grid(row=0, column=0, sticky="nsew")
        nova.set_empresa(empresa_id)
        self.controller.show_frame("TelaVendas")

