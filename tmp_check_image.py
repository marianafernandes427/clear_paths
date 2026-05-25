from PIL import Image
import os
p='mapa_inicial.png'
if os.path.exists(p):
    im=Image.open(p)
    print('exists', os.path.getsize(p), 'bytes; size', im.size, 'mode', im.mode)
else:
    print('missing')
