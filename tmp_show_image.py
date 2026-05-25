import tkinter as tk
from PIL import Image, ImageTk
root = tk.Tk()
root.title('test image')
label = tk.Label(root, text='loading')
label.pack()
try:
    pil = Image.open('mapa_inicial.png')
    pil = pil.resize((600,600))
    img = ImageTk.PhotoImage(pil)
    label.configure(image=img, text='')
    label.image = img
except Exception as e:
    label.configure(text=str(e))
root.mainloop()
