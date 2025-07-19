import tkinter as tk

def forcar_tela_cheia(win: tk.Tk | tk.Toplevel):
    """Torna a janela full‑screen, sem moldura, bloqueando Alt‑F4/Esc.
    Para sair durante os testes, press. Ctrl+Shift+Q."""
    win.attributes('-fullscreen', True)       # ocupa todo o monitor
    win.overrideredirect(True)                # remove barra de título
    win.focus_set()
    # Desabilita atalhos normais
    win.bind('<Alt-F4>',  lambda e: 'break')
    win.bind('<Escape>',  lambda e: 'break')
    # Saída de emergência p/ o desenvolvedor
    win.bind('<Control-Shift-Q>', lambda e: win.destroy())
