import qrcode
import socket
import tkinter as tk
from PIL import Image, ImageTk

def obter_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def gerar_qrcode(url):
    qr = qrcode.make(url)
    return qr

def exibir_qrcode_imagem(qr, url):
    janela = tk.Tk()
    janela.title("QR Code de Acesso ao Totem Web")

    tk.Label(janela, text=f"Acesse no Tablet:\n{url}", font=("Arial", 14), pady=10).pack()

    img = qr.resize((300, 300))
    img_tk = ImageTk.PhotoImage(img)
    lbl_img = tk.Label(janela, image=img_tk)
    lbl_img.image = img_tk
    lbl_img.pack(pady=10)

    tk.Button(janela, text="Fechar", command=janela.destroy).pack(pady=5)
    janela.mainloop()

if __name__ == "__main__":
    ip = obter_ip_local()
    url = f"http://{ip}:5000/empresas_web"
    qr = gerar_qrcode(url)
    exibir_qrcode_imagem(qr, url)
