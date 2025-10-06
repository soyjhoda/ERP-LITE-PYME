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
        
        self.cart = {}
        self.current_exchange_rate = 36.00
        
        # Variables para método de pago y monto recibido
        self.payment_method_var = ctk.StringVar(value="Seleccione método de pago")
        self.cash_currency_var = ctk.StringVar(value="Bolívares (Bs)")
        self.amount_received_var = ctk.StringVar(value="0.00")
        self.mobile_payment_id_var = ctk.StringVar(value="")
        
        style = ttk.Style(self)
        style.theme_use("clam")
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
        
        self.product_tree = ttk.Treeview(self, show='headings') 
        self.product_tree.tag_configure('out_of_stock', foreground='red', font=('Arial', 11, 'bold'))

        self.grid_columnconfigure(0, weight=1, minsize=400)
        self.grid_columnconfigure(1, weight=2, minsize=600)
        self.grid_rowconfigure(0, weight=1)

        # Izquierda: búsqueda y productos
        self.left_panel = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        self.left_panel.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.left_panel, text="BÚSQUEDA DE PRODUCTOS", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_CYAN).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.search_entry = ctk.CTkEntry(self.left_panel, 
                                         placeholder_text="Escriba código o nombre...", 
                                         width=350, height=40, 
                                         fg_color="#2c3e50", border_color=ACCENT_CYAN, border_width=1)
        self.search_entry.bind("<KeyRelease>", self.search_products)
        self.search_entry.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.search_results_frame = ctk.CTkFrame(self.left_panel, fg_color=FRAME_DARK, corner_radius=10)
        self.search_results_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.search_results_frame.grid_rowconfigure(0, weight=1)
        self.search_results_frame.grid_columnconfigure(0, weight=1)

        self.product_tree.destroy()
        self.product_tree = ttk.Treeview(self.search_results_frame, 
                                        columns=("code", "name", "price_bs", "stock_disp", "price_usd_stock"), 
                                        show='headings', 
                                        style="Cart.Treeview")
        self.product_tree.heading("code", text="Código"); self.product_tree.column("code", width=80, stretch=ctk.NO)
        self.product_tree.heading("name", text="Producto"); self.product_tree.column("name", minwidth=150, stretch=ctk.YES)
        self.product_tree.heading("price_bs", text="Precio (Bs)"); self.product_tree.column("price_bs", width=90, anchor=ctk.E)
        self.product_tree.heading("stock_disp", text="Stock Disp."); self.product_tree.column("stock_disp", width=80, anchor=ctk.CENTER)
        self.product_tree.heading("price_usd_stock", text=""); self.product_tree.column("price_usd_stock", width=0, stretch=ctk.NO)
        self.product_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.product_tree.bind("<Double-1>", self.add_to_cart_event)
        
        product_scrollbar = ctk.CTkScrollbar(self.search_results_frame, command=self.product_tree.yview)
        product_scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.product_tree.configure(yscrollcommand=product_scrollbar.set)

        # Derecha: carrito y resumen
        self.right_panel = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        self.right_panel.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.right_panel, text="CARRITO DE VENTA", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_CYAN).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.cart_frame = ctk.CTkFrame(self.right_panel, fg_color=FRAME_DARK, corner_radius=10)
        self.cart_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.cart_frame.grid_rowconfigure(0, weight=1)
        self.cart_frame.grid_columnconfigure(0, weight=1)

        self.cart_tree = ttk.Treeview(self.cart_frame, 
                                    columns=("id", "name", "qty", "price_usd", "price_bs", "subtotal_bs"), 
                                    show='headings',
                                    style="Cart.Treeview")
        self.cart_tree.heading("id", text="ID", anchor=ctk.CENTER)
        self.cart_tree.column("id", width=30, stretch=ctk.NO, anchor=ctk.CENTER)
        self.cart_tree.heading("name", text="Producto")
        self.cart_tree.column("name", minwidth=250, stretch=ctk.YES)
        self.cart_tree.heading("qty", text="Cant.")
        self.cart_tree.column("qty", width=60, anchor=ctk.CENTER)
        self.cart_tree.heading("price_usd", text="Precio ($)")
        self.cart_tree.column("price_usd", width=80, anchor=ctk.E)
        self.cart_tree.heading("price_bs", text="Precio (Bs)")
        self.cart_tree.column("price_bs", width=90, anchor=ctk.E)
        self.cart_tree.heading("subtotal_bs", text="Subtotal (Bs)")
        self.cart_tree.column("subtotal_bs", width=110, anchor=ctk.E)
        self.cart_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.cart_tree.bind("<Button-3>", self.show_cart_context_menu)
        
        cart_scrollbar = ctk.CTkScrollbar(self.cart_frame, command=self.cart_tree.yview)
        cart_scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.cart_tree.configure(yscrollcommand=cart_scrollbar.set)
        
        self.totals_frame = ctk.CTkFrame(self.right_panel, fg_color=FRAME_DARK, corner_radius=10)
        self.totals_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.totals_frame.grid_columnconfigure(0, weight=1)
        self.totals_frame.grid_columnconfigure(1, weight=1)
        self.totals_frame.grid_rowconfigure(0, weight=1)
        self.totals_frame.grid_rowconfigure(1, weight=1)

        self.rate_label = ctk.CTkLabel(self.totals_frame, text=f"Tasa Venta: Bs/ {self.current_exchange_rate:,.2f}", font=ctk.CTkFont(size=14), text_color=ACCENT_CYAN)
        self.rate_label.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")

        self.total_label = ctk.CTkLabel(self.totals_frame, text="TOTAL: Bs/ 0.00", font=ctk.CTkFont(size=28, weight="bold"), text_color=ACCENT_GREEN)
        self.total_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        self.payment_method_option = ctk.CTkOptionMenu(self.totals_frame,
                                                      values=[
                                                          "Tarjeta Débito/Crédito",
                                                          "Efectivo",
                                                          "Pago Móvil",
                                                          "Divisa Electrónica"
                                                      ],
                                                      variable=self.payment_method_var,
                                                      command=self.on_payment_method_change)
        self.payment_method_option.grid(row=2, column=0, padx=20, pady=(10,5), sticky="ew")

        self.cash_currency_option = ctk.CTkOptionMenu(self.totals_frame,
                                                      values=["Bolívares (Bs)", "Dólares (USD)"],
                                                      variable=self.cash_currency_var,
                                                      command=self.update_change_display)
        self.cash_currency_option.grid(row=3, column=0, padx=20, pady=(5,5), sticky="ew")
        self.cash_currency_option.grid_remove()

        self.amount_received_entry = ctk.CTkEntry(self.totals_frame,
                                                  placeholder_text="Monto recibido",
                                                  width=150,
                                                  height=35,
                                                  textvariable=self.amount_received_var)
        self.amount_received_entry.grid(row=4, column=0, padx=20, pady=(5,5), sticky="ew")
        self.amount_received_entry.bind("<KeyRelease>", lambda e: self.update_change_display())

        self.mobile_payment_id_entry = ctk.CTkEntry(self.totals_frame,
                                                    placeholder_text="ID Pago Móvil",
                                                    width=150,
                                                    height=35,
                                                    textvariable=self.mobile_payment_id_var)
        self.mobile_payment_id_entry.grid(row=5, column=0, padx=20, pady=(5,10), sticky="ew")
        self.mobile_payment_id_entry.grid_remove()

        ctk.CTkButton(self.totals_frame, text="✅ PROCESAR VENTA",
                      command=self.process_sale,
                      fg_color=ACCENT_GREEN, hover_color="#008a38", height=60,
                      font=ctk.CTkFont(size=18, weight="bold")).grid(row=2, column=1, rowspan=4, padx=20, pady=10, sticky="nsew")

        self.load_all_products_for_search()
        self.refresh_products()

    # Aquí siguen todos los métodos previos tal cual los tienes (search_products, add_to_cart_event, etc.)
    # Sin cambios.

    def refresh_products(self):
        if str(self.winfo_viewable()) == '1':
            self.load_all_products_for_search()
        self.after(2000, self.refresh_products)

    def update_rate(self, new_rate):
        if new_rate is not None and isinstance(new_rate, (int, float)):
            self.current_exchange_rate = new_rate
            self.rate_label.configure(text=f"Tasa Venta: Bs/ {self.current_exchange_rate:,.2f}")
            self.update_cart_display()
            self.update_change_display()
        else:
            print("Advertencia: Tasa de cambio inválida recibida.")

    def load_all_products_for_search(self):
        self.search_products()

    def search_products(self, event=None):
        query = self.search_entry.get().strip()
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
            id_prod, code, name, price_usd, stock_real = prod
            price_bs = price_usd * self.current_exchange_rate
            stock_en_carrito = self.cart.get(id_prod, {}).get('cantidad', 0)
            stock_disponible = int(stock_real) - stock_en_carrito

            row_tags = ()
            if stock_disponible <= 0:
                row_tags = ('out_of_stock',)

            data_oculta = f"{price_usd:.2f},{stock_real}"
            self.product_tree.insert("", "end", 
                                    iid=f"id_{id_prod}", 
                                    values=(code, name, f"{price_bs:,.2f}", stock_disponible, data_oculta),
                                    tags=row_tags)

    def add_to_cart_event(self, event):
        selected_item = self.product_tree.focus()
        if not selected_item:
            return

        values = self.product_tree.item(selected_item, 'values')
        try:
            stock_disponible_en_vista = int(values[3])
            data_oculta_str = values[4]
            price_usd = float(data_oculta_str.split(',')[0])
            stock_real = float(data_oculta_str.split(',')[1])
        except (ValueError, IndexError) as e:
            print(f"Error al leer datos del producto: {e}")
            messagebox.showerror("Error", "Error al leer los datos internos del producto.")
            return

        if stock_disponible_en_vista <= 0:
            messagebox.showwarning("Stock", "Stock insuficiente para añadir este producto.")
            return

        product_id = int(selected_item.split('_')[1])
        name = values[1]

        if product_id in self.cart:
            self.cart[product_id]['cantidad'] += 1
        else:
            price_bs = price_usd * self.current_exchange_rate
            self.cart[product_id] = {
                'nombre': name,
                'precio_usd': price_usd,
                'precio_bs': price_bs,
                'stock_real': stock_real,
                'cantidad': 1,
            }

        self.update_cart_display()
        self.search_products()

    def show_cart_context_menu(self, event):
        selected_item = self.cart_tree.identify_row(event.y)
        if not selected_item:
            return
        
        self.cart_tree.selection_set(selected_item)
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
        if product_id in self.cart:
            return self.cart[product_id]['stock_real']
        else:
            stock_data = self.db.fetch_one("SELECT stock FROM productos WHERE id = ?", (product_id,))
            return float(stock_data[0]) if stock_data and stock_data[0] is not None else 0.0

    def adjust_cart_quantity(self, product_id, adjustment):
        if product_id not in self.cart:
            return
        
        new_qty = self.cart[product_id]['cantidad'] + adjustment
        real_stock = self.cart[product_id]['stock_real']

        if new_qty <= 0:
            self.remove_from_cart(product_id)
            return

        if new_qty > math.floor(real_stock):
            messagebox.showwarning("Stock", f"No puedes añadir más. El stock máximo real disponible es {math.floor(real_stock)}.")
            return

        self.cart[product_id]['cantidad'] = new_qty
        price_usd = self.cart[product_id]['precio_usd']
        self.cart[product_id]['precio_bs'] = price_usd * self.current_exchange_rate

        self.update_cart_display()
        self.search_products()

    def prompt_for_quantity(self, product_id):
        if product_id not in self.cart:
            return

        current_qty = self.cart[product_id]['cantidad']
        real_stock = self.cart[product_id]['stock_real']

        new_qty_str = simpledialog.askstring("Cambiar Cantidad", f"Ingrese la nueva cantidad para '{self.cart[product_id]['nombre']}'.\nStock Real: {math.floor(real_stock)}", initialvalue=str(current_qty), parent=self)
        if new_qty_str is None:
            return
        
        try:
            new_qty = float(new_qty_str)
            new_qty_rounded = round(new_qty, 2)

            if new_qty_rounded <= 0:
                self.remove_from_cart(product_id)
                return

            if new_qty_rounded > real_stock:
                messagebox.showwarning("Stock", f"Cantidad inválida. El stock real es {real_stock:.2f}.")
                return

            self.cart[product_id]['cantidad'] = new_qty_rounded
            price_usd = self.cart[product_id]['precio_usd']
            self.cart[product_id]['precio_bs'] = price_usd * self.current_exchange_rate

            self.update_cart_display()
            self.search_products()

        except ValueError:
            messagebox.showerror("Error", "Por favor, ingrese un número válido.")
            return

    def remove_from_cart(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]
            self.update_cart_display()
            self.search_products()

    def update_cart_display(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        total_general_bs = 0.0

        for p_id, data in self.cart.items():
            cantidad = data['cantidad']
            precio_usd = data['precio_usd']
            precio_bs = precio_usd * self.current_exchange_rate
            subtotal_bs = cantidad * precio_bs
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

        if self.current_exchange_rate > 0:
            total_general_usd = total_general_bs / self.current_exchange_rate
            self.total_label.configure(text=f"TOTAL: ${total_general_usd:,.2f} / Bs/ {total_general_bs:,.2f}")
        else:
            self.total_label.configure(text=f"TOTAL: Bs/ {total_general_bs:,.2f}")

    def on_payment_method_change(self, method):
        if method == "Efectivo":
            self.cash_currency_option.grid()
            self.mobile_payment_id_entry.grid_remove()
        elif method == "Pago Móvil":
            self.cash_currency_option.grid_remove()
            self.mobile_payment_id_entry.grid()
        else:
            self.cash_currency_option.grid_remove()
            self.mobile_payment_id_entry.grid_remove()
        self.update_change_display()

    def update_change_display(self, event=None):
        try:
            total_label_text = self.total_label.cget("text")
            if "TOTAL: $" in total_label_text:
                parts = total_label_text.split("TOTAL: $")[1].split("/")
                total_usd_str = parts[0].strip().replace(",", "")
                total_usd = float(total_usd_str)
            else:
                bs_part = total_label_text.split('Bs/')[-1].strip().replace(",", "")
                total_bs = float(bs_part)
                total_usd = total_bs / self.current_exchange_rate

            method = self.payment_method_var.get()
            amount_received_str = self.amount_received_var.get().replace(',', '.').strip()
            amount_received = float(amount_received_str) if amount_received_str else 0.0

            if method == "Efectivo":
                currency = self.cash_currency_var.get()
                if "Dólares" in currency:
                    change = amount_received - total_usd
                    change_display = f"Cambio: ${change:.2f} USD"
                else:
                    change_bs = amount_received - total_usd * self.current_exchange_rate
                    change_display = f"Cambio: Bs/ {change_bs:.2f}"
            else:
                change_display = ""

            if hasattr(self, 'change_label'):
                self.change_label.configure(text=change_display)
            else:
                self.change_label = ctk.CTkLabel(self.totals_frame, text=change_display, font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_GREEN)
                self.change_label.grid(row=6, column=0, padx=20, sticky="w")
        except Exception:
            if hasattr(self, 'change_label'):
                self.change_label.configure(text="")

    def process_sale(self):
        if not self.cart:
            messagebox.showwarning("Venta", "El carrito está vacío. Añade productos para procesar la venta.")
            return
        
        if self.current_exchange_rate <= 0:
            messagebox.showerror("Error", "La tasa de cambio no es válida. Por favor, ajústela en la configuración.")
            return
        
        method = self.payment_method_var.get()
        if method == "Seleccione método de pago":
            messagebox.showwarning("Método de Pago", "Por favor, seleccione un método de pago válido.")
            return
        
        amount_received_str = self.amount_received_var.get().replace(',', '.').strip()
        try:
            amount_received = float(amount_received_str)
        except ValueError:
            messagebox.showerror("Monto Recibido", "Por favor, ingrese un monto recibido válido.")
            return

        total_label_text = self.total_label.cget("text")
        if "TOTAL: $" in total_label_text:
            parts = total_label_text.split("TOTAL: $")[1].split("/")
            total_final_usd_str = parts[0].strip().replace(",", "")
            total_final_usd = float(total_final_usd_str)
        else:
            bs_part = total_label_text.split('Bs/')[-1].strip().replace(",", "")
            total_final_bs = float(bs_part)
            total_final_usd = total_final_bs / self.current_exchange_rate
        
        if method == "Efectivo":
            currency = self.cash_currency_var.get()
            if "Dólares" in currency:
                if amount_received < total_final_usd:
                    messagebox.showerror("Pago Insuficiente", f"Monto recibido ({amount_received}) es menor al total ${total_final_usd:.2f} USD.")
                    return
                change = amount_received - total_final_usd
                amount_received_usd = amount_received
            else:
                total_bs = total_final_usd * self.current_exchange_rate
                if amount_received < total_bs:
                    messagebox.showerror("Pago Insuficiente", f"Monto recibido ({amount_received}) es menor al total Bs/ {total_bs:.2f}.")
                    return
                change = amount_received - total_bs
                amount_received_usd = amount_received / self.current_exchange_rate
        else:
            change = 0.0
            amount_received_usd = total_final_usd

        mobile_payment_id = ""
        if method == "Pago Móvil":
            mobile_payment_id = self.mobile_payment_id_var.get().strip()
            if not mobile_payment_id:
                messagebox.showwarning("ID Pago Móvil", "Por favor, ingrese el ID de Pago Móvil para esta transacción.")
                return
        
        try:
            success, message = self.db.process_sale_transaction(
                self.cart, 
                total_final_usd, 
                self.current_exchange_rate,
                self.user_id,
                payment_method=method,
                amount_received=amount_received_usd,
                change_given=change,
                mobile_payment_id=mobile_payment_id
            )
            if success:
                summary = f"Venta procesada con éxito!\n\nProductos: {len(self.cart)} artículos únicos.\nTotal Final: ${total_final_usd:,.2f} / Bs/ {total_final_usd * self.current_exchange_rate:,.2f}"
                if method == "Efectivo":
                    summary += f"\nMonto Recibido: {amount_received:.2f} {'USD' if 'Dólares' in self.cash_currency_var.get() else 'Bs'}"
                    summary += f"\nCambio: {change:.2f} {'USD' if 'Dólares' in self.cash_currency_var.get() else 'Bs'}"
                elif method == "Pago Móvil":
                    summary += f"\nID Pago Móvil: {mobile_payment_id}"
                messagebox.showinfo("Venta Exitosa", summary)

                self.cart = {}
                self.update_cart_display()
                self.search_products()
                self.amount_received_var.set("0.00")
                self.mobile_payment_id_var.set("")
                self.payment_method_var.set("Seleccione método de pago")
                self.cash_currency_option.grid_remove()
                self.mobile_payment_id_entry.grid_remove()
                self.update_change_display()
            else:
                messagebox.showerror("Error de Venta", f"No se pudo procesar la venta. Razón: {message}")
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al procesar la venta: {e}")

