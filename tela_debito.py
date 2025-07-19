import tkinter as tk
def mensagem_debito(container, controller):
    for w in container.winfo_children():
        w.destroy()

    card = tk.Frame(container, bg="white", bd=2, relief="groove")
    card.pack(padx=10, pady=10)

    tk.Label(
        card,
        text="Pagamento por Débito\nEm manutenção",
        font=("Arial", 18, "bold"),
        fg="#222",
        bg="white",
        justify="center",
        wraplength=300
    ).pack(padx=20, pady=20)

    tk.Button(
        card,
        text="OK",
        font=("Arial", 14, "bold"),
        bg="#D32F2F",
        fg="white",
        command=lambda: container.after(0, lambda: [w.destroy() for w in container.winfo_children()])
    ).pack(pady=10)
