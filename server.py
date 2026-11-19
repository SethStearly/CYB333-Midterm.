"""CYB 333: Simple localhost TCP echo server."""

import argparse
import socket
from datetime import datetime

HOST = "127.0.0.1"  # Only listen on this computer.
DEFAULT_PORT = 5050


def stamp(message: str) -> None:
    """Show the local date and time for assignment screenshots."""
    print(f"[{datetime.now().astimezone():%Y-%m-%d %H:%M:%S %Z}] {message}", flush=True)


def handle_client(connection: socket.socket, address: tuple) -> None:
    """Read newline-delimited messages and respond to each one."""
    stamp(f"Client connected: {address[0]}:{address[1]}")
    connection.settimeout(20)
    try:
        with connection, connection.makefile("r", encoding="utf-8") as incoming:
            for line in incoming:
                message = line.rstrip("\r\n")
                stamp(f"Received from client: {message}")
                if message.lower() == "quit":
                    response = "Goodbye! Connection closing."
                else:
                    response = f"Server received: {message}"
                connection.sendall((response + "\n").encode("utf-8"))
                stamp(f"Sent to client: {response}")
                if message.lower() == "quit":
                    break
    except (ConnectionError, TimeoutError, OSError) as error:
        stamp(f"Client connection ended with an error: {error}")
    finally:
        stamp("Client disconnected; connection closed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Local TCP server for CYB 333")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, args.port))
            server.listen(5)
            stamp(f"Server listening on {HOST}:{args.port}")
            print("Press Ctrl+C to stop the server.", flush=True)
            while True:
                connection, address = server.accept()
                handle_client(connection, address)
    except KeyboardInterrupt:
        stamp("Server stopped safely with Ctrl+C.")
    except OSError as error:
        stamp(f"ERROR: Server could not start or continue: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
