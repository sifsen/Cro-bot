import discord

from discord.ext import commands

class Casual(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    #################################
    ## About Command
    #################################
    @commands.command()
    async def about(self, ctx):
        """About Nessy"""
        embed = discord.Embed(
            title="✦ About Nessy ✦",
            description=(
                "Work in progress"
            ),
            color=0x2B2D31
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text=f"Buh")
        await ctx.send(embed=embed)
        
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
    
    #################################
    ## Avatar Command
    #################################
    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        """Get a user's avatar"""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=member.color)
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Casual(bot)) 