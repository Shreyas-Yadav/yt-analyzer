# YT-Analyzer System Architecture

## 1. High-Level Overview
**YT-Analyzer** is a cloud-native Single Page Application (SPA) designed to download, transcribe, and analyze YouTube videos using AI. It leverages a serverless-first approach for the API and a dedicated compute instance for heavy AI processing.

### Core Components
1.  **Frontend**: React-based SPA hosted on S3 + Cloudflare.
2.  **Authentication**: Managed by AWS Cognito (User Pools + Google OAuth).
3.  **API Layer**: Serverless AWS Lambda functions exposed via API Gateway.
4.  **Async Worker**: EC2 instance (GPU-optimized) for video processing and AI transcription (Whisper).
5.  **Data Persistence**: AWS RDS (MySQL) for relational data and S3 for object storage.

---

## 2. AWS Infrastructure Architecture

```mermaid
flowchart TD
    %% Styling
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:white;
    classDef db fill:#3355DA,stroke:#232F3E,stroke-width:2px,color:white;
    classDef ext fill:#f9f9f9,stroke:#333,stroke-width:2px;

    User[User Browser] -->|HTTPS| CF
    
    subgraph Edge_Network [Edge Network]
        direction TB
        CF{Cloudflare}
        CF -->|Static Assets| S3_Web[S3 Bucket: shri.software]
        CF -->|API Calls| APIG[API Gateway]
    end

    subgraph AWS_Cloud [AWS Region: us-east-1]
        direction TB
        
        subgraph IAM_Auth [Authentication]
            Cognito[AWS Cognito User Pool]:::aws
        end

        APIG -->|Auth Token| Cognito
        APIG -->|Proxy| Lambda[Lambda Function: FastAPI]:::aws

        subgraph VPC [Custom VPC]
            direction TB
            
            subgraph Public_Subnet [Public Subnet]
                NAT[NAT Gateway]:::aws
                IGW[Internet Gateway]:::aws
            end
            
            subgraph Private_Subnet [Private Subnet]
                Lambda
                RDS[(RDS MySQL: db.t3.micro)]:::db
                EC2[EC2 Worker: g4dn.xlarge]:::aws
            end
        end

        %% Data Flow
        Lambda -->|Read/Write| RDS
        Lambda -->|Queue Job| SQS[SQS Queue]:::aws
        
        EC2 -->|Poll Messages| SQS
        EC2 -->|Update Status| RDS
        EC2 -->|Download/Upload| S3_Data[S3 Bucket: Data Storage]:::aws
        
        %% Network Flow
        EC2 -.->|Outbound Traffic| NAT
        NAT -.->|Internet| IGW
    end
```

---

## 3. Component Breakdown

### A. Frontend (Presentation Layer)
-   **Tech Stack**: React, Vite, TailwindCSS.
-   **Hosting**: AWS S3 (Static Website Hosting).
-   **Delivery**: Cloudflare CDN (caches content at the edge).
-   **Security**:
    -   **SSL/TLS**: Flexible Mode (Cloudflare terminates HTTPS).
    -   **Bot Protection**: Cloudflare Turnstile (Smart CAPTCHA) on Login/Signup.
    -   **DDoS**: Cloudflare Bot Fight Mode.

### B. Backend API (Control Plane)
-   **Tech Stack**: Python, FastAPI, Mangum (Adapter).
-   **Compute**: AWS Lambda (Serverless).
-   **Role**: Handles user requests, authentication, CRUD operations, and job queuing.
-   **Networking**: Runs in a **Private Subnet** to access RDS securely.

### C. Asynchronous Worker (Data Plane)
-   **Tech Stack**: Python, `yt-dlp`, `faster-whisper`, `ffmpeg`.
-   **Compute**: AWS EC2 (`g4dn.xlarge` recommended for Production).
-   **Role**:
    1.  Polls SQS for new video jobs.
    2.  Downloads video/audio using `yt-dlp`.
    3.  Transcribes audio using OpenAI Whisper (AI).
    4.  Generates Flashcards/Quizzes using LLMs (Claude/GPT).
    5.  Uploads results to S3 and updates RDS.

### D. Database & Storage
-   **Relational DB**: AWS RDS (MySQL). Stores Users, Videos, Transcripts metadata.
-   **Object Storage**: AWS S3. Stores raw audio files, transcript text files, and generated JSON assets.

---

## 4. Security Architecture
1.  **Network Security**:
    -   Database and Worker are isolated in **Private Subnets** (No direct Internet access).
    -   Outbound traffic flows through a **NAT Gateway**.
    -   **Security Groups** strictly limit ports (e.g., RDS only accepts traffic on port 3306 from Lambda/EC2).

2.  **Application Security**:
    -   **JWT Authentication**: All API endpoints verify Cognito Access Tokens.
    -   **Bot Mitigation**: Turnstile prevents automated signups.
    -   **CORS**: Strictly configured to allow only `https://shri.software`.

3.  **Data Security**:
    -   **Encryption at Rest**: RDS and S3 encryption enabled.
    -   **Encryption in Transit**: HTTPS enforced via Cloudflare.

---

## 5. System Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as React App
    participant API as API Gateway + Lambda
    participant DB as RDS (MySQL)
    participant SQS as SQS Queue
    participant Worker as EC2 Worker
    participant S3 as S3 Bucket
    participant LLM as Claude/OpenAI API

    Note over User, API: 1. Submission
    User->>Frontend: Enters YouTube URL
    Frontend->>API: POST /analyze (URL, Auth Token)
    API->>DB: Create Video Record (Status: queued)
    API->>SQS: Send Message (VideoID, URL)
    API-->>Frontend: Return VideoID (202 Accepted)

    Note over Worker, S3: 2. Async Processing
    loop Poll SQS
        Worker->>SQS: Receive Message
    end
    
    Worker->>Worker: Extract Audio (yt-dlp)
    Worker->>Worker: Transcribe Audio (Local Whisper)
    
    Worker->>S3: Upload Audio, Transcript
    Worker->>DB: Update Video Status (completed) & S3 Paths
    Worker->>SQS: Delete Message

    Note over User, Frontend: 3. Result Retrieval & Generation
    loop Polling / Webhook
        Frontend->>API: GET /videos/{id}
        API->>DB: Check Status
        DB-->>API: Return Status (completed)
    end
    
    Frontend->>API: POST /flashcards/generate (VideoID)
    API->>S3: Read Transcript
    API->>LLM: Generate Flashcards (Transcript)
    LLM-->>API: Return JSON Content
    API-->>Frontend: Return Flashcards
```
