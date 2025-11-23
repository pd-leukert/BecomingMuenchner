# Manual Deployment Guide

## How to Start Everything

I've created a single script that manages both the VLM model and the API server.

**Run this command:**

```bash
cd /home/holmov/BecomingMuenchner/verity_check
./start_services.sh
```

## What it does

1. **Starts VLM Service** (`serve.sh`) on port 8000 (Internal only)
2. **Waits** for the model to load (this takes a minute)
3. **Starts API Service** (`api.py`) on port 8001 (Publicly exposed)
4. **Shows you the public URL**

## To Stop

Just press **Ctrl+C** in the terminal where the script is running. It will automatically stop both services.

## Troubleshooting

- **VLM Logs**: `tail -f vlm.log`
- **API Logs**: `tail -f api.log`
