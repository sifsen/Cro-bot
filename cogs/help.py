import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, command_name=None):
        """Shows command help and documentation"""
        if command_name:
            command = self.bot.get_command(command_name)
            if not command:
                await ctx.send("That command doesn't exist!")
                return
                
            signature = f"{ctx.prefix}{command.name} {command.signature}"
            await ctx.send(f"**{command.name}**\n{command.help or 'No description available'}\n\nUsage: `{signature}`")
            return
            
        await ctx.send(
            W.I.P
        )

    @commands.command()
    async def commands(self, ctx):
        """List all available commands"""
        commands_by_cog = {}
        
        for cog_name, cog in self.bot.cogs.items():
            if cog_name in ['EventHandlers', 'MessageEvents']:
                continue
                
            visible_commands = []
            for cmd in cog.get_commands():
                if cmd.hidden:
                    continue
                    
                try:
                    if await cmd.can_run(ctx):
                        visible_commands.append(cmd)
                except (commands.MissingPermissions, 
                       commands.MissingRole, 
                       commands.MissingAnyRole,
                       commands.NotOwner):
                    continue
                except Exception:
                    continue
                    
            if visible_commands:
                commands_by_cog[cog_name] = visible_commands
        
        embed = discord.Embed(
            title="Available commands",
            description="Use `%help <command>` for detailed information about a command",
            color=0x2B2D31
        )
        
        for cog_name, cmds in commands_by_cog.items():
            cmd_list = ", ".join(f"`{cmd.name}`" for cmd in sorted(cmds, key=lambda x: x.name))
            if cmd_list:
                embed.add_field(name=cog_name, value=cmd_list, inline=False)
            
        embed.set_footer(text="Some commands may require specific permissions")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))