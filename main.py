import discord
import asyncio
import random
import json
import os

from utils.settings import ServerSettings
from discord.ext import commands
from config import TOKEN


class Bot(commands.Bot):
    def __init__(self):
        self.default_prefixes = ['$', '%', '?', '!', '.', ',']
        
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
        print("Loading cogs...")
        for filename in os.listdir("./cogs"):
            print(f"Found file: {filename}")
            if filename.endswith(".py") and not filename.startswith("__"):
                print(f"Loading cog: cogs.{filename[:-3]}")
                await self.load_extension(f"cogs.{filename[:-3]}")
        
        print("Loading events...")
        await self.load_extension("events.handlers")
        await self.load_extension("events.messages")
        await self.load_extension("events.logging")

    #################################
    ## Ready and Status
    #################################   
    async def on_ready(self):
        print(f"{self.user} is ready and online!")
        
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
        prefixes = self.default_prefixes.copy()
        return prefixes

def main():
    bot = Bot()
    bot.run(TOKEN)

if __name__ == "__main__":
    main() 