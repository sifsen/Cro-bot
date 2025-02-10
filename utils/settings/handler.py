import json
import os
from typing import Dict, Any, Optional
from .defaults import DEFAULT_SETTINGS

class ServerSettings:
    def __init__(self):
        self.settings_file = 'data/settings.json'
        self.settings = self._load_settings()
        
        os.makedirs('data', exist_ok=True)

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_settings(self) -> None:
        """Save settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def get_server_setting(self, guild_id: int, setting: str) -> Optional[Any]:
        """Get a specific setting for a server"""
        guild_settings = self.settings.get(str(guild_id), {})
        return guild_settings.get(setting, DEFAULT_SETTINGS.get(setting))

    def get_all_server_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get all settings for a server"""
        guild_settings = self.settings.get(str(guild_id), {})
        return {**DEFAULT_SETTINGS, **guild_settings}

    def set_server_setting(self, guild_id: int, setting: str, value: Any) -> None:
        """Set a specific setting for a server"""
        if str(guild_id) not in self.settings:
            self.settings[str(guild_id)] = {}
            
        self.settings[str(guild_id)][setting] = value
        self._save_settings()

    def remove_server_setting(self, guild_id: int, setting: str) -> None:
        """Remove a specific setting for a server"""
        if str(guild_id) in self.settings:
            self.settings[str(guild_id)].pop(setting, None)
            self._save_settings()

    def clear_server_settings(self, guild_id: int) -> None:
        """Clear all settings for a server"""
        self.settings.pop(str(guild_id), None)
        self._save_settings() 