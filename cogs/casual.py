import discord
from discord.ext import commands

class Casual(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    #################################
    ## Ping Command
    #################################
    @commands.command()
    async def ping(self, ctx):
        """Check bot's latency"""
        await ctx.send(f"# Pong!\n**Latency**: {round(self.bot.latency * 1000)}ms")
        
    #################################
    ## User Info Command
    #################################
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Get info about a user"""
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info - {member.tag}", color=member.color)
        embed.add_field(name="ID", value=f"```{member.id}```")
        embed.add_field(name="Joined", value=f"```{member.joined_at.strftime('%Y-%m-%d')}```")
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Casual(bot)) 