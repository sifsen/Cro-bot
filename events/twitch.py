import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from utils.helpers import PermissionHandler
from datetime import datetime, timezone
from config import TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET

class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitch_client_id = TWITCH_CLIENT_ID
        self.twitch_client_secret = TWITCH_CLIENT_SECRET
        self.access_token = None
        self.check_streams.start()

    def cog_unload(self):
        self.check_streams.cancel()

    async def get_access_token(self):
        """Get Twitch API access token"""
        async with aiohttp.ClientSession() as session:
            params = {
                'client_id': self.twitch_client_id,
                'client_secret': self.twitch_client_secret,
                'grant_type': 'client_credentials'
            }
            async with session.post('https://id.twitch.tv/oauth2/token', params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.access_token = data['access_token']
                    return self.access_token
        return None

    async def get_stream_info(self, username):
        """Get stream information from Twitch API"""
        if not self.access_token:
            await self.get_access_token()

        headers = {
            'Client-ID': self.twitch_client_id,
            'Authorization': f'Bearer {self.access_token}'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.twitch.tv/helix/streams?user_login={username}', headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    stream_data = data['data'][0] if data['data'] else None
                    if not stream_data:
                        return None
                    
                    user_id = stream_data['user_id']
                    async with session.get(f'https://api.twitch.tv/helix/users?id={user_id}', headers=headers) as user_resp:
                        if user_resp.status == 200:
                            user_data = await user_resp.json()
                            if user_data['data']:
                                stream_data['profile_image'] = user_data['data'][0]['profile_image_url']
                                stream_data['display_name'] = user_data['data'][0]['display_name']

                    if stream_data['game_id']:
                        async with session.get(f'https://api.twitch.tv/helix/games?id={stream_data["game_id"]}', headers=headers) as game_resp:
                            if game_resp.status == 200:
                                game_data = await game_resp.json()
                                if game_data['data']:
                                    stream_data['game_box_art'] = game_data['data'][0]['box_art_url'].replace('{width}', '188').replace('{height}', '250')

                    return stream_data
                elif resp.status == 401:
                    await self.get_access_token()
                    return await self.get_stream_info(username)
        return None

    #################################
    ## Check Streams
    #################################
    @tasks.loop(minutes=2)
    async def check_streams(self):
        """Check if tracked streamers are live or ended"""

        for guild in self.bot.guilds:
            settings = self.bot.settings.get_all_server_settings(guild.id)
            if not settings.get('twitch', {}).get('streamers'):
                continue

            last_notifications = settings['twitch'].get('last_notifications', {})
            notification_messages = settings['twitch'].get('notification_messages', {})

            channel_id = settings['twitch'].get('notifications_channel')
            if not channel_id:
                continue

            channel = guild.get_channel(int(channel_id))
            if not channel:
                continue

            for streamer, streamer_data in settings['twitch']['streamers'].items():
                try:
                    stream_info = await self.get_stream_info(streamer)
                    message_key = f"{guild.id}-{streamer}"
                    
                    if stream_info:
                        last_notification = last_notifications.get(message_key)
                        stream_start = datetime.strptime(stream_info['started_at'], '%Y-%m-%dT%H:%M:%SZ')
                        
                        if not last_notification or last_notification < stream_start:
                            stream_url = f"https://twitch.tv/{streamer}"
                            message = f"**{stream_info['display_name']}** is live!"

                            embed = discord.Embed(
                                description=f"**{stream_info['title']}**\nGame: *{stream_info['game_name']}*",
                                color=0x6441A4,
                                timestamp=stream_start
                            )
                            
                            embed.set_author(
                                name=stream_info['display_name'],
                                icon_url=stream_info.get('profile_image'),
                                url=stream_url
                            )
                            
                            embed.set_image(url=stream_info['thumbnail_url'].replace('{width}', '1920').replace('{height}', '1080'))
                            
                            if stream_info.get('game_box_art'):
                                embed.set_thumbnail(url=stream_info['game_box_art'])
                            
                            embed.set_footer(text="Stream started")

                            message = f"**{stream_info['display_name']}** is live!"
                            mentions = []

                            for role_id in streamer_data.get('ping_roles', []):
                                mentions.append(f"<@&{role_id}>")
                            
                            if settings['twitch'].get('ping_role'):
                                mentions.append(f"<@&{settings['twitch']['ping_role']}>")

                            if mentions:
                                message = f"{' '.join(mentions)} {message}"

                            view = self.WatchStreamButton(stream_url)
                            sent_message = await channel.send(message, embed=embed, view=view)
                            
                            settings['twitch']['last_notifications'][message_key] = stream_start.isoformat()
                            settings['twitch']['notification_messages'][message_key] = sent_message.id
                            self.bot.settings.set_server_setting(guild.id, 'twitch', settings['twitch'])

                    elif message_key in notification_messages:
                        try:
                            message_id = notification_messages[message_key]
                            message = await channel.fetch_message(message_id)
                            
                            if message:
                                stream_start = last_notifications[message_key]
                                stream_url = f"https://twitch.tv/{streamer}"
                                
                                embed = message.embeds[0]
                                embed.color = 0x808080
                                embed.set_footer(text=f"Was live on {stream_start.strftime('%m-%d %H:%M')}")
                                
                                new_content = message.content.replace("is live!", "was live")
                                view = self.WatchStreamButton(stream_url)
                                await message.edit(content=new_content, embed=embed, view=view)
                                
                                settings['twitch']['last_notifications'].pop(message_key, None)
                                settings['twitch']['notification_messages'].pop(message_key, None)
                                self.bot.settings.set_server_setting(guild.id, 'twitch', settings['twitch'])
                                
                        except (discord.NotFound, discord.HTTPException):
                            notification_messages.pop(message_key, None)
                            last_notifications.pop(message_key, None)
                            self.bot.settings.set_server_setting(guild.id, 'twitch', settings['twitch'])

                except Exception as e:
                    print(f"Error checking stream {streamer}: {e}")
                await asyncio.sleep(1)

    @check_streams.before_loop
    async def before_check_streams(self):
        await self.bot.wait_until_ready()

    #################################
    ## Commands
    #################################
    @commands.group(invoke_without_command=True)
    @PermissionHandler.has_permissions(manage_guild=True)
    async def twitch(self, ctx):
        """Manage Twitch notifications"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        twitch_settings = settings.get('twitch', {})

        embed = discord.Embed(
            title="Twitch notifications configuration",
            color=0x6441A4
        )

        channel = ctx.guild.get_channel(int(twitch_settings.get('notifications_channel', 0) or 0))
        embed.add_field(
            name="Notifications channel",
            value=channel.mention if channel else "Not set",
            inline=False
        )

        streamers_list = []
        for streamer, data in twitch_settings.get('streamers', {}).items():
            roles = [f"<@&{role_id}>" for role_id in data.get('ping_roles', [])]
            streamers_list.append(f"• {streamer} {' '.join(roles)}")

        embed.add_field(
            name="Tracked streamers",
            value='\n'.join(streamers_list) if streamers_list else "No streamers added",
            inline=False
        )

        await ctx.send(embed=embed)

    #################################
    ## Channel
    #################################
    @twitch.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the notifications channel"""

        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        settings.setdefault('twitch', {})['notifications_channel'] = channel.id
        self.bot.settings.set_server_setting(ctx.guild.id, 'twitch', settings['twitch'])
        await ctx.send(f"Twitch notifications will be sent to {channel.mention}")

    #################################
    ## Add
    #################################
    @twitch.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def add(self, ctx, streamer: str, *, roles: str = None):

        """Add a Twitch streamer to track"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        settings.setdefault('twitch', {}).setdefault('streamers', {})

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

        settings['twitch']['streamers'][streamer.lower()] = {
            'ping_roles': role_ids
        }

        self.bot.settings.set_server_setting(ctx.guild.id, 'twitch', settings['twitch'])
        roles_text = f" with notifications for {', '.join(f'<@&{r}>' for r in role_ids)}" if role_ids else ""
        await ctx.send(f"Added channel `{streamer}`{roles_text}")

    #################################
    ## Remove
    #################################
    @twitch.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def remove(self, ctx, streamer: str):

        """Remove a tracked Twitch streamer"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        if 'twitch' in settings and 'streamers' in settings['twitch']:
            if streamer.lower() in settings['twitch']['streamers']:
                del settings['twitch']['streamers'][streamer.lower()]
                self.bot.settings.set_server_setting(ctx.guild.id, 'twitch', settings['twitch'])
                await ctx.send(f"Removed channel `{streamer}`")
                return
        await ctx.send("That streamer isn't being tracked!")

    #################################
    ## Channel Role
    #################################
    @twitch.command()
    @PermissionHandler.has_permissions(manage_guild=True)
    async def channelrole(self, ctx, streamer: str, *, role: discord.Role):
        """Add a role to be pinged when a specific streamer goes live"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        
        if 'twitch' not in settings or 'streamers' not in settings['twitch']:
            await ctx.send("No streamers are being tracked!")
            return
            
        if streamer.lower() not in settings['twitch']['streamers']:
            await ctx.send(f"`{streamer}` is not being tracked!")
            return
            
        streamer_data = settings['twitch']['streamers'][streamer.lower()]
        ping_roles = streamer_data.get('ping_roles', [])
        
        if role.id in ping_roles:
            ping_roles.remove(role.id)
            action = "removed from"
        else:
            ping_roles.append(role.id)
            action = "added to"
            
        settings['twitch']['streamers'][streamer.lower()]['ping_roles'] = ping_roles
        self.bot.settings.set_server_setting(ctx.guild.id, 'twitch', settings['twitch'])
        
        await ctx.send(f"Role {role.mention} has been {action} {streamer}'s notifications")

    #################################
    ## Global Role
    #################################
    @twitch.command(aliases=['globalrole'])
    @PermissionHandler.has_permissions(manage_guild=True)
    async def role(self, ctx, role: discord.Role):
        """Set a role to be pinged for all Twitch notifications"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        settings.setdefault('twitch', {})
        
        if 'ping_role' in settings['twitch'] and settings['twitch']['ping_role'] == role.id:
            settings['twitch'].pop('ping_role')
            await ctx.send(f"Removed {role.mention} as the Twitch notification role")
        else:
            settings['twitch']['ping_role'] = role.id
            await ctx.send(f"Set {role.mention} as the Twitch notification role")
            
        self.bot.settings.set_server_setting(ctx.guild.id, 'twitch', settings['twitch'])

    class WatchStreamButton(discord.ui.View):
        def __init__(self, stream_url):
            super().__init__(timeout=None)
            self.add_item(discord.ui.Button(
                label="Watch Stream",
                url=stream_url,
                style=discord.ButtonStyle.url
            ))

async def setup(bot):
    await bot.add_cog(Twitch(bot)) 