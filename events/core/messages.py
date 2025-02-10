from discord.ext import commands
import discord
import json
import random

class MessageEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.guild:
            self.bot.settings.set_server_setting(
                message.guild.id, 
                "server_name", 
                message.guild.name
            )

        if self.bot.user.mentioned_in(message) and not any(
            m in message.content for m in ['@everyone', '@here']
        ):
            if not message.reference and message.type != discord.MessageType.reply:
                try:
                    with open('data/strings.json', 'r') as f:
                        strings = json.load(f)
                        responses = strings['ping_responses']
                        await message.channel.send(random.choice(responses))
                except Exception as e:
                    print(f"Error handling ping response: {e}")

async def setup(bot):
    await bot.add_cog(MessageEvents(bot)) 