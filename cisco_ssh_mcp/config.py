import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    keycloak_url: str = "https://auth.internal.net"
    keycloak_realm: str = "network-operations"
    keycloak_client_id: str = "mcp-cisco-server"
    
    # Example router inventory secrets (in production, use HashiCorp Vault or Docker secrets)
    router_inventory_json: str = "{}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()