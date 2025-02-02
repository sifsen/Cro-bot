import discord

from utils.helpers import PermissionHandler
from discord.ext import commands
from datetime import datetime
import io
import contextlib
import textwrap
import traceback

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator

    #################################
    ## Nickname Command
    #################################
    @commands.command(aliases=['nick'])
    @PermissionHandler.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, new_nick=None):
        """Change a member's nickname"""
        try:
            old_nick = member.nick or member.name
            await member.edit(nick=new_nick)
            await ctx.send(f"Changed {member.mention}'s nickname from **{old_nick}** to **{new_nick}**")
        except discord.Forbidden:
            await ctx.send("I don't have permission to change nicknames.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Config Command
    #################################
    @commands.command()
    @PermissionHandler.has_permissions(administrator=True)
    async def config(self, ctx, setting=None, *, value=None):
        """Configure server settings"""
        if not setting:
            settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
            
            embed = discord.Embed(
                title="Server Configuration",
                color=discord.Color.dark_theme()
            )
            
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)

            log_channels = [
                f"• Join/Leave: {ctx.guild.get_channel(settings.get('log_channel_join_leave')).mention if settings.get('log_channel_join_leave') else '`Not Set`'}",
                f"• Mod Audit: {ctx.guild.get_channel(settings.get('log_channel_mod_audit')).mention if settings.get('log_channel_mod_audit') else '`Not Set`'}",
                f"• Edits: {ctx.guild.get_channel(settings.get('log_channel_edits')).mention if settings.get('log_channel_edits') else '`Not Set`'}",
                f"• Deletions: {ctx.guild.get_channel(settings.get('log_channel_deletions')).mention if settings.get('log_channel_deletions') else '`Not Set`'}",
                f"• Profiles: {ctx.guild.get_channel(settings.get('log_channel_profiles')).mention if settings.get('log_channel_profiles') else '`Not Set`'}"
            ]

            staff_roles = [
                f"• Mod Role: {ctx.guild.get_role(settings.get('mod_role')).mention if settings.get('mod_role') else '`Not Set`'}",
                f"• Admin Role: {ctx.guild.get_role(settings.get('admin_role')).mention if settings.get('admin_role') else '`Not Set`'}"
            ]

            starboard = [
                f"• Channel: {ctx.guild.get_channel(settings.get('starboard_channel')).mention if settings.get('starboard_channel') else '`Not Set`'}",
                f"• Threshold: {settings.get('starboard_threshold', '`Not Set`')} ⭐"
            ]
            
            description = [
                "**Logging Channels**",
                "\n".join(log_channels),
                "",
                "**Staff Roles**",
                "\n".join(staff_roles),
                "",
                "**Starboard**",
                "\n".join(starboard),
                "",
                "**Available Settings**",
                "`joinleave` `modaudit` `edits` `deletions` `profiles`",
                "`modrole` `adminrole` `starboard` `starthreshold`",
                "",
                "*Use `config <setting> <value>` to modify settings*"
            ]
            
            embed.description = "\n".join(description)
            embed.set_footer(text=f"{ctx.guild.name}")
            await ctx.send(embed=embed)
            return

        setting_map = {
            "joinleave": "log_channel_join_leave",
            "modaudit": "log_channel_mod_audit",
            "edits": "log_channel_edits",
            "deletions": "log_channel_deletions",
            "profiles": "log_channel_profiles",
            "modrole": "mod_role",
            "adminrole": "admin_role",
            "starboard": "starboard_channel",
            "starthreshold": "starboard_threshold",
            "prefix": "prefix"
        }

        if setting.lower() not in setting_map:
            await ctx.send("Invalid setting. Use `$config` to see available settings.")
            return

        setting_key = setting_map[setting.lower()]

        if not value or value.lower() in ['none', 'clear']:
            self.bot.settings.set_server_setting(ctx.guild.id, setting_key, None)
            await ctx.send(f"Cleared {setting} setting.")
            return

        if setting_key.startswith('log_channel_') or setting_key == 'starboard_channel':
            try:
                channel_id = int(''.join(filter(str.isdigit, value)))
                channel = ctx.guild.get_channel(channel_id)
                if not channel:
                    await ctx.send("Please provide a valid channel mention or ID.")
                    return
                self.bot.settings.set_server_setting(ctx.guild.id, setting_key, channel.id)
                await ctx.send(f"Set {setting} channel to {channel.mention}")
            except ValueError:
                await ctx.send("Please provide a valid channel mention or ID.")
                return

        elif setting_key.endswith('_role'):
            try:
                role_id = int(''.join(filter(str.isdigit, value)))
                role = ctx.guild.get_role(role_id)
                if not role:
                    await ctx.send("Please provide a valid role mention or ID.")
                    return
                self.bot.settings.set_server_setting(ctx.guild.id, setting_key, role.id)
                await ctx.send(f"Set {setting} to {role.mention}")
            except ValueError:
                await ctx.send("Please provide a valid role mention or ID.")
                return

        elif setting_key == 'starboard_threshold':
            try:
                threshold = int(value)
                if threshold < 1:
                    await ctx.send("Threshold must be at least 1.")
                    return
                self.bot.settings.set_server_setting(ctx.guild.id, setting_key, threshold)
                await ctx.send(f"Set starboard threshold to {threshold}⭐")
            except ValueError:
                await ctx.send("Please provide a valid number for the threshold.")
                return

        elif setting_key == 'prefix':
            if len(value) > 3:
                await ctx.send("Prefix must be 3 characters or less!")
                return
            self.bot.settings.set_server_setting(ctx.guild.id, setting_key, value)
            await ctx.send(f"Set custom prefix to `{value}`")

    @commands.command(name='exe')
    @commands.is_owner()
    async def execute_code(self, ctx, *, code: str):
        """Execute Python code"""
        await ctx.message.delete()
        
        if code.startswith('```python'):
            code = code[9:]
        elif code.startswith('```py'):
            code = code[5:]
        elif code.startswith('```'):
            code = code[3:]
        if code.endswith('```'):
            code = code[:-3]
        
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'discord': discord,
            'commands': commands,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message
        }

        env.update(globals())
        
        wrapped_code = (
            'async def _execute():\n' +
            textwrap.indent(code, '    ')
        )

        stdout = io.StringIO()
        
        try:
            exec(wrapped_code, env)
            with contextlib.redirect_stdout(stdout):
                await env['_execute']()
                
        except Exception as e:
            error = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            if len(error) > 1990:
                error = error[:1990] + "..."
            await ctx.author.send(f"```py\n{error}\n```")

    #################################
    ## Description Command
    #################################
    @commands.command(aliases=['desc'])
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
    @commands.command(aliases=['name'])
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
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def toggle_prefix(self, ctx):
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
    async def tag_create(self, ctx, name: str, *, content: str):
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
        
    @tag.command(name="list")
    async def tag_list(self, ctx):
        """List all tags"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        tags = settings.get('tags', {})
        
        if not tags:
            return await ctx.send("No tags found!")
            
        embed = discord.Embed(title="Server Tags", color=0x2B2D31)
        embed.description = "\n".join(f"`{name}`" for name in sorted(tags.keys()))
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))