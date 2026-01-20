# -------------------- IMPORTS --------------------
import mysql.connector
import tkinter as kt
from tkinter import filedialog, messagebox, ttk
import csv as c
import datetime
from tkinter import simpledialog

a=datetime.date.today()
mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql",
        database="inventory"
    )

mycursor = mydb.cursor(buffered=True)

# -------------------- SINGLE CLICK STATUS TOGGLE (✔ / ❌) --------------------
def toggle_status_from_table(event, table):
    row_id = table.identify_row(event.y)
    col_id = table.identify_column(event.x)

    # Trigger ONLY on the Status column (#7)
    if col_id != "#7" or not row_id:
        return

    row = table.item(row_id)["values"]
    product_id = row[0]
    current_symbol = row[6]

    # Decide new status and update the inventory table accordingly
    if current_symbol == "✔":
        new_status = "Deactive"
        new_symbol = "❌"
        # EFFECT IN INVENTORY: Remove the item from today's stock list
        mycursor.execute("DELETE FROM stock WHERE product_id=%s AND s_date=%s", (product_id, a))
    else:
        new_status = "Active"
        new_symbol = "✔"
        # EFFECT IN INVENTORY: Re-add the item to today's stock list if it was missing
        mycursor.execute("""
            INSERT IGNORE INTO stock (product_id, O_stock, purchase, sales, b_stock, s_date) 
            VALUES (%s, 0, 0, 0, 0, %s)
        """, (product_id, a))

    # Update the product's status in the main product table
    mycursor.execute("UPDATE product SET status=%s WHERE product_id=%s", (new_status, product_id))
    mydb.commit()

    # Update the UI Treeview immediately
    new_values = list(row)
    new_values[6] = new_symbol
    table.item(row_id, values=new_values)

def purchase_new(event, table):
    row = table.identify_row(event.y)
    column = table.identify_column(event.x)

    # Purchase column is #4 in your stock table
    if not row or column != "#4":
        return

    r = table.item(row)["values"]
    product_name = r[1]
    bal = r[5]
    
    mycursor.execute(
        "SELECT product_id FROM product WHERE product_name=%s",
        (product_name,)
    )
    result = mycursor.fetchone()
    if not result:
        return

    p_id = result[0]

    new_purchase = simpledialog.askinteger(
        "Update Stock",
        f"Enter new purchase for {product_name}:"
    )

    if new_purchase is None:
        return

    new_balance = bal + new_purchase

    mycursor.execute(
        "UPDATE stock SET purchase=%s, b_stock=%s WHERE product_id=%s AND s_date=%s",
        (new_purchase, new_balance, p_id,a)
    )
    mydb.commit()

    # ✅ REFRESH ONLY THE CURRENT TABLE
    table.delete(*table.get_children())

    # Reload data for currently selected date
    selected_date = r[8]
    for widget in table.master.winfo_children():
        if isinstance(widget, ttk.Combobox):
            selected_date = widget.get()
            break

    if selected_date:
        mycursor.execute("""
            SELECT  p.brand, p.product_name,s.O_stock, s.purchase,s.sales, s.b_stock, p.p_rate,p.s_rate, s.s_date
                FROM product p
                JOIN stock s ON p.product_id = s.product_id
                WHERE s.s_date = %s
        """, (selected_date,))
    else:
        mycursor.execute("""
             SELECT  p.brand, p.product_name,s.O_stock, s.purchase,s.sales, s.b_stock, p.p_rate,p.s_rate, s.s_date
                FROM product p
                JOIN stock s ON p.product_id = s.product_id
            
        """)

    for row in mycursor.fetchall():
        table.insert("", "end", values=row)

    

# -------------------- MAIN WINDOW --------------------
window = kt.Tk()
window.geometry("420x420")
window.title("Inventory Manager")
window.config(background="cyan")
container=kt.Frame(window)

container.pack(fill="both", expand=True)
container.grid_rowconfigure(0, weight=1)
container.grid_columnconfigure(0, weight=1)

search_frame = kt.Frame(container)
product_frame=kt.Frame(search_frame)

dash_frame=kt.Frame(container)

order_page=kt.Frame(container)
order_frame=kt.Frame(order_page)
cust_more=kt.Frame(container)
for f in (dash_frame,order_page ,cust_more,order_frame,search_frame,product_frame):
    f.grid(row=0, column=0, sticky="nsew")


icon = kt.PhotoImage(file="logo.png")
window.iconphoto(True, icon)

