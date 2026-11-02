# College Viva & Technical Interview Preparation Guide
## Small Shop Inventory Management System (AWS & DevOps)

---

## 🎤 1. The 2-Minute Architectural Pitch (Elevator Pitch)

> *"Good morning/afternoon, Sir/Madam.*
>
> *I have developed the **Small Shop Inventory Management System**, a cloud-native web application integrated with **AWS Cloud** and modern **DevOps automation**.*
>
> *Small retail shop owners traditionally track their inventory manually in notebooks, only discovering stock shortages when a customer asks for a product. My project solves this by offering real-time stock tracking, automated stock deduction on sales, custom minimum stock alert thresholds, and instant email notifications powered by **Amazon SNS**.*
>
> *From a DevOps perspective, the entire infrastructure is declared as code using **AWS CloudFormation**, provisioning a custom VPC, an **Amazon RDS MySQL** database in private subnets, and an **Amazon EC2** web server running Nginx and Gunicorn.*
>
> *To adhere to enterprise security best practices, **Port 22 (SSH) is completely closed**. Server administration and CI/CD deployments from **GitHub Actions** are executed securely through **AWS Systems Manager (SSM)** without storing SSH private keys.*
>
> *Finally, system health and application performance are monitored in real time using **Prometheus, Node Exporter, and Grafana**, ensuring 99.9% availability and full operational visibility."*

---

## 💡 2. Top 15 Technical Interview Questions & Model Answers

### Q1: Why did you close Port 22 (SSH), and how do you access the server?
**Model Answer:**
> *"Leaving Port 22 open to the internet exposes the instance to brute-force attacks, port scanning, and requires managing static `.pem` private keys. If a private key is leaked, the server is compromised.*
>
> *Instead, I implemented **AWS Systems Manager (SSM) Session Manager**. The SSM Agent on EC2 initiates an encrypted, outbound HTTPS connection over Port 443 to the AWS Systems Manager endpoint. I can open an authenticated shell directly in the AWS Console or local CLI using temporary IAM credentials, with complete audit logging in CloudTrail."*

---

### Q2: How does your system prevent duplicate email alerts (notification storms)?
**Model Answer:**
> *"In beginner projects, every time an out-of-stock product is viewed or sold repeatedly, the system spams the owner with dozens of emails.*
>
> *To prevent this, I added a boolean flag `is_low_stock_notified` to the `products` table. When a sale causes stock to drop $\le$ `min_stock_level`:*
> * *If `is_low_stock_notified` is `False`, the backend publishes the Amazon SNS email and updates `is_low_stock_notified = True`.*
> * *Subsequent sales suppress email notifications.*
> * *When the owner restocks the product above the minimum threshold, the flag automatically resets to `False` so future shortages will trigger alerts again."*

---

### Q3: Why did you place Amazon RDS in private subnets and EC2 in a public subnet?
**Model Answer:**
> *"This implements the **3-Tier Defense-in-Depth Network Architecture**.*
> * *The EC2 web server needs to receive HTTP traffic from customers, so it resides in a Public Subnet with an Internet Gateway.*
> * *The Amazon RDS MySQL database stores critical financial and business records. It has `PubliclyAccessible: false` and is placed in Private Subnets across two Availability Zones.*
> * *Its Security Group restricts inbound traffic on Port 3306 strictly to the EC2 Web Security Group ID. No external entity on the internet can connect directly to the database."*

---

### Q4: Why use Nginx and Gunicorn together instead of running Flask directly?
**Model Answer:**
> *"Flask's built-in development server is single-threaded and not designed for production security, high concurrency, or performance.*
> * ***Gunicorn** is a production WSGI HTTP server that forks multiple worker processes to handle concurrent Python requests.*
> * ***Nginx** serves as a reverse proxy sitting in front of Gunicorn. It handles SSL termination, buffers slow clients, enables gzip compression, applies security headers, and serves static files (`/static/`) directly from the filesystem without touching Python, reducing server load."*

---

### Q5: How does your GitHub Actions CI/CD pipeline deploy without SSH keys?
**Model Answer:**
> *"In our `.github/workflows/ci-cd.yml` workflow:*
> 1. *The **CI stage** runs on `ubuntu-latest`, installing dependencies and executing all 19 Pytests with Flake8 linting.*
> 2. *If all tests pass, the **CD stage** uses `aws-actions/configure-aws-credentials` with IAM credentials stored in GitHub Secrets.*
> 3. *It invokes the `aws ssm send-command` API using the `AWS-RunShellScript` document targeting our EC2 Instance ID.*
> 4. *The SSM Agent on the instance pulls the latest commit, runs migrations, restarts Gunicorn and Nginx, and verifies the `/health` endpoint.*
> 5. *GitHub Actions polls the command invocation until exit code 0 is confirmed."*

---

### Q6: What happens if an automated test fails during the CI pipeline?
**Model Answer:**
> *"GitHub Actions immediately marks the `ci-test` job as failed. Because the `cd-deploy` job specifies `needs: ci-test`, the deployment stage is automatically blocked and will never execute. This guarantees that broken code or regression bugs are never deployed to production."*

