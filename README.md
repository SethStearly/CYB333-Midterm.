# CYB 333 midterm — localhost test batch (v3)

The project contains `server.py`, `client.py`, `port_scanner.py`, and `run_midterm_tests.py`.
All socket and scanning tests are limited to localhost; the automatic runner **never contacts external hosts**.

## Windows: one-command verification

In VS Code, open the extracted `CYB333_Windows_Test_v3` folder, then open a new terminal and run:

```powershell
python .\run_midterm_tests.py
```

The runner starts the server, sends two messages, tests the port scanner and input validation, compares five- and twenty-port ranges, then stops the server, scans the now-closed 5050 port, and verifies the client shows a refused connection. It creates `evidence/test_results.txt` and `evidence/server_log.txt` with **real timestamps**.

## Why v3 uses a different closed-port test

On this student's Windows machine, port 5050 was OPEN while a test server was listening, but idle ports such as 5051 and 5052 showed `TIMED OUT / FILTERED` (likely a networking or security-software policy; cause not confirmed). A timeout cannot be called CLOSED. Version 3 proves the difference with a **known port**: it scans 5050 while the server is running (OPEN), shuts down the server, then scans 5050 again (should be CLOSED / connection refused). If a firewall still prevents the refusal, the runner marks that test FAIL rather than claiming success.

## Screenshots for the submission

Use real Windows screenshots (`Win + Shift + S`) showing timestamps. The test results log is supplemental evidence. To show the **server listening and receiving** messages directly, use two VS Code terminals:

Terminal 1: `python server.py`

Terminal 2: `python client.py --messages "Hello from my CYB 333 midterm!" "Testing socket connection" quit`

Screenshot both terminals. Stop Terminal 1 with Ctrl+C, then use Terminal 2: `python client.py --messages hello` to show a refused connection. The automatic batch also tests those actions and provides `evidence/server_log.txt`.

Save screenshots in `screenshots/` and upload `.py` scripts to GitHub. Do not upload credentials or private documents.

## External target ethical note

The course lists `scanme.nmap.org`, but the Nmap project's published permission is specifically for use of **Nmap** on that host, not necessarily Python third-party scanners: https://nmap.org/book/legal-issues.html . For external proof, use the official Nmap executable with a conservative small number of ports, or obtain explicit authorization before using your own Python scanner. The batch tool does not scan the Internet.

Reflection: **write the 1–2 pages yourself**; discuss the network security restrictions encountered, your real coding/testing steps and AI prompts, legal authorization, and an APA reference. Suggested source: Nmap Project. (n.d.). *Legal issues*. https://nmap.org/book/legal-issues.html
