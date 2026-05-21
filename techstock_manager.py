import sqlite3
from tkinter import *
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation

selected_product_id = None
AUTO_REFRESH_MS = 2000


# 1. Настройка на базата данни
def setup_db():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT, quantity INTEGER, price REAL)''')
    conn.commit()
    conn.close()


# 2. Помощни функции за валидация
def validate_inputs():
    name = name_entry.get().strip()
    qty_text = qty_entry.get().strip()
    price_text = price_entry.get().strip().replace(",", ".")

    if not name or not qty_text or not price_text:
        messagebox.showwarning("Грешка", "Попълнете всички полета!")
        return None

    try:
        quantity = int(qty_text)
    except ValueError:
        messagebox.showwarning("Грешка", "Количество трябва да бъде цяло число!")
        return None

    if quantity < 0:
        messagebox.showwarning("Грешка", "Количество не може да бъде отрицателно число!")
        return None

    try:
        price = Decimal(price_text)
    except InvalidOperation:
        messagebox.showwarning("Грешка", "Цена трябва да бъде число!")
        return None

    if price < 0:
        messagebox.showwarning("Грешка", "Цена не може да бъде отрицателно число!")
        return None

    if "." in price_text:
        decimal_part = price_text.split(".")[1]
        if len(decimal_part) > 2:
            messagebox.showwarning("Грешка", "Цена може да има максимум 2 цифри след десетичната точка!")
            return None

    return name, quantity, float(price)


def product_name_exists(name, exclude_id=None):
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute("SELECT id FROM products WHERE name=?", (name,))
    else:
        cursor.execute("SELECT id FROM products WHERE name=? AND id<>?", (name, exclude_id))

    result = cursor.fetchone()
    conn.close()

    return result is not None


# 3. CRUD операции
def add_product():
    global selected_product_id

    validated = validate_inputs()
    if validated is None:
        return

    name, quantity, price = validated

    if product_name_exists(name):
        confirm = messagebox.askyesno(
            "Повтарящо се име",
            "Вече съществува продукт с това име. Искате ли все пак да го добавите?"
        )
        if not confirm:
            return

    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)",
        (name, quantity, price)
    )
    conn.commit()
    conn.close()

    refresh_table()
    clear_entries()
    selected_product_id = None


def update_product():
    global selected_product_id

    if selected_product_id is None:
        messagebox.showwarning("Грешка", "Моля, изберете продукт за редактиране!")
        return

    validated = validate_inputs()
    if validated is None:
        return

    name, quantity, price = validated

    if product_name_exists(name, exclude_id=selected_product_id):
        confirm = messagebox.askyesno(
            "Повтарящо се име",
            "Вече съществува друг продукт с това име. Искате ли все пак да продължите?"
        )
        if not confirm:
            return

    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET name=?, quantity=?, price=? WHERE id=?",
        (name, quantity, price, selected_product_id)
    )
    conn.commit()
    conn.close()

    messagebox.showinfo("Успех", "Продуктът е редактиран успешно!")

    refresh_table()
    clear_entries()
    selected_product_id = None


def delete_product():
    global selected_product_id

    if selected_product_id is None:
        messagebox.showwarning("Грешка", "Моля, изберете продукт от таблицата!")
        return

    confirm = messagebox.askyesno(
        "Потвърждение",
        "Сигурни ли сте, че искате да изтриете избрания продукт?"
    )

    if not confirm:
        return

    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (selected_product_id,))
    conn.commit()
    conn.close()

    refresh_table()
    clear_entries()
    selected_product_id = None


def refresh_table():
    for i in tree.get_children():
        tree.delete(i)

    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        tree.insert("", END, values=row)


def auto_refresh_table():
    refresh_table()
    root.after(AUTO_REFRESH_MS, auto_refresh_table)


def clear_entries():
    name_entry.delete(0, END)
    qty_entry.delete(0, END)
    price_entry.delete(0, END)


def load_selected_product(event):
    global selected_product_id

    selected_item = tree.selection()

    if selected_item:
        item_data = tree.item(selected_item[0])
        values = item_data['values']

        selected_product_id = values[0]

        clear_entries()
        name_entry.insert(0, values[1])
        qty_entry.insert(0, values[2])
        price_entry.insert(0, values[3])


def close_app():
    confirm = messagebox.askyesno(
        "Изход",
        "Сигурни ли сте, че искате да затворите приложението?"
    )

    if confirm:
        root.destroy()


# 4. Графичен интерфейс
root = Tk()
root.title("TechStock Manager - Склад за техника")
root.geometry("850x500")
root.minsize(700, 400)

root.protocol("WM_DELETE_WINDOW", close_app)

# Настройка за разтягане при максимизиране
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=2)
root.columnconfigure(2, weight=1)
root.columnconfigure(3, weight=0)
root.rowconfigure(4, weight=1)

# Входни полета
Label(root, text="Име на продукт:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
name_entry = Entry(root)
name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

Label(root, text="Количество:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
qty_entry = Entry(root)
qty_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

Label(root, text="Цена:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
price_entry = Entry(root)
price_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

# Бутони
Button(root, text="Добави продукт", command=add_product, bg="green", fg="white").grid(
    row=3, column=0, padx=10, pady=10, sticky="ew"
)

Button(root, text="Редактирай избран", command=update_product, bg="orange", fg="black").grid(
    row=3, column=1, padx=10, pady=10, sticky="ew"
)

Button(root, text="Изтрий избран", command=delete_product, bg="red", fg="white").grid(
    row=3, column=2, padx=10, pady=10, sticky="ew"
)

# Таблица
columns = ("ID", "Име", "Количество", "Цена")
tree = ttk.Treeview(root, columns=columns, show='headings')

tree.heading("ID", text="ID")
tree.heading("Име", text="Име")
tree.heading("Количество", text="Количество")
tree.heading("Цена", text="Цена")

tree.column("ID", width=60, anchor="center")
tree.column("Име", width=250)
tree.column("Количество", width=120, anchor="center")
tree.column("Цена", width=120, anchor="center")

tree.grid(row=4, column=0, columnspan=3, padx=(10, 0), pady=10, sticky="nsew")

# Scrollbar
scrollbar_y = ttk.Scrollbar(root, orient=VERTICAL, command=tree.yview)
scrollbar_y.grid(row=4, column=3, padx=(0, 10), pady=10, sticky="ns")
tree.configure(yscrollcommand=scrollbar_y.set)

tree.bind("<<TreeviewSelect>>", load_selected_product)

setup_db()
refresh_table()
auto_refresh_table()

root.mainloop()