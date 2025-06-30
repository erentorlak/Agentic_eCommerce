# 🚀 Getting Started Guide

Welcome to the Intelligent Store Migration Assistant! This guide will help you set up and run the application locally for development or testing purposes.

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software
- **Docker** (v20.0+) and **Docker Compose** (v2.0+)
- **Make** (for simplified command execution)
- **Git** (for version control)

### Recommended Software
- **Node.js** (v18+) for frontend development
- **Python** (v3.11+) for backend development
- **VS Code** or **PyCharm** for development

### API Keys (Required for full functionality)
- **OpenAI API Key** - For AI agents functionality
- **Platform API Keys** - For connecting to source platforms (Shopify, WooCommerce, etc.)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd intelligent-store-migration-assistant
```

### 2. Environment Setup
```bash
# Copy the environment template
cp .env.example .env

# Edit the environment file with your configuration
vim .env  # or use your preferred editor
```

### 3. Configure Environment Variables

Edit the `.env` file and set the following essential variables:

```bash
# AI/ML Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Database (Use defaults for development)
DATABASE_URL=postgresql://migration_user:migration_pass@localhost:5432/migration_db
REDIS_URL=redis://localhost:6379/0

# Security (Generate secure keys for production)
JWT_SECRET_KEY=your_super_secret_jwt_key_here
ENCRYPTION_KEY=your_32_byte_encryption_key_here

# Platform API Keys (Optional for testing)
SHOPIFY_APP_KEY=your_shopify_app_key
SHOPIFY_APP_SECRET=your_shopify_app_secret
# ... add other platform keys as needed
```

## 🏃‍♂️ Quick Start

### Option 1: Docker Compose (Recommended)

Start the entire application stack with a single command:

```bash
# Start all services
make up

# Or manually with docker-compose
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis cache
- Backend API server
- Frontend application
- Celery workers
- Monitoring services (Prometheus, Grafana)

### Option 2: Development Mode

For active development with hot reloading:

```bash
# Start core services only
make dev

# This starts:
# - Database and Redis in containers
# - Backend and Frontend with hot reload
```

### Option 3: Manual Setup

If you prefer to run components individually:

```bash
# Start database services
docker-compose up -d postgres redis

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

## 🌐 Access the Application

Once the services are running, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main application interface |
| **Backend API** | http://localhost:8000 | REST API endpoints |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs (Swagger) |
| **Alternative API Docs** | http://localhost:8000/redoc | ReDoc API documentation |
| **Grafana Dashboard** | http://localhost:3001 | Monitoring dashboard (admin/admin123) |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **Flower** | http://localhost:5555 | Celery task monitoring |

## 🧪 Verify Installation

### 1. Health Check
```bash
# Check if all services are running
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":...,"version":"1.0.0"}
```

### 2. Frontend Access
Navigate to http://localhost:3000 and verify the landing page loads correctly.

### 3. API Documentation
Visit http://localhost:8000/docs to explore the interactive API documentation.

### 4. Database Connection
```bash
# Connect to the database
make shell-db

# Run a simple query
SELECT version();
```

## 🔧 Development Workflow

### Backend Development

```bash
# Format code
make format-backend

# Run linting
make lint-backend

# Run tests
make test-backend

# Run with coverage
make test-coverage

# Access backend shell
make shell-backend
```

### Frontend Development

```bash
# Run linting
make lint-frontend

# Run tests
make test-frontend

# Format code
make format-frontend

# Access frontend shell
make shell-frontend
```

### Database Operations

```bash
# Create a new migration
make migrate-create NAME="add_new_table"

# Apply migrations
make migrate

# Reset database (WARNING: Deletes all data)
make db-reset

# Create backup
make backup

# Restore from backup
make restore FILE=backup_20240101_120000.sql
```

## 📊 Monitoring

### Grafana Dashboard
1. Access http://localhost:3001
2. Login with `admin` / `admin123`
3. Import pre-configured dashboards for:
   - Application metrics
   - Database performance
   - Migration progress
   - System resources

### Logs
```bash
# View all logs
make logs

# View specific service logs
make logs-backend
make logs-frontend
make logs-db

# Follow logs in real-time
docker-compose logs -f
```

## 🧪 Testing the Migration Flow

### 1. Create a Test Migration

Using the frontend:
1. Navigate to http://localhost:3000
2. Click "Start Migration"
3. Fill in test platform details
4. Watch the AI agents analyze the source platform

Using the API:
```bash
curl -X POST http://localhost:8000/api/v1/migrations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Migration",
    "source_platform": "shopify",
    "destination_platform": "ideasoft",
    "source_config": {
      "store_url": "test-store.myshopify.com",
      "access_token": "test_token"
    }
  }'
```

### 2. Monitor Progress

Check migration status:
```bash
# Get migration status
curl http://localhost:8000/api/v1/migrations/{migration_id}

# View real-time updates in Flower
# http://localhost:5555
```

## 🔒 Security Considerations

### Development Environment
- Default credentials are provided for convenience
- Use secure, unique passwords in production
- Never commit real API keys to version control

### Production Deployment
- Change all default passwords
- Use environment-specific configuration
- Enable HTTPS/TLS
- Set up proper firewall rules
- Regular security updates

## 🐛 Troubleshooting

### Common Issues

**1. Port Conflicts**
```bash
# Check if ports are in use
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Stop conflicting services or change ports in docker-compose.yml
```

**2. Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View database logs
make logs-db

# Restart database
docker-compose restart postgres
```

**3. OpenAI API Errors**
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check API key validity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

**4. Frontend Build Issues**
```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Clear Next.js cache
rm -rf .next
npm run build
```

### Getting Help

1. **Check Logs**: Always start by checking service logs
2. **GitHub Issues**: Search existing issues or create a new one
3. **Documentation**: Review the architecture documentation
4. **Community**: Join our Discord for real-time help

### Reset Everything
If you encounter persistent issues:

```bash
# Stop all services and clean up
make clean-all

# Restart from scratch
make up
```

## 📚 Next Steps

Now that you have the application running:

1. **Explore the API**: Use the interactive docs at `/docs`
2. **Review Architecture**: Read `ARCHITECTURE.md` for technical details
3. **Contribute**: Check our contributing guidelines
4. **Customize**: Modify the configuration for your specific needs
5. **Deploy**: Follow production deployment guidelines

## 📞 Support

- 📧 **Email**: support@migration-assistant.com
- 💬 **Discord**: [Join our community](https://discord.gg/migration-assistant)
- 📖 **Documentation**: [docs.migration-assistant.com](https://docs.migration-assistant.com)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/migration-assistant/issues)

Happy migrating! 🎉