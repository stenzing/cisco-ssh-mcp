import re

VIEWER_ALLOWED_PATTERNS = [
    r"^\s*show\b",
    r"^\s*ping\b",
    r"^\s*traceroute\b",
    r"^\s*dir\b",
    r"^\s*terminal length\b"
]

def authorize_command(roles: list[str], command: str) -> tuple[bool, str]:
    """Validate if the user's assigned roles permit the requested command."""
    if not roles:
        return False, "RBAC Error: No roles assigned."
    
    if "network-admin" in roles or "admin" in roles:
        return True, ""
    
    if "noc-viewer" in roles or "viewer" in roles:
        for pattern in VIEWER_ALLOWED_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True, ""
        return False, "RBAC Error: 'viewer' role is restricted to operational 'show' and diagnostic commands."
    
    return False, "RBAC Error: Unauthorized role assignment."