import re
import discord
from discord.ext import commands
from utils.helpers import PermissionHandler
from datetime import timedelta, datetime

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_config = {
            'enabled': False,
            'patterns': {},
            'excluded_channels': [],
            'excluded_roles': []
        }

    #################################
    ## Get AutoMod Config
    #################################
    def get_automod_config(self, guild_id: int) -> dict:
        """Get automod config for a guild"""
        settings = self.bot.settings.get_all_server_settings(guild_id)
        if 'automod' not in settings:
            settings['automod'] = self.default_config.copy()
            self.bot.settings.set_server_setting(guild_id, 'automod', settings['automod'])
        return settings['automod']

    #################################
    ## Message Handler
    #################################
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        config = self.get_automod_config(message.guild.id)
        if not config['enabled']:
            return

        # Check exclusions
        if message.channel.id in config['excluded_channels']:
            return

        if any(role.id in config['excluded_roles'] for role in message.author.roles):
            return

        # Check patterns
        for pattern_name, pattern_data in config['patterns'].items():
            pattern = pattern_data['regex']
            try:
                if re.search(pattern, message.content, re.IGNORECASE):
                    await self.handle_violation(message, pattern_name, pattern_data)
                    break
            except re.error:
                continue

    #################################
    ## Violation Handler
    #################################
    async def handle_violation(self, message, pattern_name, pattern_data):
        """Handle automod violation"""
        action = pattern_data.get('action', 'delete')
        
        try:
            await message.delete()
        except discord.Forbidden:
            pass

        if action == 'timeout':
            duration = pattern_data.get('duration', 604800)
            try:
                until = discord.utils.utcnow() + timedelta(seconds=duration)
                await message.author.timeout(until, reason=f"AutoMod: {pattern_name}")
            except discord.Forbidden:
                pass

        log_channel_id = self.bot.settings.get_server_setting(message.guild.id, "log_channel_mod_audit")
        if log_channel_id:
            channel = message.guild.get_channel(int(log_channel_id))
            if channel:
                embed = discord.Embed(
                    title="AutoMod Action",
                    description=f"Pattern triggered: `{pattern_name}`",
                    color=discord.Color.red()
                )
                embed.add_field(name="User", value=f"{message.author.mention} ```{message.author.id}```")
                embed.add_field(name="Channel", value=message.channel.mention)
                embed.add_field(name="Action", value=action.title())
                embed.add_field(name="Content", value=f"```{message.content[:1024]}```", inline=False)
                await channel.send("Hey, check this out!", embed=embed)

    #################################
    ## AutoMod Commands
    #################################
    @commands.group(invoke_without_command=True)
    @PermissionHandler.has_permissions(administrator=True)
    async def automod(self, ctx):
        """Manage automod settings"""
        config = self.get_automod_config(ctx.guild.id)
        
        embed = discord.Embed(
            title="AutoMod Configuration",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Status", 
            value="Enabled" if config['enabled'] else "Disabled",
            inline=False
        )
        
        patterns = "\n".join(f"• {name}" for name in config['patterns'].keys()) or "None"
        embed.add_field(name="Patterns", value=patterns, inline=False)
        
        excluded_channels = "\n".join(f"<#{id}>" for id in config['excluded_channels']) or "None"
        embed.add_field(name="Excluded Channels", value=excluded_channels, inline=False)
        
        excluded_roles = "\n".join(f"<@&{id}>" for id in config['excluded_roles']) or "None"
        embed.add_field(name="Excluded Roles", value=excluded_roles, inline=False)
        
        await ctx.send(embed=embed)

    @automod.command()
    @PermissionHandler.has_permissions(administrator=True)
    async def toggle(self, ctx):
        """Toggle automod on/off"""
        config = self.get_automod_config(ctx.guild.id)
        config['enabled'] = not config['enabled']
        self.bot.settings.set_server_setting(ctx.guild.id, 'automod', config)
        
        status = "enabled" if config['enabled'] else "disabled"
        await ctx.send(f"AutoMod has been {status}.")

    @automod.command()
    @PermissionHandler.has_permissions(administrator=True)
    async def add(self, ctx, name: str, action: str, *, pattern: str):
        """Add an automod pattern"""
        config = self.get_automod_config(ctx.guild.id)
        
        duration = 300
        if 'duration=' in pattern:
            try:
                pattern, duration_str = pattern.rsplit('duration=', 1)
                duration_str = duration_str.strip().lower()
                pattern = pattern.strip()

                # Parse time units
                if duration_str.endswith('w'):
                    duration = int(duration_str[:-1]) * 7 * 24 * 60 * 60
                elif duration_str.endswith('d'):
                    duration = int(duration_str[:-1]) * 24 * 60 * 60
                elif duration_str.endswith('h'):
                    duration = int(duration_str[:-1]) * 60 * 60
                elif duration_str.endswith('m'):
                    duration = int(duration_str[:-1]) * 60
                elif duration_str.endswith('s'):
                    duration = int(duration_str[:-1])
                else:
                    duration = int(duration_str)

                if duration <= 0:
                    await ctx.send("Duration must be positive!")
                    return

            except ValueError:
                await ctx.send("Invalid duration value! Use format like '1w', '1d', '1h', '1m', or '1s'")
                return

        try:
            re.compile(pattern)
        except re.error:
            await ctx.send("Invalid regex pattern!")
            return

        if action not in ['delete', 'timeout']:
            await ctx.send("Invalid action! Use 'delete' or 'timeout'")
            return

        config['patterns'][name] = {
            'regex': pattern,
            'action': action,
            'duration': duration if action == 'timeout' else None
        }
        
        self.bot.settings.set_server_setting(ctx.guild.id, 'automod', config)
        
        duration_str = ""
        if action == 'timeout':
            if duration >= 604800:
                duration_str = f"{duration//604800}w"
            elif duration >= 86400:
                duration_str = f"{duration//86400}d"
            elif duration >= 3600:
                duration_str = f"{duration//3600}h"
            elif duration >= 60:
                duration_str = f"{duration//60}m"
            else:
                duration_str = f"{duration}s"

        await ctx.send(f"Added pattern `{name}` with action `{action}`" + 
                      (f" and duration {duration_str}" if action == 'timeout' else ""))

    @automod.command()
    @PermissionHandler.has_permissions(administrator=True)
    async def remove(self, ctx, name: str):
        """Remove an automod pattern"""
        config = self.get_automod_config(ctx.guild.id)
        
        if name in config['patterns']:
            del config['patterns'][name]
            self.bot.settings.set_server_setting(ctx.guild.id, 'automod', config)
            await ctx.send(f"Removed pattern `{name}`")
        else:
            await ctx.send("Pattern not found!")

    @automod.command()
    @PermissionHandler.has_permissions(administrator=True)
    async def exclude(self, ctx, target: str):
        """Add a channel or role to exclusion list"""
        config = self.get_automod_config(ctx.guild.id)
        
        if target.startswith('<#'):
            channel_id = int(target[2:-1])
            if channel_id not in config['excluded_channels']:
                config['excluded_channels'].append(channel_id)
                await ctx.send(f"Added <#{channel_id}> to excluded channels")
        
        elif target.startswith('<@&'):
            role_id = int(target[3:-1])
            if role_id not in config['excluded_roles']:
                config['excluded_roles'].append(role_id)
                await ctx.send(f"Added <@&{role_id}> to excluded roles")
        
        self.bot.settings.set_server_setting(ctx.guild.id, 'automod', config)

    @automod.command()
    @PermissionHandler.has_permissions(administrator=True)
    async def include(self, ctx, target: str):
        """Remove a channel or role from exclusion list"""
        config = self.get_automod_config(ctx.guild.id)
        
        if target.startswith('<#'):
            channel_id = int(target[2:-1])
            if channel_id in config['excluded_channels']:
                config['excluded_channels'].remove(channel_id)
                await ctx.send(f"Removed <#{channel_id}> from excluded channels")
        
        elif target.startswith('<@&'):
            role_id = int(target[3:-1])
            if role_id in config['excluded_roles']:
                config['excluded_roles'].remove(role_id)
                await ctx.send(f"Removed <@&{role_id}> from excluded roles")
        
        self.bot.settings.set_server_setting(ctx.guild.id, 'automod', config)

async def setup(bot):
    await bot.add_cog(AutoMod(bot))