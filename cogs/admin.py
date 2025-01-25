import discord

from utils.helpers import PermissionHandler
from discord.ext import commands
from datetime import datetime

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator

    #################################
    ## Nickname Command
    #################################
    @commands.command()
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
    ## Server Info Command
    #################################
    @commands.command()
    @PermissionHandler.has_permissions(manage_nicknames=True)
    async def serverinfo(self, ctx):
        """Display information about the server"""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"Server Info - {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Owner", value=guild.owner.mention)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d"))
        embed.add_field(name="Member Count", value=guild.member_count)
        
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        embed.add_field(name="Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}")
        
        embed.add_field(name="Roles", value=len(guild.roles))
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        await ctx.send(embed=embed)

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

            # Logging Channels
            log_channels = [
                f"• Join/Leave: {ctx.guild.get_channel(settings.get('log_channel_join_leave')).mention if settings.get('log_channel_join_leave') else '`Not Set`'}",
                f"• Mod Audit: {ctx.guild.get_channel(settings.get('log_channel_mod_audit')).mention if settings.get('log_channel_mod_audit') else '`Not Set`'}",
                f"• Edits: {ctx.guild.get_channel(settings.get('log_channel_edits')).mention if settings.get('log_channel_edits') else '`Not Set`'}",
                f"• Deletions: {ctx.guild.get_channel(settings.get('log_channel_deletions')).mention if settings.get('log_channel_deletions') else '`Not Set`'}",
                f"• Profiles: {ctx.guild.get_channel(settings.get('log_channel_profiles')).mention if settings.get('log_channel_profiles') else '`Not Set`'}"
            ]

            # Staff Roles
            staff_roles = [
                f"• Mod Role: {ctx.guild.get_role(settings.get('mod_role')).mention if settings.get('mod_role') else '`Not Set`'}",
                f"• Admin Role: {ctx.guild.get_role(settings.get('admin_role')).mention if settings.get('admin_role') else '`Not Set`'}"
            ]

            # Starboard
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
            "starthreshold": "starboard_threshold"
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

async def setup(bot):
    await bot.add_cog(Admin(bot))