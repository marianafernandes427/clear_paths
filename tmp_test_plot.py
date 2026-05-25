from integrate import preparar_grafo
import osmnx as ox
import networkx as nx
import os

G, grafo_dict, coords = preparar_grafo()
# analyze connectivity
G_undir = G.to_undirected()
components = list(nx.connected_components(G_undir))
print('nodes:', len(G.nodes), 'edges:', len(G.edges), 'components:', len(components))

if not components:
	print('Grafo vazio ou sem componentes.')
else:
	# pick largest component
	biggest = max(components, key=len)
	nodes_list = list(biggest)
	if len(nodes_list) < 2:
		print('Componente demasiado pequeno.')
	else:
		s = nodes_list[0]
		t = nodes_list[min(50, len(nodes_list)-1)]
		try:
			path_nodes = nx.shortest_path(G, s, t, weight='length')
			print('Plotting route between', s, t, 'path len', len(path_nodes))
			fig, ax = ox.plot_graph_route(G, path_nodes, route_color='red', show=False, close=False)
			path = os.path.abspath('test_route.png')
			fig.savefig(path, dpi=150, bbox_inches='tight')
			print('saved', os.path.exists(path), path)
		except Exception as e:
			print('Erro ao calcular/plotar rota:', e)
