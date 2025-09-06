#!/usr/bin/env python3
"""
Simple script to start the Flask server with proper error handling.
"""

import sys
import os

def main():
    try:
        # Check if required files exist
        required_files = ['app.py', 'server_classes.py', 'game.py']
        for file in required_files:
            if not os.path.exists(file):
                print(f"Error: Required file '{file}' not found!")
                return 1
        
        # Import and run the app
        from app import app, socketio
        
        print("=" * 50)
        print("STARTING IFTHEM LOGIC GAME SERVER")
        print("=" * 50)
        print("Server will be available at: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Run the server
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you have installed all dependencies:")
        print("pip install -r requirements.txt")
        return 1
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
