import os
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import osmnx as ox
import networkx as nx
try:
    from PIL import Image, ImageTk
    _PIL_AVAILABLE = True
except Exception:
    _PIL_AVAILABLE = False

from integrate import (
    preparar_grafo,
    aplicar_custo_por_perfil_nx,
    criar_heur_fn,
    calcular_dist_e_custo,
)
from problema import ProblemaRotaUrbana
from estado import PERFIS


def mostrar_mapa_no_interface(G, rota_or_none, label, saida_png="rota_interface.png"):
    """Desenha no painel direito um mapa do grafo (ou uma rota, se fornecida).

    G: grafo networkx projetado
    rota_or_none: lista de nós representando a rota, ou None para desenhar o grafo todo
    label: widget Tkinter onde inserir a imagem
    """
    # gerar PNG do mapa (pode ser chamado em thread background)
    abs_path = os.path.abspath(saida_png)
    try:
        if rota_or_none:
            fig, ax = ox.plot_graph_route(
                G,
                rota_or_none,
                route_color="red",
                route_linewidth=4,
                node_size=0,
                bgcolor="white",
                show=False,
                close=False,
            )
        else:
            fig, ax = ox.plot_graph(
                G,
                node_size=0,
                bgcolor="white",
                show=False,
                close=False,
            )

        fig.savefig(abs_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
    except Exception as e:
        # geração do ficheiro falhou
        try:
            label.after(0, lambda: label.configure(text="Erro ao gerar mapa: " + str(e)))
        except Exception:
            pass
        return

    # agora pedir ao thread principal para carregar a imagem no label (Tkinter não é thread-safe)
    def _load():
        try:
            if os.path.exists(abs_path):
                try:
                    if _PIL_AVAILABLE:
                        pil = Image.open(abs_path)
                        try:
                            label.update_idletasks()
                            w = label.winfo_width()
                            h = label.winfo_height()
                            if w < 10 or h < 10:
                                w, h = 500, 500
                        except Exception:
                            w, h = 500, 500
                        pil = pil.resize((w, h), Image.LANCZOS)
                        img = ImageTk.PhotoImage(pil)
                    else:
                        img = tk.PhotoImage(file=abs_path)

                    label.configure(image=img, text="")
                    label.image = img
                except Exception as e:
                    label.configure(text="Mapa gerado em arquivo:\n" + abs_path)
                    try:
                        messagebox.showerror("Erro a carregar imagem", str(e))
                    except Exception:
                        pass
            else:
                label.configure(text="Não foi possível gerar o mapa.")
        except Exception:
            pass

    try:
        label.after(0, _load)
    except Exception:
        pass

def _carregar_e_mostrar_inicial(label):
    try:
        global _G_cache, _grafo_dict_cache, _coords_cache
        if "_G_cache" not in globals() or _G_cache is None:
            _G_cache, _grafo_dict_cache, _coords_cache = preparar_grafo()
        mostrar_mapa_no_interface(_G_cache, None, label, saida_png="mapa_inicial.png")
    except Exception as e:
        try:
            messagebox.showerror("Erro ao carregar mapa inicial", str(e))
        except Exception:
            pass


# -----------------------------
# FUNÇÃO PRINCIPAL
# -----------------------------

def calcular_rota():
    origem = entrada_origem.get().strip()
    destino = entrada_destino.get().strip()
    perfil_text = perfil_var.get()

    def parse_coord(text: str):
        text = text.strip()
        if text in locais:
            return locais[text]
        try:
            lat, lon = text.split(",")
            return float(lat), float(lon)
        except Exception:
            return None

    o_coord = parse_coord(origem)
    d_coord = parse_coord(destino)

    if o_coord is None or d_coord is None:
        messagebox.showerror("Erro", "Origem ou destino inválido. Use um local predefinido ou 'lat,lon'.")
        return

    # mapar perfil do UI para PERFIS
    perfil_map = {
        "Utilizador Normal": "padrao",
        "Idoso": "idoso",
        "Mobilidade Reduzida": "cadeira_rodas",
        "Sensível à Poluição": "crianca",
        "Atleta": "atleta",
    }

    perfil_key = perfil_map.get(perfil_text, "padrao")
    perfil = PERFIS.get(perfil_key, PERFIS["padrao"])
    algoritmo = algoritmo_var.get()

    # carregar grafo (lazy cache)
    global _G_cache, _grafo_dict_cache, _coords_cache
    if "_G_cache" not in globals() or _G_cache is None:
        msg = "A carregar grafo — isto pode demorar alguns segundos..."
        messagebox.showinfo("A carregar", msg)
        _G_cache, _grafo_dict_cache, _coords_cache = preparar_grafo()

    G = _G_cache
    grafo_dict = _grafo_dict_cache

    print(f"[DEBUG] Grafo tem {G.number_of_nodes()} nós e {G.number_of_edges()} arestas")

    # aplicar custos para o perfil
    aplicar_custo_por_perfil_nx(G, perfil)
    
    # Verificar se as arestas têm "custo" agora
    arestas_com_custo = 0
    custos_sample = []
    for u, v, k, data in list(G.edges(keys=True, data=True))[:5]:
        if "custo" in data:
            arestas_com_custo += 1
            custos_sample.append((u, v, data.get("custo"), data.get("distancia")))
    print(f"[DEBUG] Arestas com 'custo': {arestas_com_custo} / primeiras 5: {custos_sample}")

    try:
        origem_node = ox.distance.nearest_nodes(G, o_coord[1], o_coord[0])
        destino_node = ox.distance.nearest_nodes(G, d_coord[1], d_coord[0])

        print(f"[DEBUG] Origem coord: {o_coord}, nó: {origem_node}")
        print(f"[DEBUG] Destino coord: {d_coord}, nó: {destino_node}")
        
        # Mostrar as coordenadas dos nós encontrados
        if origem_node in G.nodes:
            orig_coords = (G.nodes[origem_node]['y'], G.nodes[origem_node]['x'])
            print(f"[DEBUG] Coordenadas do nó origem: {orig_coords}")
        
        if destino_node in G.nodes:
            dest_coords = (G.nodes[destino_node]['y'], G.nodes[destino_node]['x'])
            print(f"[DEBUG] Coordenadas do nó destino: {dest_coords}")
        
        # Mostrar sucessores do nó de origem
        sucessores_origem = list(G.successors(origem_node))
        print(f"[DEBUG] Sucessores de {origem_node}: {sucessores_origem[:5]}... (total: {len(sucessores_origem)})")
        
        # Se são o mesmo nó, tentar encontrar alternativas
        if origem_node == destino_node:
            print(f"[WARNING] Origem e destino resolvem para o mesmo nó!")
            # Tentar encontrar vizinhos do nó para criar uma rota real
            if len(sucessores_origem) > 0:
                destino_node = sucessores_origem[0]
                print(f"[DEBUG] Usando sucessor como destino alternativo: {destino_node}")

        problema = ProblemaRotaUrbana(grafo=grafo_dict, coords=_coords_cache, no_origem=origem_node, no_destino=destino_node, perfil=perfil)
        heur = criar_heur_fn(__import__("heuristicas").criar_heuristica("euclidiana", perfil=perfil), problema, perfil)

        t0 = time.time()
        if algoritmo == "Dijkstra":
            rota = nx.shortest_path(G, origem_node, destino_node, weight="custo")
        else:
            rota = nx.astar_path(G, origem_node, destino_node, heuristic=heur, weight="custo")
        t1 = time.time()

        print(f"[DEBUG] Rota encontrada com {len(rota)} nós")
        print(f"[DEBUG] Rota: {rota[:5]}..." if len(rota) > 5 else f"[DEBUG] Rota: {rota}")

        distancia, custo = calcular_dist_e_custo(G, rota)
        print(f"[DEBUG] Distância: {distancia}, Custo: {custo}")
        
        mostrar_mapa_no_interface(G, rota, mapa_label)

        resumo = (
            f"Origem: {origem}\nDestino: {destino}\nPerfil: {perfil_text}\n"
            f"Distância: {distancia/1000:.2f} km\nCusto: {custo:.2f}\nTempo: {t1-t0:.3f}s\nNós: {len(rota)}"
        )

        messagebox.showinfo("Rota calculada", resumo)

    except Exception as e:
        messagebox.showerror("Erro na procura", str(e))


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
# LOCAIS PREDEFINIDOS
# -----------------------------
locais = {
    "Campus de Azurém": (41.4446, -8.2944),
    "Largo do Toural": (41.4411, -8.2936),
    "Estação CP de Guimarães": (41.4358, -8.2956),
    "Castelo de Guimarães": (41.4479, -8.2908),
    "Centro Cultural Vila Flor": (41.4377, -8.2966),
}

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

entrada_origem = ttk.Combobox(frame, width=40, font=("Arial", 11), state="readonly")
entrada_origem["values"] = tuple(locais.keys())
entrada_origem.current(0)
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

entrada_destino = ttk.Combobox(frame, width=40, font=("Arial", 11), state="readonly")
entrada_destino["values"] = tuple(locais.keys())
entrada_destino.current(1)
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
# ALGORITMO
# -----------------------------

label_algoritmo = tk.Label(
    frame,
    text="Algoritmo de Busca",
    font=("Arial", 11, "bold"),
    bg="white"
)

label_algoritmo.grid(row=6, column=0, sticky="w", pady=(20, 5))

algoritmo_var = tk.StringVar()
combo_algoritmo = ttk.Combobox(
    frame,
    textvariable=algoritmo_var,
    width=37,
    state="readonly"
)

combo_algoritmo["values"] = (
    "A*",
    "Dijkstra"
)
combo_algoritmo.current(0)
combo_algoritmo.grid(row=7, column=0)

# -----------------------------
# CRITÉRIOS
# -----------------------------

label_criterios = tk.Label(
    frame,
    text="Critérios da Rota",
    font=("Arial", 11, "bold"),
    bg="white"
)

label_criterios.grid(row=8, column=0, sticky="w", pady=(25, 10))

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

check1.grid(row=9, column=0, sticky="w")

check2 = tk.Checkbutton(
    frame,
    text="Menor Poluição",
    variable=var_poluicao,
    bg="white"
)

check2.grid(row=10, column=0, sticky="w")

check3 = tk.Checkbutton(
    frame,
    text="Mais Sombra",
    variable=var_sombra,
    bg="white"
)

check3.grid(row=11, column=0, sticky="w")

check4 = tk.Checkbutton(
    frame,
    text="Evitar Escadas",
    variable=var_escadas,
    bg="white"
)

check4.grid(row=12, column=0, sticky="w")

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

botao.grid(row=13, column=0, pady=30)

# -----------------------------
# MAPA (PLACEHOLDER)
# -----------------------------

mapa_frame = tk.Frame(
    frame,
    bg="#cbd5e1",
    width=500,
    height=500
)

mapa_frame.grid(row=0, column=1, rowspan=14, padx=40, sticky="nsew")
mapa_frame.grid_propagate(False)  # manter tamanho fixo

mapa_label = tk.Label(
    mapa_frame,
    text="Mapa da Rede Urbana",
    font=("Arial", 16, "bold"),
    bg="#cbd5e1",
    fg="#334155"
)

mapa_label.pack(fill="both", expand=True)  # preencher o frame

# carregar mapa inicial em segundo plano para não bloquear a UI
try:
    threading.Thread(target=_carregar_e_mostrar_inicial, args=(mapa_label,), daemon=True).start()
except Exception:
    pass

# Tentativa de carregar imediatamente qualquer ficheiro já gerado (ou aguardar até aparecer)
def _try_load_existing(label, path="mapa_inicial.png", attempts=20, delay_ms=500):
    def _attempt(n):
        if n <= 0:
            return
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            try:
                if _PIL_AVAILABLE:
                    pil = Image.open(abs_path)
                    # usar as dimensões do label/frame
                    try:
                        label.update_idletasks()
                        w = label.winfo_width()
                        h = label.winfo_height()
                        if w < 10 or h < 10:
                            w, h = 500, 500
                    except Exception:
                        w, h = 500, 500
                    pil = pil.resize((w, h), Image.LANCZOS)
                    img = ImageTk.PhotoImage(pil)
                else:
                    img = tk.PhotoImage(file=abs_path)
                label.configure(image=img, text="")
                label.image = img
                return
            except Exception as e:
                # falha ao carregar — agendar nova tentativa
                pass
        # agendar nova tentativa
        label.after(delay_ms, lambda: _attempt(n - 1))

    _attempt(attempts)

# tentar carregar já existente sem esperar
try:
    _try_load_existing(mapa_label, "mapa_inicial.png", attempts=10, delay_ms=500)
except Exception:
    pass

# -----------------------------
# EXECUTAR
# -----------------------------

root.mainloop()

