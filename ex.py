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

    # Allow toggle ONLY on Status column (#7)
    if col_id != "#7" or not row_id:
        return

    row = table.item(row_id)["values"]

    product_id = row[0]
    symbol = row[6]

    if symbol == "✔":
        new_symbol = "❌"
        new_status = "Deactive"
    else:
        new_symbol = "✔"
        new_status = "Active"

    mycursor.execute(
        "UPDATE product SET status=%s WHERE product_id=%s",
        (new_status, product_id)
    )
    mydb.commit()

    table.item(row_id, values=(
        row[0], row[1], row[2], row[3], row[4], row[5], new_symbol

    ))

def purchase_new(event, table):
    row = table.identify_row(event.y)
    column = table.identify_column(event.x)

    # Purchase column is #4 in your stock table
    if not row or column != "#4":
        return

    r = table.item(row)["values"]
    product_name = r[0]
    bal = r[4]

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
        "UPDATE stock SET purchase=%s, b_stock=%s WHERE product_id=%s",
        (new_purchase, new_balance, p_id)
    )
    mydb.commit()

    # ✅ REFRESH ONLY THE CURRENT TABLE
    table.delete(*table.get_children())

    # Reload data for currently selected date
    selected_date = r[6]
    for widget in table.master.winfo_children():
        if isinstance(widget, ttk.Combobox):
            selected_date = widget.get()
            break

    if selected_date:
        mycursor.execute("""
            SELECT p.product_name, p.brand, s.O_stock, s.purchase, s.b_stock, p.p_rate, s.s_date
            FROM product p
            JOIN stock s ON p.product_id = s.product_id
            WHERE s.s_date = %s
        """, (selected_date,))
    else:
        mycursor.execute("""
            SELECT p.product_name, p.brand, s.O_stock, s.purchase, s.b_stock, p.p_rate, s.s_date
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

product_frame=kt.Frame(container)
dash_frame=kt.Frame(container)
order_frame=kt.Frame(container)

for f in (dash_frame,order_frame, product_frame):
    f.grid(row=0, column=0, sticky="nsew")


icon = kt.PhotoImage(file="logo.png")
window.iconphoto(True, icon)

# -------------------- VIEW TABLE --------------------
def view_table():
    view_win = kt.Toplevel(product_frame)
    view_win.title("Product Table")
    view_win.geometry("750x500")

    search_frame = kt.Frame(view_win)
    search_frame.pack(pady=10)

    kt.Label(search_frame, text="Search: ").grid(row=0, column=0)

    search_entry = kt.Entry(search_frame, width=30)
    search_entry.grid(row=0, column=1, padx=5)

    brand_dropdown = ttk.Combobox(
        search_frame,
        values=["hp", "oppo", "earthonic"],
        state="readonly",
        width=28
    )

    kt.Label(search_frame, text="By: ").grid(row=0, column=2)

    search_type = ttk.Combobox(
        search_frame,
        values=["product_name", "brand"],
        state="readonly",
        width=15
    )
    search_type.grid(row=0, column=3)
    search_type.set("product_name")

    table = ttk.Treeview(
        view_win,
        columns=("product_id","product_name","brand","catagory","p_rate","s_rate","status"),
        show='headings',
        selectmode="none"
    )

    headings = ["ID","Product Name","Brand","Category","P Rate","S Rate","Status"]
    for col, head in zip(table["columns"], headings):
        table.heading(col, text=head)
        table.column(col, width=100, anchor="center")

    table.pack(fill="both", expand=True)
    table.bind("<Button-1>", lambda event: toggle_status_from_table(event, table))
    

    def load_data(query=None, value=None):
        for row in table.get_children():
            table.delete(row)

        if query is None:
            mycursor.execute("SELECT * FROM product")
        else:
            mycursor.execute(query, (value,))

        for row in mycursor.fetchall():
            status_symbol = "✔" if row[6] == "Active" else "❌"
            table.insert("", "end", values=(
                row[0], row[1], row[2], row[3], row[4], row[5], status_symbol
            ))

    def search():
        col = search_type.get()
        text = brand_dropdown.get() if col == "brand" else search_entry.get()

        if text == "":
            load_data()
            return

        load_data(f"SELECT * FROM product WHERE {col} LIKE %s", "%" + text + "%")

    def change_input(event):
        if search_type.get() == "brand":
            search_entry.grid_remove()
            brand_dropdown.grid(row=0, column=1, padx=5)
        else:
            brand_dropdown.grid_remove()
            search_entry.grid(row=0, column=1, padx=5)

    search_type.bind("<<ComboboxSelected>>", change_input)

    kt.Button(search_frame, text="Search", command=search).grid(row=0, column=4, padx=5)
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
    # 1. Create the Full-Screen Frame
    view_win = kt.Frame(window, bg="white")
    view_win.place(x=0, y=0, relwidth=1, relheight=1)

    # 2. Header Navbar
    header_frame = kt.Frame(view_win, height=60)
    header_frame.pack(side="top", fill="x")

    # Back Button
    kt.Button(header_frame, text="← Back", command=view_win.destroy, 
               font=("Arial", 10, "bold"), bd=0).pack(side="left", padx=10, pady=10)

    # Date Filter Label and Combobox
    kt.Label(header_frame, text="Select Date:",font=("Arial", 11)).pack(side="left", padx=(20, 5))
    
    date_filter = ttk.Combobox(header_frame, state="readonly", width=15)
    date_filter.pack(side="left", padx=5)
    
    # 3. Table Setup
    columns = ("product_name", "brand", "o_stock", "purchase", "b_stock", "p_rate", "s_date")
    tree = ttk.Treeview(view_win, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col.replace('_', ' ').upper())
        tree.column(col, width=100, anchor="center")
    tree.bind("<Button-1>", lambda revent : purchase_new(revent,tree))

    tree.pack(fill="both", expand=True)
    
    # --- THE FILTER LOGIC FUNCTION ---
    def load_filtered_data(event=None):
        # Clear the old table data
        for item in tree.get_children():
            tree.delete(item)
            
        selected_date = date_filter.get()
        
        try:
            # JOIN query filtered by the date selected in the dropdown
            query = """
                SELECT p.product_name, p.brand, s.O_stock, s.purchase, s.b_stock, p.p_rate, s.s_date
                FROM product p
                JOIN stock s ON p.product_id = s.product_id
                WHERE s.s_date = %s
            """
            mycursor.execute(query, (selected_date,))
            rows = mycursor.fetchall()

            for row in rows:
                tree.insert("", "end", values=row)
        except Exception as e:
            print(f"Error filtering data: {e}")

    # --- POPULATE THE DATE DROPDOWN ---
    try:
        # Get unique dates from the stock table
        mycursor.execute("SELECT DISTINCT s_date FROM stock ORDER BY s_date DESC")
        available_dates = [str(date[0]) for date in mycursor.fetchall()]
        
        if available_dates:
            date_filter['values'] = available_dates
            date_filter.set(available_dates[0]) # Set the most recent date as default
            load_filtered_data() # Load data for the default date immediately
        else:
            messagebox.showinfo("Info", "No stock records found yet.")

    except Exception as e:
        print(f"Error fetching dates: {e}")

    # Bind the dropdown to the filter function
    date_filter.bind("<<ComboboxSelected>>", load_filtered_data)
def build_dashboard():
    # Clear dashboard if rebuilt accidentally
    for widget in dash_frame.winfo_children():
        widget.destroy()

    # Title
    kt.Label(
        dash_frame,
        text="Inventory Management System",
        font=("Arial", 22, "bold"),
        bg="cyan"
    ).pack(pady=40)

    # Subtitle
    kt.Label(
        dash_frame,
        text="Main Dashboard",
        font=("Arial", 12),
        bg="cyan"
    ).pack(pady=5)

    # Product Button
    kt.Button(
        dash_frame,
        text="📦 Products",
        width=30,
        height=2,
        font=("Arial", 14),
        command=pro_frame   # opens product page
    ).pack(pady=15)

    # Stock Button
    kt.Button(
        dash_frame,
        text="📊 Inventory",
        width=30,
        height=2,
        font=("Arial", 14),
        command=master_function  # change_data + stock page
    ).pack(pady=15)

    kt.Button(
        dash_frame,
        text="Orders",
        width=30,
        height=2,
        font=("Arial", 14),
        command=open_order_frame
    ).pack(pady=15)
    # Exit Button
    kt.Button(
        dash_frame,
        text="❌ Exit",
        width=30,
        height=2,
        font=("Arial", 14),
        command=window.destroy
    ).pack(pady=30)
def pro_frame():
    for widget in product_frame.winfo_children():
        widget.destroy()
    show_page(product_frame)
    label = kt.Label(product_frame, text="Welcome to Product pager", font=("Arial", 16))
    label.pack(pady=20)

    label2 = kt.Label(product_frame, text="Product name", font=("Arial", 16))
    label2.pack()
    entry2 = kt.Entry(product_frame)
    entry2.pack()
    kt.Button(product_frame, text="← Back to Dashboard", 
              command=lambda: show_page(dash_frame), # Just raise the dashboard
              font=("Arial", 10, "bold"), bg="lightgrey").place(x=0,y=0)
    label3 = kt.Label(product_frame, text="Brand", font=("Arial", 16))
    label3.pack()
    entry3 = ttk.Combobox(
        product_frame,
        values=["hp", "oppo", "earthonic"],
        state="readonly"
    )
    entry3.pack()

    label4 = kt.Label(product_frame, text="Category", font=("Arial", 16))
    label4.pack()
    entry4 = ttk.Combobox(
        product_frame,
        values=["laptop", "mobile", "TV"],
        state="readonly"
    )
    entry4.pack()

    label5 = kt.Label(product_frame, text="PRate", font=("Arial", 16))
    label5.pack()
    entry5 = kt.Entry(product_frame)
    entry5.pack()

    label6 = kt.Label(product_frame, text="SRAtes", font=("Arial", 16))
    label6.pack()
    entry6 = kt.Entry(product_frame)
    entry6.pack()

    label7=kt.Label(product_frame,text="Opening stock",font=("Arial",16))
    label7.pack()
    entry7=kt.Entry(product_frame)
    entry7.pack()

    label8=kt.Label(product_frame,text="Purchase",font=("Arial",16))
    label8.pack()
    entry8=kt.Entry(product_frame)
    entry8.pack()

    label9=kt.Label(product_frame,text="sales",font=("Arial",16))
    label9.pack()
    entry9=kt.Entry(product_frame)
    entry9.pack()

    label10=kt.Label(product_frame,text="Balance stock",font=("Arial",16))
    label10.pack()
    entry10=kt.Entry(product_frame)
    entry10.pack()  
    button2 = kt.Button(product_frame, text='import csv file here', command=upload)
    button2.pack(pady=5)

    button3 = kt.Button(product_frame, text="view product", command=view_table)
    button3.pack(pady=5)

    def store_data():  
        query = """
        INSERT INTO tempo
        (product_name, brand, catagory, p_rate, s_rate, o_stock, purchase, sales, b_stock, status, s_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active', %s)
        """
        # ... rest of your values tuple ...

        values = (
            entry2.get(),
            entry3.get(),
            entry4.get(),
            entry5.get(),
            entry6.get(),
            entry7.get(),
            entry8.get(),
            entry9.get(),
            entry10.get(),
            a
        )

        mycursor.execute(query, values)
        mydb.commit()
        product_id = mycursor.lastrowid
        mycursor.execute("INSERT INTO product (product_name, brand, catagory, p_rate, s_rate, Status) select distinct product_name, brand, catagory, p_rate, s_rate, status FROM tempo WHERE product_name NOT IN (SELECT product_name FROM product)")
        
        mycursor.execute("INSERT INTO stock (product_id, O_stock, purchase, sales, b_stock,s_date) select p.product_id, t.O_stock, t.purchase, t.sales, t.b_stock,t.s_date FROM tempo t JOIN product p ON t.product_name = p.product_name")
        mydb.commit()
    
        mycursor.execute("TRUNCATE TABLE tempo")
        

        messagebox.showinfo(
            "Success",
            f"Product Stored Successfully\nGenerated Product ID: {product_id}"
        )
        entry2.delete(0, kt.END)
        entry5.delete(0, kt.END)
        entry6.delete(0, kt.END)
        entry7.delete(0, kt.END)
        entry8.delete(0, kt.END)
        entry9.delete(0, kt.END)
        entry10.delete(0, kt.END)
        
        # For Comboboxes (Brand and Category)
        entry3.set('') 
        entry4.set('')
    button = kt.Button(product_frame, text="Click Me for storing", command=store_data)
    button.pack(pady=10)
def open_order_frame():
    # 1. Clear and Show Frame
    for widget in order_frame.winfo_children():
        widget.destroy()
    show_page(order_frame)

    # --- THE UPDATE FUNCTION (Crucial Change) ---
    def update_products(event):
        selected_brand = entry11.get() # Get currently selected company
        
        # Run query based on selection
        mycursor.execute("SELECT product_name FROM product WHERE brand=%s", (selected_brand,))
        pro = mycursor.fetchall()
        
        # Build the list of names
        pst = [j[0] for j in pro]
        
        # Update the values of the second combobox
        entry12['values'] = pst
        entry12.set('') # Clear previous product choice
    def fetch_stock(event):
        z=entry12.get()
        mycursor.execute("select product_id from product where product_name=%s",(z,))
        p=mycursor.fetchone()
        q=p[0]
        mycursor.execute("SELECT b_stock FROM stock WHERE product_id=%s AND s_date=%s", (q, a))
        l=mycursor.fetchone()
        m=l[0]
        stok.config(text=f'Stock-{m}')
    # --- UI ELEMENTS ---
    kt.Button(order_frame, text="<--Back", command=lambda: show_page(dash_frame)).place(x=10, y=10)
    
    # Company Selection
    kt.Label(order_frame, font=("Arial", 14), text="Company").place(x=20, y=50)
    entry11 = ttk.Combobox(order_frame, values=["Oppo", "Earthonic", "HP"], state="readonly",width=50)
    entry11.place(x=120, y=50)

    # Product Selection (Start with empty values)
    kt.Label(order_frame, text="Products", font=("Arial", 14)).place(x=20, y=90)
    entry12 = ttk.Combobox(order_frame, values=[], state="readonly",width=50)
    entry12.place(x=120, y=90)

    kt.Label(order_frame,text="Quantity",font=("Arial", 14)).place(x=600,y=100)
    entry13=kt.Entry(order_frame,width=20).place(x=680,y=100)

    stok=kt.Label(order_frame,text="Stock-",font=("Arial", 14))
    stok.place(x=600,y=60)
    
    kt.Button(order_frame,text="Add to cart",font=('Archivo Black',20),background='red',width=20).place(x=900,y=50)
    # --- THE BINDING ---
    # This connects the company box to the function above
    entry11.bind("<<ComboboxSelected>>", update_products)
    entry12.bind("<<ComboboxSelected>>", fetch_stock)
    
def master_function():
    change_data()
    view_table_stock()  
def show_page(frame):
    frame.tkraise()

# -------------------- START APPLICATION --------------------

build_dashboard()          # build dashboard once
show_page(dash_frame) # show dashboard first
window.mainloop()
