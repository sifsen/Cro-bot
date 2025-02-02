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
                
            embed = discord.Embed(
                title=f"Command: {command.name}",
                description=command.help or "No description available",
                color=0x2B2D31
            )
            
            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join(f"`{alias}`" for alias in command.aliases),
                    inline=False
                )
            
            await ctx.send(embed=embed)
            return
            
        embed = discord.Embed(
            title="You asked for help?",
            description=(
                "**[Full Documentation](https://sen.wtf/docs/Rei)**\n\n"
                "**Key Features**\n"
                "• Comprehensive logging system\n"
                "• Advanced moderation tools\n"
                "• Custom tag system\n"
                "• Reminder functionality\n"
                "• Starboard support\n"
                "• AutoMod capabilities\n\n"
                "**Common commands**\n"
                "• `%help <command>` - Detailed command help\n"
                "• `%commands` - List all commands\n"
                "• `%tag` - Use custom tags\n"
                "• `%remindme` - Set reminders\n\n"
                "**Useful Links**\n"
                "• [Documentation](https://sen.wtf/docs/Rei)\n"
                "• [Source Code](https://github.com/CursedSen/Rei-bot/)\n"
            ),
            color=0x2B2D31
        )
        
        if ctx.author.guild_permissions.administrator:
            setup_guide = (
                "**Quicksetup guide**\n"
                "1. Set logging channels: ` config joinleave/modaudit/edits/deletions/profiles `\n"
                "2. Set staff roles: ` config modrole/adminrole `\n"
                "3. Optional: Configure starboard with ` config starboard/starthreshold `\n"
                "4. Optional: Set custom prefix with ` config prefix `\n\n"
                "**Admin commands**\n"
                "• ` %config ` - View and modify settings\n"
                "• ` %automod ` - Configure AutoMod\n"
                "• ` %toggle_prefix ` - Toggle default prefixes\n\n"
                "**Admin Tips**\n"
                "• Set up logging channels first for best experience\n"
                "• Configure AutoMod to help with moderation\n"
                "• Use tags for custom commands/responses\n"
                "• Check documentation for detailed setup guides"
            )
            embed.add_field(name="Admin setup", value=setup_guide, inline=False)
        
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
            
        await ctx.send(embed=embed)

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