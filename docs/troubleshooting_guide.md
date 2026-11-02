# Troubleshooting & Diagnostics Guide
## Small Shop Inventory Management System

This guide covers common issues, root causes, and verified fixes across local development, AWS cloud infrastructure, and CI/CD pipelines.

---

## 🛠️ 1. Local Development Issues

### Issue 1: `Address already in use: Port 5000` (macOS)
* **Symptom:** Starting `python wsgi.py` fails with `OSError: [Errno 48] Address already in use`.
* **Root Cause:** macOS Monterey and newer utilize Port 5000 for Apple's built-in **AirPlay Receiver**.
* **Fix (Option A - Recommended):** Specify an alternate port:
  ```bash
  PORT=5050 python wsgi.py
  ```
* **Fix (Option B):** Turn off AirPlay Receiver in macOS:
  * Open **System Settings** $\rightarrow$ **General** $\rightarrow$ **AirDrop & Handoff**.
  * Toggle **AirPlay Receiver** to **Off**.

---

### Issue 2: `ModuleNotFoundError: No module named 'app'` when running Pytest
* **Symptom:** Running `pytest` gives an import error.
* **Root Cause:** Current working directory is not in `PYTHONPATH`.
* **Fix:** The provided [pytest.ini](file:///Users/ammu/Cloud_project/pytest.ini) automatically resolves this. If running manually, set:
  ```bash
  PYTHONPATH=. pytest -v
  ```

---

## ☁️ 2. AWS EC2 & Systems Manager (SSM) Issues

### Issue 3: SSM Session Manager shows `"Target Not Connected"`
* **Symptom:** The EC2 console shows the Session Manager Connect button greyed out, or states the target is offline.
* **Root Causes & Fixes:**
  1. **IAM Role Missing:** Ensure the EC2 instance has an IAM Role attached with the managed policy:
     `arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore`
  2. **SSM Agent Inactive:** If you have terminal access, verify the agent status:
     ```bash
     sudo systemctl status snap.amazon-ssm-agent.amazon-ssm-agent
     sudo systemctl restart snap.amazon-ssm-agent.amazon-ssm-agent
     ```
  3. **Outbound Internet Blocked:** The EC2 instance must be able to reach AWS SSM endpoints over HTTPS Port 443. Ensure the Public Subnet route table has a route: `0.0.0.0/0` $\rightarrow$ `Internet Gateway`.

---

### Issue 4: Nginx returns `502 Bad Gateway`
* **Symptom:** Opening `http://<EC2-PUBLIC-IP>` displays an Nginx 502 error page.
* **Root Cause:** Gunicorn WSGI server is stopped or crashed upon starting.
* **Fix:**
  1. Check Gunicorn systemd service status:
     ```bash
     sudo systemctl status inventory --no-pager -l
     ```
  2. Inspect Gunicorn error logs:
     ```bash
     sudo tail -n 50 /var/log/inventory/error.log
     ```
  3. Verify that `/opt/inventory-system/.env` has valid MySQL credentials and permissions:
     ```bash
     sudo chown -R ubuntu:www-data /opt/inventory-system
     sudo systemctl restart inventory
     ```

---

## 🗄️ 3. Amazon RDS Database Connectivity

### Issue 5: `Can't connect to MySQL server on '...rds.amazonaws.com' (110)`
* **Symptom:** Application reports database timeout or connection failure.
* **Root Causes & Fixes:**
  1. **Security Group Rule Missing:** Ensure `inventory-db-sg` allows Inbound Port 3306 with Source set to the **Security Group ID** of `inventory-web-sg`.
  2. **RDS Still Initializing:** Amazon RDS MySQL takes 5–8 minutes to spin up. Verify that the RDS status in the AWS Console is **Available**.
  3. **Test Connection directly from EC2:**
     ```bash
     mysql -h <RDS-ENDPOINT> -u admin -p inventory_db
     ```

---

## 🔔 4. Amazon SNS Notifications

### Issue 6: Low-Stock Email Alert is Not Delivered
* **Symptom:** Low stock is triggered in the app, but no email arrives in the inbox.
* **Root Causes & Fixes:**
  1. **Subscription Not Confirmed:** Check your email spam folder for the AWS Confirmation email. In the AWS SNS Console, verify the subscription status is **Confirmed** (not `PendingConfirmation`).
  2. **Topic ARN Mismatch:** Verify that `SNS_TOPIC_ARN` in `/opt/inventory-system/.env` matches your actual Topic ARN.
  3. **IAM Permissions:** Verify that the EC2 IAM Role has `sns:Publish` permissions on the topic ARN.
  4. **Run the Standalone Verification Tool:**
     ```bash
     python3 scripts/test_sns_alert.py
     ```

---

## 🚀 5. GitHub Actions CI/CD Pipeline

### Issue 7: `cd-deploy` job fails with `AccessDeniedException` on `ssm:SendCommand`
* **Symptom:** GitHub Actions CI passes, but deployment fails at `aws ssm send-command`.
* **Root Cause:** The IAM User credentials stored in GitHub Secrets (`AWS_ACCESS_KEY_ID`) lack permission to execute commands on EC2 via SSM.
* **Fix:** Ensure the IAM user has this policy attached:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ssm:SendCommand"
        ],
        "Resource": [
          "arn:aws:ssm:*:*:document/AWS-RunShellScript",
          "arn:aws:ec2:*:*:instance/*"
        ]
      },
      {
        "Effect": "Allow",
        "Action": [
          "ssm:GetCommandInvocation",
          "ssm:ListCommandInvocations"
        ],
        "Resource": "*"
      }
    ]
  }
  ```
