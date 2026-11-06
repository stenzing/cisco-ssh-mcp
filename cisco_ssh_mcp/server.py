from fastmcp import FastMCP
from fastmcp.server.auth.oidc_proxy import OIDCProxy
from cisco_ssh_mcp.config import settings
from cisco_ssh_mcp.ssh_manager import ssh_manager
from cisco_ssh_mcp.rbac import authorize_command

# Initialize OIDC Auth Provider (optional - for production)
# Uses OIDCProxy which works with Keycloak and other OIDC providers
auth_provider = None
if settings.auth_enabled and settings.oidc_url.strip():
    auth_provider = OIDCProxy(
        config_url=f"{settings.oidc_url.rstrip('/')}/.well-known/openid-configuration",
        client_id=settings.oidc_client_id,
        client_secret=settings.oidc_client_secret or None,
        base_url=settings.base_url or "http://localhost:8000"
    )

# Initialize FastMCP with optional authentication middleware
mcp = FastMCP(
    "cisco-ssh-mcp",
    auth=auth_provider
)

def get_user_roles(ctx) -> list[str]:
    """Extract user roles from context, with fallback for unauthenticated mode."""
    if ctx.token_claims:
        return ctx.token_claims.get("realm_access", {}).get("roles", [])
    # Fallback for unauthenticated/local mode
    return [settings.unauthenticated_role]

@mcp.tool()
def cisco_connect(host: str, username: str, password: str, connection_id: str, ctx) -> str:
    """Connect to a Cisco device via SSH and store the active session."""
    roles = get_user_roles(ctx)
    if "network-admin" not in roles and "admin" not in roles:
        return "Access Denied: Only administrators can establish new SSH connections."
    
    return ssh_manager.connect(host, username, password, connection_id)

@mcp.tool()
def cisco_execute(connection_id: str, command: str, ctx) -> str:
    """Execute a CLI command on an active Cisco session with RBAC enforcement."""
    roles = get_user_roles(ctx)
    
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