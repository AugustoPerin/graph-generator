import tkinter as tk
from tkinter import ttk, colorchooser, simpledialog, filedialog
import networkx as nx
import math
from utils import calculate_arrow_points, point_distance
from PIL import Image, ImageDraw

import random

class GraphEditor(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.graph = nx.DiGraph() # Default to directed graph
        self.pos = {} # Store node positions manually to allow dragging
        
        self.node_radius = 20
        self.selected_node = None
        self.selected_edge = None
        self.mode = "MOVE" # MOVE, ADD_NODE, ADD_EDGE
        
        self.default_node_color = "white"
        self.default_edge_color = "black"
        
        self.pixels_per_unit = None # Will be set on first edge
        
        self.create_widgets()
        
    def on_canvas_click(self, event):
        x, y = event.x, event.y
        
        clicked_node = self.get_node_at(x, y)
        
        if self.mode == "ADD_NODE":
            if not clicked_node:
                new_node_id = 1 # Start from 1
                while new_node_id in self.graph:
                    new_node_id += 1
                
                self.graph.add_node(new_node_id, label=str(new_node_id), color=self.default_node_color)
                self.pos[new_node_id] = (x, y)
                self.draw_graph()
                # No dynamic layout on node add
                
        elif self.mode == "ADD_EDGE":
            if clicked_node is not None:
                if self.selected_node is None:
                    self.selected_node = clicked_node
                    self.lbl_info.config(text=f"Start Node: {self.graph.nodes[clicked_node].get('label')}")
                else:
                    if self.selected_node != clicked_node:
                        # Ask for weight and label
                        weight = simpledialog.askfloat("Edge Weight", "Enter edge weight:", initialvalue=1.0)
                        if weight is None: weight = 1.0
                        label = simpledialog.askstring("Edge Label", "Enter edge label (optional):", initialvalue="")
                        if label is None: label = ""
                        
                        self.graph.add_edge(self.selected_node, clicked_node, weight=weight, label=label, color=self.default_edge_color)
                        
                        # Initialize scale if first edge
                        if self.pixels_per_unit is None and weight > 0:
                            # Standard length for this first weight should be e.g. 150 pixels
                            self.pixels_per_unit = 150.0 / weight
                            print(f"Scale initialized: {self.pixels_per_unit} px/unit based on weight {weight}")
                        
                        self.selected_node = None
                        self.lbl_info.config(text="Edge added")
                        self.draw_graph()
                        self.relax_graph(iterations=50) # Adjust layout
                    else:
                        self.selected_node = None
                        self.lbl_info.config(text="Select start node")
            else:
                self.selected_node = None
                self.lbl_info.config(text="Click node to start edge")
                
        elif self.mode == "MOVE":
            self.selected_node = clicked_node
            if clicked_node is not None:
                self.update_properties_panel(node=clicked_node)
            else:
                self.update_properties_panel(None)
                
        elif self.mode == "ADD_SHAPE_TEXT":
            text = simpledialog.askstring("Add Text", "Enter text:")
            if text:
                self.canvas.create_text(x, y, text=text, fill="black", font=("Arial", 12))
                
        elif self.mode == "ADD_SHAPE_CIRCLE":
            r = 15
            self.canvas.create_oval(x-r, y-r, x+r, y+r, outline="black", width=2)
            
        elif self.mode == "ADD_SHAPE_ARROW":
            # Draw a simple arrow (fixed size for now, or drag to size could be better but keeping simple)
            # Let's make it a fixed size arrow pointing right for simplicity, or maybe click-drag?
            # For simplicity: fixed size arrow
            self.canvas.create_line(x, y, x+30, y, arrow=tk.LAST, width=2)

    def create_widgets(self):
        # Toolbar
        self.toolbar = tk.Frame(self, bg="#e0e0e0", height=40)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        self.btn_move = tk.Button(self.toolbar, text="Move/Select", command=lambda: self.set_mode("MOVE"))
        self.btn_move.pack(side=tk.LEFT, padx=2, pady=5)
        
        self.btn_add_node = tk.Button(self.toolbar, text="Add Node", command=lambda: self.set_mode("ADD_NODE"))
        self.btn_add_node.pack(side=tk.LEFT, padx=2, pady=5)
        
        self.btn_add_edge = tk.Button(self.toolbar, text="Add Edge", command=lambda: self.set_mode("ADD_EDGE"))
        self.btn_add_edge.pack(side=tk.LEFT, padx=2, pady=5)
        
        self.btn_layout = tk.Button(self.toolbar, text="Auto Layout", command=self.auto_layout)
        self.btn_layout.pack(side=tk.LEFT, padx=2, pady=5)
        
        # Additional Shapes
        self.btn_text = tk.Button(self.toolbar, text="+ Text", command=lambda: self.set_mode("ADD_SHAPE_TEXT"))
        self.btn_text.pack(side=tk.LEFT, padx=2, pady=5)
        
        self.btn_circle = tk.Button(self.toolbar, text="+ Circle", command=lambda: self.set_mode("ADD_SHAPE_CIRCLE"))
        self.btn_circle.pack(side=tk.LEFT, padx=2, pady=5)
        
        self.btn_arrow = tk.Button(self.toolbar, text="+ Arrow", command=lambda: self.set_mode("ADD_SHAPE_ARROW"))
        self.btn_arrow.pack(side=tk.LEFT, padx=2, pady=5)
        
        self.btn_bulk = tk.Button(self.toolbar, text="Bulk Input", command=self.open_bulk_input, bg="#e6f2ff")
        self.btn_bulk.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Templates Menu
        self.mb_templates = tk.Menubutton(self.toolbar, text="Templates", relief=tk.RAISED)
        self.mb_templates.menu = tk.Menu(self.mb_templates, tearoff=0)
        self.mb_templates["menu"] = self.mb_templates.menu
        self.mb_templates.menu.add_command(label="NSFNet", command=lambda: self.load_template("nsfnet"))
        self.mb_templates.menu.add_command(label="USA Topology", command=lambda: self.load_template("usa"))
        self.mb_templates.pack(side=tk.LEFT, padx=2, pady=5)
        
        self.btn_clear = tk.Button(self.toolbar, text="Clear", command=self.clear_graph)
        self.btn_clear.pack(side=tk.LEFT, padx=2, pady=5)

        self.btn_export = tk.Button(self.toolbar, text="Export PNG", command=self.export_png)
        self.btn_export.pack(side=tk.RIGHT, padx=5, pady=5)

        # Properties Panel (Sidebar)
        self.properties_panel = tk.Frame(self, bg="#f0f0f0", width=200)
        self.properties_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(self.properties_panel, text="Properties", font=("Arial", 12, "bold")).pack(pady=10)
        
        self.lbl_info = tk.Label(self.properties_panel, text="Select an item")
        self.lbl_info.pack(pady=5)
        
        self.btn_color = tk.Button(self.properties_panel, text="Change Color", command=self.change_color, state=tk.DISABLED)
        self.btn_color.pack(pady=5)
        
        self.btn_label = tk.Button(self.properties_panel, text="Edit Label", command=self.edit_label, state=tk.DISABLED)
        self.btn_label.pack(pady=5)
        
        self.btn_delete = tk.Button(self.properties_panel, text="Delete", command=self.delete_item, state=tk.DISABLED, bg="#ffcccc")
        self.btn_delete.pack(pady=20)

        # Canvas
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)



    def set_mode(self, mode):
        self.mode = mode
        print(f"Mode set to: {mode}")
        
    def clear_graph(self):
        self.graph.clear()
        self.pos.clear()
        self.draw_graph()
        
    def auto_layout(self):
        if not self.graph.nodes:
            return
        # Use spring layout
        # We need to scale the layout to the canvas size
        layout_pos = nx.spring_layout(self.graph)
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        margin = 50
        
        # Normalize and scale
        x_values = [p[0] for p in layout_pos.values()]
        y_values = [p[1] for p in layout_pos.values()]
        
        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)
        
        delta_x = max_x - min_x if max_x != min_x else 1
        delta_y = max_y - min_y if max_y != min_y else 1
        
        for node, p in layout_pos.items():
            # Map -1..1 to margin..width-margin
            nx_val = (p[0] - min_x) / delta_x
            ny_val = (p[1] - min_y) / delta_y
            
            self.pos[node] = (
                margin + nx_val * (width - 2 * margin),
                margin + ny_val * (height - 2 * margin)
            )
            
        self.draw_graph()

    def on_canvas_drag(self, event):
        if self.mode == "MOVE" and self.selected_node is not None:
            self.pos[self.selected_node] = (event.x, event.y)
            # Chain effect: relax graph while keeping selected node fixed
            self.relax_graph(fixed_nodes={self.selected_node}, iterations=5)
            self.draw_graph()

    def on_canvas_release(self, event):
        pass

    def get_node_at(self, x, y):
        for node, (nx, ny) in self.pos.items():
            if point_distance(x, y, nx, ny) <= self.node_radius:
                return node
        return None

    def draw_graph(self):
        self.canvas.delete("all")
        
        # Draw edges
        for u, v, data in self.graph.edges(data=True):
            if u not in self.pos or v not in self.pos: continue
            
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            
            color = data.get('color', 'black')
            
            # Draw line
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
            
            # Draw arrow (if directed)
            # Calculate intersection with node circle
            angle = math.atan2(y2 - y1, x2 - x1)
            end_x = x2 - self.node_radius * math.cos(angle)
            end_y = y2 - self.node_radius * math.sin(angle)
            
            arrow_points = calculate_arrow_points(x1, y1, end_x, end_y)
            self.canvas.create_polygon(arrow_points[2:], fill=color)
            
            # Draw label
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            label = data.get('label', '')
            if label:
                self.canvas.create_text(mid_x, mid_y - 10, text=label, fill="black", font=("Arial", 12, "bold"))
            
            # Weight is stored but not displayed as per request

        # Draw nodes
        for node in self.graph.nodes:
            x, y = self.pos[node]
            color = self.graph.nodes[node].get('color', 'white')
            label = self.graph.nodes[node].get('label', str(node))
            
            # Draw circle
            self.canvas.create_oval(
                x - self.node_radius, y - self.node_radius,
                x + self.node_radius, y + self.node_radius,
                fill=color, outline="black", width=2
            )
            
            # Draw label
            self.canvas.create_text(x, y, text=label)

    def relax_graph(self, fixed_nodes=None, iterations=10):
        """
        Custom constraint-based relaxation to enforce edge lengths (weights).
        Acts like a physical chain.
        """
        if not self.graph.edges:
            return
            
        if fixed_nodes is None:
            fixed_nodes = set()
            
        # If scale is not set, we can't relax based on weights properly yet
        # But we should have set it on first edge add.
        if not hasattr(self, 'pixels_per_unit') or self.pixels_per_unit is None:
            return

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        for _ in range(iterations):
            # 1. Edge constraints (Springs)
            for u, v, data in self.graph.edges(data=True):
                if u not in self.pos or v not in self.pos: continue
                
                x1, y1 = self.pos[u]
                x2, y2 = self.pos[v]
                
                weight = data.get('weight', 1.0)
                target_dist = weight * self.pixels_per_unit
                
                curr_dist = point_distance(x1, y1, x2, y2)
                if curr_dist == 0: curr_dist = 0.1 # Avoid division by zero
                
                # Calculate displacement to match target distance
                # We want to move nodes closer or further to match target_dist
                diff = (curr_dist - target_dist) / curr_dist
                
                # Move factor (stiffness)
                alpha = 0.5
                
                dx = (x2 - x1) * diff * alpha
                dy = (y2 - y1) * diff * alpha
                
                if u not in fixed_nodes:
                    self.pos[u] = (x1 + dx, y1 + dy)
                if v not in fixed_nodes:
                    self.pos[v] = (x2 - dx, y2 - dy)
                    
            # 2. Node repulsion (prevent overlap) - simplified
            # This is O(N^2), might be slow for large graphs but fine for small ones
            nodes = list(self.graph.nodes)
            for i in range(len(nodes)):
                u = nodes[i]
                for j in range(i + 1, len(nodes)):
                    v = nodes[j]
                    if u == v: continue
                    
                    x1, y1 = self.pos[u]
                    x2, y2 = self.pos[v]
                    dist = point_distance(x1, y1, x2, y2)
                    min_dist = self.node_radius * 2.5 # Minimum distance between centers
                    
                    if dist < min_dist:
                        if dist == 0: dist = 0.1
                        # Push apart
                        push = (min_dist - dist) / dist * 0.5
                        dx = (x2 - x1) * push
                        dy = (y2 - y1) * push
                        
                        if u not in fixed_nodes:
                            self.pos[u] = (x1 - dx, y1 - dy)
                        if v not in fixed_nodes:
                            self.pos[v] = (x2 + dx, y2 + dy)
                            
            # 3. Keep within bounds (optional, but good)
            margin = self.node_radius
            for node in self.graph.nodes:
                if node in fixed_nodes: continue
                x, y = self.pos[node]
                x = max(margin, min(width - margin, x))
                y = max(margin, min(height - margin, y))
                self.pos[node] = (x, y)

    def auto_layout(self):
        # Trigger a full relaxation
        self.relax_graph(iterations=100)
        self.draw_graph()
            
    def update_properties_panel(self, node=None, edge=None):
        if node is not None:
            self.lbl_info.config(text=f"Node: {self.graph.nodes[node].get('label')}")
            self.btn_color.config(state=tk.NORMAL)
            self.btn_label.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.NORMAL)
        else:
            self.lbl_info.config(text="Select an item")
            self.btn_color.config(state=tk.DISABLED)
            self.btn_label.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)

    def change_color(self):
        if self.selected_node is not None:
            color = colorchooser.askcolor(title="Choose Node Color")[1]
            if color:
                self.graph.nodes[self.selected_node]['color'] = color
                self.draw_graph()
                
    def edit_label(self):
        if self.selected_node is not None:
            current_label = self.graph.nodes[self.selected_node].get('label', '')
            new_label = simpledialog.askstring("Edit Label", "Enter new label:", initialvalue=current_label)
            if new_label is not None:
                self.graph.nodes[self.selected_node]['label'] = new_label
                self.draw_graph()
                
    def delete_item(self):
        if self.selected_node is not None:
            self.graph.remove_node(self.selected_node)
            del self.pos[self.selected_node]
            self.selected_node = None
            self.draw_graph()
            self.update_properties_panel(None)

    def export_png(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            # This is a basic export. For high res, we might need to draw to a PIL image directly.
            # Capturing canvas coordinate space to PIL
            
            # Calculate bounding box
            if not self.pos:
                return
                
            xs = [p[0] for p in self.pos.values()]
            ys = [p[1] for p in self.pos.values()]
            min_x, max_x = min(xs) - 50, max(xs) + 50
            min_y, max_y = min(ys) - 50, max(ys) + 50
            
            width = int(max_x - min_x)
            height = int(max_y - min_y)
            
            image = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(image)
            
            # Offset function
            def to_img_coords(x, y):
                return (x - min_x, y - min_y)
            
            # Draw edges
            for u, v, data in self.graph.edges(data=True):
                x1, y1 = self.pos[u]
                x2, y2 = self.pos[v]
                ix1, iy1 = to_img_coords(x1, y1)
                ix2, iy2 = to_img_coords(x2, y2)
                
                color = data.get('color', 'black')
                draw.line((ix1, iy1, ix2, iy2), fill=color, width=2)
                
                # Draw arrow (simplified for PIL)
                angle = math.atan2(y2 - y1, x2 - x1)
                end_x = x2 - self.node_radius * math.cos(angle)
                end_y = y2 - self.node_radius * math.sin(angle)
                
                # Calculate arrow points in image coordinates
                # We need to map the arrow points from graph coords to image coords
                # First get arrow points in graph coords
                ap = calculate_arrow_points(x1, y1, end_x, end_y)
                # ap is [x2, y2, p1_x, p1_y, p2_x, p2_y] (actually the first point is the tip)
                # Wait, calculate_arrow_points returns [x2, y2, p1_x, p1_y, p2_x, p2_y] where (x2,y2) is the tip.
                
                # Map to image coords
                tip_x, tip_y = to_img_coords(ap[0], ap[1])
                p1_x, p1_y = to_img_coords(ap[2], ap[3])
                p2_x, p2_y = to_img_coords(ap[4], ap[5])
                
                draw.polygon([(tip_x, tip_y), (p1_x, p1_y), (p2_x, p2_y)], fill=color)

            # Draw nodes
            for node in self.graph.nodes:
                x, y = self.pos[node]
                ix, iy = to_img_coords(x, y)
                r = self.node_radius
                color = self.graph.nodes[node].get('color', 'lightblue')
                
                draw.ellipse((ix - r, iy - r, ix + r, iy + r), fill=color, outline="black")
                
                # Text (requires font loading, skipping for basic implementation or using default)
                # draw.text(...)

            image.save(file_path)
            print(f"Exported to {file_path}")

    def open_bulk_input(self):
        from bulk_input import BulkGraphDialog
        BulkGraphDialog(self, self.process_bulk_data)
        
    def process_bulk_data(self, data):
        # data is list of (source, target, weight, label)
        self.clear_graph()
        
        # First pass: collect all unique nodes
        nodes = set()
        for row in data:
            nodes.add(str(row[0]))
            nodes.add(str(row[1]))
            
        # Add nodes
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 100: width = 800
        if height < 100: height = 600
        
        for node_label in nodes:
            if node_label not in self.graph:
                self.graph.add_node(node_label, label=node_label, color=self.default_node_color)
                # Random position to avoid overlap at start
                self.pos[node_label] = (random.randint(50, width-50), random.randint(50, height-50)) 
        
        # Add edges
        first_weight = None
        for row in data:
            u, v, w, l = row
            u, v = str(u), str(v)
            try:
                weight = float(w)
            except:
                weight = 1.0
            
            if first_weight is None and weight > 0:
                first_weight = weight
                
            self.graph.add_edge(u, v, weight=weight, label=l, color=self.default_edge_color)
            
        # Initialize scale
        if first_weight:
             self.pixels_per_unit = 150.0 / first_weight
        else:
             self.pixels_per_unit = 100.0
             
        # Auto layout
        self.auto_layout()

    def load_template(self, template_name):
        import templates
        
        data = None
        if template_name == "nsfnet":
            data = templates.nsfnet_topology
        elif template_name == "usa":
            data = templates.usa_topology
            
        if not data:
            return
            
        self.clear_graph()
        
        # Data is {node: {neighbor: weight, ...}, ...}
        
        # Add nodes first
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 100: width = 800
        if height < 100: height = 600
        
        for node in data:
            node_id = str(node)
            self.graph.add_node(node_id, label=node_id, color=self.default_node_color)
            self.pos[node_id] = (random.randint(50, width-50), random.randint(50, height-50))
            
        # Add edges
        first_weight = None
        for u, neighbors in data.items():
            u_str = str(u)
            for v, weight in neighbors.items():
                v_str = str(v)
                # Avoid duplicate edges if undirected, but here we have directed dict structure often used for undirected graphs too
                # NetworkX DiGraph will allow u->v and v->u. 
                # If we want undirected visual, we can check if edge exists.
                # But let's just add them as is.
                
                if not self.graph.has_edge(u_str, v_str):
                     self.graph.add_edge(u_str, v_str, weight=weight, label="", color=self.default_edge_color)
                     
                if first_weight is None and weight > 0:
                    first_weight = weight
                    
        # Initialize scale
        if first_weight:
             self.pixels_per_unit = 150.0 / first_weight
        else:
             self.pixels_per_unit = 100.0
             
        self.auto_layout()