# -------------------- VIEW TABLE --------------------
def view_table():
    for widget in search_frame.winfo_children():
        widget.destroy()
    
    # Theme Colors
    bg_main = "#f0f4f8"       # Light blue-grey background
    sidebar_color = "#1a365d" # Dark navy blue
    card_color = "#ffffff"    # White card background
    accent_blue = "#2b6cb0"   # Medium blue
    text_dark = "#2d3748"     # Dark grey

    search_frame.config(bg=bg_main)
    show_page(search_frame)

    # 1. Sidebar Navigation (Consistent with Dashboard)
    sidebar = kt.Frame(search_frame, bg=sidebar_color, width=220)
    sidebar.pack(side="left", fill="y")

    kt.Label(sidebar, text="Nitya Sales", font=("Arial", 16, "bold"), 
             bg=sidebar_color, fg="white", pady=25).pack()

    nav_btns = [
        ("🏠 Dashboard", lambda: [build_dashboard(), show_page(dash_frame)]),
        ("📦 Products", view_table),
        ("📊 Inventory", master_function),
        ("🛒 Orders", order_page_frame),
        ("❌ Exit", window.destroy)
    ]

    for text, cmd in nav_btns:
        kt.Button(sidebar, text=text, font=("Arial", 11), bg=sidebar_color, 
                  fg="white", bd=0, activebackground=accent_blue, 
                  activeforeground="white", anchor="w", padx=25,
                  command=cmd).pack(fill="x", pady=5)

    # 2. Main Content Area
    content = kt.Frame(search_frame, bg=bg_main, padx=30, pady=25)
    content.pack(side="right", fill="both", expand=True)

    # Header Row
    header_row = kt.Frame(content, bg=bg_main)
    header_row.pack(fill="x", pady=(0, 20))

    kt.Label(header_row, text="Product Management", font=("Arial", 22, "bold"), 
             bg=bg_main, fg=text_dark).pack(side="left")

    kt.Button(header_row, text="+ Add New Product", font=("Arial", 11, "bold"), 
              bg="#38a169", fg="white", padx=15, pady=8, bd=0,
              command=pro_frame).pack(side="right")

    # 3. Search Bar Card
    search_card = kt.Frame(content, bg=card_color, padx=15, pady=15, 
                           highlightbackground="#cbd5e0", highlightthickness=1)
    search_card.pack(fill="x", pady=(0, 20))

    kt.Label(search_card, text="Search:", font=("Arial", 10, "bold"), bg=card_color).pack(side="left")
    search_entry = kt.Entry(search_card, width=25, font=("Arial", 10))
    search_entry.pack(side="left", padx=10)

    kt.Label(search_card, text="Filter By:", font=("Arial", 10, "bold"), bg=card_color).pack(side="left")
    search_type = ttk.Combobox(search_card, values=["product_name", "brand"], state="readonly", width=15)
    search_type.set("product_name")
    search_type.pack(side="left", padx=10)

    kt.Button(search_card, text="🔍 Search", bg=accent_blue, fg="white", bd=0, 
              padx=15, command=lambda: search()).pack(side="left", padx=5)

    # 4. Product Table Card
    table_card = kt.Frame(content, bg=card_color, highlightbackground="#cbd5e0", highlightthickness=1)
    table_card.pack(fill="both", expand=True)

    table = ttk.Treeview(
        table_card, 
        columns=("id","name","brand","cat","pr","sr","status"),
        show='headings'
    )

    headings = ["ID","Product Name","Brand","Category","P Rate","S Rate","Status"]
    for col, head in zip(table["columns"], headings):
        table.heading(col, text=head.upper())
        table.column(col, anchor="center", width=110)

    table.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    
    # Logic to load data and bind click
    def load_data(query=None, value=None):
        for row in table.get_children(): table.delete(row)
        if query is None: mycursor.execute("SELECT * FROM product")
        else: mycursor.execute(query, (value,))
        
        for row in mycursor.fetchall():
            sym = "✔" if row[6] == "Active" else "❌"
            table.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], row[5], sym))

    def search():
        col = search_type.get()
        txt = search_entry.get()
        if not txt: load_data()
        else: load_data(f"SELECT * FROM product WHERE {col} LIKE %s", f"%{txt}%")

    table.bind("<Button-1>", lambda event: toggle_status_from_table(event, table))
    load_data()


# -------------------- CSV UPLOAD --------------------
def upload():
    file_path = filedialog.askopenfilename(
        title="Select CSV file",
        filetypes=[("CSV files", "*.csv")]
    )

    if not file_path:
        return

    query = """
    INSERT INTO tempo
    (product_name, brand, catagory, p_rate, s_rate,o_stock,purchase,sales,b_stock, status,s_date)
    VALUES  ( %s, %s, %s, %s, %s, %s, %s, %s, %s,'Active',%s)
    """

    with open(file_path, 'r') as csvfile:
        reader = c.DictReader(csvfile)
        for row in reader:
            values = (
                row['product_name'],
                row['brand'],
                row['category'],
                row['prate'],
                row['srate'],
                row['o_stock'],
                row['purchase'],
                row['sales'],
                row['b_stock'],
                a
                
            )
            mycursor.execute(query, values)

    mydb.commit()
    mycursor.execute("INSERT INTO product (product_name, brand, catagory, p_rate, s_rate, Status) select distinct product_name, brand, catagory, p_rate, s_rate, status FROM tempo WHERE product_name NOT IN (SELECT product_name FROM product)")
    
    mycursor.execute("INSERT INTO stock (product_id, O_stock, purchase, sales, b_stock,s_date) select p.product_id, t.O_stock, t.purchase, t.sales, t.b_stock, t.s_date FROM tempo t JOIN product p ON t.product_name = p.product_name")
    mydb.commit()
   
    mycursor.execute("TRUNCATE TABLE tempo")
    messagebox.showinfo("Success", "CSV Imported Successfully!")
