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
        
        # Estado del Carrito: {id_producto: {'nombre': str, 'precio_usd': float, 'precio_bs': float, 'cantidad': int, 'stock_real': int}}
        self.cart = {}
        # La tasa es CRÍTICA. Se usará para calcular el total final en USD para la DB si es necesario.
        self.current_exchange_rate = 36.00 # Valor por defecto, se actualiza al cargar la página
        
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
        
        # Inicialización de product_tree para evitar el error 'self.product_tree' no definido
        self.product_tree = ttk.Treeview(self, show='headings') 
        
        # Etiqueta para productos agotados
        self.product_tree.tag_configure('out_of_stock', foreground='red', font=('Arial', 11, 'bold'))



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
        self.product_tree.destroy() # Destruimos el placeholder para crear el real
        self.product_tree = ttk.Treeview(self.search_results_frame, 
                                        columns=("code", "name", "price_bs", "stock_disp", "price_usd_stock"), 
                                        show='headings', 
                                        style="Cart.Treeview")
        
        self.product_tree.heading("code", text="Código"); self.product_tree.column("code", width=80, stretch=ctk.NO)
        self.product_tree.heading("name", text="Producto"); self.product_tree.column("name", minwidth=150, stretch=ctk.YES)
        self.product_tree.heading("price_bs", text="Precio (Bs)"); self.product_tree.column("price_bs", width=90, anchor=ctk.E)
        self.product_tree.heading("stock_disp", text="Stock Disp."); self.product_tree.column("stock_disp", width=80, anchor=ctk.CENTER)
        
        # Ocultar la columna de datos reales para el usuario
        self.product_tree.heading("price_usd_stock", text=""); self.product_tree.column("price_usd_stock", width=0, stretch=ctk.NO)
        
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
                                        columns=("id", "name", "qty", "price_usd", "price_bs", "subtotal_bs"), 
                                        show='headings',
                                        style="Cart.Treeview")
        
        self.cart_tree.heading("id", text="ID", anchor=ctk.CENTER); self.cart_tree.column("id", width=30, stretch=ctk.NO, anchor=ctk.CENTER)
        self.cart_tree.heading("name", text="Producto"); self.cart_tree.column("name", minwidth=250, stretch=ctk.YES)
        self.cart_tree.heading("qty", text="Cant."); self.cart_tree.column("qty", width=60, anchor=ctk.CENTER)
        self.cart_tree.heading("price_usd", text="Precio ($)"); self.cart_tree.column("price_usd", width=80, anchor=ctk.E)
        self.cart_tree.heading("price_bs", text="Precio (Bs)"); self.cart_tree.column("price_bs", width=90, anchor=ctk.E)
        self.cart_tree.heading("subtotal_bs", text="Subtotal (Bs)"); self.cart_tree.column("subtotal_bs", width=110, anchor=ctk.E)
        
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
        self.totals_frame.grid_rowconfigure(0, weight=1)
        self.totals_frame.grid_rowconfigure(1, weight=1)


        # Etiqueta de Tasa de Cambio
        self.rate_label = ctk.CTkLabel(self.totals_frame, text=f"Tasa Venta: Bs/ {self.current_exchange_rate:,.2f}", 
                                        font=ctk.CTkFont(size=14), 
                                        text_color=ACCENT_CYAN)
        self.rate_label.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")
        
        # Etiqueta de Total
        self.total_label = ctk.CTkLabel(self.totals_frame, text="TOTAL: Bs/ 0.00", 
                                        font=ctk.CTkFont(size=28, weight="bold"), 
                                        text_color=ACCENT_GREEN)
        self.total_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")
        
        # Botón de Procesar Venta
        ctk.CTkButton(self.totals_frame, text="✅ PROCESAR VENTA", 
                      command=self.process_sale,
                      fg_color=ACCENT_GREEN, hover_color="#008a38", height=60,
                      font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=1, rowspan=2, padx=20, pady=10, sticky="nsew")
        
        # Carga inicial de todos los productos en el panel de búsqueda
        self.load_all_products_for_search()

        # Método agregado para refrescar productos automáticamente
        self.refresh_products()


    def refresh_products(self):
        """Refresca la lista de productos cada 2 segundos si la página está visible."""
        if str(self.winfo_viewable()) == '1':
            self.load_all_products_for_search()
        self.after(2000, self.refresh_products)


    def update_rate(self, new_rate):
        """Método llamado desde Dashboard para actualizar la tasa de cambio local."""
        if new_rate is not None and isinstance(new_rate, (int, float)):
            self.current_exchange_rate = new_rate
            self.rate_label.configure(text=f"Tasa Venta: Bs/ {self.current_exchange_rate:,.2f}")
            # Recalcular y actualizar el display del carrito con la nueva tasa
            self.update_cart_display()
        else:
            print("Advertencia: Tasa de cambio inválida recibida.")


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
        # precio_venta viene en USD desde la DB
        products = self.db.fetch_all(sql_query, (search_term, search_term))


        for prod in products:
            id_prod, code, name, price_usd, stock_real = prod
            
            # 1. Calcular precio en Bs para la vista
            price_bs = price_usd * self.current_exchange_rate
            
            # 2. Calcular stock disponible (Real - En Carrito)
            stock_en_carrito = self.cart.get(id_prod, {}).get('cantidad', 0)
            stock_disponible = int(stock_real) - stock_en_carrito


            row_tags = ()
            if stock_disponible <= 0:
                row_tags = ('out_of_stock',)


            # CLAVE: En la columna oculta 'price_usd_stock' se guarda: [precio_usd, stock_real]
            # Esto permite una extracción limpia de valores numéricos después.
            data_oculta = f"{price_usd:.2f},{stock_real}"


            self.product_tree.insert("", "end", 
                                    iid=f"id_{id_prod}", 
                                    values=(code, name, f"{price_bs:,.2f}", stock_disponible, data_oculta),
                                    tags=row_tags)


    def add_to_cart_event(self, event):
        """Maneja el doble clic en un producto para añadirlo al carrito, verificando el stock."""
        selected_item = self.product_tree.focus()
        if not selected_item:
            return


        values = self.product_tree.item(selected_item, 'values')
        
        try:
            # Los valores de la vista son (code, name, price_bs, stock_disp, data_oculta)
            stock_disponible_en_vista = int(values[3])
            
            # Extraer data oculta: "precio_usd,stock_real"
            data_oculta_str = values[4]
            price_usd = float(data_oculta_str.split(',')[0])
            stock_real = float(data_oculta_str.split(',')[1]) # Usamos float para ser más precisos con stock
            
        except (ValueError, IndexError) as e:
            # Esto nunca debería pasar si search_products funciona correctamente
            print(f"Error al leer datos del producto: {e}")
            messagebox.showerror("Error", "Error al leer los datos internos del producto.")
            return
        
        # Validación de stock
        if stock_disponible_en_vista <= 0:
            messagebox.showwarning("Stock", "Stock insuficiente para añadir este producto.")
            return


        product_id = int(selected_item.split('_')[1])
        name = values[1]
        
        # 1. Añadir/Actualizar en el estado del carrito
        if product_id in self.cart:
            self.cart[product_id]['cantidad'] += 1
        else:
            # Calculamos el precio en Bs al momento de añadirlo (solo para la vista, el USD es el valor real)
            price_bs = price_usd * self.current_exchange_rate
            
            self.cart[product_id] = {
                'nombre': name,
                'precio_usd': price_usd, # Almacenamos el precio base en USD
                'precio_bs': price_bs, # Almacenamos el precio convertido en Bs al momento
                'stock_real': stock_real, # Stock real para validar ajustes
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
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()


    
    def get_real_stock(self, product_id):
        """Obtiene el stock actual del producto desde la base de datos."""
        # Ahora usamos el stock_real almacenado en el carrito para evitar re-consultar la DB
        if product_id in self.cart:
            return self.cart[product_id]['stock_real']
        else:
            # Si no está en el carrito, consultamos la DB por si acaso
            stock_data = self.db.fetch_one("SELECT stock FROM productos WHERE id = ?", (product_id,))
            # Usamos el índice numérico 0 ya que fetch_one con sqlite3.Row es inconsistente para un solo campo sin nombre
            return float(stock_data[0]) if stock_data and stock_data[0] is not None else 0.0



    def adjust_cart_quantity(self, product_id, adjustment):
        """Ajusta la cantidad del producto en el carrito (+1, -1)."""
        if product_id not in self.cart:
            return
        
        new_qty = self.cart[product_id]['cantidad'] + adjustment
        real_stock = self.cart[product_id]['stock_real'] # Usar el stock real guardado


        if new_qty <= 0:
            self.remove_from_cart(product_id)
            return


        # Verificar stock máximo (usamos math.ceil para redondear hacia arriba el stock)
        if new_qty > math.floor(real_stock): 
            messagebox.showwarning("Stock", f"No puedes añadir más. El stock máximo real disponible es {math.floor(real_stock)}.")
            return
        
        # Si la cantidad es válida, se actualiza
        self.cart[product_id]['cantidad'] = new_qty
        
        # Actualizar el precio en Bs con la tasa actual (por si ha cambiado desde que se añadió)
        price_usd = self.cart[product_id]['precio_usd']
        self.cart[product_id]['precio_bs'] = price_usd * self.current_exchange_rate


        self.update_cart_display()
        self.search_products() # Actualizar vista de stock disponible



    def prompt_for_quantity(self, product_id):
        """Pide al usuario que ingrese una nueva cantidad para el producto."""
        if product_id not in self.cart:
            return


        current_qty = self.cart[product_id]['cantidad']
        real_stock = self.cart[product_id]['stock_real'] # Usar el stock real guardado
        
        # Pedir nueva cantidad (Usamos simpledialog ya que es una aplicación de escritorio)
        new_qty_str = simpledialog.askstring("Cambiar Cantidad", 
                                             f"Ingrese la nueva cantidad para '{self.cart[product_id]['nombre']}'.\nStock Real: {math.floor(real_stock)}", 
                                             initialvalue=str(current_qty),
                                             parent=self)
        
        if new_qty_str is None: # Usuario canceló
            return
            
        try:
            # Aceptamos enteros y los convertimos a int/float
            new_qty = float(new_qty_str)
            
            # Forzar a usar un valor con hasta 2 decimales si el stock lo permite
            # Aunque la mayoría de los productos son unidades, permitimos stock fraccional (ej: kg, metros)
            new_qty_rounded = round(new_qty, 2)
            
            if new_qty_rounded <= 0:
                self.remove_from_cart(product_id)
                return
                
            if new_qty_rounded > real_stock:
                messagebox.showwarning("Stock", f"Cantidad inválida. El stock real es {real_stock:.2f}.")
                return


            # Si la cantidad es válida, se actualiza
            self.cart[product_id]['cantidad'] = new_qty_rounded
            
            # Actualizar el precio en Bs (por si la tasa ha cambiado)
            price_usd = self.cart[product_id]['precio_usd']
            self.cart[product_id]['precio_bs'] = price_usd * self.current_exchange_rate


            self.update_cart_display()
            self.search_products() # Actualizar vista de stock disponible


        except ValueError:
            messagebox.showerror("Error", "Por favor, ingrese un número válido.")
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


        total_general_bs = 0.0


        for p_id, data in self.cart.items():
            cantidad = data['cantidad']
            precio_usd = data['precio_usd']
            
            # Recalcular el precio unitario y subtotal en Bs con la tasa actual
            precio_bs = precio_usd * self.current_exchange_rate
            subtotal_bs = cantidad * precio_bs
            
            # Actualizar el precio_bs en el carrito (por si la tasa cambió)
            data['precio_bs'] = precio_bs
            
            total_general_bs += subtotal_bs


            self.cart_tree.insert("", "end",
                                  iid=f"cart_item_{p_id}",
                                  values=(
                                    p_id, 
                                    data['nombre'], 
                                    f"{cantidad:,.2f}", 
                                    f"{precio_usd:,.2f}", 
                                    f"{precio_bs:,.2f}", 
                                    f"{subtotal_bs:,.2f}"
                                  ))


        # Actualizar la etiqueta del total general
        # Mostramos el total en Bs (para la vista) y, entre paréntesis, el total en USD
        if self.current_exchange_rate > 0:
            total_general_usd = total_general_bs / self.current_exchange_rate
            self.total_label.configure(text=f"TOTAL: ${total_general_usd:,.2f} / Bs/ {total_general_bs:,.2f}")
        else:
            self.total_label.configure(text=f"TOTAL: Bs/ {total_general_bs:,.2f}")



    def process_sale(self):
        """
        Llama al método transaccional de la DB para registrar la venta y descontar el stock.
        """
        if not self.cart:
            messagebox.showwarning("Venta", "El carrito está vacío. Añade productos para procesar la venta.")
            return
        
        if self.current_exchange_rate <= 0:
            messagebox.showerror("Error", "La tasa de cambio no es válida. Por favor, ajústela en la configuración.")
            return


        try:
            # 1. Extraer el total en BS del label para calcular el total en USD
            # El formato del label es "TOTAL: $<USD> / Bs/ <BS>"
            total_label_text = self.total_label.cget("text")
            
            # Extraer el valor USD directamente del label (está después de "TOTAL: $")
            if "TOTAL: $" in total_label_text:
                parts = total_label_text.split("TOTAL: $")[1].split("/")
                total_final_usd_str = parts[0].strip().replace(",", "")
                total_final_usd = float(total_final_usd_str)
            else:
                # Si el formato no incluye USD, lo calculamos desde el BS
                bs_part = total_label_text.split('Bs/')[-1].strip().replace(",", "")
                total_final_bs = float(bs_part)
                total_final_usd = total_final_bs / self.current_exchange_rate
            
            current_rate = self.current_exchange_rate 


            # 2. Llamar al método transaccional de la base de datos
            # IMPORTANTE: Pasamos el total en USD
            success, message = self.db.process_sale_transaction(
                self.cart, 
                total_final_usd, 
                current_rate, 
                self.user_id # ID del usuario actual
            )


            if success:
                # Venta Exitosa: Limpiar y notificar
                summary = f"Venta procesada con éxito!\n\nProductos: {len(self.cart)} artículos únicos.\nTotal Final: ${total_final_usd:,.2f} / Bs/ {total_final_usd * current_rate:,.2f}"
                messagebox.showinfo("Venta Exitosa", summary)
                
                # Limpiar el carrito después de la venta
                self.cart = {}
                self.update_cart_display()
                self.search_products() # Recargar la búsqueda para mostrar el stock actualizado
            else:
                # Venta Fallida (por stock insuficiente u otro error de DB)
                messagebox.showerror("Error de Venta", f"No se pudo procesar la venta. Razón: {message}")
            
        except ValueError:
            messagebox.showerror("Error", "Error al calcular los totales. Verifique la tasa y los precios.")
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al procesar la venta: {e}")

