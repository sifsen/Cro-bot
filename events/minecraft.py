import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from utils.helpers import PermissionHandler
from datetime import datetime, timezone

class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_updates.start()
        self.version_cache = {}

    def cog_unload(self):
        self.check_updates.cancel()

    async def get_latest_version(self):
        """Get latest Minecraft version information"""
        async with aiohttp.ClientSession() as session:
            url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['latest'], data['versions'][0]
        return None, None

    async def get_version_details(self, version_id):
        """Get version details from Mojang API"""
        async with aiohttp.ClientSession() as session:
            url = f"https://launchermeta.mojang.com/v1/packages/b2e6d56509565a7b62b6cc272f6e01a7/versions/{version_id}/changelog.json"
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
        return None

    @tasks.loop(minutes=5)
    async def check_updates(self):
        """Check for new Minecraft versions"""
        latest_info, version_data = await self.get_latest_version()
        if not latest_info:
            return

        for guild in self.bot.guilds:
            settings = self.bot.settings.get_all_server_settings(guild.id)
            if not settings.get('minecraft', {}).get('notifications_channel'):
                continue

            channel_id = settings['minecraft']['notifications_channel']
            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue

            cached_release = self.version_cache.get(f"{guild.id}-release")
            cached_snapshot = self.version_cache.get(f"{guild.id}-snapshot")

            if latest_info['release'] != cached_release:
                version_details = await self.get_version_details(version_data['id'])
                
                embed = discord.Embed(
                    description=f"**{latest_info['release']}** has been released!",
                    color=0x00FF00,
                    timestamp=datetime.fromisoformat(version_data['releaseTime'].replace('Z', '+00:00'))
                )
                
                embed.set_author(
                    name="New Minecraft Release",
                    icon_url="https://sen.wtf/assets/mc/grass.gif"
                )
                
                if version_details and 'changelog' in version_details:
                    changes = []
                    for entry in version_details['changelog']:
                        changes.extend(entry.get('entries', []))
                    
                    if changes:
                        changes_text = "\n".join(f"• {change}" for change in changes[:10])
                        if len(changes) > 10:
                            changes_text += "\n*(and more...)*"
                        embed.add_field(name="Changes", value=changes_text, inline=False)

                embed.set_footer(text="Release time")
                
                view = self.ReadMoreButton(latest_info['release'].replace('.', '-'))
                if settings['minecraft'].get('ping_role'):
                    await channel.send(f"<@&{settings['minecraft']['ping_role']}>", embed=embed, view=view)
                else:
                    await channel.send(embed=embed, view=view)
                
                self.version_cache[f"{guild.id}-release"] = latest_info['release']

            if latest_info['snapshot'] != cached_snapshot:
                version_details = await self.get_version_details(version_data['id'])
                
                embed = discord.Embed(
                    description=f"**{latest_info['snapshot']}** is now available!",
                    color=0xFFAA00,
                    timestamp=datetime.fromisoformat(version_data['releaseTime'].replace('Z', '+00:00'))
                )
                
                embed.set_author(
                    name="New Minecraft Snapshot",
                    icon_url="https://sen.wtf/assets/mc/enchantingtable.gif"
                )
                
                if version_details and 'changelog' in version_details:
                    changes = []
                    for entry in version_details['changelog']:
                        changes.extend(entry.get('entries', []))
                    
                    if changes:
                        changes_text = "\n".join(f"• {change}" for change in changes[:10])
                        if len(changes) > 10:
                            changes_text += "\n*(and more...)*"
                        embed.add_field(name="Changes", value=changes_text, inline=False)

                embed.set_footer(text="Release time")
                
                view = self.ReadMoreButton(latest_info['snapshot'], is_snapshot=True)
                if settings['minecraft'].get('ping_role'):
                    await channel.send(f"<@&{settings['minecraft']['ping_role']}>", embed=embed, view=view)
                else:
                    await channel.send(embed=embed, view=view)
                
                self.version_cache[f"{guild.id}-snapshot"] = latest_info['snapshot']

    @check_updates.before_loop
    async def before_check_updates(self):
        await self.bot.wait_until_ready()

    @commands.group(invoke_without_command=True)
    @PermissionHandler.has_permissions(manage_guild=True)
    async def mcupdates(self, ctx):
        """Manage Minecraft update notifications"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        minecraft_settings = settings.get('minecraft', {})

        embed = discord.Embed(
            title="Minecraft notifications configuration",
            color=0x00FF00
        )

        channel = ctx.guild.get_channel(int(minecraft_settings.get('notifications_channel', 0) or 0))
        embed.add_field(
            name="Notifications channel",
            value=channel.mention if channel else "Not set",
            inline=False
        )

        ping_role = ctx.guild.get_role(int(minecraft_settings.get('ping_role', 0) or 0))
        embed.add_field(
            name="Ping role",
            value=ping_role.mention if ping_role else "Not set",
            inline=False
        )

        await ctx.send(embed=embed)

    @mcupdates.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the notifications channel"""

        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        settings.setdefault('minecraft', {})['notifications_channel'] = channel.id
        self.bot.settings.set_server_setting(ctx.guild.id, 'minecraft', settings['minecraft'])
        await ctx.send(f"Minecraft update notifications will be sent to {channel.mention}")

    @mcupdates.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def role(self, ctx, role: discord.Role):

        """Set a role to be pinged for Minecraft updates"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        settings.setdefault('minecraft', {})

        if 'ping_role' in settings['minecraft'] and settings['minecraft']['ping_role'] == role.id:
            settings['minecraft'].pop('ping_role')
            await ctx.send(f"Removed {role.mention} as the Minecraft notification role")
        else:
            settings['minecraft']['ping_role'] = role.id
            await ctx.send(f"Set {role.mention} as the Minecraft notification role")

        self.bot.settings.set_server_setting(ctx.guild.id, 'minecraft', settings['minecraft'])

    class ReadMoreButton(discord.ui.View):
        def __init__(self, version_id, is_snapshot=False):
            super().__init__(timeout=None)
            if is_snapshot:
                url = f"https://www.minecraft.net/article/minecraft-snapshot-{version_id}"
            else:
                url = f"https://www.minecraft.net/article/minecraft-java-edition-{version_id}"
            
            self.add_item(discord.ui.Button(
                label="Read More",
                url=url,
                style=discord.ButtonStyle.url
            ))

async def setup(bot):
    await bot.add_cog(Minecraft(bot))