def change_data():
    try:
        # 1. Get the current date from the system
        today = datetime.date.today()

        # 2. Check if today's records already exist
        mycursor.execute("SELECT COUNT(*) FROM stock WHERE s_date = %s", (today,))
        if mycursor.fetchone()[0] > 0:
            print(f"Records for {today} already exist.")
            return

        # 3. Find the most recent date in the database
        mycursor.execute("SELECT MAX(s_date) FROM stock")
        last_recorded_date = mycursor.fetchone()[0]

        if last_recorded_date:
            # 4. Carry forward the 'b_stock' (Balance) from the last date 
            # to the 'o_stock' (Opening) of today.
            query = """
                INSERT INTO stock (product_id, o_stock, purchase, sales, b_stock, s_date) 
                SELECT product_id, b_stock, 0, 0, b_stock, %s 
                FROM stock 
                WHERE s_date = %s
            """
            mycursor.execute(query, (today, last_recorded_date))
            mydb.commit()
            print(f"Successfully carried stock forward from {last_recorded_date} to {today}")
        else:
            print("No previous records found to carry forward.")

    except Exception as e:
        print(f"Error updating daily stock: {e}")
def view_table_stock():
    # 1. Clear the frame to prepare for the new UI
    for widget in dash_frame.winfo_children():
        widget.destroy()
    
    # --- THEME COLORS ---
    bg_main = "#f0f4f8"       # Light blue-grey background
    sidebar_color = "#1a365d" # Dark navy blue
    card_color = "#ffffff"    # White card background
    accent_blue = "#2b6cb0"   # Medium blue
    text_dark = "#2d3748"     # Dark grey

    dash_frame.config(bg=bg_main)
    show_page(dash_frame)

    # 1. SIDEBAR NAVIGATION (Consistent with Dashboard)
    sidebar = kt.Frame(dash_frame, bg=sidebar_color, width=220)
    sidebar.pack(side="left", fill="y")

    kt.Label(sidebar, text="Nitya Sales", font=("Arial", 16, "bold"), 
             bg=sidebar_color, fg="white", pady=25).pack()

    nav_btns = [
        ("🏠 Dashboard", lambda: [build_dashboard(), show_page(dash_frame)]),
        ("📦 Products", view_table),
        ("📊 Inventory", master_function),
        ("🛒 Orders", order_page_frame),
        ("❌ Exit", window.destroy)
    ]

    for text, cmd in nav_btns:
        kt.Button(sidebar, text=text, font=("Arial", 11), bg=sidebar_color, 
                  fg="white", bd=0, activebackground=accent_blue, 
                  activeforeground="white", anchor="w", padx=25,
                  command=cmd).pack(fill="x", pady=5)

    # 2. MAIN CONTENT AREA
    content = kt.Frame(dash_frame, bg=bg_main, padx=30, pady=25)
    content.pack(side="right", fill="both", expand=True)

    # Header Row
    header_row = kt.Frame(content, bg=bg_main)
    header_row.pack(fill="x", pady=(0, 20))

    kt.Label(header_row, text="Inventory Stock Status", font=("Arial", 22, "bold"), 
             bg=bg_main, fg=text_dark).pack(side="left")

    # 3. FILTER CARD (Search Controls)
    filter_card = kt.Frame(content, bg=card_color, padx=15, pady=15, 
                           highlightbackground="#cbd5e0", highlightthickness=1)
    filter_card.pack(fill="x", pady=(0, 20))

    # Date Filter
    kt.Label(filter_card, text="Date:", font=("Arial", 10, "bold"), bg=card_color).pack(side="left", padx=(0, 5))
    date_filter = ttk.Combobox(filter_card, state="readonly", width=12)
    date_filter.pack(side="left", padx=5)

    # Brand Filter
    kt.Label(filter_card, text="Brand:", font=("Arial", 10, "bold"), bg=card_color).pack(side="left", padx=(10, 5))
    brand_filter = ttk.Combobox(filter_card, values=["All", "hp", "oppo", "earthonic"], state="readonly", width=10)
    brand_filter.set("All")
    brand_filter.pack(side="left", padx=5)

    # Model Search
    kt.Label(filter_card, text="Model:", font=("Arial", 10, "bold"), bg=card_color).pack(side="left", padx=(10, 5))
    name_search = kt.Entry(filter_card, width=20)
    name_search.pack(side="left", padx=5)

    # Search Button
    kt.Button(filter_card, text="🔍 Search", bg=accent_blue, fg="white", font=("Arial", 10, "bold"),
              padx=15, bd=0, command=lambda: load_filtered_data()).pack(side="left", padx=15)

    # 4. TABLE CARD (Inventory Treeview)
    table_card = kt.Frame(content, bg=card_color, highlightbackground="#cbd5e0", highlightthickness=1)
    table_card.pack(fill="both", expand=True)

    columns = ("brand", "product_name", "o_stock", "purchase", "sales", "b_stock", "p_rate", "s_rate", "s_date")
    tree = ttk.Treeview(table_card, columns=columns, show="headings")
    
    # Column Setup
    tree.heading("brand", text='BRAND')
    tree.column('brand', width=100, anchor='center')
    tree.heading('product_name', text='MODEL')
    tree.column('product_name', width=200, anchor='center')
    
    for i in range(2, 9):
        tree.heading(columns[i], text=columns[i].replace('_', ' ').upper())
        tree.column(columns[i], width=100, anchor="center")
    
    tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    # --- DYNAMIC FILTER LOGIC ---
    def load_filtered_data(event=None):
        for item in tree.get_children():
            tree.delete(item)
            
        selected_date = date_filter.get()
        selected_brand = brand_filter.get()
        search_text = name_search.get().strip()
        
        try:
            # Base query with custom sorting: 
            # (s.b_stock = 0) returns 1 if true, 0 if false. 
            # Sorting by this first puts 0s at the end (1 > 0).
            query = """
                SELECT p.brand, p.product_name, s.O_stock, s.purchase, s.sales, s.b_stock, p.p_rate, p.s_rate, s.s_date
                FROM product p
                JOIN stock s ON p.product_id = s.product_id
                WHERE s.s_date = %s
            """
            params = [selected_date]

            if selected_brand != "All":
                query += " AND p.brand = %s"
                params.append(selected_brand)

            if search_text:
                query += " AND p.product_name LIKE %s"
                params.append(f"%{search_text}%")

            # --- THE KEY CHANGE: SORTING LOGIC ---
            # This puts b_stock > 0 items first, then b_stock = 0 items last.
            query += " ORDER BY (s.b_stock = 0) ASC, p.product_name ASC"

            mycursor.execute(query, tuple(params))
            rows = mycursor.fetchall()

            for row in rows:
                tree.insert("", "end", values=row)
        except Exception as e:
            print(f"Error filtering data: {e}")

    # Bindings for interactive search
    tree.bind("<Button-1>", lambda revent: purchase_new(revent, tree))
    date_filter.bind("<<ComboboxSelected>>", load_filtered_data)
    brand_filter.bind("<<ComboboxSelected>>", load_filtered_data)
    name_search.bind("<Return>", lambda e: load_filtered_data())

