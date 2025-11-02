# TextScript Deployment Guide

## Production Deployment with Docker

### Prerequisites

- Docker and Docker Compose installed on the server
- SSH access to the server
- `.env` file with OpenRouter API key

### Step 1: Configure Frontend API URL

Before building for production, create `.env.local` in the `web-frontend` directory:

```bash
# web-frontend/.env.local
NEXT_PUBLIC_API_URL=http://YOUR_SERVER_IP:8000
```

**Important:** Replace `YOUR_SERVER_IP` with your actual server IP address or domain name. This must be accessible from the browser (client-side).

Example for server at `192.168.0.24`:
```bash
NEXT_PUBLIC_API_URL=http://192.168.0.24:8000
```

### Step 2: Copy Project to Server

```bash
# From your local machine
rsync -avz --exclude 'node_modules' --exclude '.git' \
  --exclude '__pycache__' --exclude '.next' \
  /path/to/TextScript/ user@server:/path/to/destination/
```

### Step 3: Build and Start Services

On the server:

```bash
cd /path/to/textscript
docker-compose up -d --build
```

### Step 4: Verify Deployment

Check container status:
```bash
docker-compose ps
```

Test backend:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","active_processes":0}
```

Test frontend:
```bash
curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK
```

### Accessing the Application

- **Frontend (Web UI)**: `http://YOUR_SERVER_IP:3000`
- **Backend API**: `http://YOUR_SERVER_IP:8000`
- **API Docs**: `http://YOUR_SERVER_IP:8000/docs`

### Troubleshooting

#### Issue: 502 Bad Gateway or CORS Errors

This usually means the frontend cannot connect to the backend.

**Solution 1: Check Frontend API URL**

Ensure `NEXT_PUBLIC_API_URL` in `web-frontend/.env.local` points to the public IP/domain of your server, not `http://backend:8000`.

```bash
# Correct for production
NEXT_PUBLIC_API_URL=http://192.168.0.24:8000

# Wrong for production (only works server-side)
NEXT_PUBLIC_API_URL=http://backend:8000
```

After fixing, rebuild the frontend:
```bash
docker-compose build frontend
docker-compose stop frontend && docker-compose rm -f frontend
docker-compose up -d frontend
```

**Solution 2: CORS Configuration**

If you see CORS errors in browser console like:
```
Access to fetch at 'http://192.168.0.24:8000/api/profiles/current'
from origin 'http://192.168.0.24:3000' has been blocked by CORS policy
```

The backend CORS is properly configured to allow all origins by default. If you need to restrict origins for security, set the `CORS_ORIGINS` environment variable:

```bash
# In .env file or docker-compose.yml
CORS_ORIGINS=http://192.168.0.24:3000,http://your-domain.com
```

Then rebuild backend:
```bash
docker-compose build backend
docker-compose stop backend && docker-compose rm -f backend
docker-compose up -d backend
```

#### Issue: Container keeps restarting

Check logs:
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Management Commands

**View logs:**
```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Restart services:**
```bash
docker-compose restart
```

**Stop services:**
```bash
docker-compose down
```

**Update deployment:**
```bash
# Pull changes from git
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Security Recommendations

1. **Use reverse proxy:** Set up Nginx with SSL/TLS certificates
2. **Configure firewall:** Restrict access to ports 3000 and 8000
3. **Use environment secrets:** Store API keys in Docker secrets instead of .env
4. **Enable log rotation:** Prevent disk space issues
5. **Regular backups:** Backup SQLite database regularly

### Architecture

```
User Browser → Frontend (Next.js:3000) → Backend (FastAPI:8000) → OpenRouter API
                                    ↓
                              SQLite Database
```

**Important:** The frontend makes API calls from two contexts:
- Server-side: Can use `http://backend:8000` (Docker DNS)
- Client-side: Must use public URL `http://YOUR_SERVER_IP:8000` (browser)

This is why `NEXT_PUBLIC_API_URL` must be set to the public URL during build time.
