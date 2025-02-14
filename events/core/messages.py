from discord.ext import commands
import discord
import json
import random
from datetime import datetime

class MessageEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages = {}

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

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        if message.guild.id not in self.deleted_messages:
            self.deleted_messages[message.guild.id] = {}

        self.deleted_messages[message.guild.id][message.channel.id] = {
            'content': message.content,
            'author': message.author,
            'timestamp': message.created_at,
            'reference': message.reference.message_id if message.reference else None,
            'attachments': [a.url for a in message.attachments] if message.attachments else []
        }

async def setup(bot):
    await bot.add_cog(MessageEvents(bot))