def build_dashboard(target_date=None):
    # Clear dashboard if rebuilt accidentally
    for widget in dash_frame.winfo_children():
        widget.destroy()

    # Define dynamic target date (defaults to current system date 'a')
    view_date = target_date if target_date else str(a)

    # --- MODERN THEME COLORS ---
    bg_main = "#f0f4f8"       # Light blue-grey background
    sidebar_color = "#1a365d" # Dark navy blue sidebar
    card_color = "#ffffff"    # White cards
    accent_blue = "#2b6cb0"   # Medium blue for accents
    text_dark = "#2d3748"     # Dark grey text

    dash_frame.config(bg=bg_main)

    # 1. SIDEBAR (Navigation Area)
    sidebar = kt.Frame(dash_frame, bg=sidebar_color, width=220)
    sidebar.pack(side="left", fill="y")

    kt.Label(sidebar, text="Nitya Sales", font=("Arial", 16, "bold"), 
             bg=sidebar_color, fg="white", pady=25).pack()

    nav_btns = [
        ("📦 Products", view_table),
        ("🤝 Dealers", customer),
        ("📊 Inventory", master_function),
        ("🛒 Orders", order_page_frame),
        ("❌ Exit", window.destroy)
    ]

    for text, cmd in nav_btns:
        kt.Button(sidebar, text=text, font=("Arial", 11), bg=sidebar_color, 
                  fg="white", bd=0, activebackground=accent_blue, 
                  activeforeground="white", anchor="w", padx=25,
                  command=cmd).pack(fill="x", pady=5)

    # 2. MAIN CONTENT AREA
    content = kt.Frame(dash_frame, bg=bg_main, padx=30, pady=25)
    content.pack(side="right", fill="both", expand=True)

    # Header Row with Title and Date Filter
    header_row = kt.Frame(content, bg=bg_main)
    header_row.pack(fill="x", pady=(0, 25))

    kt.Label(header_row, text="Inventory Overview", font=("Arial", 22, "bold"), 
             bg=bg_main, fg=text_dark).pack(side="left")

    # Date Filter Dropdown
    date_filter = ttk.Combobox(header_row, state="readonly", width=15)
    date_filter.pack(side="right", padx=10)
    
    kt.Label(header_row, text="Filter Date:", font=("Arial", 10), 
             bg=bg_main, fg=text_dark).pack(side="right")

    # Fetch unique dates from database for the filter
    mycursor.execute("SELECT DISTINCT s_date FROM stock ORDER BY s_date DESC")
    available_dates = [str(d[0]) for d in mycursor.fetchall()]
    date_filter['values'] = available_dates
    date_filter.set(view_date)

    # Auto-refresh when a new date is selected
    def on_date_change(event):
        build_dashboard(target_date=date_filter.get())

    date_filter.bind("<<ComboboxSelected>>", on_date_change)

    # --- DATABASE CALCULATIONS FOR THE SELECTED DATE ---
    # 1. Total Units Sold
    mycursor.execute("SELECT SUM(sales) FROM stock WHERE s_date = %s", (view_date,))
    sold_qty = mycursor.fetchone()[0] or 0

    # 2. Total Sales Value (Sold Quantity * Sales Rate)
    mycursor.execute("""
        SELECT SUM(s.sales * p.s_rate) 
        FROM stock s JOIN product p ON s.product_id = p.product_id 
        WHERE s.s_date = %s
    """, (view_date,))
    sales_val = mycursor.fetchone()[0] or 0

    # 3. Total Available Physical Units
    mycursor.execute("SELECT SUM(b_stock) FROM stock WHERE s_date = %s", (view_date,))
    stock_qty = mycursor.fetchone()[0] or 0

    # 4. Total Stock Investment Value (Available Units * Purchase Rate)
    mycursor.execute("""
        SELECT SUM(s.b_stock * p.p_rate) 
        FROM stock s JOIN product p ON s.product_id = p.product_id 
        WHERE s.s_date = %s
    """, (view_date,))
    stock_val = mycursor.fetchone()[0] or 0

    # --- STATISTICS CARDS DISPLAY ---
    cards_frame = kt.Frame(content, bg=bg_main)
    cards_frame.pack(fill="x")

    # Sales Performance Card
    c1 = kt.Frame(cards_frame, bg=card_color, highlightbackground="#cbd5e0", highlightthickness=1, padx=20, pady=20)
    c1.pack(side="left", expand=True, fill="both", padx=(0, 10))
    kt.Label(c1, text="SALES PERFORMANCE", font=("Arial", 9, "bold"), bg=card_color, fg="#718096").pack(anchor="w")
    kt.Label(c1, text=f"{sold_qty} Items Sold", font=("Arial", 16, "bold"), bg=card_color, fg=accent_blue).pack(anchor="w", pady=5)
    kt.Label(c1, text=f"Value: ₹{sales_val:,.2f}", font=("Arial", 11), bg=card_color, fg=text_dark).pack(anchor="w")

    # Current Inventory Card
    c2 = kt.Frame(cards_frame, bg=card_color, highlightbackground="#cbd5e0", highlightthickness=1, padx=20, pady=20)
    c2.pack(side="left", expand=True, fill="both", padx=(10, 0))
    kt.Label(c2, text="CURRENT INVENTORY", font=("Arial", 9, "bold"), bg=card_color, fg="#718096").pack(anchor="w")
    kt.Label(c2, text=f"{stock_qty} Units in Stock", font=("Arial", 16, "bold"), bg=card_color, fg=accent_blue).pack(anchor="w", pady=5)
    kt.Label(c2, text=f"Value: ₹{stock_val:,.2f}", font=("Arial", 11), bg=card_color, fg=text_dark).pack(anchor="w")

    # 3. SYSTEM LOG PANEL
    log_panel = kt.Frame(content, bg=card_color, highlightbackground="#cbd5e0", highlightthickness=1, pady=15, padx=15)
    log_panel.pack(fill="both", expand=True, pady=25)
    kt.Label(log_panel, text="System Log", font=("Arial", 12, "bold"), bg=card_color, fg=text_dark).pack(anchor="w")
    kt.Label(log_panel, text=f"• Records currently shown for date: {view_date}", 
             font=("Arial", 10), bg=card_color, fg=text_dark).pack(anchor="w", pady=5)
