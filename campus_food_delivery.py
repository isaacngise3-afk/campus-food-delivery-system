"""
Campus Food Delivery and Order Management System
Group 23 - 1203 ST Programming Fundamentals

A console-based Python program to digitize ordering, fee calculation,
rider tracking and sales reporting for a campus canteen.
"""

import json
from pathlib import Path

ORDER_FILE = Path("orders.json")

# ---------------------------------------------------------------------------
# a) Menu setup
# ---------------------------------------------------------------------------
# Menu items grouped by category. Each item has an id, a name and a price
# in UGX. Using a dictionary keyed by item id makes lookup during ordering
# fast and simple.
MENU = {
    "Meals": {
        1: {"name": "Chicken and Rice", "price": 8000},
        2: {"name": "Beef Stew and Posho", "price": 7000},
        3: {"name": "Fish and Matoke", "price": 9000},
    },
    "Drinks": {
        4: {"name": "Soda", "price": 2000},
        5: {"name": "Bottled Water", "price": 1000},
        6: {"name": "Fresh Juice", "price": 3000},
    },
    "Snacks": {
        7: {"name": "Samosa", "price": 1500},
        8: {"name": "Chapati", "price": 1000},
        9: {"name": "Doughnut", "price": 800},
    },
}

# Riders available for delivery. Orders are assigned to them in rotation.
RIDERS = ["Peter Okello", "Grace Namuli", "John Ssali", "Moses Kato"]

# Valid order statuses, in the order they must progress through.
STATUS_STAGES = ["Pending", "Out for Delivery", "Delivered"]


# ---------------------------------------------------------------------------
# e) File persistence
# ---------------------------------------------------------------------------
def load_orders():
    """Load saved orders from orders.json.

    Returns an empty list if the file does not exist yet or is corrupted,
    instead of crashing the program.
    """
    if not ORDER_FILE.exists():
        return []
    try:
        with ORDER_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Warning: orders.json was missing or corrupted. Starting fresh.")
        return []


def save_orders(orders):
    """Write the current list of orders to orders.json."""
    with ORDER_FILE.open("w", encoding="utf-8") as file:
        json.dump(orders, file, indent=2)


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------
def get_valid_integer(prompt, minimum=1):
    """Repeatedly ask the user for input until a valid integer >= minimum
    is entered."""
    while True:
        raw_value = input(prompt).strip()
        if raw_value.isdigit() and int(raw_value) >= minimum:
            return int(raw_value)
        print(f"Please enter a whole number of at least {minimum}.")


def find_item(item_id):
    """Look up a menu item by its id across all categories.

    Returns a tuple (category, name, price) or None if not found.
    """
    for category, items in MENU.items():
        if item_id in items:
            return category, items[item_id]["name"], items[item_id]["price"]
    return None


# ---------------------------------------------------------------------------
# Menu display
# ---------------------------------------------------------------------------
def show_menu():
    """Print the menu, grouped by category, with item ids and prices."""
    print("\n===== CANTEEN MENU =====")
    for category, items in MENU.items():
        print(f"\n{category}:")
        for item_id, details in items.items():
            print(f"  {item_id}. {details['name']:<22} UGX {details['price']}")
    print()


# ---------------------------------------------------------------------------
# b) Order taking
# ---------------------------------------------------------------------------
def calculate_delivery_fee(subtotal):
    """Apply a delivery fee that depends on the order's total value."""
    if subtotal >= 30000:
        return 0
    if subtotal >= 15000:
        return 1500
    return 3000


def generate_order_id(orders):
    """Generate the next sequential order id."""
    if not orders:
        return 1
    return max(order["order_id"] for order in orders) + 1


def assign_rider(orders):
    """Assign a rider by cycling through the RIDERS list using the number
    of orders placed so far."""
    return RIDERS[len(orders) % len(RIDERS)]


