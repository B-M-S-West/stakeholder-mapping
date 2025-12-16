# AWS Deployment Guide

This guide details how to deploy the Stakeholder Mapping application to AWS. Because this application uses embedded databases (SQLite and Kuzu) rather than a separate database server, this guide uses **Amazon EC2** with a Docker volume mount. This ensures your data persists between deployments and restarts.

## Prerequisites

1.  **AWS Account** with permissions to manage EC2 and ECR.
2.  **AWS CLI** installed and configured locally (`aws configure`).
3.  **Docker** installed locally.

## Step 1: Create a Repository in AWS ECR

Amazon Elastic Container Registry (ECR) is where we will store your Docker image.

1.  Log in to the AWS Console and search for **ECR**.
2.  Click **Create repository**.
3.  Name it `stakeholder-mapping` and ensure "Private" is selected.
4.  Click **Create repository**.
5.  Select the repository you just created and click **View push commands**. Keep this window open.

## Step 2: Build and Push the Image

Run the following commands in your local terminal (replace `<aws_account_id>` and `<region>` with values from the "View push commands" window):

1.  **Login to ECR:**
    ```bash
    aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
    ```

2.  **Build the Docker image:**
    ```bash
    docker buildx build -t stakeholder-mapping --load .
    ```

3.  **Tag the image:**
    ```bash
    docker tag stakeholder-mapping:latest <aws_account_id>.dkr.ecr.<region>[.amazonaws.com/stakeholder-mapping:latest]
    ```

4.  **Push to AWS:**
    ```bash
    docker push <aws_account_id>.dkr.ecr.<region>[.amazonaws.com/stakeholder-mapping:latest]
    ```

## Step 3: Launch an EC2 Instance

1.  Go to the **EC2 Dashboard** in AWS and click **Launch Instance**.
2.  **Name:** `Stakeholder-App-Server`
3.  **OS Image:** Amazon Linux 2023 AMI (Free tier eligible).
4.  **Instance Type:** `t2.micro` (or `t3.small` for better performance).
5.  **Key Pair:** Create a new key pair (save the `.pem` file) or use an existing one.
6.  **Network Settings (Security Group):**
    * Allow SSH traffic from **My IP**.
    * Allow Custom TCP traffic on port **8501** from **Anywhere** (0.0.0.0/0).
7.  Click **Launch Instance**.

## Step 4: Configure the Server

1.  SSH into your instance:
    ```bash
    ssh -i "your-key.pem" ec2-user@<your-ec2-public-ip>
    ```

2.  Install Docker on the server:
    ```bash
    sudo dnf update -y
    sudo dnf install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ec2-user
    ```

3.  **Log out and log back in** for the group changes to take effect.

4.  Authenticate Docker with ECR (run this *inside* the EC2 instance):
    * *Note: If this fails, run `aws configure` on the server or attach an IAM Role to the EC2 instance with `AmazonEC2ContainerRegistryReadOnly` permissions.*
    ```bash
    aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
    ```

## Step 5: Secure Password Setup (AWS SSM)

Instead of hardcoding passwords, we will store the app password in AWS Systems Manager (SSM) Parameter Store.

1. **Store the password** (Run this on your local machine):
    ```bash
    aws ssm put-parameter \
    --name "/stakeholder-app/TESTING_PASSWORD" \
    --value "YOUR_SECURE_PASSWORD_HERE" \
    --type "SecureString" \
    --region <region>
    ```

## Step 6: Run the Application

We will run the container and mount a volume. This maps a folder on the EC2 server (`~/app_data`) to the folder inside the container where the app saves data (`/app/data`).

1.  Create a directory for your data:
    ```bash
    mkdir -p ~/app_data
    ```

2. Fetch Password from SSM: Retrieve the password into a shell variable.
    ```bash
    PASSWORD=$(aws ssm get-parameter --name "/stakeholder-app/TESTING_PASSWORD" --with-decryption --query "Parameter.Value" --output text)
    ```

3.  Run the container:
    ```bash
    docker run -d --restart always \
      --name stakeholder-app \
      -p 8501:8501 \
      -v /home/ec2-user/app_data:/app/data \
      -e TESTING_PASSWORD="$PASSWORD" \
      <aws_account_id>.dkr.ecr.<region>[.amazonaws.com/stakeholder-mapping:latest]
    ```

    * `-d`: Runs in background (detached).
    * `-p 8501:8501`: Maps the Streamlit port.
    * `-v ...`: Maps the local `~/app_data` folder to the container's `/app/data` folder (as defined in `config.py`). **This ensures your database persists even if you stop the container.**
    * `-e ...`: Sets the required password environment variable checked in `app.py`.

## Step 6: Access the App

Open your browser and navigate to:
`http://<your-ec2-public-ip>:8501`



