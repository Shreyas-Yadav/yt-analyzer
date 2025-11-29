# YT-Analyzer Deployment Summary

## Architecture Overview
- **Frontend**: React (SPA) hosted on **AWS S3** (Static Website Hosting).
- **CDN/DNS/SSL**: **Cloudflare** (Proxies S3, provides HTTPS).
- **Backend API**: **AWS Lambda** (Python/FastAPI) via API Gateway.
- **Worker**: **AWS EC2** (t2.micro/t3.medium) polling **SQS**.
- **Database**: **AWS RDS** (MySQL) in Private Subnet.
- **Storage**: **AWS S3** for video/audio/transcripts.

---

## 1. Prerequisites
- **AWS Account**: Access to S3, Lambda, EC2, RDS, SQS, IAM.
- **Domain Name**: Purchased (e.g., Name.com).
- **Cloudflare Account**: Free plan.

---

## 2. Backend Deployment (API & Database)
### Database (RDS)
1.  Create **MySQL RDS** instance (Free Tier).
2.  Place in **Private Subnet** (Security Group: Allow Port 3306 from Lambda/Worker).
3.  **Migration**: Use `mysqldump` to migrate local DB to RDS.

### API (Lambda)
1.  **Code**: `backend/` directory.
2.  **Build**: Docker image or Zip package (exclude heavy libs like `ffmpeg`).
3.  **Env Vars**: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `SQS_QUEUE_URL`.
4.  **VPC**: Connect Lambda to the same VPC as RDS.

### Worker (EC2)
1.  **Instance**:
    -   **Dev/Testing**: `t2.micro` (Free Tier) or `t3.medium`.
    -   **Production (Recommended)**: `g4dn.xlarge` (GPU). Whisper is heavily optimized for CUDA; processing will be significantly faster (seconds vs minutes).
2.  **OS**: Ubuntu 22.04 (Use Deep Learning AMI if using GPU).
3.  **Setup Script**: Use `backend/deploy_worker.sh`.
    -   Installs `ffmpeg`, `python3`, `uv`.
    -   Clones repo & installs dependencies.
4.  **Optimization (CPU Only)**:
    -   Use **`faster-whisper`** instead of `openai-whisper` for 4x speed & low RAM.
    -   Add **2GB Swap File** if using `t2.micro` (1GB RAM) to prevent freezing.

---

## 3. Frontend Deployment (S3 + Cloudflare)
**Critical Requirement**: S3 Bucket Name **MUST** match your Domain Name (e.g., `shri.software`).

### Step A: AWS S3 Setup
1.  **Create Bucket**: Name it exactly `shri.software`.
2.  **Permissions**: Uncheck "Block all public access".
3.  **Hosting**: Enable **Static Website Hosting**.
    -   **Index Document**: `index.html`
    -   **Error Document**: `index.html` (**CRITICAL** for React Router/SPA).
4.  **Policy**: Add Bucket Policy for Public Read Access (`s3:GetObject`).
5.  **Upload**:
    ```bash
    npm run build
    aws s3 sync dist s3://shri.software
    ```

### Step B: Cloudflare Setup (HTTPS)
1.  **Nameservers**: Update your Domain Registrar (Name.com) to use Cloudflare's NS.
2.  **DNS Records**:
    -   **CNAME** `@` -> `shri.software.s3-website-us-east-1.amazonaws.com` (Proxied).
    -   **CNAME** `www` -> `shri.software.s3-website-us-east-1.amazonaws.com` (Proxied).
3.  **SSL/TLS Settings** (**CRITICAL**):
    -   **Mode**: **Flexible** (Because S3 Website is HTTP-only).
    -   **Edge Certificates**: Enable **Always Use HTTPS**.
4.  **Caching**: Purge Cache after every new deployment.

---

## 4. Authentication (Cognito + Google OAuth)
1.  **Callback URLs**: Must be HTTPS (e.g., `https://shri.software/auth/callback`).
2.  **Sign-out URLs**: `https://shri.software/login`.
3.  **Frontend Config**:
    -   Update `.env.production` (NOT just `.env`).
    -   `VITE_OAUTH_REDIRECT_SIGN_IN=https://shri.software/auth/callback`
    -   `VITE_OAUTH_REDIRECT_SIGN_OUT=https://shri.software/login`

---

## 5. Troubleshooting
-   **404 on Refresh**: You forgot to set **Error Document** to `index.html` in S3.
-   **522 Error**: You set Cloudflare SSL to **Full** instead of **Flexible**.
-   **Redirect Mismatch**: You didn't update `.env.production` or didn't purge Cloudflare cache.
-   **Worker Freezing**: You need Swap Space or `faster-whisper`.

---

## 6. Security (DDoS & Bot Protection)
-   **Frontend**: Integrated **Cloudflare Turnstile** (Smart CAPTCHA) on Login/Signup.
    -   Key is in `.env.production`.
-   **Infrastructure**: Enabled **Cloudflare Bot Fight Mode**.
    -   Blocks automated scrapers and malicious bots at the edge.
