from discord.ext import commands

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
    ## Command Error Hook
    #################################   
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("That command doesn't exist.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You can't do that.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("I couldn't find that member.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I can't do that.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide an arg.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")

async def setup(bot):
    await bot.add_cog(EventHandlers(bot)) 