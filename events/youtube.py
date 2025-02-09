# THESE ARE NOW PARKED

import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from utils.helpers import PermissionHandler
from datetime import datetime, timezone
from config import YOUTUBE_API_KEY

class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.youtube_api_key = YOUTUBE_API_KEY
        self.check_channels.start()

    def cog_unload(self):
        self.check_channels.cancel()

    async def get_channel_info(self, channel_id):
        """Get channel information from YouTube API"""
        async with aiohttp.ClientSession() as session:
            url = f"https://www.googleapis.com/youtube/v3/channels"
            params = {
                'key': self.youtube_api_key,
                'id': channel_id,
                'part': 'snippet,contentDetails'
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['items'][0] if data['items'] else None
        return None

    async def get_latest_content(self, playlist_id):
        """Get latest videos/streams from a channel's upload playlist"""
        async with aiohttp.ClientSession() as session:
            url = f"https://www.googleapis.com/youtube/v3/playlistItems"
            params = {
                'key': self.youtube_api_key,
                'playlistId': playlist_id,
                'part': 'snippet,contentDetails',
                'maxResults': 1,
                'order': 'date'
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data['items']:
                        video = data['items'][0]
                        publish_time = datetime.fromisoformat(video['snippet']['publishedAt'].replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        if (now - publish_time).total_seconds() > 3600:
                            return None
                        return video
                return None

    async def get_channel_id_from_url(self, identifier):
        """Extract or fetch channel ID from various YouTube URL formats or username"""
        if identifier.startswith('UC'):
            return identifier
            
        if '/' in identifier:
            if '@' in identifier:
                username = identifier.split('@')[-1].split('/')[0]
            elif 'channel/' in identifier:
                return identifier.split('channel/')[-1].split('/')[0]
            elif 'c/' in identifier:
                username = identifier.split('c/')[-1].split('/')[0]
            else:
                username = identifier.split('/')[-1]
        else:
            username = identifier.lstrip('@')

        async with aiohttp.ClientSession() as session:
            url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                'key': self.youtube_api_key,
                'forHandle': username,
                'part': 'id'
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('items'):
                        return data['items'][0]['id']

            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'key': self.youtube_api_key,
                'q': username,
                'type': 'channel',
                'part': 'id,snippet',
                'maxResults': 5
            }
            
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('items'):
                        for item in data['items']:
                            if item['snippet']['title'].lower() == username.lower():
                                return item['id']['channelId']
        return None

    class WatchVideoButton(discord.ui.View):
        def __init__(self, video_url):
            super().__init__(timeout=None)
            self.add_item(discord.ui.Button(
                label="Watch Video",
                url=video_url,
                style=discord.ButtonStyle.url
            ))

    @tasks.loop(minutes=2)
    async def check_channels(self):
        """Check for new YouTube uploads"""
        for guild in self.bot.guilds:
            settings = self.bot.settings.get_all_server_settings(guild.id)
            if not settings.get('youtube', {}).get('channels'):
                continue

            channel_id = settings['youtube'].get('notifications_channel')
            if not channel_id:
                continue

            discord_channel = guild.get_channel(int(channel_id))
            if not discord_channel:
                continue

            for yt_channel_id, channel_data in settings['youtube']['channels'].items():
                try:
                    channel_info = await self.get_channel_info(yt_channel_id)
                    if not channel_info:
                        continue

                    uploads_playlist = channel_info['contentDetails']['relatedPlaylists']['uploads']
                    latest_video = await self.get_latest_content(uploads_playlist)

                    if not latest_video:
                        continue

                    video_id = latest_video['contentDetails']['videoId']
                    last_video_id = settings['youtube'].setdefault('last_videos', {}).get(yt_channel_id)

                    if video_id != last_video_id:
                        video_url = f"https://youtube.com/watch?v={video_id}"
                        channel_name = channel_info['snippet']['title']
                        video_title = latest_video['snippet']['title']
                        thumbnail = latest_video['snippet']['thumbnails']['high']['url']

                        embed = discord.Embed(
                            title=video_title,
                            url=video_url,
                            color=0xFF0000,
                            timestamp=datetime.fromisoformat(latest_video['snippet']['publishedAt'].replace('Z', '+00:00'))
                        )
                        
                        embed.set_author(
                            name=channel_name,
                            url=f"https://youtube.com/channel/{yt_channel_id}",
                            icon_url=channel_info['snippet']['thumbnails']['default']['url']
                        )
                        
                        embed.set_image(url=thumbnail)
                        embed.set_footer(text="New video uploaded")

                        mentions = []
                        if channel_data.get('ping_roles'):
                            for role_id in channel_data['ping_roles']:
                                mentions.append(f"<@&{role_id}>")

                        if settings['youtube'].get('ping_role'):
                            mentions.append(f"<@&{settings['youtube']['ping_role']}>")

                        message = f"**{channel_name}** uploaded a new video!"
                        if mentions:
                            message = f"{' '.join(mentions)} {message}"

                        view = self.WatchVideoButton(video_url)
                        await discord_channel.send(message, embed=embed, view=view)

                        settings['youtube']['last_videos'][yt_channel_id] = video_id
                        self.bot.settings.set_server_setting(guild.id, 'youtube', settings['youtube'])

                except Exception as e:
                    print(f"Error checking YouTube channel {yt_channel_id}: {e}")
                await asyncio.sleep(1)

    @check_channels.before_loop
    async def before_check_channels(self):
        await self.bot.wait_until_ready()

    #################################
    ## Commands
    #################################
    @commands.group(invoke_without_command=True)
    @PermissionHandler.has_permissions(manage_guild=True)
    async def youtube(self, ctx):
        """Manage YouTube notifications"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        youtube_settings = settings.get('youtube', {})

        embed = discord.Embed(
            title="YouTube notifications configuration",
            color=0xFF0000
        )

        channel = ctx.guild.get_channel(int(youtube_settings.get('notifications_channel', 0) or 0))
        embed.add_field(
            name="Notifications channel",
            value=channel.mention if channel else "Not set",
            inline=False
        )

        channels_list = []
        for channel_id, data in youtube_settings.get('channels', {}).items():
            roles = [f"<@&{role_id}>" for role_id in data.get('ping_roles', [])]
            channel_name = data.get('channel_name', channel_id)
            channels_list.append(f"• {channel_name} ({channel_id}) {' '.join(roles)}")

        embed.add_field(
            name="Tracked channels",
            value='\n'.join(channels_list) if channels_list else "No channels added",
            inline=False
        )

        await ctx.send(embed=embed)

    @youtube.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the notifications channel"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        settings.setdefault('youtube', {})['notifications_channel'] = channel.id
        self.bot.settings.set_server_setting(ctx.guild.id, 'youtube', settings['youtube'])
        await ctx.send(f"YouTube notifications will be sent to {channel.mention}")

    @youtube.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def add(self, ctx, identifier: str, *, roles: str = None):
        """Add a YouTube channel to track (channel URL, username, or ID)"""
        try:
            channel_id = await self.get_channel_id_from_url(identifier)
            if not channel_id:
                await ctx.send("Could not find that YouTube channel. Please check the URL or username.")
                return

            settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
            settings.setdefault('youtube', {}).setdefault('channels', {})

            channel_info = await self.get_channel_info(channel_id)
            if not channel_info:
                await ctx.send("Could not fetch channel information. Please try again.")
                return

            role_ids = []
            if roles:
                for role_mention in roles.split():
                    try:
                        role_id = int(''.join(filter(str.isdigit, role_mention)))
                        role = ctx.guild.get_role(role_id)
                        if role:
                            role_ids.append(role.id)
                    except ValueError:
                        continue

            channel_name = channel_info['snippet']['title']
            settings['youtube']['channels'][channel_id] = {
                'ping_roles': role_ids,
                'channel_name': channel_name
            }

            self.bot.settings.set_server_setting(ctx.guild.id, 'youtube', settings['youtube'])
            roles_text = f" with notifications for {', '.join(f'<@&{r}>' for r in role_ids)}" if role_ids else ""
            await ctx.send(f"Added channel `{channel_name}`{roles_text}")
            
        except Exception as e:
            print(f"Error in youtube add: {e}")
            await ctx.send("An error occurred while adding the channel. Please check the URL or username.")

    @youtube.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def remove(self, ctx, channel_id: str):
        """Remove a tracked YouTube channel"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        if 'youtube' in settings and 'channels' in settings['youtube']:
            if channel_id in settings['youtube']['channels']:
                del settings['youtube']['channels'][channel_id]
                settings['youtube'].setdefault('last_videos', {}).pop(channel_id, None)
                self.bot.settings.set_server_setting(ctx.guild.id, 'youtube', settings['youtube'])
                await ctx.send(f"Removed channel `{channel_id}`")
                return
        await ctx.send("That channel isn't being tracked!")

    @youtube.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def channelrole(self, ctx, channel_id: str, *, role: discord.Role):
        """Add a role to be pinged for a specific YouTube channel"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        
        if 'youtube' not in settings or 'channels' not in settings['youtube']:
            await ctx.send("No channels are being tracked!")
            return
            
        if channel_id not in settings['youtube']['channels']:
            await ctx.send(f"`{channel_id}` is not being tracked!")
            return
            
        channel_data = settings['youtube']['channels'][channel_id]
        ping_roles = channel_data.get('ping_roles', [])
        
        if role.id in ping_roles:
            ping_roles.remove(role.id)
            action = "removed from"
        else:
            ping_roles.append(role.id)
            action = "added to"
            
        settings['youtube']['channels'][channel_id]['ping_roles'] = ping_roles
        self.bot.settings.set_server_setting(ctx.guild.id, 'youtube', settings['youtube'])
        
        await ctx.send(f"Role {role.mention} has been {action} {channel_id}'s notifications")

    @youtube.command(aliases=['globalrole'])
    @PermissionHandler.has_permissions(manage_guild=True)
    async def role(self, ctx, role: discord.Role):
        """Set a role to be pinged for all YouTube notifications"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        settings.setdefault('youtube', {})
        
        if 'ping_role' in settings['youtube'] and settings['youtube']['ping_role'] == role.id:
            settings['youtube'].pop('ping_role')
            await ctx.send(f"Removed {role.mention} as the YouTube notification role")
        else:
            settings['youtube']['ping_role'] = role.id
            await ctx.send(f"Set {role.mention} as the YouTube notification role")
            
        self.bot.settings.set_server_setting(ctx.guild.id, 'youtube', settings['youtube'])

async def setup(bot):
    await bot.add_cog(YouTube(bot))
