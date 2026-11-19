"""CYB 333: TCP client with interactive and automated-message modes."""

import argparse
import socket
from datetime import datetime

HOST = "127.0.0.1"
DEFAULT_PORT = 5050


def stamp(message: str) -> None:
    print(f"[{datetime.now().astimezone():%Y-%m-%d %H:%M:%S %Z}] {message}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Local TCP client for CYB 333")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--messages", nargs="+", help="Messages to send without typing each one")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Port must be between 1 and 65535")

    try:
        # create_connection automatically opens the socket and connects.
        with socket.create_connection((HOST, args.port), timeout=5) as client:
            client.settimeout(10)
            stamp(f"Connected to server at {HOST}:{args.port}")
            with client.makefile("r", encoding="utf-8") as incoming:
                if args.messages is None:
                    print("Enter a message; type 'quit' to disconnect.")
                    while True:
                        try:
                            message = input("You: ")
                        except (EOFError, KeyboardInterrupt):
                            message = "quit"
                            print()
                        if not exchange(client, incoming, message):
                            break
                else:
                    for message in args.messages:
                        print(f"You: {message}")
                        if not exchange(client, incoming, message):
                            break
            stamp("Client disconnected cleanly.")
    except ConnectionRefusedError:
        stamp(f"ERROR: Connection refused. Is the server running on {HOST}:{args.port}?")
        raise SystemExit(1) from None
    except (TimeoutError, ConnectionError, OSError) as error:
        stamp(f"ERROR: Could not communicate with server: {error}")
        raise SystemExit(1) from error


def exchange(client: socket.socket, incoming, message: str) -> bool:
    """Send one message and return False when the client should exit."""
    # The newline separates messages over a byte-stream TCP connection.
    client.sendall((message + "\n").encode("utf-8"))
    response = incoming.readline()
    if not response:
        stamp("Server closed the connection without a response.")
        return False
    stamp(f"Server response: {response.rstrip()}")
    return message.lower() != "quit"


if __name__ == "__main__":
    main()
