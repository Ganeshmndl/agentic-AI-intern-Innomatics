from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ─────────────────────────────────────────────
# DATA STORE
# ─────────────────────────────────────────────

products = [
    {"id": 1, "name": "Mechanical Keyboard", "price": 4490,
        "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "A4 Paper Pack", "price": 110,
        "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 770,
        "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 450,
        "category": "Stationery", "in_stock": True},
    {"id": 5, "name": "Laptop Stand", "price": 1500,
        "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mouse", "price": 2000,
        "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 5090,
        "category": "Electronics", "in_stock": False},
]

feedback_db = []
orders_db = []

# ─────────────────────────────────────────────
# DAY 1 TASKS
# ─────────────────────────────────────────────


@app.get("/")
def home():
    return {"message": "Welcome to our E-commerce API"}


@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):

    result = [
        p for p in products
        if p["category"].lower() == category_name.lower()
    ]

    if not result:
        return {"error": "No products found in this category"}

    return {
        "category": category_name,
        "products": result,
        "total": len(result)
    }


@app.get("/products/instock")
def get_instock_products():

    available = [p for p in products if p["in_stock"]]

    return {
        "in_stock_products": available,
        "count": len(available)
    }


@app.get("/store/summary")
def store_summary():

    in_stock = len([p for p in products if p["in_stock"]])
    categories = list(set(p["category"] for p in products))

    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock,
        "out_of_stock": len(products) - in_stock,
        "categories": categories
    }


@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    results = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not results:
        return {"message": "No products matched your search"}

    return {
        "keyword": keyword,
        "results": results,
        "total_matches": len(results)
    }


# ─────────────────────────────────────────────
# DAY 2 TASKS
# ─────────────────────────────────────────────

@app.get("/products/filter")
def filter_products(
        category: Optional[str] = Query(None),
        min_price: Optional[int] = Query(None),
        max_price: Optional[int] = Query(None),
        in_stock: Optional[bool] = Query(None)
):

    result = products

    if category:
        result = [p for p in result if p["category"].lower() ==
                  category.lower()]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    if in_stock is not None:
        result = [p for p in result if p["in_stock"] == in_stock]

    return {
        "filtered_products": result,
        "count": len(result)
    }


@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    return {"error": "Product not found"}


# ─────────────────────────────────────────────
# FEEDBACK SYSTEM
# ─────────────────────────────────────────────

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)


@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback_db.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data,
        "total_feedback": len(feedback_db)
    }


# ─────────────────────────────────────────────
# PRODUCT SUMMARY
# ─────────────────────────────────────────────

@app.get("/products/summary")
def product_summary():

    in_stock = len([p for p in products if p["in_stock"]])

    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {
        "total_products": len(products),
        "in_stock_count": in_stock,
        "out_of_stock_count": len(products) - in_stock,
        "most_expensive": {"name": expensive["name"], "price": expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": list(set(p["category"] for p in products))
    }


# ─────────────────────────────────────────────
# BULK ORDER SYSTEM
# ─────────────────────────────────────────────

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)


class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str
    items: List[OrderItem]


@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    total = 0

    for item in order.items:

        product = next(
            (p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({"product_id": item.product_id,
                          "reason": "Product not found"})
            continue

        if not product["in_stock"]:
            failed.append({"product_id": item.product_id,
                          "reason": f"{product['name']} is out of stock"})
            continue

        subtotal = product["price"] * item.quantity
        total += subtotal

        confirmed.append({
            "product": product["name"],
            "quantity": item.quantity,
            "subtotal": subtotal
        })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": total
    }


# ─────────────────────────────────────────────
# BONUS: ORDER TRACKING
# ─────────────────────────────────────────────

@app.post("/orders")
def create_order(product_id: int, quantity: int):

    new_order = {
        "order_id": len(orders_db) + 1,
        "product_id": product_id,
        "quantity": quantity,
        "status": "pending"
    }

    orders_db.append(new_order)

    return new_order


@app.get("/orders/{order_id}")
def get_order(order_id: int):

    order = next((o for o in orders_db if o["order_id"] == order_id), None)

    if not order:
        return {"error": "Order not found"}

    return order


@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders_db:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}

    return {"error": "Order not found"}


@app.get("/products/deals")
def get_deals():

    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])

    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }
