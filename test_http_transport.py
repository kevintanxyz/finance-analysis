#!/usr/bin/env python
"""
Test HTTP transport server startup.
"""
import subprocess
import time
import requests
import signal
import sys

def test_http_server():
    """Start HTTP server and verify it responds."""
    print("Starting HTTP server...")

    # Start server in background
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.server", "--transport", "streamable-http", "--port", "3001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to start
    time.sleep(3)

    try:
        # Check if server is running
        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            print("❌ Server exited unexpectedly")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return False

        # Try to connect to server
        try:
            response = requests.get("http://localhost:3001", timeout=2)
            print(f"✅ HTTP server responding on port 3001 (status: {response.status_code})")
            success = True
        except requests.exceptions.ConnectionError:
            # Server might still be running but not responding
            # Capture output for debugging
            stdout_data = proc.stdout.read() if proc.stdout else ""
            stderr_data = proc.stderr.read() if proc.stderr else ""

            print("❌ Could not connect to HTTP server on port 3001")
            if stderr_data:
                print("Server STDERR:")
                print(stderr_data[:1000])  # First 1000 chars
            success = False
        except Exception as e:
            print(f"❌ Error connecting to server: {e}")
            success = False

    finally:
        # Kill server
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Server stopped")

    return success

if __name__ == "__main__":
    success = test_http_server()
    sys.exit(0 if success else 1)
