# Residential Proxy Setup Guide (Raspberry Pi + Tailscale)

This guide explains how to route your AWS EC2 traffic through a Raspberry Pi at home to bypass YouTube's Data Center IP blocks.

## Architecture
**EC2 Worker** (AWS) --[Tailscale VPN]--> **Raspberry Pi** (Home) --[Tinyproxy]--> **Internet** (YouTube)

---

## Phase 1: Raspberry Pi Setup (The Proxy)

1.  **Install Tinyproxy**:
    ```bash
    sudo apt update
    sudo apt install -y tinyproxy
    ```

2.  **Configure Tinyproxy**:
    Edit the config file: `sudo nano /etc/tinyproxy/tinyproxy.conf`
    *   Ensure `Port 8888` is set.
    *   Add this line to the `Allow` section to accept traffic from the VPN:
        ```text
        Allow 100.0.0.0/8
        ```
    *   Save and exit.

3.  **Restart Tinyproxy**:
    ```bash
    sudo systemctl restart tinyproxy
    ```

4.  **Install Tailscale**:
    ```bash
    curl -fsSL https://tailscale.com/install.sh | sh
    sudo tailscale up
    ```
    *   Login with a **Personal Email** (Gmail/GitHub).
    *   **Note down the IP** assigned to the Pi (e.g., `100.x.y.z`).

---

## Phase 2: EC2 Setup (The Client)

1.  **SSH into EC2**:
    ```bash
    ssh aws
    ```

2.  **Install Tailscale**:
    ```bash
    curl -fsSL https://tailscale.com/install.sh | sh
    sudo tailscale up
    ```
    *   Login with the **SAME** account as the Pi.

3.  **Verify Connection**:
    ```bash
    ping 100.x.y.z  # Replace with Pi's Tailscale IP
    ```

---

## Phase 3: Application Configuration

1.  **Update AWS SSM Parameter**:
    *   Go to AWS Console -> Systems Manager -> Parameter Store.
    *   Create/Update Parameter: `/yt-analyzer/PROXY_URL`
    *   **Value**: `http://100.x.y.z:8888` (Replace with Pi's IP)

2.  **Deploy Worker**:
    The worker code is already updated to look for `PROXY_URL`.
    ```bash
    # On EC2
    cd yt-analyzer/backend
    git pull
    ./deploy_worker.sh
    ```

## Troubleshooting
*   **Slow Speeds?** The worker is configured to download **Audio Only** to save bandwidth.
*   **Connection Refused?** Check `sudo systemctl status tinyproxy` on the Pi.
*   **Auth Error?** Ensure both devices are on the same Tailscale network.
