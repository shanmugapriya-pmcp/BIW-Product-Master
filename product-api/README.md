# Product Master API (Flask)

Serves your product catalog (with images) over a simple REST API so it can be
called from your Odoo AI agent.

## Folder structure
```
product-api/
├── app.py                    # Flask app
├── requirements.txt
├── Procfile                  # tells Render how to start the app
├── csv_to_json.py            # optional helper: converts your existing CSV/Excel to the JSON schema
├── data/
│   └── products_master.json  # your product master data
└── static/
    └── images/                # put product images here, filenames must match "image" field in JSON
```

## 1. Fill in your data

Edit `data/products_master.json` directly, OR if you already have your 100+
products in a CSV/Excel file, use the converter:

```bash
pip install pandas openpyxl --break-system-packages
python csv_to_json.py your_products.csv
```

Then copy all product images into `static/images/`, named exactly as listed
in the `image` field (e.g. `P0001.jpg`).

## 2. Run locally

```bash
pip install -r requirements.txt --break-system-packages
python app.py
```

Test it:
```bash
curl "http://localhost:5000/api/products/search?q=bottle"
curl "http://localhost:5000/api/agent/lookup?q=earbuds"
```

The `image_url` field in every response is a full absolute URL
(e.g. `http://localhost:5000/static/images/P0001.jpg`) so it works directly
when the app is deployed and the host changes.

## 3. Deploy to Render

1. Push this folder to a GitHub repo.
2. In Render: **New +** → **Web Service** → connect the repo.
3. Settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app` (already in the Procfile, Render should auto-detect it)
4. Deploy. You'll get a URL like `https://your-app.onrender.com`.
5. Test: `https://your-app.onrender.com/api/agent/lookup?q=chair`

**Note:** Render's free tier has an ephemeral filesystem and the service
spins down when idle — that's fine here since your JSON/images are part of
the deployed code, not runtime uploads. If you later want to update products
without redeploying, you'd need a database or object storage instead of local
files — happy to help set that up when you're ready.

## 4. Use it in your Odoo AI agent

Point your agent's tool/action at:
```
GET https://your-app.onrender.com/api/agent/lookup?q=<user's search term>
```

Response shape:
```json
{
  "found": true,
  "reply_text": "Wireless Bluetooth Earbuds (Code: SKU-AUD-2002)\nCategory: Electronics\nPrice: INR 2499.0\nStock: 45 units\nTrue wireless earbuds...",
  "product": {
    "id": "P0002",
    "name": "Wireless Bluetooth Earbuds",
    "code": "SKU-AUD-2002",
    "category": "Electronics",
    "brand": "SoundWave",
    "description": "...",
    "price": 2499.0,
    "currency": "INR",
    "stock": 45,
    "image_url": "https://your-app.onrender.com/static/images/P0002.jpg"
  }
}
```

Have the agent:
1. Call this endpoint with the user's query term.
2. If `found` is `true`, reply with `reply_text` and render/attach `product.image_url` as the image.
3. If `found` is `false`, fall back to a "couldn't find that product" message.

## Other endpoints available
- `GET /api/products` — full catalog
- `GET /api/products/<id or code>` — exact lookup
- `GET /api/products/search?q=...` — all matches (not just the best one)
