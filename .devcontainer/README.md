# Devcontainer setup for Cisco SSH MCP Server

This directory contains configuration files for running the project in a development container.

## Files

- **devcontainer.json** - Main devcontainer configuration
- **launch.json** (in `.vscode/` folder) - VS Code debug configurations

## Quick Start

1. **Open in Dev Container:**
   - Press `F1` and select "Dev Containers: Reopen in Container"
   - Or click the green icon in the bottom-left corner

2. **Wait for setup to complete:**
   - The container will be built
   - Python dependencies will be installed via Poetry

3. **Debug the server:**
   - Press `F5` or go to Run and Debug
   - Select "Python: Current File" configuration
   - The server will start with authentication disabled for local development

## Configuration Details

### Environment Variables (in `.vscode/launch.json`)
- `AUTH_ENABLED=false` - Disables OIDC authentication for local debugging
- `ROUTER_STORE_TYPE=static` - Uses static router configuration
- `ROUTER_INVENTORY_JSON` - Pre-configured router credentials (host, username, password)

### Debug Settings
- Integrated terminal for output
- Server runs on port 8000 (forwarded to host)

## Advanced Usage

### Adding More Routers
Edit the `ROUTER_INVENTORY_JSON` in `.vscode/launch.json`:

```json
{
  "ROUTER_INVENTORY_JSON": "{\"rtr-01\": {\"host\": \"10.0.1.1\", \"username\": \"admin\", \"password\": \"secret\"}, \"rtr-02\": {\"host\": \"10.0.2.1\", \"username\": \"netops\", \"password\": \"pass\"}}"
}
```

### Connecting to Real Cisco Router
1. Ensure your host has network access to the Cisco router
2. Update the router credentials in `.vscode/launch.json`
3. The devcontainer will use the host's network stack
4. Password authentication is used (no SSH keys required)

## Troubleshooting

### Container Build Fails
- Check Docker is running
- Verify internet connectivity
- Try "Dev Containers: Rebuild Container"

### SSH Connection to Router Fails
- Verify network access from container to router
- Check firewall rules
- Test manually: `ssh username@router-ip`

## Notes

- The devcontainer uses Python 3.11 (matching pyproject.toml)
- All dependencies are managed by Poetry
- The server runs on port 8000 and is forwarded to host
- SSH client is pre-installed in the base image
- Router connections use password authentication
