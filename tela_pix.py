import tkinter as tk
import io
import threading
import time
import qrcode
from PIL import Image, ImageTk
from api import status_cobranca
import sqlite3
import datetime
from impressao_recibo import salvar_e_imprimir
import requests
import platform

def exibir_pagamento_pix(controller, container, payload: str, txid: str,
                         empresa_id: int, carrinho_itens: list):
    try:
        controller.frames["TelaVendas"].cancelar_timer_inatividade()
    except Exception:
        pass

    for w in container.winfo_children():
        w.destroy()
    container.configure(bg="white")
    # Buscar o nome da empresa
    conn = sqlite3.connect("totem.db")
    cur = conn.execute("SELECT nome FROM empresas WHERE id = ?", (empresa_id,))
    empresa = cur.fetchone()
    conn.close()

    qr = qrcode.make(payload)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    qr_size = int(controller.winfo_screenheight() * 0.18)
    img = Image.open(buf).resize((qr_size, qr_size))

    img_tk = ImageTk.PhotoImage(img)

    instr_lbl = tk.Label(
        container,
        text="➡ Escaneie o QR Code\npara pagar via PIX",
        font=("Arial", 16, "bold"),
        fg="#1976D2",
        bg="white",
        justify="center",
        wraplength=240,
        padx=10, pady=5
    )
    instr_lbl.pack(pady=(5, 5))

    frame_qr = tk.Frame(
        container,
        bd=2,
        relief="solid",
        highlightthickness=8,
        highlightbackground="#1976D2",
        bg="white"
    )
    frame_qr.pack(pady=10)
    lbl_qr = tk.Label(frame_qr, image=img_tk, bg="white")
    lbl_qr.image = img_tk
    lbl_qr.pack(padx=10, pady=10)

    timer_lbl = tk.Label(
        container,
        text="",
        font=("Arial", 14, "bold"),
        fg="#1976D2",
        bg="white"
    )
    timer_lbl.pack(pady=(10, 20))

    def atualizar_botoes_pagamento(segundos):
        try:
            tela = controller.frames["TelaVendas"]
            estado = "disabled" if 50 <= segundos <= 60 else "normal"
            for btn in [tela.btn_pix, tela.btn_credito, tela.btn_debito, tela.btn_voltar, tela.btn_cancelar]:
                btn.config(state=estado)
        except Exception as e:
            print(f"[ERRO] ao atualizar botões: {e}")

    def start_countdown(segundos):
        if segundos > 0:
            m, s = divmod(segundos, 60)
            timer_lbl.config(text=f"⌛ Tempo restante: {m:02d}:{s:02d}")
            timer_lbl.after(1000, start_countdown, segundos - 1)
        else:
            timer_lbl.config(text="⌛ Tempo restante: 00:00")
            container.after(2000, mostrar_expirado, controller, container)

    start_countdown(180)

    def monitorar():
        while True:
            try:
                st = status_cobranca(txid)
            except Exception:
                st = "PENDENTE"
            if st == "CONCLUIDA":
                senha = salvar_e_imprimir(empresa_id, carrinho_itens, txid)
                print(f"[DEBUG] Pix concluído, senha = {senha}")
                container.after(0, mostrar_sucesso, controller, container, senha)
                break
            time.sleep(3)

    threading.Thread(target=monitorar, daemon=True).start()

def mostrar_sucesso(controller, container, senha: int):
    try:
        tela = controller.frames["TelaVendas"]
        for nome in ["btn_pix", "btn_credito", "btn_debito", "btn_voltar", "btn_cancelar"]:
            if hasattr(tela, nome):
                getattr(tela, nome).config(state="disabled")
    except Exception:
        pass

    for w in container.winfo_children():
        try:
            w.destroy()
        except tk.TclError:
            pass

    tk.Label(
        container,
        text="✔ Pagamento Aprovado!\nRetire seu comprovante e dirija-se ao balcão",
        font=("Arial", 18, "bold"),
        fg="#4CAF50",
        bg="white",
        justify="center",
        wraplength=320,
        padx=10
    ).pack(pady=(60, 10))

    tk.Label(
        container,
        text=f"Sua senha: {senha:04}",
        font=("Arial", 16),
        bg="white"
    ).pack(pady=(0, 40))

    def voltar():
        controller.show_frame("TelaEmpresas")
        try:
            tela = controller.frames["TelaVendas"]
            for nome in ["btn_pix", "btn_credito", "btn_debito", "btn_voltar", "btn_cancelar"]:
                if hasattr(tela, nome):
                    getattr(tela, nome).config(state="normal")
            tela.iniciar_timer_inatividade()
        except Exception:
            pass

    container.after(10000, voltar)

def mostrar_expirado(controller, container):
    if not container.winfo_exists():
        return

    for w in container.winfo_children():
        try:
            w.destroy()
        except tk.TclError:
            pass

    tk.Label(
        container,
        text="⏰ Tempo expirado",
        font=("Arial", 18, "bold"),
        fg="#E53935",
        bg="white"
    ).pack(pady=20)

    def voltar_para_tela_vendas():
        try:
            tela = controller.frames["TelaVendas"]
            if hasattr(tela, "confirm_frame"):
                tela.confirm_frame.destroy()
                del tela.confirm_frame
            controller.show_frame("TelaVendas")
        except Exception as e:
            print(f"[ERRO ao voltar]: {e}")

    # Aguarda 3 segundos e retorna
    container.after(3000, voltar_para_tela_vendas)