def pro_frame():
    global product_frame
    
    # 1. Validation: If the frame doesn't exist or was destroyed, recreate it as a child of 'container'
    if not product_frame.winfo_exists():
        product_frame = kt.Frame(container)
        product_frame.grid(row=0, column=0, sticky="nsew")

    # 2. Safely clear internal contents
    try:
        for widget in product_frame.winfo_children():
            widget.destroy()
    except kt.TclError:
        # If a race condition occurs, recreate the frame entirely
        product_frame = kt.Frame(container)
        product_frame.grid(row=0, column=0, sticky="nsew")
    
    # --- THEME COLORS ---
    bg_main = "#f0f4f8"       
    sidebar_color = "#1a365d" 
    card_color = "#ffffff"    
    accent_blue = "#2b6cb0"   
    text_dark = "#2d3748"     

    product_frame.config(bg=bg_main)
    show_page(product_frame)

    # 1. SIDEBAR NAVIGATION
    sidebar = kt.Frame(product_frame, bg=sidebar_color, width=220)
    sidebar.pack(side="left", fill="y")

    kt.Label(sidebar, text="Nitya Sales", font=("Arial", 16, "bold"), 
             bg=sidebar_color, fg="white", pady=25).pack()

    nav_btns = [
        ("🏠 Dashboard", lambda: [build_dashboard(), show_page(dash_frame)]),
        ("📦 Products", view_table),
        ("📊 Inventory", master_function),
        ("🛒 Orders", order_page_frame),
        ("❌ Exit", window.destroy)
    ]

    for text, cmd in nav_btns:
        kt.Button(sidebar, text=text, font=("Arial", 11), bg=sidebar_color, 
                  fg="white", bd=0, activebackground=accent_blue, 
                  activeforeground="white", anchor="w", padx=25,
                  command=cmd).pack(fill="x", pady=5)

    # 2. MAIN CONTENT AREA
    content = kt.Frame(product_frame, bg=bg_main, padx=40, pady=30)
    content.pack(side="right", fill="both", expand=True)

    # Header
    header_row = kt.Frame(content, bg=bg_main)
    header_row.pack(fill="x", pady=(0, 20))

    kt.Label(header_row, text="Add New Product", font=("Arial", 22, "bold"), 
             bg=bg_main, fg=text_dark).pack(side="left")

    # 3. PRODUCT FORM CARD
    form_card = kt.Frame(content, bg=card_color, padx=30, pady=30, 
                         highlightbackground="#cbd5e0", highlightthickness=1)
    form_card.pack(fill="both", expand=True)

    # Helper function to create labeled entries
    def create_field(parent, label_text, row):
        kt.Label(parent, text=label_text, font=("Arial", 10, "bold"), bg=card_color, fg=text_dark).grid(row=row, column=0, sticky="w", pady=(10, 2))
        entry = kt.Entry(parent, font=("Arial", 11), width=40, bd=1, relief="solid")
        entry.grid(row=row+1, column=0, sticky="w", pady=(0, 10))
        return entry

    def create_combo(parent, label_text, values, row):
        kt.Label(parent, text=label_text, font=("Arial", 10, "bold"), bg=card_color, fg=text_dark).grid(row=row, column=0, sticky="w", pady=(10, 2))
        combo = ttk.Combobox(parent, values=values, font=("Arial", 11), width=37, state="readonly")
        combo.grid(row=row+1, column=0, sticky="w", pady=(0, 10))
        return combo

    # Form Fields
    entry_name = create_field(form_card, "Product Name", 0)
    combo_brand = create_combo(form_card, "Brand", ["hp", "oppo", "earthonic"], 2)
    combo_cat = create_combo(form_card, "Category", ["laptop", "mobile", "TV"], 4)
    entry_prate = create_field(form_card, "Purchase Rate (PRate)", 6)
    entry_srate = create_field(form_card, "Sales Rate (SRates)", 8)
    entry_ostock = create_field(form_card, "Opening Stock", 10)
    entry_bstock = create_field(form_card, "Balance Stock", 12)

    # 4. ACTION BUTTONS
    btn_frame = kt.Frame(form_card, bg=card_color)
    btn_frame.grid(row=14, column=0, sticky="w", pady=20)

    def store_data():   
        try:
            query = """
            INSERT INTO tempo
            (product_name, brand, catagory, p_rate, s_rate, o_stock, purchase, sales, b_stock, status, s_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active', %s)
            """
            values = (
                entry_name.get(), combo_brand.get(), combo_cat.get(),
                entry_prate.get(), entry_srate.get(), entry_ostock.get(),
                0, 0, entry_bstock.get(), a
            )

            mycursor.execute(query, values)
            mydb.commit()
            
            p_id = mycursor.lastrowid
            mycursor.execute("INSERT INTO product (product_name, brand, catagory, p_rate, s_rate, Status) SELECT DISTINCT product_name, brand, catagory, p_rate, s_rate, status FROM tempo WHERE product_name NOT IN (SELECT product_name FROM product)")
            mycursor.execute("INSERT INTO stock (product_id, O_stock, purchase, sales, b_stock, s_date) SELECT p.product_id, t.O_stock, t.purchase, t.sales, t.b_stock, t.s_date FROM tempo t JOIN product p ON t.product_name = p.product_name")
            mydb.commit()
            mycursor.execute("TRUNCATE TABLE tempo")

            messagebox.showinfo("Success", f"Product Stored Successfully\nID: {p_id}")
            view_table() 
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    kt.Button(btn_frame, text="💾 Save Product", font=("Arial", 11, "bold"), bg="#38a169", fg="white", padx=20, pady=8, bd=0, command=store_data).pack(side="left", padx=(0, 15))
    kt.Button(btn_frame, text="📥 Import CSV", font=("Arial", 11), bg=accent_blue, fg="white", padx=20, pady=8, bd=0, command=upload).pack(side="left")
