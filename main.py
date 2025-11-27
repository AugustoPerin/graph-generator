import tkinter as tk
from tkinter import ttk
from graph_editor import GraphEditor

def main():
    root = tk.Tk()
    root.title("Graph Generator")
    root.geometry("1200x800")

    # Set up the main styles
    style = ttk.Style()
    style.theme_use('clam')

    app = GraphEditor(root)
    app.pack(fill=tk.BOTH, expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
