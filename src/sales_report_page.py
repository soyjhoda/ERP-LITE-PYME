import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv


class SalesReportPage(ctk.CTkFrame):
    """Página para mostrar reportes y análisis de ventas."""
    def __init__(self, master, db_manager, user_role):
        super().__init__(master, fg_color="#0D1B2A")
        self.db = db_manager
        self.user_role = user_role
        
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self._create_widgets()
        
        # Vincular doble clic para mostrar detalles
        self.sales_tree.bind("<Double-1>", self.on_sale_double_click)


    def _create_widgets(self):
        ctk.CTkLabel(self, text="📊 Reportes y Análisis de Ventas", 
                     font=ctk.CTkFont(size=20, weight="bold"), text_color="#00FFFF").grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        filter_frame = ctk.CTkFrame(self, fg_color="#1B263B", corner_radius=10)
        filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        filter_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        
        ctk.CTkLabel(filter_frame, text="Desde:", text_color="#00FFFF").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.start_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD")
        self.start_date_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Hasta:", text_color="#00FFFF").grid(row=0, column=2, sticky="w", padx=10, pady=10)
        self.end_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD")
        self.end_date_entry.grid(row=0, column=3, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Vendedor:", text_color="#00FFFF").grid(row=0, column=4, sticky="w", padx=10, pady=10)
        self.seller_combobox = ctk.CTkComboBox(filter_frame, state="readonly")
        self.seller_combobox.grid(row=0, column=5, sticky="ew", padx=10, pady=10)
        self._load_sellers()
        
        search_button = ctk.CTkButton(filter_frame, text="🔍 Buscar", command=self.load_report)
        search_button.grid(row=0, column=6, sticky="ew", padx=10, pady=10)
        
        self.sales_tree = ttk.Treeview(self, columns=("id", "date", "seller", "total_bs", "total_usd"), show="headings")
        self.sales_tree.heading("id", text="ID Venta")
        self.sales_tree.heading("date", text="Fecha")
        self.sales_tree.heading("seller", text="Vendedor")
        self.sales_tree.heading("total_bs", text="Total Bs")
        self.sales_tree.heading("total_usd", text="Total USD")
        self.sales_tree.column("id", width=60)
        self.sales_tree.column("date", width=120)
        self.sales_tree.column("seller", width=120)
        self.sales_tree.column("total_bs", width=100, anchor="e")
        self.sales_tree.column("total_usd", width=100, anchor="e")
        self.sales_tree.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        
        scrollbar = ctk.CTkScrollbar(self, command=self.sales_tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns", pady=10)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)
        
        export_button = ctk.CTkButton(self, text="📁 Exportar CSV", command=self.export_csv)
        export_button.grid(row=3, column=0, sticky="e", padx=20, pady=10)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 3), dpi=100)
        self.fig.patch.set_facecolor("#0D1B2A")
        self.ax.set_facecolor("#1B263B")
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=4, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)


    def _load_sellers(self):
        sellers = self.db.fetch_all("SELECT DISTINCT nombre_completo FROM usuarios WHERE rol IN ('Vendedor', 'Gerente', 'Administrador Total')")
        seller_names = [row[0] for row in sellers] if sellers else []
        self.seller_combobox.configure(values=["Todos"] + seller_names)
        self.seller_combobox.set("Todos")


    def load_report(self):
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        seller = self.seller_combobox.get()
        
        try:
            if start_date:
                datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Fecha inválida, debe ser formato YYYY-MM-DD")
            return
        
        query = "SELECT ventas.id, ventas.fecha, usuarios.nombre_completo, ventas.total_bs, ventas.total_usd FROM ventas JOIN usuarios ON ventas.user_id = usuarios.id WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date(ventas.fecha) >= date(?)"
            params.append(start_date)
        if end_date:
            query += " AND date(ventas.fecha) <= date(?)"
            params.append(end_date)
        if seller and seller != "Todos":
            query += " AND usuarios.nombre_completo = ?"
            params.append(seller)
        
        query += " ORDER BY ventas.fecha DESC"
        
        results = self.db.fetch_all(query, tuple(params))
        
        for i in self.sales_tree.get_children():
            self.sales_tree.delete(i)
        
        for row in results:
            values = [row[col] for col in row.keys()]
            self.sales_tree.insert("", "end", values=values)
        
        self.update_chart(results)


    def on_sale_double_click(self, event):
        selected_item = self.sales_tree.focus()
        if not selected_item:
            return
        values = self.sales_tree.item(selected_item, "values")
        venta_id = values[0]  # ID de venta está en la primera columna
        self.show_sale_details(venta_id)


    def show_sale_details(self, venta_id):
        details_window = ctk.CTkToplevel(self)
        details_window.title(f"Detalles de la Venta #{venta_id}")
        details_window.geometry("700x400")
        
        columns = ("producto", "cantidad", "precio_unitario_usd", "precio_unitario_bs", "subtotal_usd", "subtotal_bs")
        tree = ttk.Treeview(details_window, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=100, anchor="center")

        tree.pack(expand=True, fill="both", padx=10, pady=10)
        
        query = """
            SELECT nombre_producto, cantidad, precio_unitario_usd, precio_unitario_bs, subtotal_usd, subtotal_bs
            FROM detalles_venta WHERE venta_id = ?
        """
        rows = self.db.fetch_all(query, (venta_id,))
        
        for r in rows:
            values = list(r)
            tree.insert("", "end", values=values)


    def update_chart(self, data):
        self.ax.clear()
        self.ax.set_facecolor("#1B263B")
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.set_title("Ventas por Fecha", color="white")

        date_totals = {}
        for row in data:
            date_str = row['fecha'][:10]
            total_bs = row['total_bs']
            date_totals[date_str] = date_totals.get(date_str, 0) + total_bs

        dates = sorted(date_totals.keys())
        totals = [date_totals[d] for d in dates]

        self.ax.bar(dates, totals, color="#00FFFF")
        self.ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()
        self.canvas.draw()


    def export_csv(self):
        rows = [self.sales_tree.item(i)["values"] for i in self.sales_tree.get_children()]
        if not rows:
            messagebox.showinfo("Aviso", "No hay datos para exportar.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Archivos CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID Venta", "Fecha", "Vendedor", "Total Bs", "Total USD"])
                for row in rows:
                    writer.writerow(row)
            messagebox.showinfo("Exportado", f"Reporte exportado correctamente en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el archivo:\n{e}")
