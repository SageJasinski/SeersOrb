"""
Seer's Orb - MTG Deck Building Assistant
Application entry point.
"""
import sys
import threading
import webbrowser
from config import get_config

# Check if running as desktop app or development server
DESKTOP_MODE = "--desktop" in sys.argv or getattr(sys, 'frozen', False)


def run_flask_server(app, host: str, port: int):
    """Run Flask server in a thread."""
    app.run(host=host, port=port, debug=False, use_reloader=False)


def run_desktop():
    """Run as desktop application with native window."""
    try:
        import webview
    except ImportError:
        print("pywebview not installed. Run: pip install pywebview")
        print("Falling back to browser mode...")
        run_browser()
        return
    
    from app import create_app
    
    config = get_config()
    app = create_app(config)
    
    host = "127.0.0.1"
    port = 5000
    
    # Start Flask in background thread
    server_thread = threading.Thread(
        target=run_flask_server, 
        args=(app, host, port),
        daemon=True
    )
    server_thread.start()
    
    # Create native window
    webview.create_window(
        title=f"{config.APP_NAME} v{config.VERSION}",
        url=f"http://{host}:{port}",
        width=1400,
        height=900,
        min_size=(1200, 700)
    )
    webview.start()


def run_browser():
    """Run as development server (opens in browser)."""
    from app import create_app
    
    config = get_config()
    app = create_app(config)
    
    host = "127.0.0.1"
    port = 5000
    url = f"http://{host}:{port}"
    
    # Open browser after short delay
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(url)
    
    if not app.debug:
        threading.Thread(target=open_browser, daemon=True).start()
    
    print(f"\n✨ {config.APP_NAME} v{config.VERSION}")
    print(f"🌐 Running at: {url}")
    print("📋 Press Ctrl+C to quit\n")
    
    app.run(host=host, port=port, debug=config.DEBUG)


def main():
    """Main entry point."""
    if DESKTOP_MODE:
        run_desktop()
    else:
        run_browser()


if __name__ == "__main__":
    main()
