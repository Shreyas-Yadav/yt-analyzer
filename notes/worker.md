# Worker Documentation

## 1. Overview
The Worker is a standalone Python application running on an **AWS EC2 Instance**. It is the "brain" of the operation, responsible for the heavy lifting: downloading videos, extracting audio, transcribing speech using AI, and generating educational content.

## 2. Architecture
-   **Pattern**: Polling Consumer.
-   **Source**: AWS SQS Queue.
-   **Compute**: EC2 (`g4dn.xlarge` recommended for GPU acceleration).
-   **OS**: Ubuntu 22.04 LTS.

## 3. The AI Pipeline
When a message is received from SQS, the worker executes the following pipeline:

### Step 1: Download (`yt-dlp`)
-   Extracts the YouTube URL from the message.
-   Uses `yt-dlp` to download **Audio Only** (`bestaudio`) to save bandwidth and storage.
-   Saves file to `/tmp/downloads`.

### Step 2: Audio Processing (`ffmpeg`)
-   Converts the downloaded audio (usually `.webm` or `.m4a`) to **MP3** format (192kbps).
-   Ensures compatibility with the transcription model.

### Step 3: Transcription (`faster-whisper`)
-   **Model**: OpenAI Whisper (Large-v3 or Medium).
-   **Optimization**: Uses `faster-whisper` implementation (CTranslate2 backend) for:
    -   4x faster inference than original OpenAI code.
    -   Significantly lower memory usage.
-   **Output**: Generates a timestamped transcript.

### Step 4: Content Generation (LLM)
-   **Flashcards**: Sends transcript chunks to Anthropic Claude (or GPT-4) to generate Q&A flashcards.
-   **Quiz**: Generates multiple-choice questions based on the content.

### Step 5: Persistence
-   **S3**: Uploads the raw audio, transcript file, and JSON assets to the S3 bucket.
-   **RDS**: Updates the `Video` status to `completed` and saves the S3 paths.

## 4. Deployment & Setup
The worker is deployed using the `backend/deploy_worker.sh` script.

### Prerequisites
-   **System**: Ubuntu 22.04.
-   **Dependencies**: `python3-pip`, `ffmpeg`, `uv` (fast package manager).
-   **GPU Drivers**: NVIDIA Drivers + CUDA Toolkit (if using GPU instance).

### Configuration
Environment variables required in `.env`:
-   `SQS_QUEUE_URL`: The URL of the SQS queue to poll.
-   `DB_HOST`, `DB_USER`, `DB_PASSWORD`: RDS credentials.
-   `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: IAM User with SQS/S3 access.

### Optimization Tips
-   **Swap Space**: If running on `t2.micro` (1GB RAM), a **2GB Swap File** is mandatory to prevent freezing during `pip install` or model loading.
-   **Concurrency**: The worker is currently single-threaded to avoid OOM (Out of Memory) errors on small instances. For high throughput, launch multiple EC2 instances (Horizontal Scaling).
