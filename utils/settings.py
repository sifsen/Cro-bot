import json
import os

from typing import Optional, Any

class ServerSettings:
    def __init__(self):
        self.settings_file = "data/server_settings.json"
        self._ensure_data_directory()
        self.settings = self._load_settings()
        self.default_settings = {
            'server_name': None,
            'prefix': None,
            'log_channel_join_leave': None,
            'log_channel_mod_audit': None,
            'log_channel_edits': None,
            'log_channel_deletions': None,
            'log_channel_profiles': None,
            'mod_role': None,
            'admin_role': None,
            'starboard_channel': None,
            'starboard_threshold': 5,
            'tags': {},
            'twitch': {
                'notifications_channel': None,
                'streamers': {},
                'last_notifications': {},
                'notification_messages': {}
            },
            'youtube': {
                'notifications_channel': None,
                'channels': {},
                'last_videos': {},
                'ping_role': None
            }
        }

    #################################
    ## Ensure Data Directory
    #################################
    def _ensure_data_directory(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.settings_file):
            with open(self.settings_file, "w") as f:
                json.dump({"servers": {}}, f, indent=2)

    #################################
    ## Load Settings
    #################################
    def _load_settings(self) -> dict:
        try:
            with open(self.settings_file, "r") as f:
                return json.load(f)
        except:
            return {"servers": {}}

    #################################
    ## Save Settings
    #################################
    def _save_settings(self):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    #################################
    ## Get All Server Settings
    #################################
    def get_all_server_settings(self, guild_id: int) -> dict:
        """Get all settings for a guild"""
        guild_id = str(guild_id)
        if guild_id not in self.settings.get("servers", {}):
            self.settings.setdefault("servers", {})[guild_id] = self.default_settings.copy()
            self._save_settings()
        return self.settings["servers"][guild_id]

    #################################
    ## Set Server Setting
    #################################
    def set_server_setting(self, guild_id: int, setting: str, value: Any):
        """Set a specific setting for a guild"""
        guild_id = str(guild_id)
        if guild_id not in self.settings.get("servers", {}):
            self.settings.setdefault("servers", {})[guild_id] = self.default_settings.copy()
        self.settings["servers"][guild_id][setting] = value
        self._save_settings()

    #################################
    ## Get Server Setting
    #################################
    def get_server_setting(self, guild_id: int, setting: str) -> Any:
        """Get a specific setting for a guild"""
        return self.get_all_server_settings(guild_id).get(setting)

    #################################
    ## Get Mod Channel
    #################################
    def get_mod_channel(self, guild_id: int) -> Optional[int]:
        guild_settings = self.settings.get(str(guild_id), {})
        return guild_settings.get("mod_channel")

    #################################
    ## Set Mod Channel
    #################################
    def set_mod_channel(self, guild_id: int, channel_id: int):
        if str(guild_id) not in self.settings:
            self.settings[str(guild_id)] = {}
        self.settings[str(guild_id)]["mod_channel"] = channel_id
        self._save_settings()

    #################################
    ## Remove Mod Channel
    #################################
    def remove_mod_channel(self, guild_id: int):
        if str(guild_id) in self.settings:
            self.settings[str(guild_id)].pop("mod_channel", None)
            self._save_settings() 