"""Router credential storage abstractions and implementations."""
from abc import ABC, abstractmethod
from typing import Optional
import json
import os


class RouterStore(ABC):
    """Abstract base class for router credential storage."""

    @abstractmethod
    def get_router(self, router_id: str) -> Optional[dict]:
        """Return connection details for a router by ID.

        Returns dict with keys: host, username, password, and optionally port.
        Returns None if router not found.
        """
        pass

    @abstractmethod
    def list_routers(self) -> list[dict]:
        """Return all available routers as list of dicts."""
        pass


class StaticRouterStore(RouterStore):
    """Load router inventory from static JSON configuration."""

    def __init__(self, inventory_json: str):
        """Initialize with JSON string containing router inventory."""
        try:
            self._inventory = json.loads(inventory_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid router inventory JSON: {e}")

    def get_router(self, router_id: str) -> Optional[dict]:
        """Get router by ID from static inventory."""
        return self._inventory.get(router_id)

    def list_routers(self) -> list[dict]:
        """List all routers in static inventory."""
        return [
            {"id": router_id, **details}
            for router_id, details in self._inventory.items()
        ]


class FileRouterStore(RouterStore):
    """Load router inventory from a JSON file."""

    def __init__(self, filepath: str):
        """Initialize with path to JSON file containing router inventory."""
        self._filepath = filepath
        self._load_inventory()

    def _load_inventory(self) -> None:
        """Load or reload inventory from file."""
        with open(self._filepath, "r") as f:
            self._inventory = json.load(f)

    def get_router(self, router_id: str) -> Optional[dict]:
        """Get router by ID from file-based inventory."""
        return self._inventory.get(router_id)

    def list_routers(self) -> list[dict]:
        """List all routers in file-based inventory."""
        return [
            {"id": router_id, **details}
            for router_id, details in self._inventory.items()
        ]


class EnvRouterStore(RouterStore):
    """Load router inventory from environment variables."""

    def __init__(self, prefix: str = "ROUTER_"):
        """Initialize with environment variable prefix.

        Expected env var format:
        ROUTER_<ID>_HOST=<host>
        ROUTER_<ID>_USERNAME=<username>
        ROUTER_<ID>_PASSWORD=<password>
        ROUTER_<ID>_PORT=<port> (optional, defaults to 22)
        """
        self._prefix = prefix.rstrip("_") + "_"
        self._inventory = self._load_from_env()

    def _load_from_env(self) -> dict:
        """Load router configs from environment variables."""
        inventory = {}
        for key, value in os.environ.items():
            if key.startswith(self._prefix):
                parts = key[len(self._prefix):].split("_", 1)
                if len(parts) == 2:
                    router_id, field = parts
                    if router_id not in inventory:
                        inventory[router_id] = {}
                    if field == "PORT":
                        inventory[router_id][field.lower()] = int(value)
                    else:
                        inventory[router_id][field.lower()] = value
        return inventory

    def get_router(self, router_id: str) -> Optional[dict]:
        """Get router by ID from environment variables."""
        return self._inventory.get(router_id)

    def list_routers(self) -> list[dict]:
        """List all routers from environment variables."""
        return [
            {"id": router_id, **details}
            for router_id, details in self._inventory.items()
        ]


def create_router_store(store_type: str, store_config: dict) -> RouterStore:
    """Factory function to create router store based on type and config."""
    if store_type == "static":
        inventory_json = store_config.get("inventory_json", "{}")
        return StaticRouterStore(inventory_json)
    elif store_type == "file":
        filepath = store_config.get("filepath", "")
        if not filepath:
            raise ValueError("FileRouterStore requires 'filepath' in config")
        return FileRouterStore(filepath)
    elif store_type == "env":
        prefix = store_config.get("prefix", "ROUTER_")
        return EnvRouterStore(prefix)
    else:
        raise ValueError(f"Unknown router store type: {store_type}")
