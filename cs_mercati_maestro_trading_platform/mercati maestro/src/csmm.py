import tkinter as tk
from tkinter import messagebox
import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('trading_simulator.db')
c = conn.cursor()

# Create orders table
c.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    order_type TEXT,
    symbol TEXT,
    quantity INTEGER,
    price REAL,
    status TEXT
)
''')
conn.commit()

# Function to insert a new order into the database
def insert_order(order_type, symbol, quantity, price, status):
    c.execute('''
    INSERT INTO orders (order_type, symbol, quantity, price, status)
    VALUES (?, ?, ?, ?, ?)
    ''', (order_type, symbol, quantity, price, status))
    conn.commit()

# Function to fetch all orders from the database
def fetch_orders():
    c.execute('SELECT * FROM orders')
    return c.fetchall()

# Function to modify an order in the database
def modify_order(order_id, quantity, price):
    c.execute('''
    UPDATE orders
    SET quantity = ?, price = ?
    WHERE id = ?
    ''', (quantity, price, order_id))
    conn.commit()

# Function to cancel an order in the database
def cancel_order(order_id):
    c.execute('''
    UPDATE orders
    SET status = 'Canceled'
    WHERE id = ?
    ''', (order_id,))
    conn.commit()

# Function to generate a FIX message (placeholder)
def generate_fix_message(order_id, action, order_type, symbol, quantity, price):
    fix_message = f"FIX Message - Order ID: {order_id}, Action: {action}, Type: {order_type}, Symbol: {symbol}, Quantity: {quantity}, Price: {price}"
    print(fix_message)
    # Here you would normally send this FIX message to the FIX engine
    return fix_message

# Main Application Class
class TradingSimulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trading Simulator")
        
        # Order Entry Frame
        self.order_frame = tk.Frame(self)
        self.order_frame.pack(pady=10)
        
        tk.Label(self.order_frame, text="Order Type").grid(row=0, column=0)
        tk.Label(self.order_frame, text="Symbol").grid(row=1, column=0)
        tk.Label(self.order_frame, text="Quantity").grid(row=2, column=0)
        tk.Label(self.order_frame, text="Price").grid(row=3, column=0)
        
        self.order_type = tk.StringVar(value="Buy")
        tk.OptionMenu(self.order_frame, self.order_type, "Buy", "Sell").grid(row=0, column=1)
        
        self.symbol_entry = tk.Entry(self.order_frame)
        self.symbol_entry.grid(row=1, column=1)
        
        self.quantity_entry = tk.Entry(self.order_frame)
        self.quantity_entry.grid(row=2, column=1)
        
        self.price_entry = tk.Entry(self.order_frame)
        self.price_entry.grid(row=3, column=1)
        
        self.place_order_button = tk.Button(self.order_frame, text="Place Order", command=self.place_order)
        self.place_order_button.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Orders Display Frame
        self.orders_frame = tk.Frame(self)
        self.orders_frame.pack(pady=10)
        
        self.orders_listbox = tk.Listbox(self.orders_frame, width=50)
        self.orders_listbox.pack(side=tk.LEFT)
        
        self.orders_scrollbar = tk.Scrollbar(self.orders_frame, command=self.orders_listbox.yview)
        self.orders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.orders_listbox.config(yscrollcommand=self.orders_scrollbar.set)
        
        self.refresh_orders_button = tk.Button(self, text="Refresh Orders", command=self.refresh_orders)
        self.refresh_orders_button.pack(pady=10)
        
        self.modify_order_button = tk.Button(self, text="Modify Order", command=self.modify_order)
        self.modify_order_button.pack(pady=5)
        
        self.cancel_order_button = tk.Button(self, text="Cancel Order", command=self.cancel_order)
        self.cancel_order_button.pack(pady=5)
        
        self.refresh_orders()

    def place_order(self):
        order_type = self.order_type.get()
        symbol = self.symbol_entry.get()
        quantity = self.quantity_entry.get()
        price = self.price_entry.get()
        
        if not symbol or not quantity or not price:
            messagebox.showwarning("Input Error", "All fields must be filled out")
            return
        
        try:
            quantity = int(quantity)
            price = float(price)
        except ValueError:
            messagebox.showwarning("Input Error", "Quantity must be an integer and Price must be a float")
            return
        
        insert_order(order_type, symbol, quantity, price, "Open")
        self.refresh_orders()
        generate_fix_message("N/A", "Place", order_type, symbol, quantity, price)  # Placeholder for actual FIX message generation

    def refresh_orders(self):
        self.orders_listbox.delete(0, tk.END)
        orders = fetch_orders()
        for order in orders:
            self.orders_listbox.insert(tk.END, f"ID: {order[0]}, Type: {order[1]}, Symbol: {order[2]}, Quantity: {order[3]}, Price: {order[4]}, Status: {order[5]}")
    
    def modify_order(self):
        selected = self.orders_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "No order selected")
            return
        
        order_id = int(self.orders_listbox.get(selected).split(",")[0].split(":")[1].strip())
        new_quantity = self.quantity_entry.get()
        new_price = self.price_entry.get()
        
        if not new_quantity or not new_price:
            messagebox.showwarning("Input Error", "Quantity and Price fields must be filled out to modify an order")
            return
        
        try:
            new_quantity = int(new_quantity)
            new_price = float(new_price)
        except ValueError:
            messagebox.showwarning("Input Error", "Quantity must be an integer and Price must be a float")
            return
        
        modify_order(order_id, new_quantity, new_price)
        self.refresh_orders()
        generate_fix_message(order_id, "Modify", None, None, new_quantity, new_price)  # Placeholder for actual FIX message generation

    def cancel_order(self):
        selected = self.orders_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "No order selected")
            return
        
        order_id = int(self.orders_listbox.get(selected).split(",")[0].split(":")[1].strip())
        cancel_order(order_id)
        self.refresh_orders()
        generate_fix_message(order_id, "Cancel", None, None, None, None)  # Placeholder for actual FIX message generation

# Run the application
if __name__ == "__main__":
    app = TradingSimulator()
    app.mainloop()
