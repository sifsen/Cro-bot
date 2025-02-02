from discord.ext import commands
import discord
import random
import re

class MessageEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.instrument_emojis = ['🎸', '🥁', '🎹', '🎺', '🎻', '🪕', '🎷']

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        content = message.content.lower()

        #################################
        ## Single Word Things
        #################################   
        if 'band' in content:
            selected_instruments = random.sample(self.instrument_emojis, 4)
            for emoji in selected_instruments:
                await message.add_reaction(emoji)

        if 'horse' in content:
            await message.add_reaction('🐴')

        if 'honse' in content:
            await message.add_reaction('🐴')

        if 'fish' in content:
            await message.add_reaction('🐟')

        if '69' in content:
            await message.channel.send('( ͡° ͜ʖ ͡°)')

        #################################
        ## Color Thing
        #################################
        hex_pattern = r'(?:#|0x)(?:[0-9a-fA-F]{6})'
        if re.search(hex_pattern, message.content):
            if not re.search(r'<[@#][!&]?\d+>', message.content):
                hex_match = re.search(hex_pattern, message.content).group()
                hex_color = hex_match.replace('0x', '#')
                color_int = int(hex_color[1:], 16)

                embed = discord.Embed(
                    title=f"{hex_color}",
                    description=f"RGB: {tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))}",
                    color=color_int
                )
                embed.set_thumbnail(url=f"https://singlecolorimage.com/get/{hex_color[1:]}/75x75")
                await message.channel.send(embed=embed)

        #################################
        ## Quote Thing
        #################################
        message_link_pattern = r'https?:\/\/(?:.*)?discord\.com\/channels\/(\d+)\/(\d+)\/(\d+)'
        if re.search(message_link_pattern, message.content):
            matches = re.finditer(message_link_pattern, message.content)
            for match in matches:
                guild_id, channel_id, message_id = map(int, match.groups())
                
                if guild_id != message.guild.id:
                    continue
                    
                try:
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        continue
                        
                    quoted_msg = await channel.fetch_message(message_id)
                    if not quoted_msg:
                        continue
                        
                    embed = discord.Embed(
                        description=quoted_msg.content or "*No text content*",
                        color=0x2B2D31,
                        timestamp=quoted_msg.created_at
                    )
                    
                    embed.set_author(
                        name=quoted_msg.author.name,
                        icon_url=quoted_msg.author.display_avatar.url
                    )
                    
                    if quoted_msg.attachments and quoted_msg.attachments[0].content_type.startswith('image/'):
                        embed.set_image(url=quoted_msg.attachments[0].url)
                    elif quoted_msg.embeds and any(e.provider and e.provider.name == "Tenor" for e in quoted_msg.embeds):
                        tenor_embed = next(e for e in quoted_msg.embeds if e.provider and e.provider.name == "Tenor")
                        if tenor_embed.thumbnail and tenor_embed.thumbnail.url:
                            tenor_match = re.match(r'^https://media\.tenor\.com/([a-zA-Z0-9_-]+)e/[a-zA-Z0-9_-]+\.png$', tenor_embed.thumbnail.url)
                            if tenor_match:
                                gif_url = f"https://c.tenor.com/{tenor_match.group(1)}C/tenor.gif"
                                embed.set_image(url=gif_url)
                                
                    embed.add_field(
                        name="", 
                        value=f"[Jump to message]({quoted_msg.jump_url})",
                        inline=False
                    )
                    
                    await message.channel.send(embed=embed)
                    
                except (discord.NotFound, discord.Forbidden):
                    continue

async def setup(bot):
    await bot.add_cog(MessageEvents(bot))
