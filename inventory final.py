# -------------------- IMPORTS --------------------
import mysql.connector
import tkinter as kt
from tkinter import filedialog, messagebox, ttk
import csv as c

mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql",
        database="inventory"
    )

mycursor = mydb.cursor()


# -------------------- DATABASE FUNCTION --------------------
def store_data():
    query = """
    INSERT INTO tempo
    (product_name, brand, catagory, p_rate, s_rate, o_stock, purchase, sales, b_stock,status)
    VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s,'Active')
    """

    values = (
        entry2.get(),
        entry3.get(),
        entry4.get(),
        entry5.get(),
        entry6.get(),
        entry7.get(),
        entry8.get(),
        entry9.get(),
        entry10.get()
    )

    mycursor.execute(query, values)
    mydb.commit()
    product_id = mycursor.lastrowid
    mycursor.execute("INSERT INTO product (product_name, brand, catagory, p_rate, s_rate, Status) select distinct product_name, brand, catagory, p_rate, s_rate, status FROM tempo WHERE product_name NOT IN (SELECT product_name FROM product)")
    
    mycursor.execute("INSERT INTO stock (product_id, O_stock, purchase, sales, b_stock) select p.product_id, t.O_stock, t.purchase, t.sales, t.b_stock FROM tempo t JOIN product p ON t.product_name = p.product_name")
    mydb.commit()
   
    mycursor.execute("TRUNCATE TABLE tempo")
    

    messagebox.showinfo(
        "Success",
        f"Product Stored Successfully\nGenerated Product ID: {product_id}"
    )


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


# -------------------- MAIN WINDOW --------------------
window = kt.Tk()
window.geometry("420x420")
window.title("Inventory Manager")
window.config(background="cyan")

icon = kt.PhotoImage(file="logo.png")
window.iconphoto(True, icon)

label = kt.Label(window, text="Welcome to Inventory Manager", font=("Arial", 16))
label.pack(pady=20)


# -------------------- FORM FIELDS --------------------
label2 = kt.Label(window, text="Product name", font=("Arial", 16))
label2.pack()
entry2 = kt.Entry(window)
entry2.pack()

label3 = kt.Label(window, text="Brand", font=("Arial", 16))
label3.pack()
entry3 = ttk.Combobox(
    window,
    values=["hp", "oppo", "earthonic"],
    state="readonly"
)
entry3.pack()

label4 = kt.Label(window, text="Category", font=("Arial", 16))
label4.pack()
entry4 = ttk.Combobox(
    window,
    values=["laptop", "mobile", "TV"],
    state="readonly"
)
entry4.pack()

label5 = kt.Label(window, text="PRate", font=("Arial", 16))
label5.pack()
entry5 = kt.Entry(window)
entry5.pack()

label6 = kt.Label(window, text="SRAtes", font=("Arial", 16))
label6.pack()
entry6 = kt.Entry(window)
entry6.pack()

label7=kt.Label(window,text="Opening stock",font=("Arial",16))
label7.pack()
entry7=kt.Entry(window)
entry7.pack()

label8=kt.Label(window,text="Purchase",font=("Arial",16))
label8.pack()
entry8=kt.Entry(window)
entry8.pack()

label9=kt.Label(window,text="sales",font=("Arial",16))
label9.pack()
entry9=kt.Entry(window)
entry9.pack()

label10=kt.Label(window,text="Balance stock",font=("Arial",16))
label10.pack()
entry10=kt.Entry(window)
entry10.pack()
# -------------------- VIEW TABLE --------------------
def view_table():
    view_win = kt.Toplevel(window)
    view_win.title("Stock Table")
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
    (product_name, brand, catagory, p_rate, s_rate,o_stock,purchase,sales,b_stock, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
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
                row['b_stock']
            )
            mycursor.execute(query, values)

    mydb.commit()
    mycursor.execute("INSERT INTO product (product_name, brand, catagory, p_rate, s_rate, Status) select distinct product_name, brand, catagory, p_rate, s_rate, status FROM tempo WHERE product_name NOT IN (SELECT product_name FROM product)")
    
    mycursor.execute("INSERT INTO stock (product_id, O_stock, purchase, sales, b_stock) select p.product_id, t.O_stock, t.purchase, t.sales, t.b_stock FROM tempo t JOIN product p ON t.product_name = p.product_name")
    mydb.commit()
   
    mycursor.execute("TRUNCATE TABLE tempo")
    messagebox.showinfo("Success", "CSV Imported Successfully!")


# -------------------- BUTTONS --------------------
button = kt.Button(window, text="Click Me for storing", command=store_data)
button.pack(pady=10)

button2 = kt.Button(window, text='import csv file here', command=upload)
button2.place(x=0, y=0)

button3 = kt.Button(window, text="view stock", command=view_table)
button3.pack()

window.mainloop()
