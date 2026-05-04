import folium
import osmnx as ox
import networkx as nx

G = ox.graph_from_xml("proj/map.osm")

orig = list(G.nodes)[0]
dest = list(G.nodes)[-1]

path = nx.shortest_path(G, orig, dest, weight="length")

m = folium.Map(location=[41.441, -8.295], zoom_start=13)

coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]

folium.PolyLine(coords, color="red", weight=5).add_to(m)

folium.Marker(coords[0], popup="Origem").add_to(m)
folium.Marker(coords[-1], popup="Destino").add_to(m)

m.save("mapa.html")