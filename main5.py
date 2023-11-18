import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Listbox, filedialog, ttk
from tkinter.ttk import Combobox, Entry
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime


# Database setup
def initialize_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (id INTEGER PRIMARY KEY, item_name TEXT, quantity INTEGER, 
                  location TEXT, sub_location TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS locations
                 (location_name TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

# Update locations in the database
def update_locations(operation, old_name=None, new_name=None):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if operation == "add" and new_name:
        c.execute('INSERT INTO locations (location_name) VALUES (?)', (new_name,))
    elif operation == "remove" and old_name:
        c.execute('DELETE FROM locations WHERE location_name = ?', (old_name,))
        c.execute('UPDATE inventory SET location = ? WHERE location = ?', ('Unknown', old_name))
    elif operation == "rename" and old_name and new_name:
        c.execute('UPDATE locations SET location_name = ? WHERE location_name = ?', (new_name, old_name))
        c.execute('UPDATE inventory SET location = ? WHERE location = ?', (new_name, old_name))
    conn.commit()
    conn.close()


# Fetch updated locations
def fetch_locations():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('SELECT location_name FROM locations')
    locations = c.fetchall()
    conn.close()
    return [loc[0] for loc in locations]

# Add item to database
def add_item(name, quantity, location, sub_location, notes):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('INSERT INTO inventory (item_name, quantity, location, sub_location, notes) VALUES (?, ?, ?, ?, ?)',
              (name, quantity, location, sub_location, notes))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Item added successfully")

# Edit item in the database
def edit_item(item_id, name, quantity, location, sub_location, notes):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''UPDATE inventory SET item_name = ?, quantity = ?, location = ?, sub_location = ?, notes = ?
                 WHERE id = ?''', (name, quantity, location, sub_location, notes, item_id))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Item edited successfully")

# Remove item from the database
def remove_item(item_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Item removed successfully")

# View inventory
def view_inventory():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('SELECT * FROM inventory')
    items = c.fetchall()
    conn.close()

    top = Toplevel(root)
    top.title("Inventory List")
    top.geometry("1920x1080")

    # Define the columns
    columns = ('ID', 'Item Name', 'Quantity', 'Location', 'Sub-Location', 'Notes')
    tree = ttk.Treeview(top, columns=columns, show='headings')

    # Define headings
    for col in columns:
        tree.heading(col, text=col)

    # Add data to the treeview
    for item in items:
        tree.insert('', tk.END, values=item)

    tree.pack(expand=True, fill='both')  # Expand and fill the available space

#location combobox declaration
global location_combobox

# Global function to refresh location combobox
def refresh_location_combobox(combobox):
    locations = fetch_locations()
    if locations:
        combobox['values'] = locations
        combobox.set(locations[0])

#Opens New Window for Export Function
def open_export_window():
    export_window = Toplevel(root)
    export_window.title("Export Inventory to PDF")
    export_window.geometry("500x200")

    # Button to print all inventory
    tk.Button(export_window, text="Print All Inventory", font=("Arial", 14), command=lambda: export_to_pdf()).pack(pady=5)

    # Combobox and button to print inventory of a specific location
    tk.Label(export_window, text="Select Location", font=("Arial", 14)).pack()
    location_export_combobox = Combobox(export_window, width=28)
    refresh_location_combobox(location_export_combobox)  # Refresh the new combobox
    location_export_combobox.pack()

    tk.Button(export_window, text="Print Inventory of Selected Location", font=("Arial", 14),
              command=lambda: export_to_pdf(location_export_combobox.get())).pack(pady=5)

#wrap the text before exporting to PDF so it doesn't extend off the end of the page
def wrap_text(text, width, canvas):
    """Wrap text to fit within a specified width."""
    wrapped_text = []
    lines = text.split('\n')
    for line in lines:
        while len(line) > 0:
            # Try to fit as many words as possible in the line within the width
            split_line = line.split()
            temp_line = ""
            while split_line and canvas.stringWidth(temp_line + split_line[0]) < width:
                temp_line += (split_line.pop(0) + " ")
            if not split_line:
                wrapped_text.append(temp_line)
                line = ""
            else:
                wrapped_text.append(temp_line)
                line = " ".join(split_line)
    return wrapped_text


# Export to PDF
def export_to_pdf(location=None):
    filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
    if not filepath:
        return  # User cancelled the save operation

    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if location:
        c.execute('SELECT * FROM inventory WHERE location = ?', (location,))
    else:
        c.execute('SELECT * FROM inventory')
    items = c.fetchall()
    conn.close()

    pdf = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter  # Get dimensions of the page
    margin = 72  # Margin size
    x = margin
    y = height - margin
    line_height = 18  # Line height
    item_spacing = 10  # Additional spacing between items

    # Current date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.drawString(x, y, f"ThermOil Inventory Report - {current_datetime}")
    y -= line_height * 2  # Move down for the first line of text

    for item in items:
        text = f"ID: {item[0]}, Item: {item[1]}, Quantity: {item[2]}, Location: {item[3]}, Sub-Loc: {item[4]}, Notes: {item[5]}"
        wrapped_lines = wrap_text(text, width - 2 * margin, pdf)
        for line in wrapped_lines:
            pdf.drawString(x, y, line)
            y -= line_height
        y -= item_spacing  # Additional space after each item
        if y < margin + item_spacing:  # Check if we need to start a new page
            pdf.showPage()
            y = height - margin
            pdf.drawString(x, y, f"ThermOil Inventory Report - {current_datetime}")
            y -= line_height * 2

    pdf.save()
    messagebox.showinfo("Success", "PDF generated successfully")

#validates quanitites so they are between 0 and 999. Used for item quantities.
def validate_quantity(P):
    if P == "":
        return True  # Allow empty field for deletion
    try:
        value = int(P)
        if 0 <= value <= 999:
            return True
        else:
            return False
    except ValueError:
        return False



# GUI setup
def setup_gui(root):
    global location_combobox

    #creates the initial location dropdown. Tied to global combobox so it's always up to date.
    tk.Label(root, text="Location", font=("Arial", 14)).pack()
    location_combobox = Combobox(root, font=("Arial", 14), width=28)
    refresh_location_combobox(location_combobox)
    location_combobox.pack()

    # Registering the validation function
    validate_command = (root.register(validate_quantity), '%P')

    # GUI for editing items
    def edit_item_gui():
        item_id = simpledialog.askinteger("Edit Item", "Enter the ID of the item to edit:")
        if item_id is None:
            return

        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute('SELECT item_name, quantity, location, sub_location, notes FROM inventory WHERE id = ?', (item_id,))
        item_data = c.fetchone()

        locations = fetch_locations()  # Fetch the latest locations

        conn.close()

        if item_data:
            edit_window = Toplevel(root)
            edit_window.title("Edit Item")

            tk.Label(edit_window, text="Item Name").pack()
            name_entry = Entry(edit_window, width=30)
            name_entry.insert(0, item_data[0])
            name_entry.pack()

            tk.Label(edit_window, text="Quantity").pack()
            quantity_entry = Entry(edit_window, width=30, validate="key", validatecommand=validate_command)
            quantity_entry.insert(0, str(item_data[1]))
            quantity_entry.pack()

            tk.Label(edit_window, text="Location").pack()
            location_combobox = Combobox(edit_window, width=28)
            refresh_location_combobox(location_combobox)
            location_combobox.set(item_data[2])  # Set to current location
            location_combobox.pack()

            tk.Label(edit_window, text="Sub-Location").pack()
            sub_location_entry = Entry(edit_window, width=30)
            sub_location_entry.insert(0, item_data[3])
            sub_location_entry.pack()

            tk.Label(edit_window, text="Notes").pack()
            notes_entry = Entry(edit_window, width=30)
            notes_entry.insert(0, item_data[4])
            notes_entry.pack()

            def save_changes():
                edit_item(item_id, name_entry.get(), quantity_entry.get(), 
                        location_combobox.get(), sub_location_entry.get(), notes_entry.get())
                edit_window.destroy()
                update_message("Item updated successfully.")

            tk.Button(edit_window, text="Save Changes", command=save_changes).pack()
        else:
            messagebox.showerror("Error", "Item not found.")


    # GUI for removing items
    def remove_item_gui():
        item_id = simpledialog.askinteger("Remove Item", "Enter the ID of the item to remove:")
        if item_id is not None:
            remove_item(item_id)

    # Other GUI elements for item details
    tk.Label(root, text="Item Name", font=("Arial", 14)).pack()
    item_name_entry = tk.Entry(root, font=("Arial", 14), width=30)
    item_name_entry.pack()

    tk.Label(root, text="Quantity", font=("Arial", 14)).pack()
    quantity_entry = tk.Entry(root, font=("Arial", 14), width=30, validate="key", validatecommand=validate_command)
    quantity_entry.pack()

    tk.Label(root, text="Sub-Location", font=("Arial", 14)).pack()
    sub_location_entry = tk.Entry(root, font=("Arial", 14), width=30)
    sub_location_entry.pack()

    tk.Label(root, text="Notes", font=("Arial", 14)).pack()
    notes_entry = tk.Entry(root, font=("Arial", 14), width=30)
    notes_entry.pack()

    # Divider before item buttons
    divider1 = tk.Frame(root, height=2, bg="SystemButtonFace", relief="sunken")
    divider1.pack(fill="x", padx=5, pady=10)

    # Buttons for Item Management (Add, Edit, Remove)
    item_buttons_frame = tk.Frame(root)  # Frame for item management buttons
    tk.Button(item_buttons_frame, text="Add Item", font=("Arial", 14), 
              command=lambda: add_item(item_name_entry.get(), 
              quantity_entry.get(), location_combobox.get(), 
              sub_location_entry.get(), notes_entry.get())).pack(side=tk.LEFT, padx=5)

    tk.Button(item_buttons_frame, text="Edit Item", font=("Arial", 14), 
              command=edit_item_gui).pack(side=tk.LEFT, padx=5)

    tk.Button(item_buttons_frame, text="Remove Item", font=("Arial", 14), 
              command=remove_item_gui).pack(side=tk.LEFT, padx=5)

    item_buttons_frame.pack(pady=5)  # Pack the frame

    # Divider before location buttons
    divider2 = tk.Frame(root, height=2, bg="grey", relief="sunken")
    divider2.pack(fill="x", padx=5, pady=10)

    # Buttons for Location Management (Add, Remove, Rename)
    location_buttons_frame = tk.Frame(root)  # Frame for location management buttons
    tk.Button(location_buttons_frame, text="Add Location", font=("Arial", 14), command=lambda: add_location()).pack(side=tk.LEFT, padx=5)
    tk.Button(location_buttons_frame, text="Remove Location", font=("Arial", 14), command=lambda: remove_location()).pack(side=tk.LEFT, padx=5)
    tk.Button(location_buttons_frame, text="Rename Location", font=("Arial", 14), command=lambda: rename_location()).pack(side=tk.LEFT, padx=5)
    location_buttons_frame.pack(pady=5)  # Pack the frame

    # Location Management Functions
    def add_location():
        new_location = simpledialog.askstring("Add Location", "Enter new location name:")
        if new_location:
            update_locations("add", new_name=new_location)
        refresh_location_combobox(location_combobox)  # Refresh both comboboxes

    def remove_location():
        location_to_remove = location_combobox.get()
        if location_to_remove:
            update_locations("remove", old_name=location_to_remove)
        refresh_location_combobox(location_combobox)  # Refresh both comboboxes

    def rename_location():
        old_location = location_combobox.get()
        new_location = simpledialog.askstring("Rename Location", "Enter new location name for " + old_location + ":")
        if new_location:
            update_locations("rename", old_name=old_location, new_name=new_location)
        refresh_location_combobox(location_combobox)  # Refresh both comboboxes

    # Divider before view/export inventory buttons
    divider3 = tk.Frame(root, height=2, bg="grey", relief="sunken")
    divider3.pack(fill="x", padx=5, pady=10)

    # Buttons for viewing inventory and exporting to PDF
    tk.Button(root, text="View Inventory", font=("Arial", 14), command=view_inventory).pack(pady=5)
    tk.Button(root, text="Export to PDF", font=("Arial", 14), command=open_export_window).pack(pady=5)

    message_label = tk.Label(root, text="", font=("Arial", 10))
    message_label.pack(side=tk.BOTTOM, fill=tk.X)

    def update_message(message):
        message_label.config(text=message)



# Initialize database and GUI
initialize_db()
root = tk.Tk()
root.title("ThermOil Inventory Management System")
root.geometry("600x550")  # Adjust the window size as needed
setup_gui(root)
root.mainloop()

#Notes: In this query, item_data is a tuple containing the following elements in order:
#
#    item_data[0]: Item Name
#    item_data[1]: Quantity
#    item_data[2]: Location
#    item_data[3]: Sub-Location
#    item_data[4]: Notes