def open_order_frame():
    global order_frame
    
    # 1. Re-create or Clear the Frame
    if not order_frame.winfo_exists():
        order_frame = kt.Frame(order_page)
        order_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    for widget in order_frame.winfo_children():
        widget.destroy()
    
    # UI Theme Colors
    bg_color = "#f4f4f4"
    accent_green = "#2dcf58"
    accent_blue = "#2b6cb0"
    order_frame.config(bg=bg_color)
    show_page(order_frame)

    # --- LOGIC FUNCTIONS ---
    def update_products(event):
        selected_brand = brand_cb.get()
        query = "SELECT product_name FROM product WHERE brand=%s"
        if selected_brand == "All":
            mycursor.execute("SELECT product_name FROM product")
        else:
            mycursor.execute(query, (selected_brand,))
        pro = mycursor.fetchall()
        prod_cb['values'] = [j[0] for j in pro]
        prod_cb.set('')
        selling_rate_var.set("")
        stok_lbl.config(text="Available Stock: -", fg="black")

    def fetch_details(event):
        p_name = prod_cb.get()
        mycursor.execute("SELECT product_id, s_rate FROM product WHERE product_name=%s", (p_name,))
        res = mycursor.fetchone()
        if res:
            p_id, s_rate = res
            selling_rate_var.set(s_rate)
            # Fetch stock for current date 'a'
            mycursor.execute("SELECT b_stock FROM stock WHERE product_id=%s AND s_date=%s", (p_id, a))
            stock_res = mycursor.fetchone()
            m = stock_res[0] if stock_res else 0
            stok_lbl.config(text=f"Available Stock: {m}", fg="green" if m > 0 else "red")

    def add_to_cart():
        # 1. Get the current values from your input fields
        p_name = prod_cb.get()
        rate = selling_rate_var.get()
        qty = qty_entry.get()
        
        # 2. Validation: Ensure fields aren't empty
        if not p_name or not qty.isdigit():
            messagebox.showerror("Error", "Please select a product and enter a valid quantity")
            return

        # 3. Calculate the total for this specific item
        item_total = float(rate) * int(qty)
        
        # 4. Fetch the Product ID from the database for the selected name
        mycursor.execute("SELECT product_id FROM product WHERE product_name=%s", (p_name,))
        result = mycursor.fetchone()
        p_id = result[0] if result else "N/A"
        
        # 5. INSERT INTO THE TREEVIEW (This makes it visible in the UI)
        cart_table.insert("", "end", values=(p_id, p_name, rate, qty, item_total))
        
        # 6. Update the Running Total label at the bottom
        update_running_total()
        
        # 7. Clear the quantity entry for the next item
        qty_entry.delete(0, kt.END)

    def remove_selected():
        # 1. Get all selected items from the Treeview
        selected_items = cart_table.selection()
        
        # 2. Check if anything is actually selected
        if not selected_items:
            messagebox.showwarning("Selection Error", "Please select an item from the cart to remove.")
            return

        # 3. Delete each selected item from the table
        for item in selected_items:
            cart_table.delete(item)
            
        # 4. Recalculate the running total immediately
        update_running_total()

    def update_running_total():
        total_sum = 0
        # Iterate through every remaining row in the cart
        for item in cart_table.get_children():
            # Index 4 corresponds to the 'Total' column in your cart
            item_values = cart_table.item(item)['values']
            if item_values:
                total_sum += float(item_values[4])
        
        # Update the UI label variable
        running_total_var.set(f"Running Total: ₹ {total_sum:,.2f}")

    # --- UI ELEMENTS (Layout matched to image) ---
    # Top Panel
    top_panel = kt.Frame(order_frame, bg=bg_color, pady=10, padx=20)
    top_panel.pack(fill="x")
    kt.Button(top_panel, text="← Back to Dashboard", command=lambda: show_page(dash_frame), font=("Arial", 10)).pack(side="left")

    # Entry Form Frame
    form_frame = kt.Frame(order_frame, bg=bg_color, padx=20)
    form_frame.pack(fill="x")

    # Column 1 & 2
    kt.Label(form_frame, text="Company Filter:", font=("Arial", 14), bg=bg_color).grid(row=0, column=0, sticky="w", pady=5)
    brand_cb = ttk.Combobox(form_frame, values=["All", "Oppo", "Earthonic", "HP"], state="readonly", width=25)
    brand_cb.grid(row=0, column=1, padx=10)
    brand_cb.set("All")

    kt.Label(form_frame, text="Party/Dealer Name:", font=("Arial", 14), bg=bg_color).grid(row=0, column=2, padx=10)
    dealer_cb = ttk.Combobox(form_frame, width=30) # Ideally fetch from dealer table
    dealer_cb.grid(row=0, column=3, padx=10)

    # Column 3 (Add to Cart Button)
    kt.Button(form_frame, text="+ Add to Cart", bg=accent_green, fg="white", font=("Arial", 14, "bold"), 
              command=add_to_cart, padx=20, pady=10).grid(row=0, column=4, rowspan=2, padx=20)

    # Row 2
    kt.Label(form_frame, text="Product Name:", font=("Arial", 14), bg=bg_color).grid(row=1, column=0, sticky="w", pady=5)
    prod_cb = ttk.Combobox(form_frame, state="readonly", width=25)
    prod_cb.grid(row=1, column=1, padx=10)

    stok_lbl = kt.Label(form_frame, text="Available Stock: -", font=("Arial", 14, "bold"), bg=bg_color)
    stok_lbl.grid(row=1, column=2, columnspan=2, sticky="w", padx=10)

    # Row 3
    selling_rate_var = kt.StringVar()
    kt.Label(form_frame, text="Selling Rate (₹):", font=("Arial", 14), bg=bg_color).grid(row=2, column=0, sticky="w", pady=10)
    kt.Entry(form_frame, textvariable=selling_rate_var, font=("Arial", 12), width=27).grid(row=2, column=1, padx=10)

    kt.Label(form_frame, text="Quantity:", font=("Arial", 14), bg=bg_color).grid(row=2, column=2, sticky="e")
    qty_entry = kt.Entry(form_frame, font=("Arial", 12), width=20)
    qty_entry.grid(row=2, column=3, padx=10, sticky="w")

    # --- CART TABLE ---
    kt.Label(order_frame, text="Current Order Cart", font=("Arial", 16, "bold"), bg=bg_color).pack(pady=(20, 5))
    
    cart_container = kt.Frame(order_frame, bg="white", bd=1, relief="solid")
    cart_container.pack(fill="both", expand=True, padx=20, pady=5)

    columns = ("id", "name", "rate", "qty", "total")
    cart_table = ttk.Treeview(cart_container, columns=columns, show="headings", height=10)
    
    cart_table.heading("id", text="ID")
    cart_table.heading("name", text="Product Name")
    cart_table.heading("rate", text="Rate")
    cart_table.heading("qty", text="Qty")
    cart_table.heading("total", text="Total")
    
    cart_table.column("id", width=100, anchor="center")
    cart_table.column("name", width=400, anchor="w")
    cart_table.pack(fill="both", expand=True)

    # --- FOOTER ---
    footer_frame = kt.Frame(order_frame, bg=bg_color, padx=20, pady=10)
    footer_frame.pack(fill="x")

    kt.Button(footer_frame, text="✘ Remove Selected", bg="#d9534f", fg="white", font=("Arial", 10, "bold"), 
              command=remove_selected).pack(side="left")

    running_total_var = kt.StringVar(value="Running Total: ₹ 0")
    kt.Label(footer_frame, textvariable=running_total_var, font=("Arial", 16, "bold"), bg=bg_color).pack(side="right", padx=10)
    
    kt.Button(footer_frame, text="➡ Proceed to Billing", bg=accent_blue, fg="white", font=("Arial", 14, "bold"), 
              padx=20, pady=10).pack(side="right", padx=20)

    # --- BINDINGS ---
    brand_cb.bind("<<ComboboxSelected>>", update_products)
    prod_cb.bind("<<ComboboxSelected>>", fetch_details)
