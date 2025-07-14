# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Hostaway Message Database application.

## General Debugging

### Enable Debug Logging

Add to your `.env` file:
```bash
LOG_LEVEL=DEBUG
```

This provides detailed information about:
- API requests and responses
- Database operations
- Authentication flows
- Error stack traces

### Check Log Files

Logs are stored in the `logs/` directory with daily rotation:
```bash
# View today's log
cat logs/$(date +%Y-%m-%d).log

# Follow live log output
tail -f logs/$(date +%Y-%m-%d).log

# Search for errors
grep -i error logs/$(date +%Y-%m-%d).log
```

### Dry Run Mode

Test your configuration without making changes:
```bash
# Add to .env
ENABLE_DRY_RUN=true

# Run ETL to see what would happen
python -m src.main etl --days 1
```

## Configuration Issues

### Missing Environment Variables

**Error**: `ValueError: Missing required environment variables: HOSTAWAY_CLIENT_ID, MONGODB_URI`

**Solution**:
1. Check your `.env` file exists in the project root
2. Verify all required variables are set:
   ```bash
   # Check if .env exists
   ls -la .env
   
   # Validate configuration
   python -c "from src.config import validate_config; validate_config()"
   ```

### Invalid Configuration Values

**Error**: `ValueError: Invalid configuration value for LOG_LEVEL`

**Solution**:
```bash
# Valid log levels
LOG_LEVEL=DEBUG     # Most verbose
LOG_LEVEL=INFO      # Default
LOG_LEVEL=WARNING   # Warnings and errors only
LOG_LEVEL=ERROR     # Errors only
LOG_LEVEL=CRITICAL  # Critical errors only
```

## API Connection Issues

### Authentication Failures

**Error**: `HostawayAPIError: Authentication failed: 401 Unauthorized`

**Symptoms**:
- Can't retrieve access token
- API requests return 401 errors

**Debugging Steps**:
1. Verify credentials:
   ```bash
   echo "Client ID: $HOSTAWAY_CLIENT_ID"
   echo "Client Secret: $HOSTAWAY_CLIENT_SECRET"
   ```

2. Test API endpoint:
   ```bash
   curl -X POST "https://api.hostaway.com/v1/accessTokens" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials&client_id=YOUR_ID&client_secret=YOUR_SECRET&scope=general"
   ```

3. Check API permissions:
   - Ensure your Hostaway account has API access
   - Verify the OAuth application is active
   - Check scope permissions

### Rate Limiting

**Error**: `HostawayAPIError: Rate limit exceeded`

**Symptoms**:
- API requests return 429 errors
- Intermittent connection failures

**Solutions**:
1. Increase request delay:
   ```bash
   # In .env file
   API_REQUEST_DELAY=2.0  # Increase from default 1.0
   ```

2. Implement backoff strategy:
   ```python
   # Custom retry logic
   import time
   from src.api.hostaway_client import api_client, HostawayAPIError
   
   def fetch_with_backoff(func, *args, **kwargs):
       for attempt in range(5):
           try:
               return func(*args, **kwargs)
           except HostawayAPIError as e:
               if "rate limit" in str(e).lower():
                   wait_time = 2 ** attempt  # Exponential backoff
                   time.sleep(wait_time)
                   continue
               raise
   ```

### Network Issues

**Error**: `ConnectionError: Failed to establish connection`

**Debugging Steps**:
1. Test internet connectivity:
   ```bash
   ping api.hostaway.com
   ```

2. Check firewall/proxy settings
3. Verify DNS resolution:
   ```bash
   nslookup api.hostaway.com
   ```

4. Test with curl:
   ```bash
   curl -I https://api.hostaway.com/v1/
   ```

## Database Issues

### MongoDB Connection Failures

**Error**: `ConnectionFailure: Could not connect to MongoDB`

**Common Causes & Solutions**:

1. **MongoDB not running**:
   ```bash
   # Start MongoDB service
   sudo systemctl start mongod  # Linux
   brew services start mongodb  # macOS
   ```

2. **Wrong connection string**:
   ```bash
   # Test connection
   mongo "mongodb://localhost:27017"
   
   # For MongoDB Atlas
   mongo "mongodb+srv://username:password@cluster.mongodb.net/test"
   ```

3. **Network/firewall issues**:
   ```bash
   # Test port connectivity
   telnet localhost 27017
   
   # Check MongoDB logs
   tail -f /var/log/mongodb/mongod.log
   ```

4. **Authentication issues**:
   ```bash
   # Test with authentication
   mongo "mongodb://username:password@localhost:27017/admin"
   ```

### SSL/TLS Certificate Issues

**Error**: `ServerSelectionTimeoutError: SSL handshake failed`

**Solutions**:
1. For development, allow invalid certificates:
   ```bash
   # In .env (not recommended for production)
   MONGODB_URI=mongodb://localhost:27017/?ssl=false
   ```

2. For production, use proper certificates or MongoDB Atlas

### Database Permission Issues

**Error**: `OperationFailure: not authorized`

**Solutions**:
1. Check user permissions:
   ```javascript
   // In MongoDB shell
   db.runCommand({usersInfo: "username"})
   ```

2. Grant required permissions:
   ```javascript
   // Grant read/write access
   db.grantRolesToUser("username", ["readWrite"])
   ```

## ETL Pipeline Issues

### No Messages Retrieved

**Symptoms**:
- ETL completes successfully but processes 0 messages
- Database remains empty

**Debugging Steps**:
1. Check date range:
   ```bash
   # Try broader date range
   python -m src.main etl --days 30
   ```

