# Documentation Index

Welcome to the Hostaway Message Database documentation. This page provides an overview of all available documentation to help you get started, understand the APIs, and troubleshoot issues.

## 📚 Documentation Overview

| Document | Description | Best For |
|----------|-------------|----------|
| [📋 API Reference](api_reference.md) | Complete API documentation with examples | Developers integrating with the APIs |
| [🚀 Quickstart Guide](quickstart_guide.md) | Step-by-step setup and first run | New users getting started |
| [🔧 Troubleshooting](troubleshooting.md) | Common issues and solutions | Debugging problems |
| [🏗️ Architecture](architecture.md) | System design and components | Understanding the system |
| [📊 ETL Pipeline](etl_pipeline.md) | Detailed ETL process documentation | Understanding data flow |
| [🚀 Deployment](deployment.md) | Production deployment guide | DevOps and deployment |
| [✅ Authentication](authentication.md) | API authentication setup | Setting up API access |

## 🎯 Quick Navigation

### New to the Project?
1. Start with the [**Quickstart Guide**](quickstart_guide.md) for setup instructions
2. Review the [**Architecture**](architecture.md) to understand the system
3. Check [**Authentication**](authentication.md) for API setup

### Looking for API Documentation?
- [**API Reference**](api_reference.md) - Complete function documentation with examples
- [**ETL Pipeline**](etl_pipeline.md) - Understanding the data processing flow

### Having Issues?
- [**Troubleshooting Guide**](troubleshooting.md) - Common problems and solutions
- Check the project logs in `logs/` directory
- Review configuration in your `.env` file

### Ready for Production?
- [**Deployment Guide**](deployment.md) - Production setup instructions
- [**Architecture**](architecture.md) - System design considerations

## 🔍 Quick Reference

### Core Components

- **HostawayClient** - API communication and authentication
- **MongoDB** - Database operations and connection management  
- **Message Models** - Data structures and validation
- **ETL Pipeline** - Extract, Transform, Load process
- **Configuration** - Environment variables and settings
- **Utilities** - Logging and error notifications
- **Scheduler** - Automated job execution

### Key Configuration Variables

```bash
# Required
HOSTAWAY_CLIENT_ID=your_client_id
HOSTAWAY_CLIENT_SECRET=your_client_secret
MONGODB_URI=mongodb://localhost:27017

# Optional
LOG_LEVEL=INFO
API_REQUEST_DELAY=1.0
ENABLE_DRY_RUN=false
```

### Common Commands

```bash
# Run ETL for recent messages
python -m src.main etl --days 5

# Run ETL for specific date range
python -m src.main etl --since 2024-01-01T00:00:00

# Test configuration
python -c "from src.config import validate_config; validate_config()"

# Run daily job (for cron)
python -m src.scheduler.daily_job
```

## 📖 Detailed Documentation

### [API Reference](api_reference.md)
Comprehensive documentation of all public APIs, functions, and components with detailed examples and usage instructions.

**Includes:**
- HostawayClient methods and parameters
- Database operations and connection management
- Data models and validation
- ETL pipeline functions
- Configuration options
- Utility functions
- Complete code examples

### [Quickstart Guide](quickstart_guide.md)
Step-by-step instructions to get the application running quickly.

**Includes:**
- Installation instructions
- Environment setup
- Basic configuration
- First ETL run
- Common usage patterns
- Development setup

### [Troubleshooting Guide](troubleshooting.md)
Comprehensive guide for diagnosing and resolving common issues.

**Includes:**
- Debug techniques
- Common error patterns
- Configuration issues
- API connection problems
- Database issues
- Performance optimization
- Recovery procedures

### [Architecture](architecture.md)
Overview of the system design and component relationships.

**Includes:**
- System overview
- Component architecture
- Data flow diagrams
- Technology stack
- Design decisions

### [ETL Pipeline](etl_pipeline.md)
Detailed documentation of the Extract, Transform, Load process.

**Includes:**
- Pipeline overview
- Data extraction from Hostaway API
- Transformation logic
- Database loading
- Error handling
- Performance considerations

### [Deployment](deployment.md)
Guide for setting up the application in production environments.

**Includes:**
- Production deployment
- Docker setup
- Environment configuration
- Monitoring setup
- Backup strategies
- Scaling considerations

### [Authentication](authentication.md)
Setup and configuration of API authentication.

**Includes:**
- OAuth 2.0 setup
- API credential management
- Token handling
- Security best practices

## 💡 Tips and Best Practices

### Getting Started
1. Always start with the quickstart guide
2. Use dry run mode for testing: `ENABLE_DRY_RUN=true`
3. Enable debug logging for troubleshooting: `LOG_LEVEL=DEBUG`
4. Test your configuration before running full ETL

### Development
1. Use virtual environments for Python dependencies
2. Follow the logging patterns for consistent output
3. Use the provided data models for type safety
4. Implement proper error handling in custom scripts

### Production
1. Set up monitoring and alerting
2. Use environment-specific configuration
3. Implement backup strategies
4. Monitor API rate limits
5. Set up log rotation

### Troubleshooting
1. Check logs first: `tail -f logs/$(date +%Y-%m-%d).log`
2. Verify configuration: validate_config()
3. Test individual components before running full ETL
4. Use dry run mode to test changes

## 🆘 Getting Help

### Documentation Issues
If you find issues with the documentation:
1. Check if there's an existing issue
2. Create a detailed issue report
3. Include specific examples of unclear sections

### Technical Support
For technical issues:
1. Check the [troubleshooting guide](troubleshooting.md) first
2. Review logs for error messages
3. Include debug information when reporting issues
4. Never include sensitive data like API keys

### Contributing
To contribute to the documentation:
1. Follow the existing documentation style
2. Include code examples where helpful
3. Test all code examples before submitting
4. Update this index when adding new documentation

## 📋 Documentation Checklist

When using this documentation:
- [ ] I've read the quickstart guide
- [ ] I've configured my environment variables
- [ ] I've tested my configuration
- [ ] I understand the basic architecture
- [ ] I know where to find troubleshooting help
- [ ] I've reviewed the API reference for my use case

## 🔄 Document Updates

This documentation is updated regularly. Key changes:
- **API Reference**: Complete rewrite with comprehensive examples
- **Quickstart Guide**: Added development setup section
- **Troubleshooting**: Expanded error handling and recovery procedures
- **Architecture**: Updated component diagrams and explanations

---

*Last updated: December 2024*