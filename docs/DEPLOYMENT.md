# Deployment Guide

## Overview
This guide covers deployment options for the CrewAI Workflow Orchestration Platform, from development to production environments.

## Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- Python 3.9+
- Node.js 16+
- Redis
- Domain name (for production)
- SSL certificate (for production)

## Development Deployment

### Local Development
```bash
# Backend
python app.py

# Frontend
npm start

# Redis
redis-server

# Celery Worker
celery -A tasks worker --loglevel=info
```

## Production Deployment

### 1. Server Setup

#### Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.9 python3.9-venv python3-pip -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs -y

# Install Redis
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Install Nginx
sudo apt install nginx -y
```

### 2. Application Setup

#### Clone Repository
```bash
cd /opt
sudo git clone https://github.com/pranavrajput12/Precall-report.git crewai-workflow
sudo chown -R $USER:$USER /opt/crewai-workflow
cd /opt/crewai-workflow
```

#### Backend Setup
```bash
# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with production values
```

#### Frontend Build
```bash
# Install dependencies
npm install

# Build for production
npm run build
```

### 3. Systemd Services

#### Backend Service
Create `/etc/systemd/system/crewai-backend.service`:
```ini
[Unit]
Description=CrewAI Backend API
After=network.target redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/crewai-workflow
Environment="PATH=/opt/crewai-workflow/venv/bin"
ExecStart=/opt/crewai-workflow/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Celery Worker Service
Create `/etc/systemd/system/crewai-celery.service`:
```ini
[Unit]
Description=CrewAI Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/crewai-workflow
Environment="PATH=/opt/crewai-workflow/venv/bin"
ExecStart=/opt/crewai-workflow/venv/bin/celery -A tasks worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable crewai-backend
sudo systemctl enable crewai-celery
sudo systemctl start crewai-backend
sudo systemctl start crewai-celery
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/crewai`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /opt/crewai-workflow/build;
        try_files $uri /index.html;
    }

    # API Proxy
    location /api {
        proxy_pass http://localhost:8100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/crewai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL Configuration

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Docker Deployment

### Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: .
    ports:
      - "8100:8100"
    environment:
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env
    depends_on:
      - redis
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config

  celery:
    build: .
    command: celery -A tasks worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379
    env_file:
      - .env
    depends_on:
      - redis
      - backend

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  redis_data:
```

### Dockerfile (Backend)
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8100

CMD ["python", "app.py"]
```

### Dockerfile.frontend
```dockerfile
FROM node:16 as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

### Deploy with Docker
```bash
docker-compose up -d
```

## Environment Variables

### Production .env
```env
# API Keys
OPENAI_API_KEY=your_production_key
ANTHROPIC_API_KEY=your_production_key

# Redis
REDIS_URL=redis://localhost:6379

# Application
APP_ENV=production
APP_PORT=8100
WORKERS=4

# Security
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=your-domain.com

# Monitoring (optional)
SENTRY_DSN=your_sentry_dsn
LANGTRACE_API_KEY=your_langtrace_key
```

## Monitoring

### Health Checks
```bash
# Check services
sudo systemctl status crewai-backend
sudo systemctl status crewai-celery
sudo systemctl status redis
sudo systemctl status nginx

# Check logs
sudo journalctl -u crewai-backend -f
sudo journalctl -u crewai-celery -f
```

### Monitoring Setup
1. **Application Monitoring**: Use the built-in observability endpoints
2. **System Monitoring**: Set up Prometheus + Grafana
3. **Error Tracking**: Configure Sentry
4. **Uptime Monitoring**: Use services like UptimeRobot

## Backup Strategy

### Data Backup
```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backup/crewai"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup config
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/crewai-workflow/config

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz /opt/crewai-workflow/logs

# Backup FAQ database
cp /opt/crewai-workflow/faq_knowledge_base.csv $BACKUP_DIR/faq_$DATE.csv

# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$DATE.rdb
```

### Automated Backups
Add to crontab:
```bash
0 2 * * * /opt/crewai-workflow/scripts/backup.sh
```

## Scaling

### Horizontal Scaling
1. **Multiple Celery Workers**: Increase worker count
   ```bash
   celery -A tasks worker --concurrency=4
   ```

2. **Load Balancing**: Use multiple backend instances behind Nginx

3. **Redis Clustering**: For high-throughput caching

### Vertical Scaling
- Increase server resources (CPU, RAM)
- Optimize Python with PyPy or Cython
- Use connection pooling

## Security

### Best Practices
1. **API Security**:
   - Implement authentication (JWT, OAuth)
   - Rate limiting
   - Input validation

2. **Network Security**:
   - Firewall configuration
   - VPN for admin access
   - Regular security updates

3. **Data Security**:
   - Encrypt sensitive data
   - Secure environment variables
   - Regular security audits

### Firewall Rules
```bash
# Allow SSH
sudo ufw allow 22

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Enable firewall
sudo ufw enable
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   sudo lsof -i :8100
   sudo kill -9 <PID>
   ```

2. **Redis Connection Failed**
   ```bash
   sudo systemctl restart redis
   redis-cli ping
   ```

3. **Frontend Not Loading**
   - Check Nginx configuration
   - Verify build files exist
   - Check browser console for errors

4. **Celery Tasks Not Running**
   - Check Celery worker logs
   - Verify Redis connection
   - Check task queue

## Performance Optimization

1. **Backend**:
   - Use production WSGI server (Gunicorn)
   - Enable response caching
   - Optimize database queries

2. **Frontend**:
   - Enable Gzip compression
   - Use CDN for static assets
   - Implement lazy loading

3. **Infrastructure**:
   - Use SSD storage
   - Optimize Redis configuration
   - Monitor resource usage