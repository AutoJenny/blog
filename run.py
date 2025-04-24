from app import create_app
import os
import sys


def main():
    app = create_app()
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    try:
        app.run(host="127.0.0.1", port=port, debug=True)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Error: Port {port} is still in use.")
            print(
                "Please run './run_server.sh' again to force kill any existing processes."
            )
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
