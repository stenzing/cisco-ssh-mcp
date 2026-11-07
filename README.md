# Cisco SSH Model Context Protocol (MCP) Server

A secure, remote MCP server that bridges AI assistants with Cisco network infrastructure via SSH. Built with Python, it features OIDC-based authentication (Keycloak and other providers), role-based access control (RBAC), and containerized deployment.

---

## Features

- **Secure Remote Transport**: Runs over Streamable HTTP/SSE, decoupling credentials and execution from local LLM desktop clients
- **OIDC Integration**: Verifies JWTs issued by any OIDC provider (Keycloak, Auth0, Okta, etc.); supports multi-factor auth and FIDO2/WebAuthn hardware keys
- **Optional Authentication**: Run in development mode without authentication for local testing
- **Role-Based Access Control (RBAC)**: Granular permissions mapping user roles to permitted CLI commands:
  - `network-admin` / `admin`: full access (connect, execute any command)
  - `noc-viewer` / `viewer`: read-only (`show`, `ping`, `traceroute`, `dir`, `terminal length`)
- **Paramiko SSH Core**: Manages persistent sessions and safely executes commands on Cisco equipment
- **Poetry & Dockerized**: Modern dependency management with Poetry; secure, non-root multi-stage Docker build

---

## Project Structure

```
cisco-ssh-mcp/
├── pyproject.toml
├── Dockerfile
├── README.md
├── router_inventory.json (example router inventory for file store)
├── .env.example
└── cisco_ssh_mcp/
    ├── __init__.py
    ├── config.py
    ├── server.py
    ├── ssh_manager.py
    ├── rbac.py
    └── router_store.py (new - generic interface for credential stores)
```

---

## Quick Start

### Development Mode (Local, No Authentication)

For local development without an OIDC server:

```bash
# Option 1: Set environment variable to disable authentication
# Windows PowerShell:
#   $env:AUTH_ENABLED='false'

# Linux/macOS:
#   export AUTH_ENABLED=false

# Option 2: Create a .env file with:
#   AUTH_ENABLED=false

# Install dependencies
poetry install

# Run the server
poetry run mcp-server
```

The server will run on port `8000` with no authentication required. All operations are available as `network-admin`.

### Production Mode (With OIDC Authentication)

#### 1. Build the Container Image

```bash
docker build -t cisco-ssh-mcp:latest .
```

#### 2. Run the Server

Start the container in the background with OIDC configuration:

```bash
docker run -d \
  -p 8000:8000 \
  -e AUTH_ENABLED=true \
  -e OIDC_URL=https://auth.internal.net \
  -e OIDC_REALM=network-operations \
  -e OIDC_CLIENT_ID=mcp-cisco-server \
  --name cisco-mcp-server \
  cisco-ssh-mcp:latest
```

> **Note**: Replace `https://auth.internal.net`, `network-operations`, and `mcp-cisco-server` with your OIDC provider details.

The server listens on port `8000` via Streamable HTTP transport.

---

## Connecting to the MCP Server

### Client Configuration (Claude Desktop / MCP Clients)

#### Development Mode (No Auth)

```json
{
  "mcpServers": {
    "cisco-ssh-local": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

#### Production Mode (With OIDC)

Add the server entry to your MCP client configuration with an Authorization header:

```json
{
  "mcpServers": {
    "cisco-ssh-secure": {
      "url": "http://localhost:8000/sse",
      "headers": {
        "Authorization": "Bearer <YOUR_OIDC_JWT_TOKEN>"
      }
    }
  }
}
```

> **For production**: Replace `http://localhost:8000/sse` with your public endpoint (e.g., `https://mcp.internal.net/sse`).

### Obtaining an OIDC JWT Token

Before connecting in production mode, obtain a valid JWT token from your OIDC provider:

**Keycloak example:**
```bash
curl -X POST \
  "https://auth.internal.net/realms/network-operations/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=mcp-cisco-server" \
  -d "grant_type=password" \
  -d "username=<YOUR_USERNAME>" \
  -d "password=<YOUR_PASSWORD>"
```

**Auth0 example:**
```bash
curl -X POST \
  "https://your-domain.auth0.com/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=<YOUR_CLIENT_ID>" \
  -d "client_secret=<YOUR_CLIENT_SECRET>" \
  -d "grant_type=client_credentials" \
  -d "audience=https://your-api-domain.com/"
```

Extract the `access_token` from the JSON response and use it in your client config.

---

## Available Tools

Once connected, the MCP server exposes the following tools:

### `cisco_connect`

Connects to a Cisco device via SSH using pre-configured credentials from the router store.

**Parameters:**
- `router_id` (string): ID of the router to connect to (from configured router store)
- `ctx`: FastMCP context for authentication/authorization

**Authorization:** Requires `network-admin` or `admin` role.

### `cisco_list_routers`

Lists all available routers from the configured router store.

**Parameters:**
- `ctx`: FastMCP context for authentication/authorization

