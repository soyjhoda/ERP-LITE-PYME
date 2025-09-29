import customtkinter as ctk
from tkinter import messagebox, ttk, simpledialog, Menu
import math

# Definición de colores
ACCENT_CYAN = "#00FFFF"       
ACCENT_GREEN = "#00c853"      
BACKGROUND_DARK = "#0D1B2A"   
FRAME_MID = "#1B263B"         
FRAME_DARK = "#1B263B"        

class PosPage(ctk.CTkFrame):
    """Clase para la página de Punto de Venta (POS)."""
    def __init__(self, master, db_manager, user_id):
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.user_id = user_id
        
        # Estado del Carrito: {id_producto: {'nombre': str, 'precio': float, 'cantidad': int}}
        self.cart = {}
        
        # 0. Configuración de Estilos TTK para la tabla del carrito
        style = ttk.Style(self)
        style.theme_use("clam")
        
        # Aplicamos la configuración al estilo base de TTK "Treeview" y sus encabezados.
        style.configure("Cart.Treeview", 
                        background=FRAME_DARK, 
                        foreground="white", 
                        fieldbackground=FRAME_DARK,
                        rowheight=25,
                        font=('Arial', 11))
        
        style.configure("Cart.Treeview.Heading", 
                        background="#2c3e50", 
                        foreground="white", 
                        font=('Arial', 11, 'bold'))
        style.layout("Cart.Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) 

        # 1. Configuración del layout (Dos columnas: 40% Productos, 60% Carrito)
        self.grid_columnconfigure(0, weight=1, minsize=400) # Columna de búsqueda y productos
        self.grid_columnconfigure(1, weight=2, minsize=600) # Columna del carrito
        self.grid_rowconfigure(0, weight=1)

        # --- SECCIÓN IZQUIERDA: BÚSQUEDA Y PRODUCTOS ---
        self.left_panel = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        self.left_panel.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(2, weight=1) # El área de la tabla de resultados debe expandirse
        
        ctk.CTkLabel(self.left_panel, text="BÚSQUEDA DE PRODUCTOS", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_CYAN).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Campo de Búsqueda
        self.search_entry = ctk.CTkEntry(self.left_panel, 
                                         placeholder_text="Escriba código o nombre...", 
                                         width=350, height=40, 
                                         fg_color="#2c3e50", border_color=ACCENT_CYAN, border_width=1)
        self.search_entry.bind("<KeyRelease>", self.search_products)
        self.search_entry.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Frame para la tabla de resultados de búsqueda
        self.search_results_frame = ctk.CTkFrame(self.left_panel, fg_color=FRAME_DARK, corner_radius=10)
        self.search_results_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.search_results_frame.grid_rowconfigure(0, weight=1)
        self.search_results_frame.grid_columnconfigure(0, weight=1)

        # Treeview de Resultados de Búsqueda
        self.product_tree = ttk.Treeview(self.search_results_frame, 
                                         columns=("code", "name", "price", "stock"), 
                                         show='headings', 
                                         style="Cart.Treeview")
        
        self.product_tree.heading("code", text="Código"); self.product_tree.column("code", width=80, stretch=ctk.NO)
        self.product_tree.heading("name", text="Producto"); self.product_tree.column("name", minwidth=150, stretch=ctk.YES)
        self.product_tree.heading("price", text="Precio"); self.product_tree.column("price", width=70, anchor=ctk.E)
        self.product_tree.heading("stock", text="Stock"); self.product_tree.column("stock", width=60, anchor=ctk.CENTER)
        
        self.product_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.product_tree.bind("<Double-1>", self.add_to_cart_event) # Doble click para añadir
        
        # Scrollbar para la tabla de resultados
        product_scrollbar = ctk.CTkScrollbar(self.search_results_frame, command=self.product_tree.yview)
        product_scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.product_tree.configure(yscrollcommand=product_scrollbar.set)

        # --- SECCIÓN DERECHA: CARRITO Y RESUMEN ---
        self.right_panel = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        self.right_panel.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1) # La tabla del carrito debe expandirse
        
        ctk.CTkLabel(self.right_panel, text="CARRITO DE VENTA", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_CYAN).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Frame para la tabla del carrito
        self.cart_frame = ctk.CTkFrame(self.right_panel, fg_color=FRAME_DARK, corner_radius=10)
        self.cart_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.cart_frame.grid_rowconfigure(0, weight=1)
        self.cart_frame.grid_columnconfigure(0, weight=1)

        # Treeview del Carrito
        self.cart_tree = ttk.Treeview(self.cart_frame, 
                                      columns=("id", "name", "qty", "price", "subtotal"), 
                                      show='headings',
                                      style="Cart.Treeview")
        
        self.cart_tree.heading("id", text="ID", anchor=ctk.CENTER); self.cart_tree.column("id", width=30, stretch=ctk.NO, anchor=ctk.CENTER)
        self.cart_tree.heading("name", text="Producto"); self.cart_tree.column("name", minwidth=250, stretch=ctk.YES)
        self.cart_tree.heading("qty", text="Cant."); self.cart_tree.column("qty", width=60, anchor=ctk.CENTER)
        self.cart_tree.heading("price", text="Precio U."); self.cart_tree.column("price", width=90, anchor=ctk.E)
        self.cart_tree.heading("subtotal", text="Subtotal"); self.cart_tree.column("subtotal", width=100, anchor=ctk.E)
        
        self.cart_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.cart_tree.bind("<Button-3>", self.show_cart_context_menu) # Clic derecho para menú
        
        # Scrollbar para la tabla del carrito
        cart_scrollbar = ctk.CTkScrollbar(self.cart_frame, command=self.cart_tree.yview)
        cart_scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
        
        # Área de totales
        self.totals_frame = ctk.CTkFrame(self.right_panel, fg_color=FRAME_DARK, corner_radius=10)
        self.totals_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.totals_frame.grid_columnconfigure(0, weight=1)
        self.totals_frame.grid_columnconfigure(1, weight=1)

        # Etiqueta de Total
        self.total_label = ctk.CTkLabel(self.totals_frame, text="TOTAL: Bs/ 0.00", 
                                        font=ctk.CTkFont(size=24, weight="bold"), 
                                        text_color=ACCENT_GREEN)
        self.total_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Botón de Procesar Venta
        ctk.CTkButton(self.totals_frame, text="✅ PROCESAR VENTA", 
                      command=self.process_sale,
                      fg_color=ACCENT_GREEN, hover_color="#008a38", height=50,
                      font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=1, padx=20, pady=10, sticky="e")
        
        # Carga inicial de todos los productos en el panel de búsqueda
        self.load_all_products_for_search()


    def load_all_products_for_search(self):
        """Carga todos los productos en la tabla de resultados de búsqueda al inicio."""
        self.search_products()


    def search_products(self, event=None):
        """Busca productos en tiempo real en la base de datos."""
        query = self.search_entry.get().strip()
        
        # Limpiar la tabla de resultados
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        sql_query = """
            SELECT id, codigo, nombre, precio_venta, stock 
            FROM productos 
            WHERE codigo LIKE ? OR nombre LIKE ?
            ORDER BY nombre
        """
        search_term = f"%{query}%"
        products = self.db.fetch_all(sql_query, (search_term, search_term))

        for prod in products:
            id_prod, code, name, price, stock = prod
            # Añadir una etiqueta con el ID en el Treeview para referencia
            tag = f"id_{id_prod}" 
            
            # Verificar si el stock es cero y aplicar un color de fondo (tag)
            row_tags = ()
            if stock <= 0:
                row_tags = ('out_of_stock',)
                self.product_tree.tag_configure('out_of_stock', foreground='red', font=('Arial', 11, 'bold'))

            # CLAVE: Modificación para calcular el stock disponible (Real - En Carrito)
            stock_en_carrito = self.cart.get(id_prod, {}).get('cantidad', 0)
            stock_disponible = int(stock) - stock_en_carrito

            self.product_tree.insert("", "end", iid=tag, 
                                     values=(code, name, f"Bs/{price:,.2f}", stock_disponible),
                                     tags=row_tags)

    
    def add_to_cart_event(self, event):
        """Maneja el doble clic en un producto para añadirlo al carrito, verificando el stock."""
        selected_item = self.product_tree.focus()
        if not selected_item:
            return

        values = self.product_tree.item(selected_item, 'values')
        
        # El stock disponible ahora está en values[3] (calculado por search_products)
        try:
            stock_disponible_en_vista = int(values[3])
        except (ValueError, IndexError):
            # Esto puede pasar si se hace doble clic en un espacio vacío, aunque la verificación de focus debería evitarlo.
            return
        
        if stock_disponible_en_vista <= 0:
            messagebox.showwarning("Stock", "Stock insuficiente para añadir este producto.")
            return

        # Extraer el ID del IID (que guardamos como "id_X")
        product_id = int(selected_item.split('_')[1])
        name = values[1]
        
        # Limpiar y convertir el precio
        try:
            price_str = values[2].replace("Bs/", "").replace(",", "")
            price = float(price_str)
        except ValueError:
            messagebox.showerror("Error", "Error al leer el precio del producto.")
            return

        # 1. Añadir/Actualizar en el estado del carrito
        # Ya verificamos que stock_disponible_en_vista > 0, así que podemos aumentar la cantidad.
        if product_id in self.cart:
            self.cart[product_id]['cantidad'] += 1
        else:
            self.cart[product_id] = {
                'nombre': name,
                'precio': price,
                'cantidad': 1,
            }
        
        self.update_cart_display()
        
        # 2. Después de añadir, refrescar la tabla de búsqueda para mostrar el stock descontado
        self.search_products() 
    
    
    def show_cart_context_menu(self, event):
        """Muestra un menú contextual al hacer clic derecho en un ítem del carrito."""
        selected_item = self.cart_tree.identify_row(event.y)
        if not selected_item:
            return
        
        self.cart_tree.selection_set(selected_item)
        
        # Extraer el ID del producto (el IID es "cart_item_X")
        product_id = int(selected_item.split('_')[-1])

        menu = Menu(self, tearoff=0)
        menu.add_command(label="➕ Aumentar Cantidad (+1)", command=lambda: self.adjust_cart_quantity(product_id, 1))
        menu.add_command(label="➖ Disminuir Cantidad (-1)", command=lambda: self.adjust_cart_quantity(product_id, -1))
        menu.add_separator()
        menu.add_command(label="✏️ Cambiar Cantidad...", command=lambda: self.prompt_for_quantity(product_id))
        menu.add_command(label="❌ Eliminar Producto", command=lambda: self.remove_from_cart(product_id))
        
        # Mostrar el menú en la posición del clic
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    
    def get_real_stock(self, product_id):
        """Obtiene el stock actual del producto desde la base de datos."""
        stock_data = self.db.fetch_one("SELECT stock FROM productos WHERE id = ?", (product_id,))
        return stock_data[0] if stock_data else 0


    def adjust_cart_quantity(self, product_id, adjustment):
        """Ajusta la cantidad del producto en el carrito (+1, -1)."""
        if product_id not in self.cart:
            return
        
        new_qty = self.cart[product_id]['cantidad'] + adjustment
        
        if new_qty <= 0:
            self.remove_from_cart(product_id)
            return

        # Verificar stock máximo si estamos aumentando
        if adjustment > 0:
            real_stock = self.get_real_stock(product_id)
            if new_qty > real_stock:
                messagebox.showwarning("Stock", f"No puedes añadir más. Stock máximo disponible es {real_stock}.")
                return
        
        self.cart[product_id]['cantidad'] = new_qty
        self.update_cart_display()
        self.search_products() # Actualizar vista de stock disponible


    def prompt_for_quantity(self, product_id):
        """Pide al usuario que ingrese una nueva cantidad para el producto."""
        if product_id not in self.cart:
            return

        current_qty = self.cart[product_id]['cantidad']
        real_stock = self.get_real_stock(product_id)
        
        # Pedir nueva cantidad (Usamos simpledialog ya que es una aplicación de escritorio)
        new_qty_str = simpledialog.askstring("Cambiar Cantidad", 
                                             f"Ingrese la nueva cantidad para '{self.cart[product_id]['nombre']}'.\nStock Real: {real_stock}", 
                                             initialvalue=str(current_qty),
                                             parent=self)
        
        if new_qty_str is None: # Usuario canceló
            return
            
        try:
            new_qty = int(new_qty_str)
            if new_qty <= 0:
                self.remove_from_cart(product_id)
                return
                
            if new_qty > real_stock:
                messagebox.showwarning("Stock", f"Cantidad inválida. El stock real es {real_stock}.")
                return

            self.cart[product_id]['cantidad'] = new_qty
            self.update_cart_display()
            self.search_products() # Actualizar vista de stock disponible

        except ValueError:
            messagebox.showerror("Error", "Por favor, ingrese un número entero válido.")
            return


    def remove_from_cart(self, product_id):
        """Elimina un producto del carrito."""
        if product_id in self.cart:
            del self.cart[product_id]
            self.update_cart_display()
            self.search_products() # Devolver el stock a la vista de búsqueda
    
    
    def update_cart_display(self):
        """Actualiza el Treeview del carrito con los datos del estado self.cart."""
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        total_general = 0.0

        for p_id, data in self.cart.items():
            cantidad = data['cantidad']
            precio = data['precio']
            subtotal = cantidad * precio
            total_general += subtotal
            
            self.cart_tree.insert("", "end", iid=f"cart_item_{p_id}", 
                                  values=(p_id, data['nombre'], cantidad, 
                                          f"Bs/{precio:,.2f}", f"Bs/{subtotal:,.2f}"))

        # Actualizar el total general
        self.total_label.configure(text=f"TOTAL: Bs/ {total_general:,.2f}")
        
    
    def process_sale(self):
        """Simula el procesamiento de la venta y realiza el descuento de stock en la DB."""
        if not self.cart:
            messagebox.showwarning("Venta", "El carrito está vacío. Añade productos para procesar la venta.")
            return

        # NOTA: En una app real, esta lógica debería estar dentro de una transacción para garantizar atomicidad.
        try:
            # Extraer el total antes de resetear el carrito
            total_final = float(self.total_label.cget("text").split('/')[-1].replace(",", "").strip())

            # 1. Descontar Stock en la Base de Datos
            for p_id, data in self.cart.items():
                cantidad_vendida = data['cantidad']
                
                # Obtener stock actual real
                current_stock_data = self.db.fetch_one("SELECT stock FROM productos WHERE id = ?", (p_id,))
                
                if current_stock_data is None:
                    messagebox.showerror("Error", f"Producto ID {p_id} no encontrado.")
                    continue
                    
                current_stock = current_stock_data[0]
                new_stock = current_stock - cantidad_vendida
                
                # Actualizar stock
                self.db.execute_query("UPDATE productos SET stock = ? WHERE id = ?", (new_stock, p_id))

            # 2. Resumen y Limpieza
            summary = f"Venta procesada con éxito!\n\nProductos: {len(self.cart)} artículos únicos.\nTotal Final: Bs/ {total_final:,.2f}"
            messagebox.showinfo("Venta Exitosa", summary)
            
            # Limpiar el carrito después de la venta
            self.cart = {}
            self.update_cart_display()
            self.search_products() # Recargar la búsqueda para mostrar el stock actualizado
            
        except Exception as e:
            messagebox.showerror("Error de Venta", f"Ocurrió un error al procesar la venta: {e}")
