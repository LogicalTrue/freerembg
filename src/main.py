# main.py

import tkinter as tk
from ui import ApplicationUI
from multiprocessing import freeze_support

if __name__ == "__main__":
    # Esta línea es importante para que multiprocessing funcione bien en ejecutables
    freeze_support() 
    
    root = tk.Tk()
    app = ApplicationUI(root)
    root.mainloop()