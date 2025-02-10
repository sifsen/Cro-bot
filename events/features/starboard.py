import discord
from discord.ext import commands
import re

class StarboardEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.starboard_cache = {}

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.handle_starboard(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.handle_starboard(payload)

    async def handle_starboard(self, payload):
        if payload.member and payload.member.bot:
            return
            
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
            
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
            
        settings = self.bot.settings.get_all_server_settings(payload.guild_id)
        starboard_channel_id = settings.get('starboard_channel')
        threshold = settings.get('starboard_threshold', 3)
        
        if not starboard_channel_id:
            return
            
        starboard_channel = channel.guild.get_channel(int(starboard_channel_id))
        if not starboard_channel:
            return
            
        valid_emojis = ['⭐', '🌟', '✨', '🔥']
        
        if str(payload.emoji) not in valid_emojis:
            return
            
        star_count = 0
        active_emoji = None
        for emoji in valid_emojis:
            reaction = discord.utils.get(message.reactions, emoji=emoji)
            if reaction:
                star_count = reaction.count
                active_emoji = emoji
                break
        
        if not active_emoji:
            return
            
        existing_star_message_id = self.starboard_cache.get(message.id)
        
        if star_count < threshold and not existing_star_message_id:
            return
            
        if star_count < threshold and existing_star_message_id:
            try:
                star_message = await starboard_channel.fetch_message(existing_star_message_id)
                await star_message.delete()
                self.starboard_cache.pop(message.id, None)
            except:
                pass
            return

        embed = await self.create_starboard_embed(message)
        content = f"{active_emoji} **{star_count}** {message.channel.mention}"
        
        try:
            if existing_star_message_id:
                star_message = await starboard_channel.fetch_message(existing_star_message_id)
                await star_message.edit(content=content, embed=embed)
            else:
                star_message = await starboard_channel.send(content=content, embed=embed)
                self.starboard_cache[message.id] = star_message.id
        except Exception as e:
            print(f"Error handling starboard message: {e}")

    async def create_starboard_embed(self, message):
        embed = discord.Embed(
            description=message.content or "*No text content*",
            color=0xFFAC33,
            timestamp=message.created_at
        )
        embed.add_field(name="", value=f"[Jump to message]({message.jump_url})")
        embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
        embed.set_footer(text=f"ID: {message.id}")
        
        if message.attachments and message.attachments[0].content_type.startswith('image/'):
            embed.set_image(url=message.attachments[0].url)
        elif message.embeds and any(e.provider and e.provider.name == "Tenor" for e in message.embeds):
            tenor_embed = next(e for e in message.embeds if e.provider and e.provider.name == "Tenor")
            if tenor_embed.thumbnail and tenor_embed.thumbnail.url:
                tenor_match = re.match(r'^https://media\.tenor\.com/([a-zA-Z0-9_-]+)e/[a-zA-Z0-9_-]+\.png$', tenor_embed.thumbnail.url)
                if tenor_match:
                    gif_url = f"https://c.tenor.com/{tenor_match.group(1)}C/tenor.gif"
                    embed.set_image(url=gif_url)
        elif message.content:
            cdn_match = re.search(r'https?://(?:cdn|media)\.discordapp\.(?:com|net)/attachments/\d+/\d+/[^\s]+(?:\.gif|\.png|\.jpg|\.jpeg|\.webp)', message.content)
            if cdn_match:
                embed.set_image(url=cdn_match.group(0))
                
        return embed

async def setup(bot):
    await bot.add_cog(StarboardEvents(bot))
