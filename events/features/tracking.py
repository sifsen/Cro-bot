import discord
from discord.ext import commands
from datetime import datetime

class MessageTrackingEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.deleted_messages = {}
        self.edited_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
            
        if not message.guild:
            return
            
        if not message.content and not message.attachments:
            return
            
        if message.guild.id not in self.deleted_messages:
            self.deleted_messages[message.guild.id] = {}
            
        self.deleted_messages[message.guild.id][message.channel.id] = {
            'content': message.content,
            'author': message.author,
            'timestamp': message.created_at,
            'attachments': [a.url for a in message.attachments if a.content_type and a.content_type.startswith('image/')],
            'reference': message.reference.message_id if message.reference else None
        }

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
            
        if not before.guild:
            return
            
        if before.content == after.content:
            return
            
        if before.guild.id not in self.edited_messages:
            self.edited_messages[before.guild.id] = {}
            
        if before.channel.id not in self.edited_messages[before.guild.id]:
            self.edited_messages[before.guild.id][before.channel.id] = []
            
        self.edited_messages[before.guild.id][before.channel.id].append({
            'before': before.content,
            'after': after.content,
            'author': before.author,
            'timestamp': datetime.utcnow(),
            'message_id': before.id
        })
        
        self.edited_messages[before.guild.id][before.channel.id] = \
            self.edited_messages[before.guild.id][before.channel.id][-5:]

async def setup(bot):
    await bot.add_cog(MessageTrackingEvents(bot)) 