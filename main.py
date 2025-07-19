import tkinter as tk

from tela_inicial import TelaInicial, FONTE_H1, FONTE_BTN
from tela_vendas import TelaVendas
from tela_pix import exibir_pagamento_pix

import cadastro_empresas
import cadastro_grupos
import cadastro_produtos


class TelaMenu(tk.Frame):
    """
    Menu principal com opções para iniciar o totem e acessar cadastros.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#FFFFFF")  # fundo branco para visual mais clean
        self.controller = controller

        # Título do menu
        lbl_title = tk.Label(self, text="Menu Principal", font=FONTE_H1, bg="#FFFFFF")
        lbl_title.pack(pady=40)

        # Argumentos comuns aos botões
        btn_args = {"font": FONTE_BTN, "width": 30, "height": 2, "padx": 10, "pady": 10}

        # Botões de navegação
        tk.Button(
            self,
            text="Iniciar Totem de Vendas",
            command=lambda: controller.show_frame("TelaEmpresas"),
            **btn_args
        ).pack(pady=5)

        tk.Button(
            self,
            text="Cadastrar Empresas",
            command=lambda: cadastro_empresas.abrir_interface(
                callback_voltar=lambda: controller.show_frame("TelaMenu")
            ),
            **btn_args
        ).pack(pady=5)

        tk.Button(
            self,
            text="Cadastrar Grupos",
            command=lambda: cadastro_grupos.abrir_interface(
                callback_voltar=lambda: controller.show_frame("TelaMenu")
            ),
            **btn_args
        ).pack(pady=5)

        tk.Button(
            self,
            text="Cadastrar Produtos",
            command=lambda: cadastro_produtos.abrir_interface(
                callback_voltar=lambda: controller.show_frame("TelaMenu")
            ),
            **btn_args
        ).pack(pady=5)

        tk.Button(
            self,
            text="Sair",
            command=controller.destroy,
            **btn_args
        ).pack(pady=20)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Totem de Autoatendimento")
        self.configure(bg="#FFFFFF")  # fundo branco consistente

        
        # Fullscreen (esconde bordas e taskbar)
        self.attributes('-fullscreen', True)
        # Tecla ESC para sair do fullscreen (manutenção)
        self.bind('<Escape>', lambda e: self.attributes('-fullscreen', False))
        # Tecla de atalho para sair completamente do app
        self.bind_all('<Control-q>', lambda e: self.destroy())
        # <<< Fim do bloco de fullscreen

        # Container para as telas
        container = tk.Frame(self, bg="#FFFFFF")
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        # Registro dos frames
        self.frames = {}
        for Cls, name in [
            (TelaMenu, "TelaMenu"),
            (TelaInicial, "TelaEmpresas"),
            (TelaVendas, "TelaVendas"),
        ]:
            frame = Cls(parent=container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Exibe o menu principal
        self.show_frame("TelaMenu")

    def show_frame(self, name: str):
        """Traz o frame especificado para frente."""
        frame = self.frames.get(name)
        if frame:
            frame.tkraise()


if __name__ == "__main__":
    App().mainloop()
