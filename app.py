import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger
from models import db, Product

app = Flask(__name__)
CORS(app)

# Swagger Settings
app.config['SWAGGER'] = {
    'title': 'GlobalPrice Product API',
    'uiversion': 3
}

app.json.sort_keys = False 
swagger = Swagger(app)

# PostgreSQL Settings if using Docker or SQLite if locally
if os.environ.get('DOCKER_ENV'):
    db_user = os.environ.get('POSTGRES_USER', 'admin')
    db_pass = os.environ.get('POSTGRES_PASSWORD', 'admin_password')
    db_host = os.environ.get('DB_HOST', 'db')
    db_name = os.environ.get('POSTGRES_DB', 'products_db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
    print("Environment: Docker (PostgreSQL)")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///products.db'
    print("Environment: Local (SQLite)")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# API Routes
@app.route('/', methods=['GET'])
def home():
    """
    Health check route.
    ---
    responses:
      200:
        description: Returns the service status
    """
    return jsonify({
        "status": "Product Service is running",
        "service": "GlobalPrice Primary API",
        "docs": "/apidocs"
    })


@app.route('/products', methods=['POST'])
def create_product():
    """
    Create a new product
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: "iPhone 15 Pro"
            base_price:
              type: number
              example: 7000.00
            description:
              type: string
              example: "Smartphone Apple Titanium"
    responses:
      201:
        description: Product created successfully
      400:
        description: Invalid input
    """
    data = request.get_json()

    if not data or 'name' not in data or 'base_price' not in data:
        return jsonify({"error": "Invalid data. Name and base_price are required."}), 400
    
    new_product = Product(
        name=data['name'],
        description=data.get('description', ''),
        base_price=float(data['base_price'])
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify(new_product.to_dict()), 201


@app.route('/products', methods=['GET'])
def list_products():
    """
    List all products
    ---
    responses:
      200:
        description: A list of products
    """
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    """
    Get a specific product by ID
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Numeric ID of the product
    responses:
      200:
        description: Product found
      404:
        description: Product not found
    """
    product = Product.query.get_or_404(id)
    return jsonify(product.to_dict())


@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    """
    Update a product
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        schema:
          type: object
          properties:
            name:
              type: string
            base_price:
              type: number
            description:
              type: string
    responses:
      200:
        description: Product updated
    """
    product = Product.query.get_or_404(id)
    data = request.get_json()

    if 'name' in data:
        product.name = data['name']
    if 'base_price' in data:
        product.base_price = float(data['base_price'])
    if 'description' in data:
        product.description = data['description']

    db.session.commit()
    return jsonify(product.to_dict())


@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    """
    Delete a product
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Product deleted
    """
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"})


@app.route('/products/<int:id>/price/<currency>', methods=['GET'])
def get_product_price_in_currency(id, currency):
    """
    Get product price converted to target currency (Integration)
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Product ID
      - name: currency
        in: path
        type: string
        required: true
        description: Target currency code (USD, EUR, BTC, GBP, JPY, ETH, ARS, etc.)
    responses:
      200:
        description: Returns product details with converted price
      502:
        description: Error communicating with Pricing Service
    """
    product = Product.query.get_or_404(id)

    # URL settings for Secondary API
    # If it is running locally, it assumes the other API is running on port 5001
    pricing_service_url = os.environ.get('PRICING_SERVICE_URL', 'http://localhost:5001')

    payload = {
        "base_price": product.base_price,
        "target_currency": currency.upper()
    }

    try:
        response = requests.post(f"{pricing_service_url}/convert", json=payload, timeout=30)

        if response.status_code == 200:
            conversion_data = response.json()
            result = product.to_dict()
            result['price_in_currency'] = conversion_data
            return jsonify(result)
        else:
            return jsonify({"error": "Failed to convert price via Pricing Service"}), 502
    
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "pricing Service is unreachable. Is it running?",
            "tip": "If running locally, ensure the Pricing API is on port 5001."
        }), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
