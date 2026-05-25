import os, time
p='mapa_inicial.png'
if os.path.exists(p):
    print('mtime', time.ctime(os.path.getmtime(p)))
    print('size', os.path.getsize(p))
else:
    print('no file')
