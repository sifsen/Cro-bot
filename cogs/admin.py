import discord
import io
import contextlib
import textwrap
import traceback
from datetime import datetime

from utils.permissions.handler import PermissionHandler
from utils.helpers.formatting import EmbedBuilder, TextFormatter
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator

    #################################
    ## Config Command
    #################################
    @commands.command()
    @PermissionHandler.has_permissions(administrator=True)
    async def config(self, ctx, setting=None, *, value=None):
        """Configure server settings"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        
        if not setting:
            embed = discord.Embed(
                title="Server Configuration",
                color=discord.Color.blue()
            )
            
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)

            for key, value in settings.items():
                if key.startswith('log_channel_'):
                    channel = ctx.guild.get_channel(value) if value else None
                    embed.add_field(
                        name=key.replace('log_channel_', '').replace('_', ' ').title(),
                        value=channel.mention if channel else '`Not Set`',
                        inline=True
                    )
                    
            await ctx.send(embed=embed)
            return

        if setting in ['messages', 'profiles', 'mod_audit', 'join_leave']:
            setting = f'log_channel_{setting}'
        
        if setting not in settings:
            await ctx.send(f"Unknown setting: `{setting}`")
            return

        if value and value.lower() == 'none':
            self.bot.settings.set_server_setting(ctx.guild.id, setting, None)
            await ctx.send(f"Cleared setting: `{setting}`")
            return
            
        if ctx.message.channel_mentions:
            channel = ctx.message.channel_mentions[0]
            self.bot.settings.set_server_setting(ctx.guild.id, setting, channel.id)
            await ctx.send(f"Set `{setting}` to {channel.mention}")
        else:
            await ctx.send("Please mention a channel to set.")

    #################################
    ## Eval Command
    #################################
    @commands.command(name='eval')
    @PermissionHandler.is_bot_master()
    async def _eval(self, ctx, *, code):
        """Evaluates Python code"""
        env = {
            'ctx': ctx,
            'bot': self.bot,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'discord': discord
        }

        env.update(globals())
        
        if code.startswith('```') and code.endswith('```'):
            code = '\n'.join(code.split('\n')[1:-1])
            
        code = TextFormatter.clean_text(code)
        
        stdout = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(stdout):
                exec(f'async def func():\n{textwrap.indent(code, "  ")}', env)
                obj = await env['func']()
                result = f'{stdout.getvalue()}\n-- {obj}\n'
        except Exception as e:
            result = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            
        embed = EmbedBuilder(
            title="Eval result",
            color=discord.Color.blue() if 'error' not in result.lower() else discord.Color.red()
        ).add_field(
            name="Input",
            value=f"```py\n{code[:1000]}```",
            inline=False
        ).add_field(
            name="Output",
            value=f"```py\n{result[:1000]}```",
            inline=False
        )
        
        await ctx.send(embed=embed.build())

    #################################
    ## Description Command
    #################################
    @commands.command(aliases=['desc', 'topic', 'cd'])
    @PermissionHandler.has_permissions(manage_channels=True)
    async def description(self, ctx, *, description: str = None):
        """Change a channel's description/topic"""
        try:
            channel = ctx.channel
            
            if not description:
                current_topic = channel.topic or "No topic set"
                await ctx.send(f"Current topic for {channel.mention}:\n> {current_topic}")
                return
            
            await channel.edit(topic=description)
            await ctx.send(f"Updated topic for {channel.mention}")
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to edit this channel.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Channel Name Command
    #################################
    @commands.command(aliases=['name', 'cn'])
    @PermissionHandler.has_permissions(manage_channels=True)
    async def channelname(self, ctx, *, new_name: str = None):
        """Change a channel's name"""
        try:
            channel = ctx.channel
            
            if not new_name:
                await ctx.send(f"Current name: `{channel.name}`")
                return
            
            if new_name.startswith('<#') and '>' in new_name:
                parts = new_name.split('>', 1)
                try:
                    channel_id = int(parts[0][2:])
                    channel = ctx.guild.get_channel(channel_id)
                    new_name = parts[1].strip()
                except (ValueError, IndexError):
                    pass
            
            old_name = channel.name
            await channel.edit(name=new_name)
            await ctx.send(f"Changed channel name from `{old_name}` to `{new_name}`")
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to edit this channel.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Toggle Prefix Command
    #################################
    @commands.command(aliases=['tp'])
    @commands.has_permissions(administrator=True)
    async def toggleprefix(self, ctx):
        """Toggle whether default prefixes work in this server"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        current = settings.get('use_default_prefix', True)
        custom_prefix = settings.get('prefix')
        
        if not custom_prefix and current:
            await ctx.send("You need to set a custom prefix before disabling default prefixes!\nUse `config prefix <prefix>` to set one.")
            return
        
        self.bot.settings.set_server_setting(ctx.guild.id, 'use_default_prefix', not current)
        
        if current:
            await ctx.send(f"Default prefixes have been disabled.\nOnly the custom prefix `{custom_prefix}` will work.")
        else:
            await ctx.send(f"Default prefixes have been enabled.\nBoth `{custom_prefix}` and default prefixes will work.")

    #################################
    ## Tags
    #################################
    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, *, name: str = None):
        """Get a tag's content"""
        if not name:
            return await ctx.send_help(ctx.command)
            
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        tags = settings.get('tags', {})
        
        if name not in tags:
            return await ctx.send("Tag not found!")
            
        tag = tags[name]
        await ctx.send(tag['content'])
        
    @tag.command(name="create")
    @commands.has_permissions(manage_messages=True)
    async def tagcreate(self, ctx, name: str, *, content: str):
        """Create a new tag"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        tags = settings.get('tags', {})
        
        if name in tags:
            return await ctx.send("Tag already exists!")
            
        tags[name] = {
            'content': content,
            'author_id': ctx.author.id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.bot.settings.set_server_setting(ctx.guild.id, 'tags', tags)
        await ctx.send(f"Tag created: `{name}`")
        
    @tag.command(name="tlist")
    async def taglist(self, ctx):
        """List all tags"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        tags = settings.get('tags', {})
        
        if not tags:
            return await ctx.send("No tags found!")
            
        embed = discord.Embed(title="Server Tags", color=0x2B2D31)
        embed.description = "\n".join(f"`{name}`" for name in sorted(tags.keys()))
        await ctx.send(embed=embed)

    #################################
    ## Logging Channel Commands
    #################################
    @commands.group(aliases=['jl'], invoke_without_command=True)
    @PermissionHandler.has_permissions(administrator=True)
    async def joinleave(self, ctx, channel: discord.TextChannel = None):
        """
        Manage join/leave logging settings
        
        Subcommands:
        - view: Show current join/leave log channel
        - disable: Disable join/leave logging
        
        Examples:
        %joinleave #welcome-logs
        %jl #member-logs
        %joinleave view
        %joinleave disable
        """
        if not channel:
            channel = ctx.channel
            
        self.bot.settings.set_server_setting(ctx.guild.id, 'log_channel_join_leave', channel.id)
        await ctx.send(f"Join/Leave logs will be sent to {channel.mention}")

    @joinleave.command(name='view')
    @PermissionHandler.has_permissions(administrator=True)
    async def joinleave_view(self, ctx):
        """View current join/leave log channel"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        channel_id = settings.get('log_channel_join_leave')
        
        if not channel_id:
            await ctx.send("No join/leave log channel set")
            return
            
        channel = ctx.guild.get_channel(int(channel_id))
        if not channel:
            await ctx.send("Join/leave log channel no longer exists!")
            return
            
        await ctx.send(f"Join/leave log channel: {channel.mention}")

    @joinleave.command(name='disable')
    @PermissionHandler.has_permissions(administrator=True)
    async def joinleave_disable(self, ctx):
        """Disable join/leave logging"""
        self.bot.settings.set_server_setting(ctx.guild.id, 'log_channel_join_leave', None)
        await ctx.send("Join/leave logging has been disabled")

    @commands.group(aliases=['ml'], invoke_without_command=True)
    @PermissionHandler.has_permissions(administrator=True)
    async def messagelogs(self, ctx, channel: discord.TextChannel = None):
        """
        Manage message logging settings
        
        Subcommands:
        - view: Show current message logs channel
        - disable: Disable message logging
        
        Examples:
        %messagelogs #message-logs
        %ml #logs
        %messagelogs view
        %messagelogs disable
        """
        if not channel:
            channel = ctx.channel
            
        self.bot.settings.set_server_setting(ctx.guild.id, 'log_channel_messages', channel.id)
        await ctx.send(f"Message logs (edits/deletions) will be sent to {channel.mention}")

    @messagelogs.command(name='view')
    @PermissionHandler.has_permissions(administrator=True)
    async def messagelogsview(self, ctx):
        """View current message logs channel"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        channel_id = settings.get('log_channel_messages')

        if not channel_id:
            await ctx.send("No message logs channel set")
            return
            
        channel = ctx.guild.get_channel(int(channel_id))
        if not channel:
            await ctx.send("Message logs channel no longer exists!")
            return
            
        await ctx.send(f"Message logs channel: {channel.mention}")

    @messagelogs.command(name='disable')
    @PermissionHandler.has_permissions(administrator=True)
    async def messagelogsdisable(self, ctx):
        """Disable message logging"""
        self.bot.settings.set_server_setting(ctx.guild.id, 'log_channel_messages', None)
        await ctx.send("Message logging has been disabled")

    @commands.group(aliases=['ma'], invoke_without_command=True)
    @PermissionHandler.has_permissions(administrator=True)
    async def modaudit(self, ctx, channel: discord.TextChannel = None):
        """
        Manage moderation audit logging settings
        
        Subcommands:
        - view: Show current mod audit log channel
        - disable: Disable mod audit logging
        
        Examples:
        %modaudit #mod-logs
        %ma #audit-logs
        %modaudit view
        %modaudit disable
        """
        if not channel:
            channel = ctx.channel
            
        self.bot.settings.set_server_setting(ctx.guild.id, 'log_channel_mod_audit', channel.id)
        await ctx.send(f"Moderation logs will be sent to {channel.mention}")

    @modaudit.command(name='view')
    @PermissionHandler.has_permissions(administrator=True)
    async def modaudit_view(self, ctx):
        """View current mod audit log channel"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        channel_id = settings.get('log_channel_mod_audit')
        
        if not channel_id:
            await ctx.send("No mod audit log channel set")
            return
            
        channel = ctx.guild.get_channel(int(channel_id))
        if not channel:
            await ctx.send("Mod audit log channel no longer exists!")
            return
            
        await ctx.send(f"Mod audit log channel: {channel.mention}")

    @modaudit.command(name='disable')
    @PermissionHandler.has_permissions(administrator=True)
    async def modaudit_disable(self, ctx):
        """Disable mod audit logging"""
        self.bot.settings.set_server_setting(ctx.guild.id, 'log_channel_mod_audit', None)
        await ctx.send("Mod audit logging has been disabled")

    @commands.group(aliases=['sb'], invoke_without_command=True)
    @PermissionHandler.has_permissions(administrator=True)
    async def starboard(self, ctx, channel: discord.TextChannel = None):
        """
        Manage starboard settings
        
        Subcommands:
        - view: Show current starboard channel
        - disable: Disable starboard
        - limit <number>: Set minimum stars needed (default: 3)
        
        Examples:
        %starboard #starboard-channel
        %sb #highlights
        %starboard view
        %starboard disable
        %starboard limit 5
        """
        if ctx.invoked_subcommand is None:
            if not channel:
                channel = ctx.channel
                
            self.bot.settings.set_server_setting(ctx.guild.id, 'starboard_channel', channel.id)
            await ctx.send(f"Starboard messages will be sent to {channel.mention}")

    @starboard.command(name='limit')
    @PermissionHandler.has_permissions(administrator=True)
    async def starboard_limit(self, ctx, number: int):
        """Set the minimum number of stars needed"""
        if number < 1:
            await ctx.send("Limit must be at least 1")
            return
            
        self.bot.settings.set_server_setting(ctx.guild.id, 'starboard_threshold', number)
        await ctx.send(f"Starboard limit set to {number} stars")

    @starboard.command(name='view')
    @PermissionHandler.has_permissions(administrator=True)
    async def starboard_view(self, ctx):
        """View current starboard settings"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        channel_id = settings.get('starboard_channel')
        threshold = settings.get('starboard_threshold', 3)
        
        if not channel_id:
            await ctx.send("No starboard channel set")
            return
            
        channel = ctx.guild.get_channel(int(channel_id))
        if not channel:
            await ctx.send("Starboard channel no longer exists!")
            return
            
        await ctx.send(f"Starboard channel: {channel.mention}\nRequired stars: {threshold}")

    @starboard.command(name='disable')
    @PermissionHandler.has_permissions(administrator=True)
    async def starboard_disable(self, ctx):
        """Disable the starboard"""
        self.bot.settings.set_server_setting(ctx.guild.id, 'starboard_channel', None)
        await ctx.send("Starboard has been disabled")

async def setup(bot):
    await bot.add_cog(Admin(bot))