"""CYB 333: Run localhost socket/port-scanner demonstrations as one safe batch.

The test runner only makes TCP connections to 127.0.0.1.  It never scans
external networks or mislabels a timeout as proof that a port is closed.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
EVIDENCE = PROJECT / 'evidence'
EVIDENCE.mkdir(exist_ok=True)
REPORT = EVIDENCE / 'test_results.txt'
SERVER_LOG = EVIDENCE / 'server_log.txt'
PYTHON = sys.executable
lines: list[str] = []
results: list[tuple[str, bool]] = []


def stamp() -> str:
    return datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')


def record(message: str = '') -> None:
    print(message, flush=True)
    lines.append(message)


def run_case(title: str, script: str, *args: str,
             exit_code: int = 0, contains: tuple[str, ...] = (),
             absent: tuple[str, ...] = ()) -> bool:
    record(f'\n========== {title} ==========')
    record('Command: python ' + ' '.join([script, *args]))
    try:
        run = subprocess.run(
            [PYTHON, str(PROJECT / script), *args],
            cwd=PROJECT, capture_output=True, text=True, timeout=60,
        )
        output = (run.stdout + run.stderr).rstrip()
        record(output)
        errors = [f'missing expected output: {s}' for s in contains if s not in output]
        errors += [f'unexpected output: {s}' for s in absent if s in output]
        passed = run.returncode == exit_code and not errors
        if run.returncode != exit_code:
            errors.append(f'exit code {run.returncode} instead of {exit_code}')
        record(f'Result: {"PASS" if passed else "FAIL"}')
        for error in errors:
            record('  - ' + error)
    except subprocess.TimeoutExpired:
        passed = False
        record('Result: FAIL (test took more than 60 seconds)')
    results.append((title, passed))
    return passed


def server_ready(process: subprocess.Popen) -> bool:
    for _ in range(35):
        if process.poll() is not None:
            return False
        try:
            with socket.create_connection(('127.0.0.1', 5050), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def main() -> None:
    record('CYB 333 MIDTERM - AUTOMATED LOCAL TESTS v3')
    record('Started: ' + stamp())
    record('Scanning scope: 127.0.0.1 ONLY (no external host scanning)')
    record('Note: Timed out/filtered is not the same as closed.')
    record('Windows firewall/security software can filter unused localhost ports.')
    record('We verify CLOSED by scanning port 5050 AFTER stopping its server.')

    # Start one disposable local server for the complete connected-test section.
    with SERVER_LOG.open('w', encoding='utf-8') as server_log:
        server = subprocess.Popen(
            [PYTHON, '-u', str(PROJECT / 'server.py')],
            stdout=server_log, stderr=subprocess.STDOUT, cwd=PROJECT,
        )
        try:
            ready = server_ready(server)
            record('\n========== SERVER STARTUP ==========')
            record('PASS: Listening on 127.0.0.1:5050' if ready else
                   'FAIL: Could not start the local server on port 5050')
            results.append(('SERVER STARTUP', ready))
            if not ready:
                record('Check that no other server has port 5050 open.')
                return
            run_case('CLIENT: TWO MESSAGES AND CLEAN DISCONNECT', 'client.py',
                     '--messages', 'Hello from my CYB 333 midterm!',
                     'Testing socket connection', 'quit',
                     contains=('Connected to server',
                               'Server received: Hello from my CYB 333 midterm!',
                               'Server received: Testing socket connection',
                               'Client disconnected cleanly.'))
            run_case('SCANNER: OPEN PORT + OTHER PORT STATUS', 'port_scanner.py',
                     '127.0.0.1', '5050-5055',
                     contains=('Port  5050: OPEN', '6 scanned,'))
            run_case('SCANNER: COMMON PORTS', 'port_scanner.py',
                     '127.0.0.1', '21,22,80,443',
                     contains=('Port    21:', 'Port    22:', 'Port    80:',
                               'Port   443:', '4 scanned,'))
            run_case('SCANNER: INVALID PORT', 'port_scanner.py',
                     '127.0.0.1', '70000', exit_code=1,
                     contains=('Port numbers must be between 1 and 65535',))
            run_case('SCANNER: BAD HOSTNAME', 'port_scanner.py',
                     'nonexistent-host.invalid', '80', exit_code=1,
                     contains=('Host cannot be resolved',))
            run_case('PERFORMANCE: 5 PORTS', 'port_scanner.py',
                     '127.0.0.1', '5050-5054', contains=('5 scanned,', ' seconds'))
            run_case('PERFORMANCE: 20 PORTS', 'port_scanner.py',
                     '127.0.0.1', '5050-5069', contains=('20 scanned,', ' seconds'))
        finally:
            server.terminate()
            try:
                server.wait(timeout=4)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=4)
    record('\n========== SERVER SHUTDOWN ==========')
    record('Stopped the test server on port 5050.')
    # A refused connection is actual CLOSED evidence; a timeout is not.
    run_case('SCANNER: CLOSED PORT AFTER SERVER STOP', 'port_scanner.py',
             '127.0.0.1', '5050', contains=('Port  5050: CLOSED (connection refused)',))
    run_case('CLIENT: CONNECTION REFUSED WHEN SERVER OFFLINE', 'client.py',
             '--messages', 'hello', exit_code=1,
             contains=('Connection refused',))


if __name__ == '__main__':
    try:
        main()
    finally:
        record('\n========== SUMMARY ==========')
        passed = sum(ok for _, ok in results)
        record(f'{passed}/{len(results)} checks passed')
        for name, ok in results:
            if not ok:
                record('NEEDS REVIEW: ' + name)
        record('Completed: ' + stamp())
        REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        record('Saved report: ' + str(REPORT))
        record('Server log: ' + str(SERVER_LOG))
        if passed != len(results):
            raise SystemExit(1)
