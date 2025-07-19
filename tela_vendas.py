import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import sqlite3
import os
import datetime
from carrinho import Carrinho
from api import criar_cobranca
from tela_pix import exibir_pagamento_pix  # ajustaremos esta função em tela_pix.py
from tela_credito import mensagem_credito
from tela_debito import mensagem_debito

DB_PATH = "totem.db"

# -------------------------------------------------------------------
# CONFIGURAÇÕES DE CORES E FONTES
# -------------------------------------------------------------------

FONTE_TITULO    = ("Arial", 32, "bold")
FONTE_CATEGORIA = ("Arial", 16, "bold")
FONTE_PRODUTO   = ("Arial", 14)
FONTE_PRECO     = ("Arial", 14, "bold")
FONTE_CARRINHO  = ("Arial", 12)
FONTE_BOTAO     = ("Arial", 14, "bold")

class TelaVendas(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#D7CCC8")
        self.container = tk.Frame(self, bg="#FAF3E0")
        self.container.pack(expand=True, fill="both", padx=10, pady=10)

        # Cabeçalho no topo
        topo = tk.Frame(self.container, bg="#B71C1C", height=120)
        topo.pack(fill="x")
        topo.pack_propagate(False)

        self.lbl_empresa_nome = tk.Label(
            topo,
            text="",
            font=("Arial", 32, "bold"),
            fg="#2196F3",
            bg="#FFFFFF",
            anchor="center",
            justify="center"
        )
        self.lbl_empresa_nome.pack(pady=(10, 2), fill="x")

        tk.Frame(
            topo,
            bg="#DDDDDD",  # Cinza claro
            height=2
        ).pack(fill="x")

        tk.Label(
            topo,
            text="SELECIONE SEU PEDIDO",
            font = ("Arial", 28, "bold"),  # maior hierarquia
            fg = "white",
            bg = "#B71C1C"
        ).pack(pady=(2, 5))

        tk.Frame(
            topo,
            bg="white",
            height=2
        ).pack(fill="x", padx=80)

        # ─── Contêiner das categorias ───────────────────────────────
        frame_topo = tk.Frame(self.container, bg="#FFFFFF")
        frame_topo.pack(side="top", fill="x")

        # Barra de categorias
        self.frame_categorias = tk.Frame(frame_topo, bg="#FFFFFF", height=40)
        self.frame_categorias.pack(fill="x")
        self.frame_categorias.pack_propagate(False)

        # Área de conteúdo (produtos + carrinho)
        frame_conteudo = tk.Frame(self.container, bg="#FFFFFF")
        frame_conteudo.pack(side="top", fill="both", expand=True)

        frame_conteudo.grid_rowconfigure(0, weight=1)
        frame_conteudo.grid_columnconfigure(0, weight=3)
        frame_conteudo.grid_columnconfigure(1, weight=1)
        frame_conteudo.grid_rowconfigure(0, weight=1)

        self.bot_categorias = {}
        self.controller = controller
        self.empresa_id = None
        self.sacola = []
        self.carrinho = Carrinho(self.sacola)

        # Ajuste dinâmico do número de colunas para evitar corte dos cards
        self.num_colunas = 2

        # Frame de produtos com scroll vertical
        frame_prod = tk.Frame(frame_conteudo, bg="#FAF3E0")
        frame_prod.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        frame_conteudo.grid_columnconfigure(0, weight=2)
        frame_prod.grid_propagate(False)

        frame_prod.update_idletasks()
        frame_prod.update()

        canvas_prod = tk.Canvas(frame_prod, bg="#FAF3E0", highlightthickness=0)

        scrollbar_prod = tk.Scrollbar(frame_prod, orient="vertical", command=canvas_prod.yview)
        canvas_prod.configure(yscrollcommand=scrollbar_prod.set)
        canvas_prod.pack(fill="both", expand=True)
        canvas_prod.update_idletasks()
        canvas_prod.config(scrollregion=canvas_prod.bbox("all"))
        container_prod = tk.Frame(canvas_prod, bg="#FAF3E0")
        container_prod.bind("<Configure>", lambda e: canvas_prod.configure(scrollregion=canvas_prod.bbox("all")))
        canvas_prod.create_window((0, 0), window=container_prod, anchor="nw")

        canvas_prod.pack(side="left", fill="both", expand=True)
        scrollbar_prod.pack(side="right", fill="y")
        self.frame_produtos = container_prod

        # Configura colunas uniformes no grid de produtos
        for c in range(self.num_colunas):
            self.frame_produtos.grid_columnconfigure(c, weight=1, uniform="prod")

        canvas_prod.bind_all("<MouseWheel>", lambda e: canvas_prod.yview_scroll(-1 * int(e.delta / 120), "units"))

        # Frame do carrinho
        frame_car = tk.Frame(frame_conteudo, bg="#FAF3E0")
        frame_car.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        frame_conteudo.grid_columnconfigure(1, weight=2)
        frame_car.grid_propagate(False)

        # ------------------- Parte de cima (carrinho de itens) -------------------
        frame_carrinho_lista = tk.Frame(frame_car, bg="#FAF3E0")
        frame_carrinho_lista.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        canvas_car = tk.Canvas(frame_carrinho_lista, bg="#FAF3E0", highlightthickness=0)
        scrollbar_car = tk.Scrollbar(frame_carrinho_lista, orient="vertical", command=canvas_car.yview)
        self.lista_itens = tk.Frame(canvas_car, bg="#FAF3E0")

        self.lista_itens.bind("<Configure>", lambda e: canvas_car.configure(scrollregion=canvas_car.bbox("all")))
        canvas_car.create_window((0, 0), window=self.lista_itens, anchor="nw")
        canvas_car.configure(yscrollcommand=scrollbar_car.set)

        canvas_car.pack(side="left", fill="both", expand=True)
        scrollbar_car.pack(side="right", fill="y")

        self.lista_itens = tk.Frame(canvas_car, bg="#FAF3E0")
        self.lista_itens.bind("<Configure>", lambda e: canvas_car.configure(scrollregion=canvas_car.bbox("all")))
        canvas_car.create_window((0, 0), window=self.lista_itens, anchor="nw")

        # ------------------- Parte de baixo (subtotal + continuar) -------------------
        frame_rodape_car = tk.Frame(frame_car, bg="#FFF8F0")
        frame_rodape_car.pack(fill="x", pady=(10, 10), padx=10)

        self.label_total = tk.Label(
            frame_rodape_car,
            text="Subtotal: R$ 0.00",
            font=("Arial", 24, "bold"),
            fg="#2E7D32",
            bg="#FFF8F0",
            anchor="e"
        )
        self.label_total.pack(fill="x", pady=(0, 10))

        # Criar uma borda com cor diferente usando um Frame como contorno
        self.frame_borda_continuar = tk.Frame(  # ← agora atributo da classe
            frame_rodape_car,
            bg="#1B5E20",
            highlightthickness=0,
            padx=3,
            pady=3
        )
        self.frame_borda_continuar.pack(fill="x", padx=5, pady=(0, 10))

        self.btn_continuar = tk.Button(
            self.frame_borda_continuar,
            text="👉 IR PARA PAGAMENTO",
            font=("Arial", 20, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#388E3C",
            activeforeground="white",
            height=2,
            padx=10,
            pady=5,
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.exibir_conferencia
        )
        self.btn_continuar.pack(fill="x")

        rodape = tk.Frame(self.container, bg="#EEEEEE", height=150)
        rodape.pack(fill="x")
        rodape.pack_propagate(False)

        # Botão Voltar ao Menu Principal com borda
        frame_borda_voltar = tk.Frame(
            rodape,
            bg="#E65100",  # Tom mais escuro da cor do botão
            padx=3,
            pady=3
        )
        frame_borda_voltar.pack(side="left", padx=30, pady=20)

        tk.Button(
            frame_borda_voltar,
            text="⏮ VOLTAR AO MENU PRINCIPAL",
            font=("Arial", 24, "bold"),
            bg="#EF6C00",
            fg="white",
            activebackground="#FF6F00",
            activeforeground="white",
            height=3,
            width=32,
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.voltar
        ).pack(fill="x")

        # Botão Ajuda com borda
        frame_borda_ajuda = tk.Frame(
            rodape,
            bg="#0D47A1",  # Tom mais escuro da cor do botão
            padx=3,
            pady=3
        )
        frame_borda_ajuda.pack(side="left", padx=10, pady=20)

        tk.Button(
            frame_borda_ajuda,
            text="❓ AJUDA",
            font=("Arial", 20, "bold"),
            bg="#1976D2",
            fg="white",
            activebackground="#1565C0",
            activeforeground="white",
            height=3,
            width=20,
            bd=0,
            relief="flat",
            cursor="hand2",
            command=self.exibir_ajuda
        ).pack(fill="x")

        self._timer_inatividade = None
        self.bind_all("<Any-KeyPress>", lambda e: self.iniciar_timer_inatividade())
        self.bind_all("<Any-Button>",   lambda e: self.iniciar_timer_inatividade())

    def exibir_ajuda(self):
        help_win = tk.Toplevel(self)
        help_win.title("Ajuda")
        help_win.configure(bg="#FAF3E0")
        help_win.transient(self)
        help_win.grab_set()

        # ─── ajuste de tamanho e posição ───────────────────────────────────
        largura, altura = 500, 380
        sw = help_win.winfo_screenwidth()
        sh = help_win.winfo_screenheight()
        x = (sw - largura) // 2
        y = (sh - altura) // 2
        help_win.geometry(f"{largura}x{altura}+{x}+{y}")
        # ────────────────────────────────────────────────────────────────────

        # Cabeçalho
        header = tk.Frame(help_win, bg="#1976D2", height=50)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Ajuda",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#1976D2"
        ).pack(pady=10)

        # Conteúdo
        body = tk.Frame(help_win, bg="#FAF3E0", padx=20, pady=10)
        body.pack(fill="both", expand=True)

        instrucoes = [
            "Toque em uma categoria na barra superior para ver produtos.",
            "Clique em qualquer card de produto para adicioná-lo ao carrinho.",
            'Use [+] e [–] no carrinho para ajustar quantidades.',
            "Toque no ícone 🗑️ ao lado do item para removê-lo.",
            "Ao finalizar, selecione PIX, CRÉDITO ou DÉBITO para pagar."
        ]
        for linha in instrucoes:
            lbl = tk.Label(
                body,
                text="• " + linha,
                font=("Arial", 12),
                bg="#FAF3E0",
                anchor="w",
                justify="left"
            )
            lbl.pack(fill="x", pady=2)

        # Botão fechar
        tk.Button(
            help_win,
            text="Fechar",
            font=("Arial", 12, "bold"),
            bg="#1976D2",
            fg="white",
            bd=0,
            command=help_win.destroy
        ).pack(pady=10)

    # -------------------------------------------------------------------
    # MÉTODOS DE TIMER DE INATIVIDADE
    # -------------------------------------------------------------------
    def iniciar_timer_inatividade(self):
        self.cancelar_timer_inatividade()
        self._timer_inatividade = self.after(240_000, self._resetar_para_tela_inicial)

    def cancelar_timer_inatividade(self):
        if self._timer_inatividade:
            self.after_cancel(self._timer_inatividade)
            self._timer_inatividade = None

    def _resetar_para_tela_inicial(self):
        self.sacola.clear()
        print(
            f"[DEBUG] Total atual no carrinho após 4 min: R$ {sum(item['valor'] * item['quantidade'] for item in self.sacola):.2f}")

        self.controller.show_frame('TelaEmpresas')

    # -------------------------------------------------------------------
    # MÉTODOS DE CARREGAMENTO (Empresas → Categorias → Produtos)
    # -------------------------------------------------------------------
    def _selecionar_e_carregar(self, grupo_id: int):
        self.grupo_id = grupo_id

        # Atualiza os botões da barra de categorias
        for gid_, btn in self.bot_categorias.items():
            if gid_ == grupo_id:
                btn.config(
                    bg="#880E4F",  # destaque forte para o selecionado
                    fg="white",
                    font=("Arial", 13, "bold"),
                    relief="raised",
                    bd=4,
                    highlightthickness=2,
                    highlightbackground="#FFFFFF"
                )
            else:
                btn.config(
                    bg="#B71C1C",  # cor padrão inativa
                    fg="white",
                    font=("Arial", 12, "bold"),
                    relief="flat",
                    bd=0,
                    highlightthickness=0
                )

        self.carregar_produtos(grupo_id)

    def set_empresa(self, empresa_id: int):
        self.empresa_id = empresa_id
        self.sacola.clear()
        self.carrinho = Carrinho(self.sacola)
        self._atualizar_carrinho()

        for w in self.frame_categorias.winfo_children():
            w.destroy()
        self.bot_categorias.clear()

        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("SELECT id, nome FROM grupos WHERE empresa_id = ?", (self.empresa_id,))
        grupos = cur.fetchall()
        conn.close()

        cores_grupos = ["#1976D2", "#388E3C", "#EF6C00", "#8E24AA", "#0097A7"]
        cor_padrao_fg = "#FFFFFF"
        self.cor_original_botao = {}

        self.grupo_id = None  # Nenhuma categoria ativa

        # Limpa os produtos visíveis
        for w in self.frame_produtos.winfo_children():
            w.destroy()

        for gid, nome in grupos:
            # Dentro de set_empresa(), substitua a criação de btn por isto:
            btn = tk.Button(
                self.frame_categorias,
                text=nome.upper(),
                font=("Arial", 12, "bold"),
                bg="#C62828",
                fg="white",
                activebackground="#B71C1C",
                activeforeground="white",
                relief="flat",
                bd=0,
                padx=20,  # largura da “pill”
                pady=6,  # altura menor para canto suave
                command=lambda g=gid: self._selecionar_e_carregar(g)
            )
            btn.pack(side="left", padx=8, pady=6)

            self.bot_categorias[gid] = btn

        # Atualizar o nome da empresa no topo
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute("SELECT nome FROM empresas WHERE id = ?", (self.empresa_id,))
        empresa_row = cur.fetchone()
        conn.close()

        if empresa_row:
            self.lbl_empresa_nome.config(text=empresa_row[0].upper())

    def carregar_produtos(self, grupo_id: int):
        # 1) Limpa o frame de produtos
        for w in self.frame_produtos.winfo_children():
            w.destroy()

        # 2) Busca no banco
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute(
            "SELECT id, nome, preco, foto FROM produtos WHERE grupo_id = ?",
            (grupo_id,)
        )
        produtos = cur.fetchall()
        conn.close()

        colunas = self.num_colunas

        # 3) Loop único que monta cada card
        for idx, (pid, nome, preco, foto) in enumerate(produtos):
            linha, coluna = divmod(idx, colunas)

            # cartão único, sem sombra, cor de fundo igual ao container
            card = tk.Frame(self.frame_produtos, bg="#FAF3E0", width=200, height=220)
            card.grid(row=linha, column=coluna, padx=15, pady=15)
            card.grid_propagate(False)

            # tenta resolver caminhos relativos ao projeto
            possiveis = [
                foto,
                os.path.join("static", "imagens", os.path.basename(foto or "")),
                os.path.join(os.getcwd(), "static", "imagens", os.path.basename(foto or ""))
            ]
            foto_real = next((p for p in possiveis if p and os.path.exists(p)), "")

            # Imagem do produto (ou placeholder)
            # ─── Imagem do produto (ou placeholder) ────────────────────────
            if foto_real:
                try:
                    # 1) Carrega, converte para RGBA e redimensiona
                    pil_img = (
                        Image.open(foto_real)
                        .convert("RGBA")
                        .resize((150, 150), Image.LANCZOS)
                    )
                    # 2) Cria o PhotoImage para o Tkinter
                    img_tk = ImageTk.PhotoImage(pil_img)

                    # 3) Exibe no Label e guarda referência pra não ser coletado
                    lbl_img = tk.Label(card, image=img_tk, bg="#FAF3E0")
                    lbl_img.image = img_tk

                except Exception:
                    # Fallback caso algo dê errado ao abrir o PNG
                    lbl_img = tk.Label(
                        card,
                        text="Sem Imagem",
                        font=FONTE_PRODUTO,
                        fg="#A0A0A0",
                        bg="#FAF3E0"
                    )
            else:
                # Caso não encontre arquivo
                lbl_img = tk.Label(
                    card,
                    text="Sem Imagem",
                    font=FONTE_PRODUTO,
                    fg="#A0A0A0",
                    bg="#FAF3E0"
                )

            lbl_img.pack(pady=(10, 5))


            lbl_nome = tk.Label(
                card,
                text=nome,
                font=("Arial", 12, "bold"),
                fg="#444444",
                bg="#FAF3E0",
                wraplength=180,
                justify="center"
            )
            lbl_nome.pack(pady=(4, 4))  # espaçamento apertado, só pra separar da imagem e do preço

            # → Em seguida, o preço
            lbl_preco = tk.Label(
                card,
                text=f"R$ {preco:.2f}",
                font=("Arial", 11, "bold"),
                fg="#2E7D32",
                bg="#FAF3E0"
            )
            lbl_preco.pack(pady=(2, 6))

            # Bind para adicionar ao carrinho ao clicar em qualquer parte do card
            def _bind_add(widget):
                widget.bind(
                    "<Button-1>",
                    lambda e, p=(pid, nome, preco): self.adicionar_ao_carrinho(p)
                )

            _bind_add(card)
            for child in card.winfo_children():
                _bind_add(child)

    # -------------------------------------------------------------------
    # MÉTODOS DO CARRINHO (Adicionar / Atualizar / Limpar)
    # -------------------------------------------------------------------
    def adicionar_ao_carrinho(self, produto: tuple):
        pid, nome, valor = produto
        for item in self.sacola:
            if item['id'] == pid:
                item['quantidade'] += 1
                break
        else:
            self.sacola.append({'id': pid, 'nome': nome, 'valor': valor, 'quantidade': 1})
        self._atualizar_carrinho()

    def _atualizar_carrinho(self):
        for w in self.lista_itens.winfo_children():
            w.destroy()

        total = 0.0
        for idx in reversed(range(len(self.sacola))):
            item = self.sacola[idx]

            linha = tk.Frame(self.lista_itens, bg="#FFF8F0")
            linha.pack(fill="x", pady=4, padx=5)

            # Nome
            nome_lbl = tk.Label(
                linha,
                text=item['nome'],
                font=("Arial", 12, "bold"),
                bg="#FFF8F0",
                fg="#222222",
                anchor="w"
            )
            nome_lbl.pack(side="left", fill="x", expand=True)

            # Botão remover
            tk.Button(
                linha,
                text="🗑️",
                font=("Arial", 12),
                bg="#FFF8F0",
                fg="#C62828",
                bd=0,
                command=lambda i=idx: self._remover_item(i)
            ).pack(side="right", padx=4)

            # Quantidade
            tk.Label(
                linha,
                text=str(item['quantidade']),
                font=("Arial", 12, "bold"),
                bg="#FFF8F0",
                width=3
            ).pack(side="right", padx=(0, 4))

            # Botões + e -
            tk.Button(
                linha,
                text="+",
                font=("Arial", 12, "bold"),
                bg="#E0E0E0",
                width=2,
                command=lambda i=idx: self._alterar_quantidade(i, +1)
            ).pack(side="right", padx=(0, 2))

            tk.Button(
                linha,
                text="-",
                font=("Arial", 12, "bold"),
                bg="#E0E0E0",
                width=2,
                command=lambda i=idx: self._alterar_quantidade(i, -1)
            ).pack(side="right", padx=(0, 4))

            subtotal = item['quantidade'] * item['valor']
            total += subtotal
            tk.Label(
                linha,
                text=f"R$ {subtotal:.2f}",
                font=("Arial", 12, "bold"),
                bg="#FFF8F0",
                fg="#2E7D32"
            ).pack(side="right", padx=6)

        self.label_total.config(
            text=f"Subtotal: R$ {total:.2f}",
            font=("Arial", 14, "bold"),
            fg="#2E7D32",
            bg="#FFF8F0"
        )

        # Exibir ou ocultar o botão CONTINUAR conforme itens no carrinho
        if len(self.sacola) > 0:
            # mostra frame + botão
            self.frame_borda_continuar.pack(fill="x", padx=5, pady=(0, 10))
            self.btn_continuar.pack(fill="x")
        else:
            # esconde ambos
            self.btn_continuar.pack_forget()
            self.frame_borda_continuar.pack_forget()

    def _alterar_quantidade(self, indice: int, delta: int):
        item = self.sacola[indice]
        item["quantidade"] += delta
        if item["quantidade"] <= 0:
            self.sacola.pop(indice)
        self._atualizar_carrinho()

    def _remover_item(self, indice: int):
        self.sacola.pop(indice)
        self._atualizar_carrinho()

    # -------------------------------------------------------------------
    # FLUXO DE PAGAMENTO (PIX / CRÉDITO / DÉBITO)
    # -------------------------------------------------------------------
    def exibir_conferencia(self):
        """
        Abre um Toplevel em tela cheia para confirmar o pedido e
        escolher forma de pagamento.
        """
        if not self.sacola:
            messagebox.showwarning("Carrinho vazio", "Adicione itens antes de confirmar.")
            return

        total = sum(item['valor'] * item['quantidade'] for item in self.sacola)

        # Container principal
        self.confirm_frame = tk.Frame(self, bg="#FAF3E0")
        self.confirm_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Nome da empresa
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT nome FROM empresas WHERE id = ?", (self.empresa_id,)).fetchone()
        conn.close()
        if row:
            tk.Label(
                self.confirm_frame,
                text=row[0].upper(),
                font=("Arial", 22, "bold"),
                fg="#1976D2",
                bg="#FAF3E0"
            ).pack(pady=(10,5))

        # Cabeçalho
        hdr = tk.Frame(self.confirm_frame, bg="#1976D2", height=80)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="Selecione a forma de pagamento",
            font=("Arial", 24, "bold"),
            fg="white",
            bg="#1976D2"
        ).pack(pady=20)

        # Área PIX: valor + QR
        self.pix_area = tk.Frame(self.confirm_frame, bg="#FAF3E0")
        self.pix_area.pack(pady=(30,10))
        self.lbl_total_pix = tk.Label(
            self.pix_area,
            text=f"Total: R$ {total:.2f}",
            font=("Arial", 26, "bold"),
            bg="#FAF3E0",
            fg="#2E7D32"
        )
        self.lbl_total_pix.pack(pady=(0,15))
        self.qr_container = tk.Frame(self.pix_area, bg="#FAF3E0")
        self.qr_container.pack()

        # Barra de botões única
        btn_bar = tk.Frame(self.confirm_frame, bg="#FAF3E0")
        btn_bar.pack(pady=(25, 10))
        btn_cfg = {"font": ("Arial", 16, "bold"), "height": 2, "width": 12}

        # Handlers internos
        def clique_pix():
            for w in self.msg_area.winfo_children(): w.destroy()
            self._exibir_pix(self.qr_container)

        def clique_credito():
            from tela_credito import mensagem_credito
            mensagem_credito(self.qr_container, self.controller)

        def clique_debito():
            from tela_debito import mensagem_debito
            mensagem_debito(self.qr_container, self.controller)

        def clique_voltar():
            self.confirm_frame.destroy()

        def clique_cancelar():
            self.sacola.clear()
            self._atualizar_carrinho()
            self.confirm_frame.destroy()

        # Botões com comando embutido
        self.btn_pix = tk.Button(btn_bar, text="PIX", command=clique_pix, bg="#D32F2F", fg="white", **btn_cfg)
        self.btn_credito = tk.Button(btn_bar, text="CRÉDITO", command=clique_credito, bg="#1565C0", fg="white",
                                     **btn_cfg)
        self.btn_debito = tk.Button(btn_bar, text="DÉBITO", command=clique_debito, bg="#00695C", fg="white", **btn_cfg)
        self.btn_voltar = tk.Button(btn_bar, text="← VOLTAR", command=clique_voltar, bg="#757575", fg="white",
                                    **btn_cfg)
        self.btn_cancelar = tk.Button(btn_bar, text="CANCELAR", command=clique_cancelar, bg="#B71C1C", fg="white",
                                      **btn_cfg)
        for btn in (self.btn_pix, self.btn_credito, self.btn_debito, self.btn_voltar, self.btn_cancelar):
            btn.pack(side="left", padx=12)

        # Área de mensagem abaixo dos botões
        self.msg_area = tk.Frame(self.confirm_frame, bg="#FAF3E0")
        self.msg_area.pack(fill="x", pady=(10, 20))
        # ----- FIM do layout de conferência -----------------------------

    def _exibir_pix(self, pix_area):
        """
        Quando o usuário clica em PIX: limpa pix_area e chama
        exibir_pagamento_pix() para desenhar o QR, a instrução
        e o temporizador dentro de pix_area.
        """
        for widget in pix_area.winfo_children():
            widget.destroy()

        try:
            total = sum(i['valor'] * i['quantidade'] for i in self.sacola)
            cobr = criar_cobranca(total, self.buscar_chave_pix())
            payload = cobr['pixCopiaECola']
            txid = cobr['txid']

            # Chama a função que desenha o QR dentro de pix_area
            exibir_pagamento_pix(
                controller=self.controller,
                container=pix_area,
                payload=payload,
                txid=txid,
                empresa_id=self.empresa_id,
                carrinho_itens=list(self.sacola)
            )
        except Exception as e:
            messagebox.showerror("Erro Pix", f"Falha ao criar cobrança Pix:\n{e}")

    def _exibir_credito(self, container):
        for widget in container.winfo_children():
            widget.destroy()
        # passe também o controller
        mensagem_credito(container, self.controller)

    def _exibir_debito(self, container):
        for widget in container.winfo_children():
            widget.destroy()
        # passe também o controller
        mensagem_debito(container, self.controller)

    def buscar_chave_pix(self) -> str:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT chave_pix FROM empresas WHERE id = ?",
            (self.empresa_id,)
        ).fetchone()
        conn.close()

        if not row or not row[0]:
            raise ValueError("Chave Pix não cadastrada para esta empresa.")
        return row[0]

    # -------------------------------------------------------------------
    # MÉTODOS DE NAVEGAÇÃO
    # -------------------------------------------------------------------
    def voltar(self):
        self.controller.show_frame('TelaEmpresas')

    def encerrar_totem(self, event=None):
        os._exit(0)


# Ajuste para que, se alguém importar TelaVendas em tela_inicial.py, ela seja registrada
try:
    import tela_inicial
    tela_inicial.TelaVendas = TelaVendas
except ImportError:
    pass