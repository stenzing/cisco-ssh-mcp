from fastmcp import FastMCP
from fastmcp.server.auth.oidc_proxy import OIDCProxy
from cisco_ssh_mcp.config import settings
from cisco_ssh_mcp.ssh_manager import ssh_manager
from cisco_ssh_mcp.rbac import authorize_command
from cisco_ssh_mcp.router_store import create_router_store
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cisco-ssh-mcp")

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

# Initialize router store based on configuration
router_store = create_router_store(
    settings.router_store_type,
    settings.router_store_config
)

# Initialize FastMCP with optional authentication middleware
mcp = FastMCP(
    "cisco-ssh-mcp",
    auth=auth_provider
)

# Bootup logging
logger.info("=" * 60)
logger.info("Cisco SSH MCP Server Booting Up")
logger.info("=" * 60)

# Log authentication configuration
if settings.auth_enabled:
    if settings.oidc_url.strip():
        logger.info(f"Authentication: ENABLED (OIDC)")
        logger.info(f"  OIDC URL: {settings.oidc_url}")
        logger.info(f"  Client ID: {settings.oidc_client_id}")
        logger.info(f"  Realm: {settings.oidc_realm}")
    else:
        logger.info("Authentication: ENABLED (but no OIDC URL configured)")
else:
    logger.info("Authentication: DISABLED")
    logger.info(f"  Unauthenticated role: {settings.unauthenticated_role}")

# Log router store configuration
logger.info(f"Router Store: {settings.router_store_type.upper()}")
routers = router_store.list_routers()
router_ids = [r.get("id", "unknown") for r in routers]
logger.info(f"  Routers loaded: {len(routers)}")
if router_ids:
    logger.info(f"  Router IDs: {', '.join(router_ids)}")
logger.info("=" * 60)


def get_user_roles(ctx) -> list[str]:
    """Extract user roles from context, with fallback for unauthenticated mode."""
    if ctx.token_claims:
        return ctx.token_claims.get("realm_access", {}).get("roles", [])
    # Fallback for unauthenticated/local mode
    return [settings.unauthenticated_role]


@mcp.tool()
def cisco_connect(host: str, username: str, password: str, connection_id: str, ctx) -> str:
    """Connect to a Cisco device via SSH by connection details."""
    roles = get_user_roles(ctx)
    if "network-admin" not in roles and "admin" not in roles:
        return "Access Denied: Only administrators can establish new SSH connections."

    return ssh_manager.connect(host, username, password, connection_id)


@mcp.tool()
def cisco_connect(router_id: str, ctx) -> str:
    """Connect to a Cisco device via SSH using pre-configured credentials.

    Args:
        router_id: ID of the router to connect to (from configured router store)
        ctx: FastMCP context for authentication/authorization

    Returns:
        Success message with connection details or error message
    """
    roles = get_user_roles(ctx)
    if "network-admin" not in roles and "admin" not in roles:
        return "Access Denied: Only administrators can establish new SSH connections."

    router_config = router_store.get_router(router_id)
    if not router_config:
        return f"Error: Router '{router_id}' not found in configured inventory."

    host = router_config.get("host")
    username = router_config.get("username")
    password = router_config.get("password")
    port = router_config.get("port", 22)

    if not all([host, username, password]):
        return f"Error: Router '{router_id}' is missing required credentials (host, username, password)."

    connection_id = ssh_manager.connect(host, username, password, router_id)
    return f"Connected to {host}:{port} as {username} (session ID: {connection_id})"

@mcp.tool()
def cisco_list_routers(ctx) -> str:
    """List all available routers from the configured store.

    Args:
        ctx: FastMCP context for authentication/authorization

    Returns:
        JSON string of all available routers with their IDs and host addresses
    """
    roles = get_user_roles(ctx)
    if "network-admin" not in roles and "admin" not in roles:
        return "Access Denied: Only administrators can list router inventory."

    routers = router_store.list_routers()
    return json.dumps(routers, indent=2)


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