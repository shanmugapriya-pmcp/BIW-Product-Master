import json
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import re

STOPWORDS = {"the", "a", "an", "for", "with", "of", "and", "in", "on"}



DATA_FILE = os.path.join(BASE_DIR, "data", "products_master.json")
IMAGES_DIR = os.path.join(BASE_DIR, "static", "images")

app = Flask(__name__)
CORS(app)  # allow calls from Odoo / any origin

def tokenize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ---------- Data loading ----------

def load_products():
    """Load the product master JSON fresh from disk each time.
    Keeps things simple: edit products_master.json and changes are live
    on next request without restarting the server."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("products", [])


def build_image_url(image_filename):
    if not image_filename:
        return None
    return f"{request.host_url.rstrip('/')}/static/images/{image_filename}"


def serialize_product(p):
    # Support both the old single "image" field and the new "images" list,
    # so older data keeps working.
    image_files = p.get("images")
    if not image_files:
        single = p.get("image")
        image_files = [single] if single else []

    image_urls = [build_image_url(f) for f in image_files]

    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "code": p.get("code"),
        "category": p.get("category"),
        "brand": p.get("brand"),
        "description": p.get("description"),
        "price": p.get("price"),
        "currency": p.get("currency"),
        "size": p.get("size"),
        "colour": p.get("colour"),
        "stock": p.get("stock"),
        "image_url": image_urls[0] if image_urls else None,  # primary image, for simple replies
        "image_urls": image_urls,  # all images, for richer replies
    }


# ---------- Routes ----------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "Product Master API is running.",
        "endpoints": [
            "GET /api/products",
            "GET /api/products/<id>",
            "GET /api/products/search?q=<keyword>",
            "GET /api/agent/lookup?q=<keyword>"
        ]
    })


@app.route("/api/products", methods=["GET"])
def get_all_products():
    products = load_products()
    return jsonify({"count": len(products), "products": [serialize_product(p) for p in products]})


@app.route("/api/products/<product_id>", methods=["GET"])
def get_product_by_id(product_id):
    products = load_products()
    for p in products:
        if p.get("id", "").lower() == product_id.lower() or p.get("code", "").lower() == product_id.lower():
            return jsonify(serialize_product(p))
    return jsonify({"error": "Product not found"}), 404


@app.route("/api/products/search", methods=["GET"])
def search_products():
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    products = load_products()
    results = []
    for p in products:
        haystack = " ".join([
            p.get("name", ""),
            p.get("code", ""),
            p.get("category", ""),
            p.get("brand", ""),
            p.get("description", ""),
            " ".join(p.get("keywords", [])),
        ]).lower()
        if query in haystack:
            results.append(serialize_product(p))

    return jsonify({"count": len(results), "products": results})


@app.route("/api/agent/lookup", methods=["GET"])
def agent_lookup():
    """
    Designed specifically for the Odoo AI agent to call.
    Returns the single best-matching product in a compact,
    reply-ready format including the image URL.
    """
    query = request.args.get("q", "").strip().lower()
    if not query:
        return jsonify({"found": False, "message": "No query provided."}), 400

    query_words = set(tokenize(query))
    if not query_words:
        return jsonify({"found": False, "message": "No usable search terms."})

    products = load_products()
    best_match = None
    best_score = 0

    for p in products:
        haystack = " ".join([
            p.get("name", ""),
            p.get("code", ""),
            p.get("category", ""),
            p.get("brand", ""),
            " ".join(p.get("keywords", [])),
        ])
        haystack_words = set(tokenize(haystack))

        overlap = query_words & haystack_words
        score = len(overlap) / len(query_words)

        if score > best_score:
            best_score = score
            best_match = p

    if not best_match or best_score < 0.5:
        return jsonify({"found": False, "message": f"No product found matching '{query}'."})

    product = serialize_product(best_match)
    size_line = f"Available sizes: {', '.join(as_list(product['size']))}\n" if product.get("size") else ""
    colour_line = f"Colours: {', '.join(as_list(product['colour']))}\n" if product.get("colour") else ""
    reply_text = (
        f"{product['name']} (Code: {product['code']})\n"
        f"Category: {product['category']}\n"
        f"Price: {product['currency']} {product['price']}\n"
        f"{size_line}"
        f"{colour_line}"
        f"{product['description']}"
    )

    return jsonify({
        "found": True,
        "reply_text": reply_text,
        "product": product
    })
def as_list(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    return [v.strip() for v in str(value).split(",") if v.strip()]
    product = serialize_product(best_match)
    size_line = f"Available sizes: {', '.join(product['size'])}\n" if product.get("size") else ""
    colour_line = f"Colours: {', '.join(product['colour'])}\n" if product.get("colour") else ""
    reply_text = (
        f"{product['name']} (Code: {product['code']})\n"
        f"Category: {product['category']}\n"
        f"Price: {product['currency']} {product['price']}\n"
        f"{size_line}"
        f"{colour_line}"
        f"{product['description']}"
    )

    return jsonify({
        "found": True,
        "reply_text": reply_text,
        "product": product
    })


@app.route("/static/images/<path:filename>", methods=["GET"])
def get_image(filename):
    return send_from_directory(IMAGES_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
