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
    'uiversion': 3,
    'description': 'Product Management & Global Price Orchestration API.'
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
    tags:
      - System Status
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
    tags:
      - Product Management
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
    tags:
      - Product Management
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
    tags:
      - Product Management
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
    tags:
      - Product Management
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
    tags:
      - Product Management
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
     Global Price Simulator (AI + Watchdog).
    ---
    tags:
      - Pricing Simulation
    description: >
        Calculates the final product price in the target currency, applying dynamic risk margins.
        Use the fields below to simulate different market scenarios and business strategies.
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Product ID (e.g., 1)
      - name: currency
        in: path
        type: string
        required: true
        description: Target currency code (e.g., USD, EUR, BTC, ETH)
      
      - name: admin_fee
        in: query
        type: number
        required: false
        default: 0.005
        description: >
            PROFIT & FEES: How much extra margin do you want?
            Use 0.0 for aggressive promos or increase it to cover credit card taxes.
            (e.g., 0.005 = 0.5% | 0.02 = 2.0%)
      
      - name: volatility_threshold
        in: query
        type: number
        required: false
        default: 5.0
        description: >
            RISK TOLERANCE: How "nervous" is your system?
            If daily market volatility exceeds this value (%), the 'Auto-Hedge' protection kicks in.
            (e.g., 2.0 = Conservative/Safe | 10.0 = Aggressive/Risky)
      
      - name: max_panic_margin
        in: query
        type: number
        required: false
        default: 1.50
        description: >
             PANIC CEILING: The maximum price multiplier allowed during a market crash.
             Protects brand reputation by preventing abusive pricing.
             (e.g., 1.50 = Max price increase of 50%)

      - name: force_panic
        in: query
        type: boolean
        required: false
        default: false
        description: >
            🚨 PANIC BUTTON (Simulation): Forces 'Walter Watchdog' behavior 
            to test how the system protects revenue during an immediate market crash.
    
    responses:
      200:
        description: Successfully calculated price with strategy details.
      502:
        description: Error communicating with Pricing Service.
    """
    product = Product.query.get_or_404(id)

    # URL settings for Secondary API
    # If it is running locally, it assumes the other API is running on port 5001
    pricing_service_url = os.environ.get('PRICING_SERVICE_URL', 'http://localhost:5001')

    payload = {
        "base_price": product.base_price,
        "target_currency": currency.upper()
    }

    # Add optional overrides if they exist in the request URL
    if request.args.get('admin_fee'):
        try:
            payload['admin_fee'] = float(request.args.get('admin_fee'))
        except ValueError:
            pass # Ignore invalid numbers and use default
    
    if request.args.get('volatility_threshold'):
        try:
            payload['volatility_threshold'] = float(request.args.get('volatility_threshold'))
        except ValueError:
            pass
    
    if request.args.get('max_panic_margin'):
        try:
            payload['max_panic_margin'] = float(request.args.get('max_panic_margin'))
        except ValueError:
            pass
    
    # Check for boolean flag (strings like 'true', '1', 'yes' are considered True)
    force_panic_raw = request.args.get('force_panic', '').lower()
    if force_panic_raw in ['true', '1', 'yes', 'on']:
        payload['force_panic'] = True

    try:
        response = requests.post(f"{pricing_service_url}/convert", json=payload, timeout=30)

        if response.status_code == 200:
            conversion_data = response.json()
            result = product.to_dict()
            result['price_in_currency'] = conversion_data
            return jsonify(result)
        else:
            return jsonify({"error": "Failed to convert price via Pricing Service", "details": response.text}), 502
    
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "pricing Service is unreachable. Is it running?",
            "tip": "If running locally, ensure the Pricing API is on port 5001."
        }), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
