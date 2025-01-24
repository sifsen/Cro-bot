import discord
import os

from discord.ext import commands
from config import TOKEN

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="$",
            intents=discord.Intents.all(),
            help_command=None
        )

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

    #################################
    ## On Ready Hook
    #################################   
    async def on_ready(self):
        print(f"{self.user} is ready and online!")
        await self.change_presence(activity=discord.Game(name="!help"))

def main():
    bot = Bot()
    bot.run(TOKEN)

if __name__ == "__main__":
    main() 