# Flask Logging Guide

## Overview

This guide documents the proper implementation of logging in our Flask application, based on real debugging experiences. The standard Flask logging configuration may not work as expected in all environments, so we provide multiple approaches to ensure logging works reliably.

## The Problem We Encountered

During development, we found that:
- Flask's `current_app.logger` was not writing to `logs/app.log` in route handlers
- Print statements were not captured in Flask logs
- The app-level logger configuration was not propagating to route-level code
- This caused hours of debugging when trying to trace variable values in workflow endpoints

## Solution: Direct File Logging

The most reliable approach is **direct file logging** that bypasses Flask's logging system entirely.

### Implementation Pattern

```python
import os
from datetime import datetime

@bp.route('/your-endpoint', methods=['POST'])
def your_endpoint():
    # DIRECT FILE LOGGING - GUARANTEED TO WORK
    import os
    from datetime import datetime
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Write immediate function entry log
    with open('logs/your_endpoint_direct.log', 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] FUNCTION CALLED - your parameters\n")
        f.write(f"[{datetime.now().isoformat()}] Request method: {request.method}\n")
        f.flush()  # Force immediate write
    
    # Your endpoint logic here...
    
    # Log throughout the function
    with open('logs/your_endpoint_direct.log', 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] VARIABLE VALUES - key variables\n")
        f.flush()
    
    # Log at function completion
    with open('logs/your_endpoint_direct.log', 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] FUNCTION COMPLETED SUCCESSFULLY\n")
        f.flush()
```

### Key Points

1. **Always use `flush()`** - This forces immediate writing to disk
2. **Use append mode (`'a'`)** - This preserves previous logs
3. **Include timestamps** - Use `datetime.now().isoformat()` for precise timing
4. **Create logs directory** - Use `os.makedirs('logs', exist_ok=True)`
5. **Use descriptive log names** - Include the endpoint name in the log filename

## Alternative Approaches

### 1. Flask Logger (May Not Work)

```python
from flask import current_app

@bp.route('/your-endpoint', methods=['POST'])
def your_endpoint():
    current_app.logger.info("This may not appear in logs/app.log")
    current_app.logger.error("This might work better")
```

**Note**: This approach is unreliable in our environment and should not be trusted for critical debugging.

### 2. Print Statements (Not Captured)

```python
@bp.route('/your-endpoint', methods=['POST'])
def your_endpoint():
    print("This will not appear in Flask logs")
```

**Note**: Print statements are not captured by Flask's logging system.

### 3. Runtime Logger Handler

```python
import logging

@bp.route('/test-logging-advanced', methods=['GET'])
def test_logging_advanced():
    # Create a new logger handler at runtime
    logger = logging.getLogger('runtime_logger')
    logger.setLevel(logging.INFO)
    
    # Create file handler
    file_handler = logging.FileHandler('logs/runtime_added_handler.log')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Log messages
    logger.info("This will appear in runtime_added_handler.log")
    
    return jsonify({'success': True, 'message': 'Logging test completed'})
```

## Best Practices

### 1. Always Test Logging

Before claiming any functionality works, test the logging:

```bash
# Test the endpoint
curl -X POST http://localhost:5000/api/your-endpoint -H "Content-Type: application/json" -d '{"test": "data"}'

# Check if logs were written
ls -la logs/your_endpoint_direct.log
cat logs/your_endpoint_direct.log
```

### 2. Use Descriptive Log Messages

```python
# Good
f.write(f"[{datetime.now().isoformat()}] DB QUERY RESULT - step_result found: {step_result is not None}\n")
f.write(f"[{datetime.now().isoformat()}] step_result type: {type(step_result)}\n")

# Bad
f.write("Found result\n")
```

### 3. Log at Key Points

- Function entry
- Database queries
- Variable assignments
- Error conditions
- Function completion

### 4. Include Context

```python
f.write(f"[{datetime.now().isoformat()}] FUNCTION CALLED - post_id: {post_id}, stage: {stage}, substage: {substage}\n")
```

## File Locations

- **Direct logs**: `logs/endpoint_name_direct.log`
- **Flask app logs**: `logs/app.log` (unreliable)
- **Runtime logs**: `logs/runtime_added_handler.log`

## Troubleshooting

### If Logs Don't Appear

1. **Check file permissions**: Ensure the process can write to the logs directory
2. **Verify flush() calls**: Make sure `flush()` is called after each write
3. **Check directory creation**: Ensure `os.makedirs('logs', exist_ok=True)` is called
4. **Test with simple file write**: Create a test route that writes directly to a file

### Test Route for Logging

```python
@bp.route('/test-direct-file', methods=['GET'])
def test_direct_file():
    import os
    from datetime import datetime
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Write test log
    with open('logs/test_direct_file.log', 'w') as f:
        f.write(f"Test log written at {datetime.now().isoformat()}\n")
        f.flush()
    
    return jsonify({'success': True, 'message': 'Test log written'})
```

## Real Example: Planning Stage Logging

See `app/api/workflow/routes.py` in the `run_workflow_llm` function for a complete example of proper logging implementation that successfully traces:

- Function entry
- Database query results
- Config parsing
- Variable assignments
- Function completion

## Summary

**Always use direct file logging for critical debugging.** Flask's built-in logging system is unreliable in our environment. The direct file approach guarantees that logs will be written and can be easily found and analyzed.

**Remember**: If you need to trace variables or debug an endpoint, implement direct file logging immediately. Don't rely on Flask's logging system or print statements. 