**Authorization:** Requires `network-admin` or `admin` role.

**Returns:** JSON string of all available routers with their IDs and host addresses.

### `cisco_execute`

Executes a CLI command on an active Cisco session with RBAC enforcement.

**Parameters:**
- `connection_id` (string): Session ID returned by `cisco_connect`
- `command` (string): CLI command to execute

**Authorization:**
- `network-admin` / `admin`: any command allowed
- `noc-viewer` / `viewer`: only operational/diagnostic commands (`show`, `ping`, `traceroute`, etc.)

---

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AUTH_ENABLED` | Enable/disable authentication (false for local dev) | `true` | No |
| `OIDC_URL` | OIDC provider URL (set to empty string to disable) | `""` | Yes (if auth enabled) |
| `OIDC_REALM` | OIDC realm or tenant name | `network-operations` | Yes (if auth enabled) |
| `OIDC_CLIENT_ID` | OIDC client ID for this service | `mcp-cisco-server` | Yes (if auth enabled) |
| `UNAUTHENTICATED_ROLE` | Role assigned when auth is disabled (`network-admin` or `viewer`) | `network-admin` | No |
| `ROUTER_STORE_TYPE` | Router store type: static, file, or env | `static` | No |
| `ROUTER_INVENTORY_JSON` | JSON string with router inventory (used by static store) | `{}` | No |
| `ROUTER_STORE_CONFIG` | Additional store-specific config as JSON | `{}` | No |

### Router Store Configuration

The server supports multiple router store types:

**Static Store** (`ROUTER_STORE_TYPE=static`):
```bash
ROUTER_INVENTORY_JSON='{"rtr-01": {"host": "10.0.1.1", "username": "admin", "password": "secret"}}'
```

**File Store** (`ROUTER_STORE_TYPE=file`):
```bash
ROUTER_STORE_CONFIG={"filepath": "./router_inventory.json"}
```

**Environment Store** (`ROUTER_STORE_TYPE=env`):
```bash
ROUTER_STORE_CONFIG={"prefix": "ROUTER_"}
ROUTER_RTR01_HOST=10.0.1.1
ROUTER_RTR01_USERNAME=admin
ROUTER_RTR01_PASSWORD=secret
```

---

## Security Notes

- **Development Mode**: When `AUTH_ENABLED=false`, all operations are available without authentication. Only use this for local development.
- **Production Mode**: Always enable authentication in production. Protect the server with TLS via a reverse proxy.
- **Credentials**: Do not hardcode credentials. Use Docker secrets, HashiCorp Vault, or environment variables. The router store interface allows flexible credential management.
- **Transport**: The server exposes an SSE endpoint; protect it with TLS in production (e.g., via a reverse proxy like NGINX).
- **RBAC**: Customize roles and allowed command patterns in `cisco_ssh_mcp/rbac.py` to match your organization's policy.
- **Router Store**: Implement custom stores for production use (e.g., Vault-backed, API-backed). See `cisco_ssh_mcp/router_store.py` for the interface.

---

## Development

### Local Run with Poetry

```bash
# Install dependencies
poetry install

# Development mode (no authentication)
# Windows PowerShell: $env:AUTH_ENABLED='false'
# Linux/macOS: export AUTH_ENABLED=false
poetry run mcp-server

# Production mode (with OIDC authentication)
# Windows PowerShell:
#   $env:AUTH_ENABLED='true'
#   $env:OIDC_URL='https://your-oidc-provider.com'
#   $env:OIDC_REALM='your-realm'
#   $env:OIDC_CLIENT_ID='your-client-id'
#   $env:ROUTER_STORE_TYPE='file'
#   $env:ROUTER_STORE_CONFIG='{"filepath": "./router_inventory.json"}'
# Linux/macOS:
#   export AUTH_ENABLED=true
#   export OIDC_URL=https://your-oidc-provider.com
#   export OIDC_REALM=your-realm
#   export OIDC_CLIENT_ID=your-client-id
#   export ROUTER_STORE_TYPE=file
#   export ROUTER_STORE_CONFIG='{"filepath": "./router_inventory.json"}'
poetry run mcp-server
```

### Custom Router Store Implementation

To implement a custom router store, extend the `RouterStore` abstract base class:

```python
from cisco_ssh_mcp.router_store import RouterStore

class VaultRouterStore(RouterStore):
    def __init__(self, vault_url: str, token: str):
        self.vault_url = vault_url
        self.token = token
    
    def get_router(self, router_id: str) -> Optional[dict]:
        # Fetch credentials from HashiCorp Vault
        ...
    
    def list_routers(self) -> list[dict]:
        # List all routers from Vault
        ...

# Then configure:
# ROUTER_STORE_TYPE=custom
# ROUTER_STORE_CONFIG={"vault_url": "...", "token": "..."}
```

### Run Tests (if added)

```bash
poetry run pytest
```

---

## License

MIT
