# Security Documentation

## Overview

This document outlines the security measures implemented in the CrewAI Workflow Orchestration Platform and provides guidelines for secure deployment and usage.

## Recent Security Improvements

### 1. API Key Management
- **Removed hardcoded API keys** from version control
- Created `.env.example` file showing required environment variables without exposing actual keys
- Added `.env` to `.gitignore` to prevent accidental commits

**Action Required**: 
- Copy `.env.example` to `.env`
- Add your actual API keys to `.env`
- Never commit `.env` to version control

### 2. CORS Configuration
- **Restricted CORS origins** from wildcard (*) to specific allowed origins
- Configurable via `CORS_ALLOWED_ORIGINS` environment variable
- Default allows only localhost:3000 and localhost:8100

**Configuration**:
```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8100,https://yourdomain.com
```

### 3. Authentication & Authorization
- **JWT-based authentication** system implemented
- Protected sensitive endpoints with authentication requirements
- Admin-only endpoints for critical operations
- Configurable authentication via `ENABLE_AUTH` environment variable

**Default Users** (Change these immediately!):
- Username: `admin`, Password: `admin123` (Admin role)
- Username: `user`, Password: `user123` (User role)

**Configuration**:
```env
ENABLE_AUTH=true
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=24
```

### 4. Input Validation
- **Pydantic models** with strict validation for all API endpoints
- URL validation for LinkedIn and website URLs
- Length limits on text inputs
- Regex patterns for channel and URL validation

### 5. Error Handling
- Fixed undefined variable errors in error handlers
- Added proper logging for all errors
- Implemented React Error Boundaries for frontend
- Async error handling for Promise rejections

## Security Best Practices

### Environment Variables
1. **Generate strong secrets**:
   ```bash
   # Generate SECRET_KEY
   openssl rand -hex 32
   
   # Generate JWT_SECRET_KEY
   openssl rand -hex 32
   ```

2. **Required environment variables**:
   - `AZURE_OPENAI_API_KEY` or `OPENAI_API_KEY`
   - `SECRET_KEY`
   - `JWT_SECRET_KEY`
   - `CORS_ALLOWED_ORIGINS`

### Authentication Setup
1. **Enable authentication in production**:
   ```env
   ENABLE_AUTH=true
   ```

2. **Change default passwords immediately**:
   - Update the `DEMO_USERS` in `auth.py`
   - Implement a proper user database
   - Add user registration endpoint

3. **Implement refresh tokens** for better security

### API Security
1. **Rate limiting** is enabled via SlowAPI
2. **Request size limits** via Pydantic validation
3. **SQL injection protection** via parameterized queries
4. **XSS protection** via proper data sanitization

### Deployment Security

#### HTTPS Setup
Always use HTTPS in production:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8100;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Database Security
1. Use PostgreSQL instead of SQLite in production
2. Enable SSL for database connections
3. Use connection pooling
4. Regular backups

#### Redis Security
1. Set a password for Redis:
   ```env
   REDIS_URL=redis://:password@localhost:6379
   ```
2. Bind Redis to localhost only
3. Use Redis ACLs for fine-grained access control

### Monitoring & Auditing

1. **Enable Sentry** for error tracking:
   ```env
   SENTRY_DSN=your-sentry-dsn
   ```

2. **Audit logs** for sensitive operations
3. **Monitor failed login attempts**
4. **Set up alerts** for suspicious activities

## Security Checklist

- [ ] Changed all default passwords
- [ ] Generated strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Configured CORS_ALLOWED_ORIGINS for your domains
- [ ] Enabled HTTPS in production
- [ ] Set up proper database with SSL
- [ ] Configured Redis with authentication
- [ ] Enabled authentication (ENABLE_AUTH=true)
- [ ] Set up monitoring and alerting
- [ ] Regular security updates for dependencies
- [ ] Implemented proper logging
- [ ] Configured firewall rules
- [ ] Set up regular backups

## Reporting Security Issues

If you discover a security vulnerability, please:
1. **Do not** open a public issue
2. Email security concerns to [your-security-email@example.com]
3. Include detailed steps to reproduce
4. Allow time for patching before public disclosure

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [React Security Best Practices](https://reactjs.org/docs/security.html)