def order_page_frame():
    # 1. Clear previous content
    for widget in order_page.winfo_children():
        widget.destroy()
    
    # --- THEME COLORS ---
    bg_main = "#f0f4f8"       # Light blue-grey background
    sidebar_color = "#1a365d" # Dark navy blue
    card_color = "#ffffff"    # White card for the table
    accent_blue = "#2b6cb0"   # Medium blue
    text_dark = "#2d3748"     # Dark grey

    order_page.config(bg=bg_main)
    show_page(order_page)

    # 1. SIDEBAR (Consistent with Dashboard)
    sidebar = kt.Frame(order_page, bg=sidebar_color, width=220)
    sidebar.pack(side="left", fill="y")

    kt.Label(sidebar, text="Nitya Sales", font=("Arial", 16, "bold"), 
             bg=sidebar_color, fg="white", pady=25).pack()

    nav_btns = [
        ("🏠 Dashboard", lambda: [build_dashboard(), show_page(dash_frame)]),
        ("📦 Products", view_table),
        ("📊 Inventory", master_function),
        ("🛒 Orders", order_page_frame),
        ("❌ Exit", window.destroy)
    ]

    for text, cmd in nav_btns:
        kt.Button(sidebar, text=text, font=("Arial", 11), bg=sidebar_color, 
                  fg="white", bd=0, activebackground=accent_blue, 
                  activeforeground="white", anchor="w", padx=25,
                  command=cmd).pack(fill="x", pady=5)

    # 2. MAIN CONTENT AREA
    content = kt.Frame(order_page, bg=bg_main, padx=30, pady=25)
    content.pack(side="right", fill="both", expand=True)

    # Header Row
    header_row = kt.Frame(content, bg=bg_main)
    header_row.pack(fill="x", pady=(0, 20))

    kt.Label(header_row, text="Order History", font=("Arial", 22, "bold"), 
             bg=bg_main, fg=text_dark).pack(side="left")

    # "Add New" Button styled like your reference image
    kt.Button(header_row, text="+ Create New Order", font=("Arial", 12, "bold"), 
              bg="#38a169", fg="white", padx=15, pady=8, bd=0,
              command=open_order_frame).pack(side="right")

    # 3. ORDERS TABLE (Inside a white card)
    table_card = kt.Frame(content, bg=card_color, highlightbackground="#cbd5e0", highlightthickness=1)
    table_card.pack(fill="both", expand=True)

    cols = ("order_id", "date", "party", "total_items", "total_amt")
    tree = ttk.Treeview(table_card, columns=cols, show="headings")
    
    tree.heading("order_id", text="Order ID")
    tree.heading("date", text="Date")
    tree.heading("party", text="Party Name")
    tree.heading("total_items", text="Items")
    tree.heading("total_amt", text="Total Amount")

    # Configure Column Widths
    tree.column("order_id", width=100, anchor="center")
    tree.column("party", width=300, anchor="w")
    
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # --- LOAD DATA LOGIC ---
    try:
        # Note: You will need an 'orders' table in your DB for this to populate
        mycursor.execute("SELECT order_id, date, party_name, items_qty, amount FROM orders ORDER BY date DESC")
        for row in mycursor.fetchall():
            tree.insert("", "end", values=row)
    except:
        # If table doesn't exist yet, show a placeholder
        tree.insert("", "end", values=("Example-001", a, "Tech Distributors Ltd.", 5, "₹ 1,80,000"))

