# Propply AI - Digital Ocean Deployment Guide

## Overview
This guide covers deploying Propply AI to a Digital Ocean droplet using Docker and Docker Compose with full support for AI analysis (120-second timeouts).

## Features
- ✅ **Full AI Analysis Support** - 120-second timeouts for comprehensive analysis
- ✅ **Nginx Reverse Proxy** - Rate limiting, caching, SSL ready
- ✅ **Health Checks** - Automatic container monitoring
- ✅ **Security** - Firewall, fail2ban, non-root containers
- ✅ **Production Ready** - Gunicorn with optimized settings

## Prerequisites
- Digital Ocean Ubuntu 20.04+ droplet (minimum 1GB RAM, 2GB recommended)
- Domain name pointed to your server IP (optional)
- SSH access to your server

## Quick Deployment

### 1. Server Setup
```bash
# SSH into your Digital Ocean server
ssh root@your-server-ip

# Download and run server setup script
curl -o setup-server.sh https://raw.githubusercontent.com/propplyai/agent4NYC/main/setup-server.sh
chmod +x setup-server.sh
./setup-server.sh

# Log out and back in for Docker permissions
exit
ssh root@your-server-ip
```

### 2. Deploy Application
```bash
# Clone repository
git clone https://github.com/propplyai/agent4NYC.git /opt/propply-ai
cd /opt/propply-ai

# Deploy application
./deploy.sh
```

### 3. Verify Deployment
```bash
# Check health
curl http://your-server-ip/health

# Test application
curl http://your-server-ip/

# View logs
docker-compose logs -f
```

## Configuration

### Environment Variables
The application uses these environment variables (set in docker-compose.yml):
- `FLASK_ENV=production`
- `PYTHONPATH=/app`

### Timeouts
- **Gunicorn**: 120 seconds (supports full AI analysis)
- **Nginx**: 120 seconds for API endpoints, 60 seconds for web pages
- **AI Analysis**: ~31-37 seconds processing time

### Ports
- **Port 80**: HTTP traffic (Nginx)
- **Port 443**: HTTPS traffic (when SSL configured)
- **Internal Port 5000**: Flask application (not exposed)

## Management Commands

### View Application Status
```bash
docker-compose ps
```

### View Logs
```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f propply-ai
docker-compose logs -f nginx
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart propply-ai
```

### Update Application
```bash
cd /opt/propply-ai
git pull
./deploy.sh
```

### Stop Application
```bash
docker-compose down
```

## SSL Configuration (Optional)

### Using Let's Encrypt
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Update nginx.conf to enable SSL section
# Restart containers
docker-compose restart nginx
```

## Monitoring

### Health Check Endpoint
- URL: `http://your-server-ip/health`
- Returns: JSON with service status

### Log Files
- Application logs: `./logs/`
- Nginx logs: Container logs via `docker-compose logs nginx`

### Resource Usage
```bash
# Container stats
docker stats

# Disk usage
df -h
docker system df
```

## Troubleshooting

### Common Issues

#### Application Not Starting
```bash
# Check logs
docker-compose logs propply-ai

# Check if port is in use
sudo netstat -tulpn | grep :80
```

#### Health Check Failing
```bash
# Test internally
docker-compose exec propply-ai curl localhost:5000/health

# Check container status
docker-compose ps
```

#### AI Analysis Timeout
- The Docker setup supports 120-second timeouts
- Check logs for specific AI webhook errors
- Verify network connectivity to AI service

#### Memory Issues
```bash
# Check memory usage
free -h
docker stats

# Check for OOM kills
dmesg | grep -i "killed process"
```

### Performance Tuning

#### For High Traffic
Update docker-compose.yml:
```yaml
propply-ai:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.0'
```

Update Dockerfile CMD:
```bash
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

## Security Notes

### Firewall Configuration
- Only ports 22 (SSH), 80 (HTTP), and 443 (HTTPS) are open
- fail2ban protects against brute force attacks

### Container Security
- Application runs as non-root user
- Minimal attack surface with slim Python image

### Regular Maintenance
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d

# Clean up unused images
docker system prune -f
```

## API Documentation

### Endpoints
- `GET /` - Main application interface
- `GET /health` - Health check
- `POST /api/analyze-property` - Property analysis (supports 120s timeout)

### Example Usage
```bash
curl -X POST http://your-server-ip/api/analyze-property \
  -H "Content-Type: application/json" \
  -d '{"address": "140 West 28th Street, New York, NY"}'
```

## Support

For issues and questions:
1. Check logs: `docker-compose logs -f`
2. Verify health: `curl http://your-server-ip/health`
3. Check resource usage: `docker stats`
4. Review this documentation

The application is designed to be resilient and self-healing with proper health checks and restart policies.