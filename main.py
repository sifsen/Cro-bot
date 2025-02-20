import discord
import asyncio
import random
import json

from utils.settings.handler import ServerSettings
from discord.ext import commands
from config import TOKEN


class Bot(commands.Bot):
    def __init__(self):
        self.default_prefixes = ['$', '%', '?', '!', '.']
        
        super().__init__(
            command_prefix=self.get_prefix,
            intents=discord.Intents.all(),
            help_command=None,
        )
        self.settings = ServerSettings()

    #################################
    ## Setup Hook
    #################################   
    async def setup_hook(self):
        print("Loading core events...")
        for event in ['logging', 'messages', 'errors']:
            try:
                await self.load_extension(f"events.core.{event}")
                print(f"Loaded events.core.{event}")
            except Exception as e:
                print(f"Failed to load events.core.{event}: {e}")
        
        print("Loading feature events...")
        for event in ['starboard', 'tracking']:
            try:
                await self.load_extension(f"events.features.{event}")
                print(f"Loaded events.features.{event}")
            except Exception as e:
                print(f"Failed to load events.features.{event}: {e}")
        
        print("Loading cogs...")
        for extension in [
            "cogs.moderation",
            "cogs.admin",
            "cogs.casual",
            "cogs.fun",
            "cogs.help"
        ]:
            try:
                await self.load_extension(extension)

                print(f"Loaded {extension}")
            except Exception as e:
                print(f"Failed to load {extension}: {e}")

    #################################
    ## Ready and Status
    #################################   
    async def on_ready(self):
        print(f"{self.user} is online!")
        
        with open('data/strings.json', 'r') as f:
            strings = json.load(f)
            status_messages = strings['status']
        
        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.CustomActivity(
                name=random.choice(status_messages)
            )
        )
        
        #################################
        ## Status Rotator
        #################################
        async def rotate_status():
            while True:
                await asyncio.sleep(30)
                await self.change_presence(
                    status=discord.Status.idle,
                    activity=discord.CustomActivity(
                        name=random.choice(status_messages)
                    )
                )
        
        self.loop.create_task(rotate_status())

    #################################
    ## Get Prefix
    #################################
    async def get_prefix(self, message):
        if not message.guild:
            return self.default_prefixes

        settings = self.settings.get_all_server_settings(message.guild.id)
        prefixes = []
        
        custom_prefix = settings.get('prefix')
        if custom_prefix:
            prefixes.append(custom_prefix)
        
        if settings.get('use_default_prefix', True):
            prefixes.extend(self.default_prefixes)
        
        return prefixes if prefixes else self.default_prefixes

def main():
    bot = Bot()
    bot.run(TOKEN)

if __name__ == "__main__":
    main() 