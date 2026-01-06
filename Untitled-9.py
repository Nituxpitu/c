import tkinter as tk
from tkinter import filedialog, messagebox

import sqlite3

def upload_and_process():
    # 1. Open the file browser to pick a CSV
    file_path = filedialog.askopenfilename(
        title="Select Inventory CSV",
        filetypes=[("CSV files", "*.csv")]
    )
    
    # If the user cancels the file browser, stop
    if not file_path:
        return

    try:
        # 2. Process: Load CSV into Pandas
        df = pd.read_csv(file_path)
        
        # --- Engineering Tip: Simple Processing ---
        # Example: Ensure all product names are Uppercase
        if 'product_name' in df.columns:
            df['product_name'] = df['product_name'].str.upper()
        
        # 3. Store: Save to SQLite Database
        conn = sqlite3.connect("inventory_system.db")
        
        # 'if_exists' options: 
        # 'append' adds to the table
        # 'replace' deletes the old table and starts fresh
        df.to_sql("products", conn, if_exists="append", index=False)
        
        conn.close()
        
        messagebox.showinfo("Success", f"Imported {len(df)} items successfully!")
        
    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong: {e}")

# --- Simple GUI Setup ---
root = tk.Tk()
root.title("CSV Data Importer")
root.geometry("300x150")

label = tk.Label(root, text="Inventory Data Loader", font=("Arial", 12, "bold"))
label.pack(pady=10)

# The Upload Button
btn_upload = tk.Button(
    root, 
    text="📁 Select CSV & Save to DB", 
    command=upload_and_process,
    bg="#4CAF50", # Green color
    fg="white"
)
btn_upload.pack(pady=20)

root.mainloop()