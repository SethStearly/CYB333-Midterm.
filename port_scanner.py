"""CYB 333: Rate-limited TCP connect scanner for assigned test hosts only."""

import argparse
import errno
import socket
import time
from datetime import datetime

LOCAL_HOSTS = {"127.0.0.1", "localhost"}
TEST_HOST = "scanme.nmap.org"
ERROR_HOST = "nonexistent-host.invalid"  # Reserved invalid domain for error handling.
CLOSED_CODES = {errno.ECONNREFUSED, 10061}  # 10061 is Windows WSAECONNREFUSED.
TIMEOUT_CODES = {errno.ETIMEDOUT, 10060}


def stamp(message: str) -> None:
    print(f"[{datetime.now().astimezone():%Y-%m-%d %H:%M:%S %Z}] {message}", flush=True)


def parse_ports(specification: str) -> list[int]:
    """Accept comma-separated numbers and inclusive ranges (e.g., 22,80,5050-5055)."""
    ports = []
    try:
        for piece in specification.split(","):
            piece = piece.strip()
            if "-" in piece:
                start_text, end_text = piece.split("-", 1)
                start, end = int(start_text), int(end_text)
                if start > end:
                    raise ValueError("Starting port cannot exceed ending port.")
                ports.extend(range(start, end + 1))
            else:
                ports.append(int(piece))
    except (ValueError, TypeError) as error:
        raise ValueError(f"Invalid port specification: {specification}. {error}") from error
    if not ports or any(port < 1 or port > 65535 for port in ports):
        raise ValueError("Port numbers must be between 1 and 65535.")
    return list(dict.fromkeys(ports))  # Remove duplicates without changing order.


def scan_port(address: str, port: int, timeout: float) -> str:
    """Attempt a TCP connection and distinguish refusal from a timeout.

    On Windows, connect_ex() with a timeout can return WSAEWOULDBLOCK
    (10035) while the connection is still being attempted. Using
    create_connection() waits for the connection to complete and raises
    the final socket error instead.
    """
    try:
        with socket.create_connection((address, port), timeout=timeout):
            return "OPEN"
    except ConnectionRefusedError:
        return "CLOSED (connection refused)"
    except (socket.timeout, TimeoutError):
        return "TIMED OUT / FILTERED"
    except OSError as error:
        if getattr(error, "winerror", None) == 10061 or error.errno in CLOSED_CODES:
            return "CLOSED (connection refused)"
        if getattr(error, "winerror", None) == 10060 or error.errno in TIMEOUT_CODES:
            return "TIMED OUT / FILTERED"
        return f"OTHER ERROR ({error})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Small TCP scanner for CYB 333")
    parser.add_argument("host", help="localhost, 127.0.0.1, or scanme.nmap.org")
    parser.add_argument("ports", help="Examples: 21,22,80,443 or 5050-5069")
    args = parser.parse_args()
    host = args.host.lower().strip()

    # Restrict connections to the targets described in the assignment.
    if host not in LOCAL_HOSTS | {TEST_HOST, ERROR_HOST}:
        stamp("ERROR: Target not permitted for this assignment.")
        raise SystemExit(1)
    try:
        ports = parse_ports(args.ports)
    except ValueError as error:
        stamp(f"ERROR: {error}")
        raise SystemExit(1) from None

    # An invalid domain name tests DNS error handling but is never scanned.
    if host == ERROR_HOST:
        try:
            socket.gethostbyname(host)
        except socket.gaierror as error:
            stamp(f"ERROR: Host cannot be resolved: {host} ({error})")
            raise SystemExit(1) from None
        stamp("ERROR: Reserved invalid domain unexpectedly resolved; refusing to scan.")
        raise SystemExit(1)

    is_external = host == TEST_HOST
    if len(ports) > (10 if is_external else 100):
        stamp("ERROR: Too many ports. Limit: 10 external or 100 localhost.")
        raise SystemExit(1)
    try:
        address = socket.gethostbyname(host)
    except socket.gaierror as error:
        stamp(f"ERROR: Host cannot be resolved: {host} ({error})")
        raise SystemExit(1) from None

    timeout, delay = (1.0, 0.5) if is_external else ((5.0 if len(ports) == 1 else 0.5), 0.05)
    stamp(f"Scanning {host} ({address}) | ports: {args.ports}")
    started = time.monotonic()
    counts = {"OPEN": 0, "CLOSED": 0, "OTHER": 0}
    for index, port in enumerate(ports):
        result = scan_port(address, port, timeout)
        print(f"Port {port:5d}: {result}", flush=True)
        if result.startswith("OPEN"):
            counts["OPEN"] += 1
        elif result.startswith("CLOSED"):
            counts["CLOSED"] += 1
        else:
            counts["OTHER"] += 1
        if index < len(ports) - 1:
            time.sleep(delay)  # Pause between attempts to avoid aggressive scanning.
    stamp(f"Finished: {len(ports)} scanned, {counts['OPEN']} open, "
          f"{counts['CLOSED']} closed, {counts['OTHER']} other | "
          f"{time.monotonic() - started:.2f} seconds")


if __name__ == "__main__":
    main()
