# Small Shop Inventory Management System
### Cloud-Native AWS & DevOps Integrated Web Application

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask_3.x-black?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![AWS](https://img.shields.io/badge/Cloud-Amazon_AWS-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![MySQL](https://img.shields.io/badge/Database-MySQL_RDS_8.0-4479A1?logo=mysql&logoColor=white)](https://aws.amazon.com/rds/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![Prometheus](https://img.shields.io/badge/Monitoring-Prometheus-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Observability-Grafana-F46800?logo=grafana&logoColor=white)](https://grafana.com/)
[![Tests](https://img.shields.io/badge/Pytest-19%2F19_Passed-brightgreen?logo=pytest&logoColor=white)](https://docs.pytest.org/)

---

## 📌 1. Project Overview & Problem Statement

### The Problem
Small retail store owners (groceries, pharmacies, hardware shops) traditionally manage stock records manually in notebooks or spreadsheets. As a result:
* **Unexpected Stockouts:** Shortages are only realized when a customer requests an item, leading to lost sales and dissatisfied customers.
* **Overstocking / Idle Capital:** Inability to track fast-moving vs. slow-moving stock ties up operating cash flow.
* **Manual Errors:** Human calculation errors during busy checkout hours cause inventory ledger discrepancies.

### The Solution
The **Small Shop Inventory Management System** is an end-to-end cloud-native web application that automates:
* **Product Cataloging & Dynamic Search:** Instant search and category filtering across all inventory.
* **Point of Sale (POS) Checkout:** Automatic stock deduction upon customer purchase with live pricing calculations.
* **Automated Low-Stock Detection:** Evaluates remaining stock against custom minimum safety thresholds.
* **Cloud Email Alerts via Amazon SNS:** Immediately alerts the shop owner via email when items drop below threshold, featuring intelligent deduplication to prevent notification spam.
* **Complete Inventory Audit Trail:** Immutable ledger logging every restock, sale, and adjustment.
* **Enterprise DevOps Integration:** Full CI/CD via **GitHub Actions**, zero-SSH remote server management via **AWS Systems Manager (SSM)**, Infrastructure as Code via **AWS CloudFormation**, and metrics monitoring via **Prometheus and Grafana**.

---

## 🏗️ 2. End-to-End AWS Architecture

```mermaid
flowchart TD
    subgraph Client_Tier["Client Tier"]
        Browser["Shop Owner Browser (Bootstrap 5 Responsive UI)"]
    end

    subgraph CI_CD_Pipeline["DevOps & CI/CD Tier"]
        GitHub["GitHub Repository (Push to main)"]
        GHA["GitHub Actions Runner (Lint, 19 Pytests, Build)"]
        GitHub --> GHA
    end

    subgraph AWS_Cloud["AWS Cloud (us-east-1 / ap-south-1)"]
        
        subgraph VPC["Virtual Private Cloud (VPC: 10.0.0.0/16)"]
            
            subgraph PublicSubnet["Public Subnet (10.0.1.0/24)"]
                EC2["Amazon EC2 (Ubuntu 22.04 LTS)\n- Nginx Reverse Proxy (Port 80)\n- Gunicorn WSGI Server (127.0.0.1:5000)\n- Flask Core App\n- Node Exporter (Port 9100)\n- AWS SSM Agent"]
            end
            
            subgraph PrivateSubnets["Private Subnets (10.0.11.0/24 & 10.0.12.0/24)"]
                RDS[("Amazon RDS MySQL 8.0\n- DB: inventory_db\n- Port 3306 Restricted to EC2 SG")]
            end
            
        end

        subgraph Management_Tier["AWS Management & Security"]
            SSM["AWS Systems Manager (SSM)\n- Session Manager (Zero-SSH Console)\n- Run Command (Automated Deploys)"]
            SNS["Amazon SNS Topic (ShopAlerts)\n- Email Subscription"]
            IAM["IAM Instance Profile\n- AmazonSSMManagedInstanceCore\n- SNS Publish Scoped Policy"]
        end

        subgraph Monitoring_Tier["Observability Stack"]
            Prometheus["Prometheus Server (:9090)\n- Scrapes Node Exporter & /metrics"]
            Grafana["Grafana Dashboard (:3000)\n- Real-time CPU, RAM, Disk & RPS Visuals"]
        end

    end

    Browser -->|HTTP Port 80| EC2
    EC2 -->|SQL Queries Port 3306| RDS
    EC2 -->|Boto3 Low Stock Alert| SNS
    SNS -->|Instant Email| Inbox[("Shop Owner Email Inbox")]
    GHA -->|SSM Run Command Deploy| EC2
    SSM -.->|Outbound Port 443 Tunnel| EC2
    IAM -.->|Assigned to| EC2
    Prometheus -->|Scrape :9100 & :5000/metrics| EC2
    Grafana -->|PromQL Queries| Prometheus
```

---

## ⚙️ 3. Technology Stack

| Category | Technology | Usage in Project |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JS, Bootstrap 5.3 | Responsive UI, live sales calculators, instant table search, and modal dialogues. |
| **Backend** | Python 3.12+, Flask 3.x, Gunicorn | Application factory architecture, session authentication, and transactional services. |
| **Database** | MySQL 8.0 / Amazon RDS, SQLAlchemy | ACID-compliant relational storage, foreign key cascade constraints, and indexing. |
| **Compute** | Amazon EC2 (Ubuntu 22.04 LTS) | Production web host running Gunicorn systemd service and Nginx reverse proxy. |
| **Notifications** | Amazon SNS (Simple Notification Service) | Decoupled pub/sub topic sending email alerts for low inventory. |
| **Server Management** | AWS Systems Manager (SSM) | **Zero-SSH** browser shell (Session Manager) and remote command execution. |
| **IaC** | AWS CloudFormation | Declarative YAML template provisioning 20 cloud resources reproducibly. |
| **CI/CD** | GitHub Actions | Automated linting, testing, and continuous deployment to EC2 via AWS SSM. |
| **Monitoring** | Prometheus, Node Exporter, Grafana | Real-time observability for CPU, memory, disk, availability, and HTTP metrics. |

---

## 🔔 4. Low-Stock Notification Workflow (Anti-Duplicate Logic)

```mermaid
sequenceDiagram
    autonumber
    actor Cashier as Cashier / Owner
    participant POS as Point of Sale UI
    participant Backend as Flask App (/sales/record)
    participant DB as Amazon RDS MySQL
    participant SNS as Amazon SNS Topic
    actor Email as Owner Email Inbox

    Cashier->>POS: Record customer sale (e.g. 6 units Milk)
    POS->>Backend: POST /sales/record {product_id: 1, quantity: 6}
    Backend->>DB: Fetch current quantity & min_stock_level
    DB-->>Backend: Current: 10 units, Min Threshold: 5 units, Notified: FALSE
    
    Backend->>Backend: Validate stock sufficiency (10 >= 6? Yes)
    Backend->>DB: Atomic Transaction:
    Backend->>DB: 1. INSERT INTO sales (qty_sold: 6, unit_price: 3.50, total: 21.00)
    Backend->>DB: 2. UPDATE products SET quantity = 4 (10 - 6)
    Backend->>DB: 3. INSERT INTO stock_history (type: 'SALE', change: -6, resulting: 4)
    Backend->>DB: Commit Transaction
    
    Backend->>Backend: Evaluate: New Qty (4) <= Min Level (5) AND Notified == FALSE? (TRUE)
    
    Backend->>SNS: Publish Message: "WARNING: Product 'Milk' has dropped to 4 units!"
    SNS-->>Email: Immediate Email Alert Delivered to Owner
    Backend->>DB: UPDATE products SET is_low_stock_notified = TRUE
    
    Note over Backend,DB: When another sale happens (e.g. 1 unit, remaining 3):\nNotified is already TRUE -> Duplicate alert is suppressed!

    Note over Backend,DB: When Owner RESTOCKS (+20 units, new qty 23 > 5):\nBackend automatically RESETS is_low_stock_notified = FALSE!

    Backend-->>POS: HTTP 200 OK (Sale completed + warning badge)
    POS-->>Cashier: Show success toast and low-stock warning
```

---

## 📁 5. Project Directory Structure

```text
/Users/ammu/Cloud_project
├── .github/
│   └── workflows/
│       └── ci-cd.yml             # GitHub Actions CI/CD Pipeline (Test & SSM Deploy)
├── app/                          # Core Flask Application
│   ├── __init__.py               # Application factory, DB init, Prometheus metrics hook
│   ├── config.py                 # Environments (Development, Testing, Production)
│   ├── models.py                 # SQLAlchemy models (User, Product, Sale, StockHistory)
│   ├── routes.py                 # HTTP routes (Auth, Products, Sales, History, /health)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sns_service.py        # Amazon SNS Boto3 notification client
│   │   └── stock_service.py      # Business logic: Sales deduction, restock & low stock check
│   ├── static/
│   │   ├── css/style.css         # Modern, custom CSS design system
│   │   └── js/
│   │       ├── main.js           # Modal handlers & live sales checkout auto-calculator
│   │       └── search_filter.js  # Instant client-side search & category filtering
│   └── templates/                # Bootstrap 5 Jinja2 Templates
│       ├── base.html             # Common layout, responsive navbar, flash alerts
│       ├── login.html            # Authentication page with demo credentials
│       ├── dashboard.html        # Telemetry cards, low-stock table, recent sales
│       ├── products.html         # Product catalog CRUD (Add, Edit, Restock, Delete)
│       ├── sales.html            # POS interface with live price calculation
│       └── stock_history.html    # Full immutable movement audit log
├── cloudformation/
│   └── master-stack.yaml         # Complete CloudFormation template (20 AWS Resources)
├── database/
│   ├── schema.sql                # MySQL 8.0 DDL script (tables, foreign keys, constraints)
│   └── seed_data.sql             # Starter seed data (admin user, sample products, sales)
├── docs/
│   ├── viva_interview_prep.md    # Technical interview questions, answers & architecture defense
│   └── troubleshooting_guide.md  # Detailed troubleshooting solutions
├── lambda/
│   └── low_stock_processor.py    # Serverless daily stock scanner & digest alert function
├── monitoring/
│   ├── prometheus.yml            # Prometheus scrape configuration
│   ├── alerts.yml                # Prometheus alert rules (CPU, RAM, Disk, 5xx errors)
│   ├── docker-compose.yml        # One-click containerized Prometheus + Grafana stack
│   └── grafana/
│       └── dashboard.json        # Pre-built 8-panel Grafana dashboard JSON
├── scripts/
│   ├── setup_local.sh            # One-click local setup, seeding, and pytest execution
│   ├── setup_ec2.sh              # EC2 UserData / bootstrap automation script
│   ├── inventory.service         # Systemd unit file for Gunicorn production server
│   ├── nginx_inventory.conf      # Production Nginx reverse proxy configuration
│   ├── init_db.py                # Database initializer & seeder utility
│   ├── test_sns_alert.py         # Amazon SNS alert testing utility
│   ├── ssm_run_maintenance.sh    # Remote administration utility via AWS Systems Manager
│   └── cleanup_aws.sh            # Safe teardown script to prevent unwanted AWS charges
├── tests/                        # Automated Pytest Suite (19 Tests)
│   ├── conftest.py               # Fixtures for in-memory SQLite and auth clients
│   ├── test_auth.py              # 6 Authentication & session tests
│   ├── test_inventory.py         # 6 Product CRUD and restock tests
│   ├── test_sales.py             # 5 Sales, stock deduction & low-stock trigger tests
│   └── test_health.py            # 2 Deployment health check & Prometheus metric tests
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore file (prevents secret leaks)
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Production Python dependencies
├── requirements-dev.txt          # Development & test dependencies
├── wsgi.py                       # WSGI entrypoint for Gunicorn
└── README.md                     # Comprehensive project documentation
```

---

## 💻 6. Local Quickstart (Zero Cloud Dependencies)

You can run the entire application and test suite locally on your computer with a single command:

```bash
# 1. Run the automated local setup script
./scripts/setup_local.sh
```

### Manual Step-by-Step Local Setup:
```bash
# 1. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt

# 3. Initialize SQLite database and seed starter products
python scripts/init_db.py

# 4. Run automated test suite (19 tests)
pytest -v

# 5. Start the web application
# (Port 5050 is recommended on macOS to avoid Apple's AirPlay Receiver conflict on 5000)
PORT=5050 python wsgi.py
```

* Open your browser at: **`http://localhost:5050`**
* Log in with:
  * **Username:** `admin`
  * **Password:** `admin123`

---

## 🧪 7. Automated Testing Suite

The project includes **19 automated unit & integration tests** achieving **85% code coverage**:

```bash
# Run all tests
pytest -v

# Run with test coverage report
pytest --cov=app tests/
```

### Test Suite Breakdown:
1. **`tests/test_auth.py` (6 Tests):**
   * Login page rendering.
   * Valid login redirects to dashboard.
   * Invalid password rejection.
   * Nonexistent user rejection.
   * Unauthenticated redirect protection on protected routes.
   * Logout session invalidation.
2. **`tests/test_inventory.py` (6 Tests):**
   * Product catalog rendering.
   * Adding new product and initial audit history entry.
   * Rejecting duplicate SKUs.
   * Editing product details and minimum threshold.
   * Restocking items, quantity balance calculation, and notification flag reset.
   * Product deletion with foreign key cascading.
3. **`tests/test_sales.py` (5 Tests):**
   * POS sales page rendering with in-stock dropdown.
   * Valid customer purchase, pricing multiplication, and stock reduction.
   * Rejecting purchase when requested quantity exceeds available stock.
   * **Low-stock detection:** triggers alert when remaining stock $\le$ threshold.
   * **Anti-duplicate protection:** suppresses subsequent alerts for already low-stock items.
4. **`tests/test_health.py` (2 Tests):**
   * System `/health` endpoint returning JSON status.
   * Prometheus `/metrics` telemetry scrape endpoint.

---

## 🚀 8. AWS Cloud Deployment (Production)

### Method A: One-Command CloudFormation Deployment (Recommended)
Deploy the full VPC, RDS MySQL, EC2, SNS, and IAM stack with AWS CLI:

```bash
aws cloudformation create-stack \
    --stack-name small-shop-inventory-stack \
    --template-body file://cloudformation/master-stack.yaml \
    --parameters \
        ParameterKey=EnvironmentName,ParameterValue=production \
        ParameterKey=InstanceType,ParameterValue=t2.micro \
        ParameterKey=AlertEmail,ParameterValue=your-email@example.com \
        ParameterKey=DBMasterUsername,ParameterValue=admin \
        ParameterKey=DBMasterPassword,ParameterValue="ShopAdminPass123!" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1
```

### View Stack Outputs Once Complete:
```bash
aws cloudformation describe-stacks \
    --stack-name small-shop-inventory-stack \
    --query "Stacks[0].Outputs" \
    --output table
```

---

## 🔐 9. AWS Systems Manager (SSM) Zero-SSH Server Administration

Our EC2 instance has **Port 22 (SSH) completely closed**. Manage the instance securely using the provided administration utility:

```bash
# 1. Check live Gunicorn, Nginx, and resource status remotely
./scripts/ssm_run_maintenance.sh <EC2_INSTANCE_ID> status

# 2. Restart services remotely
./scripts/ssm_run_maintenance.sh <EC2_INSTANCE_ID> restart

# 3. Tail latest application error logs
./scripts/ssm_run_maintenance.sh <EC2_INSTANCE_ID> logs

# 4. Open an encrypted terminal shell in your terminal (No SSH key needed)
./scripts/ssm_run_maintenance.sh <EC2_INSTANCE_ID> shell
```

---

## 🔄 10. GitHub Actions CI/CD Pipeline Setup

Configure these 4 secrets in your GitHub repository (**Settings $\rightarrow$ Secrets and variables $\rightarrow$ Actions**):

| Secret Name | Value | Purpose |
| :--- | :--- | :--- |
| `AWS_ACCESS_KEY_ID` | `AKIAIOSFODNN7EXAMPLE` | IAM deployment user access key. |
| `AWS_SECRET_ACCESS_KEY` | `wJalrXUtnFEMI/K7MDENG/bPxRfiCY...` | IAM deployment user secret key. |
| `AWS_REGION` | `us-east-1` | AWS deployment region. |
| `EC2_INSTANCE_ID` | `i-0123456789abcdef0` | EC2 web server instance ID. |

Whenever code is pushed to `main`:
1. GitHub Actions runs **Flake8 linting** and **all 19 Pytests**.
2. If tests pass, it calls **AWS SSM Run Command** to pull the latest code on EC2, updates virtualenv dependencies, applies database migrations, restarts Gunicorn and Nginx, and verifies `/health`.

---

## 📊 11. Prometheus and Grafana Observability Stack

Launch the containerized observability stack:
```bash
docker compose -f monitoring/docker-compose.yml up -d
```

1. **Prometheus UI:** Open `http://localhost:9090` $\rightarrow$ Check **Status $\rightarrow$ Targets** (Node Exporter & Flask app should be `UP`).
2. **Grafana UI:** Open `http://localhost:3000` (Login: `admin` / `admin`).
3. **Import Pre-configured Dashboard:**
   * Go to **Dashboards $\rightarrow$ New $\rightarrow$ Import**.
   * Upload `monitoring/grafana/dashboard.json`.
   * Observe real-time **CPU Utilization, Memory Consumed, Disk Usage, Requests per Second (RPS), and Latencies**.

---

## 🧹 12. Safe AWS Teardown (Prevent Unwanted Bills)

When finished testing or presenting your demonstration, terminate all AWS resources cleanly:

```bash
./scripts/cleanup_aws.sh
```
*This command invokes CloudFormation to terminate EC2, delete the RDS MySQL database, and remove VPC networking automatically.*

---

## 📖 13. Additional Documentation
* 🎓 [Technical Interview & College Viva Preparation Guide](docs/viva_interview_prep.md)
* 🛠️ [Troubleshooting & Common Gotchas Guide](docs/troubleshooting_guide.md)
