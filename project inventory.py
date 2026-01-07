# -------------------- IMPORTS --------------------
import mysql.connector
import tkinter as kt
from tkinter import filedialog, messagebox, ttk
import csv as c


# -------------------- DATABASE CONNECTION --------------------
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
    INSERT INTO product
    (product_id, product_name, brand, catagory, p_rate, s_rate, status)
    VALUES (NULL, %s, %s, %s, %s, %s, 'Active')
    """

    values = (
        entry2.get(),
        entry3.get(),
        entry4.get(),
        entry5.get(),
        entry6.get(),
    )

    mycursor.execute(query, values)
    mydb.commit()

    product_id = mycursor.lastrowid

    messagebox.showinfo(
        "Success",
        f"Product Stored Successfully\nGenerated Product ID: {product_id}"
    )

    entry2.delete(0, kt.END)
    entry3.set('')
    entry4.set('')
    entry5.delete(0, kt.END)
    entry6.delete(0, kt.END)


# -------------------- SINGLE CLICK STATUS TOGGLE --------------------
def toggle_status_from_table(event, table):
    row_id = table.identify_row(event.y)
    col_id = table.identify_column(event.x)

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
window.geometry("480x600")
window.title("Inventory Manager")
window.config(bg="#f4f6f8")
window.resizable(True, True)

icon = kt.PhotoImage(file="logo.png")
window.iconphoto(True, icon)

# -------------------- STYLES --------------------
style = ttk.Style()
style.theme_use("clam")

style.configure("TButton", font=("Segoe UI", 11), padding=6)
style.configure("TCombobox", padding=5, font=("Segoe UI", 10))


# -------------------- HEADER --------------------
header = kt.Frame(window, bg="#1f2937", height=70)
header.pack(fill="x")

title = kt.Label(
    header,
    text="Inventory Management System",
    font=("Segoe UI", 18, "bold"),
    fg="white",
    bg="#1f2937"
)
title.pack(pady=18)


# -------------------- FORM CARD --------------------
card = kt.Frame(window, bg="white", bd=1, relief="solid")
card.pack(padx=20, pady=20, fill="both", expand=True)


def field_label(text):
    return kt.Label(
        card,
        text=text,
        bg="white",
        fg="#374151",
        font=("Segoe UI", 11, "bold")
    )


# -------------------- FORM FIELDS --------------------
field_label("Product Name").pack(anchor="w", padx=20, pady=(15, 2))
entry2 = kt.Entry(card, font=("Segoe UI", 11))
entry2.pack(fill="x", padx=20)

field_label("Brand").pack(anchor="w", padx=20, pady=(15, 2))
entry3 = ttk.Combobox(
    card,
    values=["hp", "oppo", "earthonic"],
    state="readonly"
)
entry3.pack(fill="x", padx=20)

field_label("Category").pack(anchor="w", padx=20, pady=(15, 2))
entry4 = ttk.Combobox(
    card,
    values=["mobile", "laptop", "TV"],
    state="readonly"
)
entry4.pack(fill="x", padx=20)

field_label("Purchase Rate").pack(anchor="w", padx=20, pady=(15, 2))
entry5 = kt.Entry(card, font=("Segoe UI", 11))
entry5.pack(fill="x", padx=20)

field_label("Selling Rate").pack(anchor="w", padx=20, pady=(15, 2))
entry6 = kt.Entry(card, font=("Segoe UI", 11))
entry6.pack(fill="x", padx=20)


# -------------------- BUTTONS --------------------
btn_frame = kt.Frame(card, bg="white")
btn_frame.pack(pady=25)

button = ttk.Button(
    btn_frame,
    text="Save Product",
    command=store_data
)
button.grid(row=0, column=0, padx=10)



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
button3 = ttk.Button(
    btn_frame,
    text="View Stock",
    command=view_table
)
button3.grid(row=0, column=1, padx=10)


# -------------------- CSV UPLOAD --------------------
def upload():
    file_path = filedialog.askopenfilename(
        title="Select CSV file",
        filetypes=[("CSV files", "*.csv")]
    )

    if not file_path:
        return

    query = """
    INSERT INTO product
    (product_name, brand, catagory, p_rate, s_rate, status)
    VALUES (%s, %s, %s, %s, %s, 'Active')
    """

    with open(file_path, 'r') as csvfile:
        reader = c.DictReader(csvfile)
        for row in reader:
            values = (
                row['product_name'],
                row['brand'],
                row['category'],
                row['prate'],
                row['srate']
            )
            mycursor.execute(query, values)

    mydb.commit()
    
    
    messagebox.showinfo("Success", "CSV Imported Successfully!")


# -------------------- TOP CSV BUTTON --------------------
button2 = ttk.Button(window, text="Import CSV", command=upload)
button2.place(x=10, y=10)

window.mainloop()
