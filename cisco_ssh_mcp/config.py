from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    # OIDC authentication settings (set to empty string or false to disable)
    oidc_url: str = ""
    oidc_realm: str = "network-operations"
    oidc_client_id: str = "mcp-cisco-server"
    oidc_client_secret: str = ""  # Required for OIDCProxy with client credentials
    
    # Enable/disable authentication (set to false for local development)
    auth_enabled: bool = True
    
    # Role to assign when auth is disabled (use 'viewer' for read-only local dev)
    unauthenticated_role: str = "network-admin"
    
    # Server base URL (required for OIDC callback redirect)
    base_url: str = "http://localhost:8000"
    
    # Example router inventory secrets (in production, use HashiCorp Vault or Docker secrets)
    router_inventory_json: str = "{}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()