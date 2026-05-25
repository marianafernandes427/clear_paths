import tkinter as tk
from tkinter import ttk, messagebox

# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------

def calcular_rota():
    origem = entrada_origem.get()
    destino = entrada_destino.get()
    perfil = perfil_var.get()

    criterios = []

    if var_distancia.get():
        criterios.append("Menor Distância")

    if var_poluicao.get():
        criterios.append("Menor Poluição")

    if var_sombra.get():
        criterios.append("Mais Sombra")

    if var_escadas.get():
        criterios.append("Evitar Escadas")

    resultado = f"""
Origem: {origem}
Destino: {destino}

Perfil: {perfil}

Critérios:
- {' | '.join(criterios)}

Rota calculada com sucesso!
"""

    messagebox.showinfo("Resultado", resultado)


# -----------------------------
# JANELA PRINCIPAL
# -----------------------------

root = tk.Tk()
root.title("SmartWalk Guimarães")
root.geometry("900x650")
root.configure(bg="#f1f5f9")

# -----------------------------
# TÍTULO
# -----------------------------

titulo = tk.Label(
    root,
    text="SmartWalk Guimarães",
    font=("Arial", 24, "bold"),
    bg="#f1f5f9",
    fg="#0f172a"
)

titulo.pack(pady=20)

subtitulo = tk.Label(
    root,
    text="Sistema Inteligente de Navegação Pedonal",
    font=("Arial", 12),
    bg="#f1f5f9",
    fg="#475569"
)

subtitulo.pack()

# -----------------------------
# FRAME PRINCIPAL
# -----------------------------

frame = tk.Frame(root, bg="white", padx=25, pady=25)
frame.pack(padx=30, pady=30, fill="both", expand=True)

# -----------------------------
# ORIGEM
# -----------------------------

label_origem = tk.Label(
    frame,
    text="Origem",
    font=("Arial", 11, "bold"),
    bg="white"
)

label_origem.grid(row=0, column=0, sticky="w")

entrada_origem = tk.Entry(frame, width=40, font=("Arial", 11))
entrada_origem.grid(row=1, column=0, pady=10)

# -----------------------------
# DESTINO
# -----------------------------

label_destino = tk.Label(
    frame,
    text="Destino",
    font=("Arial", 11, "bold"),
    bg="white"
)

label_destino.grid(row=2, column=0, sticky="w")

entrada_destino = tk.Entry(frame, width=40, font=("Arial", 11))
entrada_destino.grid(row=3, column=0, pady=10)

# -----------------------------
# PERFIL
# -----------------------------

label_perfil = tk.Label(
    frame,
    text="Perfil do Utilizador",
    font=("Arial", 11, "bold"),
    bg="white"
)

label_perfil.grid(row=4, column=0, sticky="w", pady=(20, 5))

perfil_var = tk.StringVar()

combo_perfil = ttk.Combobox(
    frame,
    textvariable=perfil_var,
    width=37,
    state="readonly"
)

combo_perfil["values"] = (
    "Utilizador Normal",
    "Idoso",
    "Mobilidade Reduzida",
    "Sensível à Poluição",
    "Atleta"
)

combo_perfil.current(0)
combo_perfil.grid(row=5, column=0)

# -----------------------------
# CRITÉRIOS
# -----------------------------

label_criterios = tk.Label(
    frame,
    text="Critérios da Rota",
    font=("Arial", 11, "bold"),
    bg="white"
)

label_criterios.grid(row=6, column=0, sticky="w", pady=(25, 10))

var_distancia = tk.BooleanVar(value=True)
var_poluicao = tk.BooleanVar(value=True)
var_sombra = tk.BooleanVar(value=True)
var_escadas = tk.BooleanVar()

check1 = tk.Checkbutton(
    frame,
    text="Menor Distância",
    variable=var_distancia,
    bg="white"
)

check1.grid(row=7, column=0, sticky="w")

check2 = tk.Checkbutton(
    frame,
    text="Menor Poluição",
    variable=var_poluicao,
    bg="white"
)

check2.grid(row=8, column=0, sticky="w")

check3 = tk.Checkbutton(
    frame,
    text="Mais Sombra",
    variable=var_sombra,
    bg="white"
)

check3.grid(row=9, column=0, sticky="w")

check4 = tk.Checkbutton(
    frame,
    text="Evitar Escadas",
    variable=var_escadas,
    bg="white"
)

check4.grid(row=10, column=0, sticky="w")

# -----------------------------
# BOTÃO
# -----------------------------

botao = tk.Button(
    frame,
    text="Calcular Melhor Rota",
    font=("Arial", 12, "bold"),
    bg="#0f172a",
    fg="white",
    padx=20,
    pady=10,
    command=calcular_rota
)

botao.grid(row=11, column=0, pady=30)

# -----------------------------
# MAPA (PLACEHOLDER)
# -----------------------------

mapa_frame = tk.Frame(
    frame,
    bg="#cbd5e1",
    width=450,
    height=400
)

mapa_frame.grid(row=0, column=1, rowspan=12, padx=40)

mapa_label = tk.Label(
    mapa_frame,
    text="Mapa da Rede Urbana",
    font=("Arial", 16, "bold"),
    bg="#cbd5e1",
    fg="#334155"
)

mapa_label.place(relx=0.5, rely=0.5, anchor="center")

# -----------------------------
# EXECUTAR
# -----------------------------

root.mainloop()

