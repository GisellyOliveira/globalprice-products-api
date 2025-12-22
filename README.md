# 🌍 GlobalPrice - Product Microservice (Orchestrator)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0-000000?style=flat&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13-336791?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Server-Gunicorn-499D4B?style=flat&logo=gunicorn&logoColor=white)
![Swagger](https://img.shields.io/badge/Docs-Swagger-85EA2D?style=flat&logo=swagger&logoColor=black)

> **Core Orchestrator** for the GlobalPrice architecture. Handles product catalog management, persistence, and delegates real-time risk analysis to the AI & Watchdog engines.

## 📋 Project Description
GlobalPrice is a resilient distributed system designed to solve currency volatility risks in international e-commerce. It implements a **Hybrid Risk Strategy**:
1.  **AI-Driven Optimization:** Uses Generative AI (Gemini) to calculate optimal spreads during calm market days.
2.  **Event-Driven Protection:** Uses a real-time **Watchdog ("Walter")** that monitors the Binance WebSocket stream. If a market crash is detected, the system automatically switches to "Panic Mode", overriding AI decisions to protect revenue.

---

## 🏗️ Architecture and Design Patterns

GlobalPrice was developed following modern software architecture patterns to ensure scalability, decoupling, and resilience.

### 🌐 RESTful Interface

External communication and inter-service connectivity follow the **REST (Representational State Transfer)** architectural style, achieving **Level 2 of the Richardson Maturity Model**:

* **Well-Defined Resources:** Clear identification of resources through URIs (e.g., /products, /config).
* **Semantic HTTP Verbs:** Rigorous implementation of GET for queries, POST for creation, PATCH for partial updates, and DELETE for removal/state resets.
* **Statelessness:** The server does not store client session state, ensuring that every request is independent and self-explanatory.
* **Standardized Representations:** Communication is based entirely on JSON, utilizing appropriate HTTP status codes (200 OK, 201 Created, 404 Not Found, 502 Bad Gateway).

### 📡 Event-Driven Coordination (Pub/Sub Logic)

For real-time market monitoring, the system utilizes a **Reactive Signaling** structure via **Redis**, which acts as the event mediator between the Watchdog service and the pricing engine:

* **Publisher (Watchdog "Walter"):** Acts as the signal broadcaster. It monitors the Binance WebSocket data stream and, upon detecting an anomaly, "publishes" a panic state to Redis with a controlled Time-To-Live (TTL).
* **Shared State / Subscriber Logic (Pricing API):** The Pricing API acts as the consumer of this state. Before processing any calculation, it consults Redis (state subscription) to dynamically decide whether to follow the AI-driven optimization flow or trigger the safety "Circuit Breaker" (Hard-Hedge).


This approach ensures that the safety system is non-blocking and maintains ultra-low latency, allowing the application to react to market crashes in milliseconds without impacting the performance of the core business logic.

---

## 📂 Project Structure

```text
/globalprice-products-api
├── assets/             # 📸 Project documentation assets (diagrams, images)
│   └── architecture.png
├── app.py              # 🧠 Main application logic & Routes
├── models.py           # 🗄️ Database Schema (SQLAlchemy)
├── docker-compose.yml  # 🐳 Orchestration of all services
├── Dockerfile          # 🏗️ Container definition (Python 3.11)
├── requirements.txt    # 📦 Dependencies list
├── README.md           # 📖 Project documentation
└── .env.example        # 🔐 Secrets & Config (Must be edited to generate .env file)
```

---

## 🏗 Architecture Flowchart

The following diagram illustrates the **Scenario 2.1 Microservices Architecture**, highlighting the communication between the Orchestrator, the Business Logic Engine, and External Services.

![GlobalPrice Architecture Diagram](assets/architecture.png)

---

## ✨ Key Features
- **Advanced Orchestration:** Uses Docker Compose to manage 5 containers: Main API, Pricing API, Watchdog, PostgreSQL, and Redis.

- **Real-Time Watchdog:** 🐶 "Walter" (our watchdog service) listens to Binance WebSockets 24/7.

- **Circuit Breaker Logic:** If the market crashes (volatility spikes), the system instantly switches strategies via Redis pub/sub.

- **AI Integration:** Connects with the Pricing Service to deliver AI-calculated profit margins based on market volatility.

- **Simulation Engine:** The API allows users to override risk parameters (Admin Fee, Risk Tolerance) per request to simulate different business scenarios.

- **Resilient Database:** Production-ready PostgreSQL with healthchecks.

---

## 🔌 External APIs Used

This project integrates with third-party public services:
1. **AwesomeAPI (Currency Data):** 
    * **Service:** Real-time exchange rates.
    * **License:** Free for public use.
    * **Routes Used:** https://economia.awesomeapi.com.br/last/{coin}-{target}
2. **Google Gemini (Artificial Intelligence):** 
    * **Service:** Generative AI for financial risk analysis.
    * **Access:** Requires API Key (Free Tier).
    * **Model:** Gemini 2.5 Flash.
 3. **Binance WebSocket:**
 -  * **Service:** For real-time, high-frequency volatility monitoring (Stream).

---

## ⚙️ Installation & Execution
You can run this project using **Docker** *(Recommended)* or a **Local Environment** *(Python)*.

### Prerequisites

- **Git** installed.
- **[Docker Desktop](https://www.docker.com/)** installed and running *(Required for Method 1)*.
- **Python 3.11** *(for Local Environment - Method 2)*.
- A Google Gemini API Key (Get it free [here](https://aistudio.google.com/app/api-keys)).



### 1. Clone the repositories
    Ensure both repositories are in the same parent directory.
    ```bash
    # Folder structure example:
    # /Projects
    #   ├── globalprice-products-api
    #   └── globalprice-pricing-api
    
    git clone https://github.com/GisellyOliveira/globalprice-products-api.git
    git clone https://github.com/GisellyOliveira/globalprice-pricing-api.git
    ```

### 2. Configure Environment
This project requires environment variables for Database credentials and the AI API Key. A template is provided in `.env.example`.

  **a. Create your local configuration file:**

Copy the template to a new file named `.env`.
    
```bash
cp .env.example .env   # Linux/Mac
# copy .env.example .env # Windows CMD
```

  **b. Edit the `.env` file:**
    Open the newly created `.env` file and fill in the **required** fields (leave the others as default unless you have port conflicts).

```bash
# Database Settings (REQUIRED)
# Define credentials for the PostgreSQL container
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=products_db

# Network and Port Configurations (Optional - Defaults provided)
PORT_MAIN=5000
PORT_SEC=5001

# Service URLs (Do not change if using Docker Compose)
PRICING_SERVICE_URL=http://pricing_service:5000

# API Key (REQUIRED for AI Risk Analysis)
# Get your free key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIwpkyT...
```

### 3. Running the System:

## a. 🐳 Running with Docker: Docker Compose (Recommended)
This method automatically orchestrates the Database, the Pricing Service, and this API without requiring local Python configuration.

**Run the System:**
```bash
    cd globalprice-products-api
    docker-compose up --build
```
*The system is ready when you see logs indicating `database system is ready` and `Running on http://0.0.0.0:5000`.*


## b. 🐍 Running Locally: Local Environment (Manual)
Use this method if you want to develop or debug this specific service in isolation, using a local SQLite database.

1.  **Create Virtual Environment:**
It is best practice to isolate dependencies.

```bash
cd globalprice-products-api
python -m venv venv
    
# Activate:
source venv/bin/activate  # Mac/Linux
# .\venv\Scripts\activate # Windows
```

2.  **Install Dependencies:**
```bash
    pip install -r requirements.txt
```

3.  **Set Environment Variables (Optional):**
    If running locally without Docker, the app defaults to SQLite. To use Gemini AI, export the key:
```bash
export GEMINI_API_KEY="YOUR_KEY" # Mac/Linux
# set GEMINI_API_KEY="YOUR_KEY"  # Windows
```

4.  **Run Application:**
```bash
python app.py
```
    
*Access at: http://localhost:5000*

---

## 📖 API Documentation (Swagger)

Once the system is running, access the **Interactive Swagger UI** to test all endpoints visually without writing code:

👉 **[http://localhost:5000/apidocs](http://localhost:5000/apidocs)**

### 🔌 Available Endpoints

✅ **System Status**
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | **Health Check:** Verifies if the API is running and healthy. |

📦 **Product Management**
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/products` | **List:** Retrieves all registered products from the database. |
| `POST` | `/products` | **Create:** Adds a new product to the catalog. |
| `GET` | `/products/{id}` | **Read:** Retrieves details of a specific product by its ID. |
| `PUT` | `/products/{id}` | **Update:** Modifies an existing product's data. |
| `DELETE` | `/products/{id}` | **Delete:** Removes a product from the database. |

💵⇆💶 **Pricing Simulation**
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/products/{id}/price/{currency}` | **⭐ Hybrid Pricing Engine:** Converts price to target currency using a dynamic strategy that switches between 🧠 **Generative AI (Gemini)** for optimization and a 🐶 **Real-Time Watchdog** for crash protection. Supports scenario simulation (panic mode, profit margins) via query params. |


### ⚙️ Simulation Parameters (Query Strings):
You can customize the pricing strategy by adding these parameters to the URL (or via Swagger):

- **admin_fee:** (Float) Profit margin. Default: 0.005 (0.5%).
    - *Example: ?admin_fee=0.02 (Simulate 2% credit card fee).
- **volatility_threshold:** (Float) Sensitivity of the Auto-Hedge. Default: 5.0%.
    - *Example: ?volatility_threshold=2.0 (Conservative Mode).*
- **max_panic_margin:** (Float) The ceiling for price increases during a crash.       Default: 1.50 (50%).
- **force_panic:** (Boolean) Test the Watchdog. Forces the system to act as if a market crash is happening right now.
    - *Example: ?force_panic=true.*

---

## 📄 License
This project is licensed under the **MIT License** and is part of the GlobalPrice MVP architecture for the Software Architecture postgraduate course at the Pontifical Catholic University of Rio de Janeiro (PUC-Rio).

See the [LICENSE](LICENSE) file for more details.