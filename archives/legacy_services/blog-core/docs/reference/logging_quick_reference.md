# Logging Quick Reference

## 🚨 CRITICAL: Always Use Direct File Logging

**Flask's built-in logging is unreliable in our environment. Use direct file logging for all debugging.**

## Quick Implementation

```python
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
        f.flush()  # Force immediate write
    
    # Your logic here...
    
    # Log throughout the function
    with open('logs/your_endpoint_direct.log', 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] VARIABLE VALUES - key variables\n")
        f.flush()
    
    # Log at function completion
    with open('logs/your_endpoint_direct.log', 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] FUNCTION COMPLETED SUCCESSFULLY\n")
        f.flush()
```

## Key Points

✅ **Always use `flush()`** - Forces immediate writing  
✅ **Use append mode (`'a'`)** - Preserves previous logs  
✅ **Include timestamps** - `datetime.now().isoformat()`  
✅ **Create logs directory** - `os.makedirs('logs', exist_ok=True)`  
✅ **Use descriptive filenames** - Include endpoint name  

## What NOT to Use

❌ `current_app.logger` - Unreliable  
❌ `print()` statements - Not captured  
❌ Flask's built-in logging - May not work  

## Test Your Logging

```bash
# Test endpoint
curl -X POST http://localhost:5000/api/your-endpoint -H "Content-Type: application/json" -d '{"test": "data"}'

# Check logs
ls -la logs/your_endpoint_direct.log
cat logs/your_endpoint_direct.log
```

## Real Example

See `app/api/workflow/routes.py` in `run_workflow_llm` function for complete working example.

---

**Remember**: If you need to debug an endpoint, implement direct file logging immediately. Don't waste time with Flask's logging system. 