# Import required libraries from FastAPI
from fastapi import FastAPI, Query, HTTPException, Response, status

# Pydantic is used for request body validation
from pydantic import BaseModel, Field

# Typing helps with type hints
from typing import Optional, List


# Create FastAPI application instance
app = FastAPI()


# ==========================================================
# DATA MODELS (Pydantic Models)
# ==========================================================

# Model used when adding a new product
class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True


# Model used for checkout request body
class CheckoutRequest(BaseModel):

    # Customer name must have at least 2 characters
    customer_name: str = Field(..., min_length=2)

    # Delivery address must have at least 10 characters
    delivery_address: str = Field(..., min_length=10)


# ==========================================================
# FAKE DATABASE (In-memory storage)
# ==========================================================
# Product list (7 products available in store)
products = [

    {'id': 1, 'name': 'Wireless Mouse', 'price': 499,
        'category': 'Electronics', 'in_stock': True},

    {'id': 2, 'name': 'Notebook', 'price': 99,
        'category': 'Stationery', 'in_stock': True},

    {'id': 3, 'name': 'USB Hub', 'price': 799,
        'category': 'Electronics', 'in_stock': False},

    {'id': 4, 'name': 'Pen Set', 'price': 49,
        'category': 'Stationery', 'in_stock': True},

    {'id': 5, 'name': 'Laptop Stand', 'price': 1299,
        'category': 'Electronics', 'in_stock': True},

    {'id': 6, 'name': 'Mechanical Keyboard', 'price': 2499,
        'category': 'Electronics', 'in_stock': True},

    {'id': 7, 'name': 'Webcam', 'price': 1999,
        'category': 'Electronics', 'in_stock': False},

]

# Cart storage (temporary list)
cart = []

# Orders storage
orders = []

# Order ID counter
order_counter = 1


# ==========================================================
# HELPER FUNCTION
# ==========================================================

# Function to find a product by ID
def find_product(product_id: int):

    # Returns first matching product
    return next((p for p in products if p['id'] == product_id), None)


# ==========================================================
# HOME & PRODUCT VIEW ENDPOINTS
# ==========================================================

# Home endpoint
@app.get("/")
def home():
    return {"message": "Welcome to Innomatics E-commerce API"}


# Get all products
@app.get("/products")
def get_all_products():

    return {
        "products": products,
        "total": len(products)
    }


# ==========================================================
# CATEGORY FILTER
# ==========================================================

@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):

    # Filter products by category name
    result = [
        p for p in products
        if p['category'].lower() == category_name.lower()
    ]

    if not result:
        return {"error": "No products found in this category"}

    return {
        "category": category_name,
        "products": result
    }


# ==========================================================
# IN-STOCK FILTER
# ==========================================================

@app.get("/products/instock")
def get_instock():

    # Only return products that are in stock
    result = [p for p in products if p['in_stock']]

    return {
        "in_stock_products": result,
        "count": len(result)
    }


# ==========================================================
# SEARCH PRODUCT BY NAME
# ==========================================================

@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    # Search product names containing keyword
    matched = [
        p for p in products
        if keyword.lower() in p['name'].lower()
    ]

    if not matched:
        return {"message": "No products matched your search"}

    return {
        "matched_products": matched,
        "total_matches": len(matched)
    }


# ==========================================================
# CART SYSTEM
# ==========================================================

# ----------------------------------------------------------
# Add Item to Cart
# ----------------------------------------------------------

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):

    # Find product in product list
    product = find_product(product_id)

    # If product not found
    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check if product is out of stock
    if not product['in_stock']:
        raise HTTPException(
            status_code=400,
            detail=f"{product['name']} is out of stock"
        )

    # Check if product already exists in cart
    for item in cart:

        if item['product_id'] == product_id:

            # Increase quantity
            item['quantity'] += quantity

            # Recalculate subtotal
            item['subtotal'] = item['quantity'] * item['unit_price']

            return {
                "message": "Cart updated",
                "cart_item": item
            }

    # If product not already in cart → add new item
    new_item = {

        "product_id": product_id,
        "product_name": product['name'],
        "quantity": quantity,
        "unit_price": product['price'],
        "subtotal": product['price'] * quantity
    }

    cart.append(new_item)

    return {
        "message": "Added to cart",
        "cart_item": new_item
    }


# ----------------------------------------------------------
# View Cart
# ----------------------------------------------------------

@app.get("/cart")
def view_cart():

    # If cart empty
    if not cart:
        return {
            "message": "Cart is empty",
            "items": [],
            "grand_total": 0
        }

    # Calculate total cost
    grand_total = sum(item['subtotal'] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }


# ----------------------------------------------------------
# Remove Item from Cart
# ----------------------------------------------------------

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):

    global cart

    # Find product in cart
    product = next(
        (item for item in cart if item['product_id'] == product_id),
        None
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not in cart"
        )

    # Remove item from cart
    cart = [
        item for item in cart
        if item['product_id'] != product_id
    ]

    return {
        "message": f"{product['product_name']} removed from cart"
    }


# ----------------------------------------------------------
# Checkout Cart
# ----------------------------------------------------------

@app.post("/cart/checkout")
def checkout(data: CheckoutRequest):

    global order_counter, cart

    # Prevent checkout if cart empty
    if not cart:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty — add items first"
        )

    # Copy cart items
    order_items = list(cart)

    # Calculate total price
    total_price = sum(item['subtotal'] for item in order_items)

    # Create new order
    new_order = {

        "order_id": order_counter,
        "customer_name": data.customer_name,
        "items": order_items,
        "grand_total": total_price,
        "status": "confirmed"
    }

    # Save order
    orders.append(new_order)

    # Increase order ID
    order_counter += 1

    # Clear cart after checkout
    cart = []

    return {
        "message": "Checkout successful",
        "order": new_order
    }


# ----------------------------------------------------------
# View All Orders
# ----------------------------------------------------------

@app.get("/orders")
def get_orders():

    return {
        "orders": orders,
        "total_orders": len(orders)
    }