---

### Q7: How is ACID compliance maintained during concurrent customer purchases?
**Model Answer:**
> *"In `app/services/stock_service.py`, sales processing is wrapped in an atomic database transaction using SQLAlchemy:*
> 1. *It checks that available stock $\ge$ requested quantity.*
> 2. *It writes the sale record, updates the product stock balance, and inserts an audit log into `stock_history` within the same transaction.*
> 3. *If any step fails or an unexpected error occurs, `db.session.rollback()` cancels all changes, guaranteeing that stock balances and financial records never go out of sync."*

---

### Q8: How does Boto3 authenticate with AWS when running on EC2?
**Model Answer:**
> *"Instead of hardcoding `AWS_ACCESS_KEY_ID` or saving credentials in a configuration file on the server, I attached an **IAM Instance Profile** (`inventory-ec2-ssm-role`) to the EC2 instance.*
>
> *When Boto3 initializes, it automatically queries the **EC2 Instance Metadata Service (IMDSv2)** at `http://169.254.169.254/latest/meta-data/iam/` to retrieve temporary security credentials that rotate automatically, adhering to AWS security best practices."*

---

### Q9: What is the purpose of the `/health` endpoint?
**Model Answer:**
> *"The `/health` endpoint acts as an active telemetry probe. It returns a JSON object verifying that both the web service and the MySQL database connection are operational (`SELECT 1`).*
>
> *It is used by:*
> * *AWS Application Load Balancers for target group health checks.*
> * *GitHub Actions CI/CD to verify successful deployment before concluding.*
> * *Prometheus and uptime monitors to alert if the service degrades."*

---

### Q10: What metrics do Prometheus and Node Exporter collect?
**Model Answer:**
> * ***Node Exporter (:9100):** Gathers host infrastructure telemetry: CPU idle/system percentage, memory available vs. total, disk space consumption, and network I/O.*
> * ***Flask Metrics (:5000/metrics):** Gathers application-level telemetry: HTTP request throughput (RPS), endpoint distribution, response duration (latency in ms), and HTTP status code counts (200, 400, 500).*
> * ***Grafana (:3000):** Queries Prometheus using PromQL and visualizes these metrics on an 8-panel dashboard."*

---

### Q11: Why use CloudFormation (IaC) instead of creating resources manually in the AWS Console?
**Model Answer:**
> *"Manual creation in the AWS Console is prone to human error, configuration drift, and cannot be version-controlled.*
>
> *With our CloudFormation template (`cloudformation/master-stack.yaml`), all 20 AWS resources are declared in YAML. We can spin up an identical staging or production environment in any AWS region in 8 minutes, and tear it down cleanly with `cleanup_aws.sh` to avoid unexpected costs."*

---

### Q12: How would you scale this application to handle 100,000 daily users?
**Model Answer:**
> *"To scale this architecture:*
> 1. ***Compute Tier:** Place the EC2 instance inside an **Auto Scaling Group (ASG)** behind an **Application Load Balancer (ALB)** spanning multiple Availability Zones.*
> 2. ***Database Tier:** Enable **Amazon RDS Multi-AZ** for high availability and add **Read Replicas** to offload read-heavy product catalog queries.*
> 3. ***Caching Tier:** Introduce an **Amazon ElastiCache (Redis)** cluster to cache frequently viewed product listings and user sessions.*
> 4. ***Static Content:** Serve CSS, JS, and product images through **Amazon CloudFront (CDN)** backed by **Amazon S3**."*

---

## 🎬 3. Live Demonstration Script for Examiners / Viva

Follow this sequence during your live project presentation:

| Step | Action | What to Explain to the Examiner |
| :---: | :--- | :--- |
| **1** | Open Web Application in Browser | Show the clean Bootstrap 5 dashboard, active AWS badges, and KPI metric cards. |
| **2** | Show Catalog & Filtering | Search for a product (e.g. `Milk`) and demonstrate instant client-side filtering by category and stock status. |
| **3** | Demonstrate Low-Stock Alert | Go to POS Sales, sell enough units of a product to drop its stock below the minimum threshold. |
| **4** | Show Live Email Delivery | Open your email inbox and show the immediate Amazon SNS alert: `⚠️ [AWS ALERT] Low Stock Warning`. |
| **5** | Demonstrate Anti-Duplicate | Sell 1 more unit. Show that the sale completes, but no duplicate email is spammed. |
| **6** | Demonstrate Restock | Click Restock, add 20 units. Show that the product returns to healthy status and the alert flag resets. |
| **7** | Show Audit Log (`stock-history`) | Show the immutable audit trail displaying `INITIAL`, `SALE` (-6), and `RESTOCK` (+20). |
| **8** | Show GitHub Actions Pipeline | Open GitHub $\rightarrow$ Actions. Show the green CI (19 Pytests) and CD (SSM Run Command) logs. |
| **9** | Show Grafana Observability | Open Grafana (`:3000`). Show the real-time CPU gauge, RAM utilization, and request throughput graphs. |
| **10** | Show CloudFormation Code | Open `cloudformation/master-stack.yaml` and explain the 20 resources declared as code. |
