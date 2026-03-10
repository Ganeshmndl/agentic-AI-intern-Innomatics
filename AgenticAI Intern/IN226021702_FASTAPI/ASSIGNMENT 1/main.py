from fastapi import FastAPI

app = FastAPI()

# ── MOCK DATABASE ───────────────────────────────────────────
products = [
    {"id": 1, "name": "Mechanical Keyboard", "price": 4490, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "A4 Paper Pack", "price": 110, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 770, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 450, "category": "Stationery", "in_stock": True},
    {"id": 5, "name": "Laptop Stand", "price": 1500, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mouse", "price": 2000, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 5090, "category": "Electronics", "in_stock": False},
]

# ── ENDPOINTS ───────────────────────────────────────────────

# Home
@app.get('/')
def home():
    return {'message': 'Welcome to our E-commerce API'}

# Get all products
@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

# Get only in-stock products
@app.get('/products/instock')
def get_instock_products():
    result = [p for p in products if p['in_stock']]
    return {"in_stock_products": result, "count": len(result)}

# Get cheapest and most expensive products
@app.get('/products/deals')
def get_product_deals():
    return {
        "best_deal": min(products, key=lambda x: x['price']),
        "premium_pick": max(products, key=lambda x: x['price'])
    }

# Search products by keyword (case-insensitive)
@app.get('/products/search/{keyword}')
def search_products(keyword: str):
    matched = [p for p in products if keyword.lower() in p['name'].lower()]
    if not matched:
        return {"message": "No products matched your search"}
    return {"search_keyword": keyword, "matched_products": matched, "total_matches": len(matched)}

# Get products by category (case-insensitive)
@app.get('/products/category/{category_name}')
def get_products_by_category(category_name: str):
    result = [p for p in products if p['category'].lower() == category_name.lower()]
    if not result:
        return {"error": "No products found in this category"}
    return {"category": category_name, "products": result}

# Get a specific product by ID
@app.get('/products/{product_id}')
def get_product(product_id: int):
    for product in products:
        if product['id'] == product_id:
            return {'product': product}
    return {'error': 'Product not found'}

# Get overall store summary
@app.get('/store/summary')
def get_store_summary():
    # Streamlined using a generator expression and set comprehension
    in_stock_count = sum(1 for p in products if p['in_stock']) 
    unique_categories = list({p['category'] for p in products})
    
    return {
        "store_name": "My E-commerce Store",
        "total_products": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": len(products) - in_stock_count,
        "categories": unique_categories
    }