2. Verify API has data:
   ```python
   from src.api.hostaway_client import api_client
   
   # Test direct API call
   response = api_client.get_messages(limit=1)
   print(f"API response: {response}")
   ```

3. Check conversation retrieval:
   ```python
   conversations = list(api_client.get_all_messages())
   print(f"Found {len(conversations)} conversations")
   ```

### Data Transformation Errors

**Error**: `ValidationError: Invalid field value`

**Debugging**:
1. Check raw API data structure:
   ```python
   from src.api.hostaway_client import api_client
   import json
   
   for conv in api_client.get_all_messages():
       print(json.dumps(conv, indent=2))
       break  # Just check first one
   ```

2. Validate against model:
   ```python
   from src.models.message import Message
   
   try:
       message = Message.from_api_response(api_data)
   except Exception as e:
       print(f"Validation error: {e}")
       print(f"Raw data: {api_data}")
   ```

### Memory Issues

**Error**: `MemoryError: Out of memory`

**Solutions**:
1. Process in smaller batches:
   ```python
   # Process one day at a time
   from datetime import datetime, timedelta
   
   for i in range(30):
       date = datetime.now() - timedelta(days=i)
       pipeline.extract_transform_load(date.isoformat())
   ```

2. Use streaming processing:
   ```python
   # Generator-based processing (already implemented)
   for message in api_client.get_all_messages():
       # Process immediately, don't store in memory
       pass
   ```

## Performance Issues

### Slow ETL Processing

**Symptoms**:
- ETL takes very long to complete
- High CPU/memory usage

**Optimization Steps**:
1. Increase API delay to reduce load:
   ```bash
   API_REQUEST_DELAY=0.5  # Reduce from 1.0 if API allows
   ```

2. Monitor progress:
   ```python
   # Add progress logging to your custom scripts
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

3. Use indexes for better database performance:
   ```python
   # Indexes are created automatically, but you can verify:
   from src.database.mongodb import db
   db.connect()
   print(db.collection.index_information())
   ```

### High Memory Usage

**Solutions**:
1. Use generator patterns (already implemented)
2. Process in smaller time windows
3. Implement garbage collection:
   ```python
   import gc
   
   # Force garbage collection periodically
   gc.collect()
   ```

## Error Patterns and Solutions

### Common Error Messages

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| `ModuleNotFoundError: No module named 'src'` | Wrong working directory | Run from project root |
| `KeyError: 'access_token'` | API authentication failed | Check credentials |
| `TypeError: 'NoneType' object is not iterable` | API returned no data | Check date range/API connectivity |
| `DuplicateKeyError` | Duplicate message IDs | Normal - upsert handles this |
| `TimeoutError` | Network/database timeout | Check connectivity, increase timeouts |

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Normal completion |
| 1 | General error | Check logs for details |
| 2 | Configuration error | Fix .env file |
| 3 | Database error | Check MongoDB connection |
| 4 | API error | Check Hostaway credentials |

## Monitoring and Alerts

### Setting Up Monitoring

1. **Log monitoring**:
   ```bash
   # Watch for errors in real-time
   tail -f logs/*.log | grep -i error
   ```

2. **Database monitoring**:
   ```python
   # Check database health
   from src.database.mongodb import db
   
   db.connect()
   stats = db.db.command("dbStats")
   print(f"Database size: {stats['dataSize']} bytes")
   ```

3. **API monitoring**:
   ```python
   # Test API connectivity
   from src.api.hostaway_client import api_client
   
   try:
       response = api_client.get_messages(limit=1)
       print("API is accessible")
   except Exception as e:
       print(f"API error: {e}")
   ```

### Email Notifications

Configure error notifications:
```bash
# In .env
NOTIFICATION_EMAIL=admin@yourdomain.com
```

Test notifications:
```python
from src.utils.logger import send_error_notification

send_error_notification("Test Alert", "This is a test notification")
```

## Recovery Procedures

### Recovering from Failed ETL

1. **Check last successful timestamp**:
   ```python
   from src.database.mongodb import db
   
   db.connect()
   last_timestamp = db.get_latest_message_timestamp()
   print(f"Resume from: {last_timestamp}")
   ```

2. **Resume from last successful point**:
   ```bash
   python -m src.main etl --since "2024-01-15T10:30:00"
   ```

### Database Recovery

1. **Backup before recovery**:
   ```bash
   mongodump --db hostaway_messages --out backup/
   ```

2. **Clear corrupted data**:
   ```python
   from src.database.mongodb import db
   
   db.connect()
   # Remove corrupted records if needed
   db.collection.delete_many({"corrupted_field": {"$exists": True}})
   ```

3. **Rebuild indexes**:
   ```python
   from src.database.mongodb import db
   
   db.connect()
   db._create_indexes()  # Recreate indexes
   ```

## Getting Help

### Collecting Debug Information

When reporting issues, include:

1. **System information**:
   ```bash
   python --version
   pip list | grep -E "(pymongo|requests|pydantic)"
   ```

2. **Configuration** (sanitized):
   ```bash
   # Don't include secrets!
   env | grep -E "(MONGODB|LOG|API)" | grep -v SECRET
   ```

3. **Error logs**:
   ```bash
   tail -50 logs/$(date +%Y-%m-%d).log
   ```

4. **Test results**:
   ```bash
   python -c "from src.config import validate_config; validate_config()"
   ```

### Contact and Support

1. Check existing documentation
2. Search GitHub issues
3. Create detailed bug report with debug information
4. Include steps to reproduce the issue

Remember to never include sensitive information like API keys or passwords in bug reports!