#!/bin/bash

# Ollama Service Management Script

case "$1" in
    start)
        echo "Starting Ollama service..."
        launchctl load /Users/autojenny/Library/LaunchAgents/com.ollama.serve.plist
        sleep 2
        if curl -s http://localhost:11434/api/tags > /dev/null; then
            echo "✅ Ollama is running"
        else
            echo "❌ Ollama failed to start"
        fi
        ;;
    stop)
        echo "Stopping Ollama service..."
        launchctl unload /Users/autojenny/Library/LaunchAgents/com.ollama.serve.plist
        echo "✅ Ollama stopped"
        ;;
    restart)
        echo "Restarting Ollama service..."
        launchctl unload /Users/autojenny/Library/LaunchAgents/com.ollama.serve.plist
        sleep 2
        launchctl load /Users/autojenny/Library/LaunchAgents/com.ollama.serve.plist
        sleep 2
        if curl -s http://localhost:11434/api/tags > /dev/null; then
            echo "✅ Ollama restarted successfully"
        else
            echo "❌ Ollama failed to restart"
        fi
        ;;
    status)
        if curl -s http://localhost:11434/api/tags > /dev/null; then
            echo "✅ Ollama is running"
            echo "Available models:"
            curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print('  - ' + '\n  - '.join([m['name'] for m in data.get('models', [])]) if data.get('models') else '  No models installed')"
        else
            echo "❌ Ollama is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Ollama service"
        echo "  stop    - Stop Ollama service"
        echo "  restart - Restart Ollama service"
        echo "  status  - Check Ollama status and show models"
        exit 1
        ;;
esac
