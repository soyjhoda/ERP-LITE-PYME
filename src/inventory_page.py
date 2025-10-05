import customtkinter as ctk
from tkinter import messagebox, ttk, simpledialog
import re


ACCENT_CYAN = "#00FFFF"
ACCENT_GREEN = "#00c853"
BACKGROUND_DARK = "#0D1B2A"
FRAME_MID = "#1B263B"
FRAME_DARK = "#1B263B"
ACCENT_RED = "#e74c3c"


class InventoryPage(ctk.CTkFrame):
    def __init__(self, master, db_manager, user_id, user_role):
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.user_id = user_id
        self.user_role = user_role
        
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=FRAME_DARK, foreground="white",
                        fieldbackground=FRAME_DARK, rowheight=25, font=('Arial', 11))
        style.configure("Treeview.Heading", background="#2c3e50", foreground="white",
                        font=('Arial', 11, 'bold'))
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.search_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, height=60, corner_radius=10)
        self.search_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(self.search_frame,
                                         placeholder_text="Buscar producto por nombre o código...",
                                         width=350, height=40, fg_color="#2c3e50",
                                         border_color=ACCENT_CYAN, border_width=1)
        self.search_entry.bind("<KeyRelease>", self.search_products)
        self.search_entry.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        self.add_button = ctk.CTkButton(self.search_frame, text="➕ Añadir Producto", command=self.open_add_product_window,
                      fg_color=ACCENT_GREEN, hover_color="#008a38", height=40)
        self.add_button.grid(row=0, column=1, padx=(10,5), pady=10, sticky="e")

        self.edit_button = ctk.CTkButton(self.search_frame, text="✏️ Editar Producto", command=self.open_edit_product_window,
                      fg_color="#3498db", hover_color="#2980b9", height=40)
        self.edit_button.grid(row=0, column=2, padx=5, pady=10, sticky="e")

        self.delete_button = ctk.CTkButton(self.search_frame, text="🗑️ Eliminar Producto", command=self.delete_selected_product,
                      fg_color=ACCENT_RED, hover_color="#c0392b", height=40)
        self.delete_button.grid(row=0, column=3, padx=(5,20), pady=10, sticky="e")

        # Deshabilitar botones si rol no autorizado
        if self.user_role not in ("Administrador Total", "Gerente"):
            self.add_button.configure(state="disabled")
            self.edit_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")

        self.table_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        self.table_frame.grid(row=1, column=0, padx=20, pady=(10,20), sticky="nsew")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        self.inventory_tree = ttk.Treeview(self.table_frame,
            columns=("id","code","name","stock","stock_min","price","cost","category","brand","supplier"),
            show='headings')

        self.inventory_tree.heading("id", text="ID")
        self.inventory_tree.column("id", width=40, stretch=ctk.NO)
        self.inventory_tree.heading("code", text="Código")
        self.inventory_tree.column("code", width=100, stretch=ctk.NO)
        self.inventory_tree.heading("name", text="Nombre del Producto")
        self.inventory_tree.column("name", minwidth=200, stretch=ctk.YES)
        self.inventory_tree.heading("stock", text="Stock")
        self.inventory_tree.column("stock", width=70, anchor=ctk.CENTER)
        self.inventory_tree.heading("stock_min", text="Stock Min.")
        self.inventory_tree.column("stock_min", width=70, anchor=ctk.CENTER)
        self.inventory_tree.heading("price", text="Venta (USD)")
        self.inventory_tree.column("price", width=100, anchor=ctk.E)
        self.inventory_tree.heading("cost", text="Costo (USD)")
        self.inventory_tree.column("cost", width=100, anchor=ctk.E)
        self.inventory_tree.heading("category", text="Categoría")
        self.inventory_tree.column("category", width=120)
        self.inventory_tree.heading("brand", text="Marca")
        self.inventory_tree.column("brand", width=100)
        self.inventory_tree.heading("supplier", text="Proveedor")
        self.inventory_tree.column("supplier", width=150)

        self.inventory_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        scrollbar = ctk.CTkScrollbar(self.table_frame, command=self.inventory_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)

        self.load_products()

    def load_products(self, rate=None):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        products = self.db.get_all_products()

        for product in products:
            stock = product['stock']
            stock_minimo = product['stock_minimo']
            tags = ()
            if stock <= stock_minimo:
                tags = ('min_stock',)
            formatted_product = [
                product['id'],
                product['codigo'],
                product['nombre'],
                f"{stock:g}",
                f"{stock_minimo:g}",
                f"$.{product['precio_venta']:,.2f}",
                f"$.{product['precio_costo']:,.2f}",
                product['categoria'] if product['categoria'] else 'N/A',
                product['marca'] if product['marca'] else 'N/A',
                product['proveedor'] if product['proveedor'] else 'N/A'
            ]

            self.inventory_tree.insert("", "end", values=formatted_product, tags=tags)

        self.inventory_tree.tag_configure('min_stock', background=ACCENT_RED, foreground='white')

    def search_products(self, event=None):
        query = self.search_entry.get().strip()

        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        if not query:
            self.load_products()
            return

        search_term = f"%{query}%"
        sql_query = """
            SELECT id, codigo, nombre, stock, stock_minimo, 
            precio_venta, precio_costo, categoria, marca, proveedor 
            FROM productos
            WHERE codigo LIKE ? OR nombre LIKE ? OR marca LIKE ?
        """
        products = self.db.fetch_all(sql_query, (search_term, search_term, search_term))

        for product in products:
            stock = product['stock']
            stock_minimo = product['stock_minimo']
            tags = ()
            if stock <= stock_minimo:
                tags = ('min_stock',)

            formatted_product = [
                product['id'],
                product['codigo'],
                product['nombre'],
                f"{stock:g}",
                f"{stock_minimo:g}",
                f"$.{product['precio_venta']:,.2f}",
                f"$.{product['precio_costo']:,.2f}",
                product['categoria'] if product['categoria'] else 'N/A',
                product['marca'] if product['marca'] else 'N/A',
                product['proveedor'] if product['proveedor'] else 'N/A'
            ]

            self.inventory_tree.insert("", "end", values=formatted_product, tags=tags)

    def open_add_product_window(self):
        if self.user_role not in ("Administrador Total", "Gerente"):
            messagebox.showwarning("Sin permiso", "No tienes permisos para añadir productos.")
            return
        self._open_product_window(is_edit=False)

    def open_edit_product_window(self):
        if self.user_role not in ("Administrador Total", "Gerente"):
            messagebox.showwarning("Sin permiso", "No tienes permisos para editar productos.")
            return
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un producto para editar.")
            return
        item = self.inventory_tree.item(selected[0])
        values = item['values']

        product_data = {
            "id": values[0],
            "codigo": values[1],
            "nombre": values[2],
            "stock": float(values[3]),
            "stock_minimo": float(values[4]),
            "precio_venta": float(str(values[5]).replace("$.", "").replace(",", "")),
            "precio_costo": float(str(values[6]).replace("$.", "").replace(",", "")),
            "categoria": values[7] if values[7] != 'N/A' else "",
            "marca": values[8] if values[8] != 'N/A' else "",
            "proveedor": values[9] if values[9] != 'N/A' else "",
        }
        self._open_product_window(is_edit=True, product_data=product_data)

    def _open_product_window(self, is_edit=False, product_data=None):
        action = "Editar Producto" if is_edit else "Añadir Nuevo Producto"

        self.product_window = ctk.CTkToplevel(self)
        self.product_window.title(action)
        self.product_window.geometry("500x700")
        self.product_window.transient(self.master.master)
        self.product_window.grab_set()

        self.product_window.grid_columnconfigure(0, weight=1)
        self.product_window.configure(fg_color=BACKGROUND_DARK)

        ctk.CTkLabel(self.product_window, text=action, font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT_CYAN).grid(row=0, column=0, pady=20)

        input_frame = ctk.CTkFrame(self.product_window, fg_color=FRAME_MID, corner_radius=10)
        input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        input_frame.grid_columnconfigure(1, weight=1)

        fields = {
            "Código de Producto (único):": ctk.StringVar(),
            "Nombre del Producto:": ctk.StringVar(),
            "Stock Inicial (Unidades):": ctk.StringVar(value="0"),
            "Stock Mínimo (Alerta):": ctk.StringVar(value="0"),
            "Precio de Venta (USD):": ctk.StringVar(),
            "Precio de Costo (USD):": ctk.StringVar(),
            "Marca:": ctk.StringVar(),
        }

        self.supplier_var = ctk.StringVar(value="Proveedor Principal")
        self.category_var = ctk.StringVar(value="Electrónica")

        supplier_options = ["Proveedor Principal", "TechGlobal Inc.", "FerreMax S.A.", "AccesoCorp", "Otro..."]
        category_options = ["Electrónica", "Herramientas", "Accesorios", "Iluminación", "Hogar", "Otro..."]

        row_idx = 0
        self.entry_widgets = {}

        for label_text, var in fields.items():
            ctk.CTkLabel(input_frame, text=label_text, anchor="w", text_color="white").grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(input_frame, textvariable=var, height=30, fg_color="#2c3e50")
            entry.grid(row=row_idx, column=1, padx=10, pady=5, sticky="ew")
            self.entry_widgets[label_text] = entry
            row_idx += 1

        ctk.CTkLabel(input_frame, text="Proveedor:", anchor="w", text_color="white").grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkComboBox(input_frame, variable=self.supplier_var, values=supplier_options, fg_color="#2c3e50",
                        button_color=ACCENT_CYAN, button_hover_color="#00aaff").grid(row=row_idx, column=1, padx=10, pady=5, sticky="ew")
        row_idx += 1

        ctk.CTkLabel(input_frame, text="Categoría:", anchor="w", text_color="white").grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkComboBox(input_frame, variable=self.category_var, values=category_options, fg_color="#2c3e50",
                        button_color=ACCENT_CYAN, button_hover_color="#00aaff").grid(row=row_idx, column=1, padx=10, pady=5, sticky="ew")
        row_idx += 1

        if is_edit:
            ctk.CTkButton(self.product_window, text="✅ Guardar Cambios",
                          command=lambda: self.save_edited_product(fields, product_data["id"]),
                          fg_color=ACCENT_GREEN, hover_color="#008a38", height=40).grid(row=2, column=0, padx=20, pady=(20, 10), sticky="ew")
        else:
            ctk.CTkButton(self.product_window, text="✅ Guardar Producto",
                          command=lambda: self.save_new_product(fields),
                          fg_color=ACCENT_GREEN, hover_color="#008a38", height=40).grid(row=2, column=0, padx=20, pady=(20, 10), sticky="ew")

        ctk.CTkButton(self.product_window, text="❌ Cancelar", command=self.product_window.destroy,
                      fg_color="#34495e", hover_color="#2c3e50", height=40).grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

        if is_edit and product_data:
            fields["Código de Producto (único):"].set(product_data["codigo"])
            fields["Nombre del Producto:"].set(product_data["nombre"])
            fields["Stock Inicial (Unidades):"].set(str(product_data["stock"]))
            fields["Stock Mínimo (Alerta):"].set(str(product_data["stock_minimo"]))
            fields["Precio de Venta (USD):"].set(str(product_data["precio_venta"]))
            fields["Precio de Costo (USD):"].set(str(product_data["precio_costo"]))
            fields["Marca:"].set(product_data["marca"])
            self.supplier_var.set(product_data["proveedor"])
            self.category_var.set(product_data["categoria"])

    def save_new_product(self, fields):
        if self.user_role not in ("Administrador Total", "Gerente"):
            messagebox.showwarning("Sin permiso", "No tienes permisos para añadir productos.")
            return
        try:
            codigo = fields["Código de Producto (único):"].get().strip().upper()
            nombre = fields["Nombre del Producto:"].get().strip()
            stock = float(fields["Stock Inicial (Unidades):"].get())
            stock_minimo = float(fields["Stock Mínimo (Alerta):"].get())
            precio_venta = float(fields["Precio de Venta (USD):"].get())
            precio_costo = float(fields["Precio de Costo (USD):"].get())
            marca = fields["Marca:"].get().strip()
            
            proveedor = self.supplier_var.get()
            categoria = self.category_var.get()
            
        except ValueError:
            messagebox.showerror("Error de Datos", "Stock, Stock Mínimo, Precio de Venta y Precio de Costo deben ser números válidos.")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Faltan campos por llenar o error de formato: {e}")
            return

        if not all([codigo, nombre]):
            messagebox.showerror("Error de Validación", "El Código y el Nombre del Producto son obligatorios.")
            return

        if precio_venta <= 0 or precio_costo <= 0:
            messagebox.showerror("Error de Validación", "Los precios de Venta y Costo deben ser mayores a cero.")
            return
            
        if stock < 0 or stock_minimo < 0:
            messagebox.showerror("Error de Validación", "El stock y el stock mínimo no pueden ser números negativos.")
            return

        result = self.db.create_product(codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca)

        if result:
            messagebox.showinfo("Éxito", f"Producto '{nombre}' ({codigo}) guardado correctamente.")
            self.product_window.destroy()
            self.load_products()
        else:
            messagebox.showerror("Error DB", "No se pudo guardar el producto. El código de producto podría ya existir.")
            
    def save_edited_product(self, fields, product_id):
        if self.user_role not in ("Administrador Total", "Gerente"):
            messagebox.showwarning("Sin permiso", "No tienes permisos para editar productos.")
            return
        try:
            codigo = fields["Código de Producto (único):"].get().strip().upper()
            nombre = fields["Nombre del Producto:"].get().strip()
            stock = float(fields["Stock Inicial (Unidades):"].get())
            stock_minimo = float(fields["Stock Mínimo (Alerta):"].get())
            precio_venta = float(fields["Precio de Venta (USD):"].get())
            precio_costo = float(fields["Precio de Costo (USD):"].get())
            marca = fields["Marca:"].get().strip()
            
            proveedor = self.supplier_var.get()
            categoria = self.category_var.get()
            
        except ValueError:
            messagebox.showerror("Error de Datos", "Stock, Stock Mínimo, Precio de Venta y Precio de Costo deben ser números válidos.")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Faltan campos por llenar o error de formato: {e}")
            return

        if not all([codigo, nombre]):
            messagebox.showerror("Error de Validación", "El Código y el Nombre del Producto son obligatorios.")
            return

        if precio_venta <= 0 or precio_costo <= 0:
            messagebox.showerror("Error de Validación", "Los precios de Venta y Costo deben ser mayores a cero.")
            return
            
        if stock < 0 or stock_minimo < 0:
            messagebox.showerror("Error de Validación", "El stock y el stock mínimo no pueden ser números negativos.")
            return

        result = self.db.update_product(product_id, codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca)

        if result:
            messagebox.showinfo("Éxito", f"Producto '{nombre}' ({codigo}) actualizado correctamente.")
            self.product_window.destroy()
            self.load_products()
        else:
            messagebox.showerror("Error DB", "No se pudo actualizar el producto.")

    def delete_selected_product(self):
        if self.user_role not in ("Administrador Total", "Gerente"):
            messagebox.showwarning("Sin permiso", "No tienes permisos para eliminar productos.")
            return
        selected = self.inventory_tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un producto para eliminar.")
            return

        confirm = messagebox.askyesno("Confirmar eliminación", "¿Está seguro que desea eliminar este producto?")
        if confirm:
            product_id = self.inventory_tree.item(selected[0])['values'][0]
            result = self.db.delete_product(product_id)
            if result:
                messagebox.showinfo("Éxito", "Producto eliminado correctamente.")
                self.load_products()
            else:
                messagebox.showerror("Error DB", "No se pudo eliminar el producto.")