def add_order(orders):
    """Build a customer order interactively and append it to orders."""
    show_menu()
    cart = []

    while True:
        item_id = get_valid_integer("Enter item number to add (0 to finish): ", minimum=0)
        if item_id == 0:
            break

        result = find_item(item_id)
        if result is None:
            print("That item number doesn't exist. Try again.")
            continue

        category, name, price = result
        quantity = get_valid_integer(f"Quantity for {name}: ", minimum=1)
        cart.append({"name": name, "category": category, "price": price, "quantity": quantity})
        print(f"Added {quantity} x {name} to the cart.")

    if not cart:
        print("No items were selected. Order cancelled.")
        return

    subtotal = sum(item["price"] * item["quantity"] for item in cart)
    delivery_fee = calculate_delivery_fee(subtotal)
    total = subtotal + delivery_fee
    rider = assign_rider(orders)

    order = {
        "order_id": generate_order_id(orders),
        "items": cart,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "rider": rider,
        "status": STATUS_STAGES[0],
    }

    orders.append(order)
    save_orders(orders)

    print("\n----- ORDER CONFIRMED -----")
    print(f"Order ID:      {order['order_id']}")
    print(f"Subtotal:      UGX {subtotal}")
    print(f"Delivery fee:  UGX {delivery_fee}")
    print(f"Total:         UGX {total}")
    print(f"Rider:         {rider}")
    print(f"Status:        {order['status']}\n")


# ---------------------------------------------------------------------------
# c) Rider assignment and status tracking
# ---------------------------------------------------------------------------
def find_order(orders, order_id):
    """Find an order dict by its id, or return None."""
    for order in orders:
        if order["order_id"] == order_id:
            return order
    return None


def change_status(orders):
    """Move an order forward through its status stages, refusing to skip
    stages out of order."""
    if not orders:
        print("There are no orders yet.")
        return

    order_id = get_valid_integer("Enter the order ID to update: ")
    order = find_order(orders, order_id)
    if order is None:
        print("No order found with that ID.")
        return

    current_index = STATUS_STAGES.index(order["status"])
    if current_index == len(STATUS_STAGES) - 1:
        print(f"Order {order_id} is already {order['status']}. Nothing to update.")
        return

    next_status = STATUS_STAGES[current_index + 1]
    confirm = input(f"Move order {order_id} from '{order['status']}' to '{next_status}'? (y/n): ")
    if confirm.strip().lower() == "y":
        order["status"] = next_status
        save_orders(orders)
        print(f"Order {order_id} is now '{next_status}'.")
    else:
        print("Status update cancelled.")


# ---------------------------------------------------------------------------
# d) Sales and reporting
# ---------------------------------------------------------------------------
def show_report(orders):
    """Display total revenue, the best-selling item and the number of
    orders in each status category."""
    if not orders:
        print("No orders have been placed yet.")
        return

    total_revenue = sum(order["total"] for order in orders)

    item_counts = {}
    for order in orders:
        for item in order["items"]:
            item_counts[item["name"]] = item_counts.get(item["name"], 0) + item["quantity"]
    best_seller = max(item_counts, key=item_counts.get)

    status_counts = {stage: 0 for stage in STATUS_STAGES}
    for order in orders:
        status_counts[order["status"]] += 1

    print("\n===== DAILY SALES REPORT =====")
    print(f"Total revenue:      UGX {total_revenue}")
    print(f"Best-selling item:  {best_seller} ({item_counts[best_seller]} sold)")
    print("Orders by status:")
    for stage, count in status_counts.items():
        print(f"  {stage:<18} {count}")
    print()


# ---------------------------------------------------------------------------
# f) Menu-driven driver programme
# ---------------------------------------------------------------------------
def main():
    orders = load_orders()

    menu_options = {
        "1": "Place a new order",
        "2": "View menu",
        "3": "Update an order's status",
        "4": "View daily sales report",
        "5": "Exit",
    }

    while True:
        print("\n===== CAMPUS FOOD DELIVERY SYSTEM =====")
        for key, label in menu_options.items():
            print(f"{key}. {label}")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_order(orders)
        elif choice == "2":
            show_menu()
        elif choice == "3":
            change_status(orders)
        elif choice == "4":
            show_report(orders)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please choose a number from 1 to 5.")


if __name__ == "__main__":
    main()
