\# Cisco SSH Model Context Protocol (MCP) Server



A secure, remote MCP server built in Python that bridges AI assistants with Cisco network infrastructure. It features token-based authentication via \*\*Keycloak\*\* (supporting FIDO2/WebAuthn hardware keys like YubiKeys), role-based access control (RBAC), and containerized multi-stage Docker deployment.



\---



\## Features



\- \*\*Secure Remote Transport:\*\* Runs over Streamable HTTP/SSE, decoupling credentials and execution from local LLM desktop clients.

\- \*\*Keycloak Integration:\*\* Verifies JSON Web Tokens (JWTs) issued by Keycloak, enabling robust authentication workflows, including multi-factor and hardware security keys.

\- \*\*Role-Based Access Control (RBAC):\*\* Granular permission enforcement mapping user roles (`network-admin`, `noc-viewer`) to permitted CLI commands (e.g., restricting viewers to read-only `show` and diagnostic commands).

\- \*\*Paramiko SSH Core:\*\* Manages persistent sessions and executes commands safely on target Cisco equipment.

\- \*\*Poetry \& Dockerized:\*\* Modern dependency management with Poetry and a secure, non-root multi-stage Docker build.



\---



\## Project Structure



```text

cisco-ssh-mcp/

├── pyproject.toml

├── Dockerfile

├── README.md

└── cisco\_ssh\_mcp/

&#x20;   ├── \_\_init\_\_.py

&#x20;   ├── config.py

&#x20;   ├── server.py

&#x20;   ├── ssh\_manager.py

&#x20;   └── rbac.py

