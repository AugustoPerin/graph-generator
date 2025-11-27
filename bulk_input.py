import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

class BulkGraphDialog(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Bulk Graph Input")
        self.geometry("600x400")
        self.callback = callback
        
        self.create_widgets()
        
    def create_widgets(self):
        # Instructions
        lbl_instr = tk.Label(self, text="Enter connections (Source -> Target). Weight is optional (default 1).")
        lbl_instr.pack(pady=5)
        
        # Treeview for table
        columns = ("source", "target", "weight", "label")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("source", text="Source Node")
        self.tree.heading("target", text="Target Node")
        self.tree.heading("weight", text="Weight")
        self.tree.heading("label", text="Label")
        
        self.tree.column("source", width=100)
        self.tree.column("target", width=100)
        self.tree.column("weight", width=80)
        self.tree.column("label", width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Input Frame
        input_frame = tk.Frame(self)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(input_frame, text="Source:").grid(row=0, column=0)
        self.ent_source = tk.Entry(input_frame, width=10)
        self.ent_source.grid(row=0, column=1, padx=5)
        
        tk.Label(input_frame, text="Target:").grid(row=0, column=2)
        self.ent_target = tk.Entry(input_frame, width=10)
        self.ent_target.grid(row=0, column=3, padx=5)
        
        tk.Label(input_frame, text="Weight:").grid(row=0, column=4)
        self.ent_weight = tk.Entry(input_frame, width=8)
        self.ent_weight.grid(row=0, column=5, padx=5)
        
        tk.Label(input_frame, text="Label:").grid(row=0, column=6)
        self.ent_label = tk.Entry(input_frame, width=10)
        self.ent_label.grid(row=0, column=7, padx=5)
        
        btn_add = tk.Button(input_frame, text="Add Row", command=self.add_row)
        btn_add.grid(row=0, column=8, padx=10)
        
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        btn_generate = tk.Button(btn_frame, text="Generate Graph", command=self.generate, bg="#ccffcc")
        btn_generate.pack(side=tk.RIGHT, padx=5)
        
        btn_clear = tk.Button(btn_frame, text="Clear Table", command=self.clear_table)
        btn_clear.pack(side=tk.LEFT, padx=5)
        
        btn_delete = tk.Button(btn_frame, text="Delete Row", command=self.delete_row, bg="#ffcccc")
        btn_delete.pack(side=tk.LEFT, padx=5)

    def delete_row(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a row to delete.")
            return
        
        for item in selected_item:
            self.tree.delete(item)

    def add_row(self):
        source = self.ent_source.get().strip()
        target = self.ent_target.get().strip()
        weight = self.ent_weight.get().strip()
        label = self.ent_label.get().strip()
        
        if not source or not target:
            messagebox.showwarning("Input Error", "Source and Target are required.")
            return
            
        if not weight: weight = "1.0"
        
        self.tree.insert("", tk.END, values=(source, target, weight, label))
        
        # Clear inputs
        self.ent_source.delete(0, tk.END)
        self.ent_target.delete(0, tk.END)
        self.ent_weight.delete(0, tk.END)
        self.ent_label.delete(0, tk.END)
        self.ent_source.focus()

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def generate(self):
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            data.append(values)
        
        if not data:
            messagebox.showwarning("No Data", "Please add at least one connection.")
            return
            
        self.callback(data)
        self.destroy()
