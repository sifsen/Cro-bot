import discord
from discord.ext import commands

class ErrorEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            prefixes = await self.bot.get_prefix(ctx.message)
            content = ctx.message.content
            
            used_prefix = None
            for prefix in prefixes:
                if content.startswith(prefix):
                    used_prefix = prefix
                    break
                
            if not used_prefix:
                return
            
            while content.startswith(used_prefix):
                content = content[len(used_prefix):]
            
            if not content or content.isspace():
                return
            
            expressions = ['?', '!', '.', '...', '????', '!!!!', '....']
            if content.strip() in expressions or all(c in '?!.' for c in content.strip()):
                return
            
            await ctx.send(f"**Unknown command**.\nUse `{ctx.prefix}help` for a list of commands.")
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You can't do that.")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            perms = ', '.join(error.missing_permissions)
            await ctx.send(f"I can't do that.\nI need the following permissions:\n```{perms}```")
            return

        if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            command = ctx.command
            await ctx.send(
                f"**Invalid usage of `{command.name}`**\n"
                f"Usage: `{ctx.prefix}{command.name} {command.signature}`\n"
                f"See `{ctx.prefix}help {command.name}` for more details."
            )
            return

        print(f"Error in {ctx.command}: {str(error)}")
        await ctx.send("An unexpected error occurred. Tag my dev if it persists.")

async def setup(bot):
    await bot.add_cog(ErrorEvents(bot))
