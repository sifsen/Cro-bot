import discord
from discord.ext import commands

################################
## Event Handlers
################################
class EventHandlers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #################################
    ## Message Hook
    #################################   
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

    #################################
    ## Member Join Hook
    #################################   
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel:
            await channel.send(f'Welcome {member.mention} to the server!')

    #################################
    ## Command Error Hook
    #################################   
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found!")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")

async def setup(bot):
    await bot.add_cog(EventHandlers(bot)) 