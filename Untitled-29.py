import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Product Master")

tk.Label(root, text="Product Name").grid(row=0, column=0)
product_name = tk.Entry(root)
product_name.grid(row=0, column=1)

tk.Label(root, text="Brand").grid(row=1, column=0)
brand = tk.Entry(root)
brand.grid(row=1, column=1)

tk.Label(root, text="Category").grid(row=2, column=0)
category = ttk.Combobox(root, values=["Mobile", "Laptop"])
category.grid(row=2, column=1)

tk.Label(root, text="MRP").grid(row=3, column=0)
mrp = tk.Entry(root)
mrp.grid(row=3, column=1)

tk.Label(root, text="Status").grid(row=4, column=0)
status = ttk.Combobox(root, values=["Active", "Inactive"])
status.grid(row=4, column=1)

tk.Button(root, text="Save Product").grid(row=5, column=0, columnspan=2)

root.mainloop()
