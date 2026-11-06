from fastmcp import FastMCP
from fastmcp.server.auth.providers.keycloak import KeycloakAuthProvider
from cisco_ssh_mcp.config import settings
from cisco_ssh_mcp.ssh_manager import ssh_manager
from cisco_ssh_mcp.rbac import authorize_command

# Initialize Keycloak Auth Provider for hardware-key verified JWTs
auth_provider = KeycloakAuthProvider(
    url=settings.keycloak_url,
    realm=settings.keycloak_realm,
    client_id=settings.keycloak_client_id
)

# Initialize FastMCP with authentication middleware
mcp = FastMCP(
    "cisco-ssh-mcp",
    auth=auth_provider
)

@mcp.tool()
def cisco_connect(host: str, username: str, password: str, connection_id: str, ctx) -> str:
    """Connect to a Cisco device via SSH and store the active session."""
    # Context automatically exposes verified claims/roles from Keycloak token
    roles = ctx.token_claims.get("realm_access", {}).get("roles", [])
    if "network-admin" not in roles and "admin" not in roles:
        return "Access Denied: Only administrators can establish new SSH connections."
    
    return ssh_manager.connect(host, username, password, connection_id)

@mcp.tool()
def cisco_execute(connection_id: str, command: str, ctx) -> str:
    """Execute a CLI command on an active Cisco session with RBAC enforcement."""
    roles = ctx.token_claims.get("realm_access", {}).get("roles", [])
    
    # Enforce role-based command restrictions
    is_allowed, error_msg = authorize_command(roles, command)
    if not is_allowed:
        return error_msg
        
    return ssh_manager.execute(connection_id, command)

def main():
    # Run server via Streamable HTTP transport bound to local interface or container network
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()