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


    def _create_widgets(self):
        # Título
        ctk.CTkLabel(self, text="📊 Reportes y Análisis de Ventas", 
                     font=ctk.CTkFont(size=20, weight="bold"), text_color="#00FFFF").grid(row=0, column=0, sticky="w", padx=20, pady=10)
        
        # Frame filtros
        filter_frame = ctk.CTkFrame(self, fg_color="#1B263B", corner_radius=10)
        filter_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        filter_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        
        # Desde Fecha
        ctk.CTkLabel(filter_frame, text="Desde:", text_color="#00FFFF").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.start_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD")
        self.start_date_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        # Hasta Fecha
        ctk.CTkLabel(filter_frame, text="Hasta:", text_color="#00FFFF").grid(row=0, column=2, sticky="w", padx=10, pady=10)
        self.end_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="YYYY-MM-DD")
        self.end_date_entry.grid(row=0, column=3, sticky="ew", padx=10, pady=10)
        
        # Vendedor
        ctk.CTkLabel(filter_frame, text="Vendedor:", text_color="#00FFFF").grid(row=0, column=4, sticky="w", padx=10, pady=10)
        self.seller_combobox = ctk.CTkComboBox(filter_frame, state="readonly")
        self.seller_combobox.grid(row=0, column=5, sticky="ew", padx=10, pady=10)
        self._load_sellers()
        
        # Botón Buscar
        search_button = ctk.CTkButton(filter_frame, text="🔍 Buscar", command=self.load_report)
        search_button.grid(row=0, column=6, sticky="ew", padx=10, pady=10)
        
        # Tabla ventas
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
        
        # Scroll para tabla
        scrollbar = ctk.CTkScrollbar(self, command=self.sales_tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns", pady=10)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)
        
        # Botón Exportar
        export_button = ctk.CTkButton(self, text="📁 Exportar CSV", command=self.export_csv)
        export_button.grid(row=3, column=0, sticky="e", padx=20, pady=10)
        
        # Gráfica
        self.fig, self.ax = plt.subplots(figsize=(8, 3), dpi=100)
        self.fig.patch.set_facecolor("#0D1B2A")
        self.ax.set_facecolor("#1B263B")
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=4, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)


    def _load_sellers(self):
        # Cargar vendedores desde la DB para filtro
        sellers = self.db.fetch_all("SELECT DISTINCT nombre_completo FROM usuarios WHERE rol IN ('Vendedor', 'Gerente', 'Administrador Total')")
        seller_names = [row[0] for row in sellers] if sellers else []
        self.seller_combobox.configure(values=["Todos"] + seller_names)
        self.seller_combobox.set("Todos")


    def load_report(self):
        # Obtener filtros
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        seller = self.seller_combobox.get()
        
        # Validaciones simples de fecha
        try:
            if start_date:
                datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Fecha inválida, debe ser formato YYYY-MM-DD")
            return
        
        # Consulta base corregida: user_id en lugar de usuario_id
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
        
        # Limpiar tabla
        for i in self.sales_tree.get_children():
            self.sales_tree.delete(i)
        
        # Insertar datos desempaquetando sqlite3.Row a lista
        for row in results:
            values = [row[col] for col in row.keys()]
            self.sales_tree.insert("", "end", values=values)
        
        # Actualizar gráfica
        self.update_chart(results)


    def update_chart(self, data):
        self.ax.clear()
        self.ax.set_facecolor("#1B263B")
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.set_title("Ventas por Fecha", color="white")


        # Contar ventas por fecha
        date_totals = {}
        for row in data:
            date_str = row['fecha'][:10]  # Extraer fecha YYYY-MM-DD usando clave en vez de índice
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
