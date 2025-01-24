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

        #################################
        ## Color Thing
        #################################
        hex_pattern = r'(?:#|0x)(?:[0-9a-fA-F]{6})'
        if re.search(hex_pattern, message.content):
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

async def setup(bot):
    await bot.add_cog(MessageEvents(bot))