def customer():
    def stre():
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv")]
        )

        if not file_path:
            return
        qry='insert into dealer (d_id,d_name,address,c_person,c_no,GST,FOS,delivery_p) values(%s,%s,%s,%s,%s,%s,%s,%s)'
        with open(file_path, 'r') as csvfile:
            reader= c.DictReader(csvfile)
            for row in reader:
                values = (
                    row['d_id'],
                    row['d_name'],
                    row['address'],
                    row['c_person'],
                    row['c_no'],
                    row['GST'],
                    row['FOS'],
                    row['delivery_p']
                )
                mycursor.execute(qry, values)
        mydb.commit()
    for widget in cust_more.winfo_children():
        widget.destroy()
    show_page(cust_more)
    kt.Button(cust_more,text='Upload csv',command=stre).place(x=0,y=0)
    kt.Button(cust_more, text="← Back to Dashboard", 
              command=lambda: show_page(dash_frame), # Just raise the dashboard
              font=("Arial", 10, "bold"), bg="lightgrey").place(x=10,y=100)
    
def master_function():
    change_data()
    view_table_stock()  
def show_page(frame):
    frame.tkraise()
# -------------------- START APPLICATION --------------------
build_dashboard()          # build dashboard once
show_page(dash_frame) # show dashboard first
window.mainloop()
