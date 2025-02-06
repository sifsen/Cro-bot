import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import parsedatetime
import time
import re
import aiohttp
from config import STEAM_API_KEY

class Casual(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cal = parsedatetime.Calendar()
        self.active_reminders = {}
        self.afk_users = {}
        
    #################################
    ## About Command
    #################################
    @commands.command()
    async def about(self, ctx):
        """About Kael"""
        embed = discord.Embed(
            title="About Kael",
            description=(
                "Work in progress"
            ),
            color=0x2B2D31
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text=f"Buh")
        await ctx.send(embed=embed)

    #################################
    ## Issues Command
    ################################
    @commands.command(aliases=["issue", "features", "request", "suggestion"])
    async def issues(self, ctx):
        """Report an issue or request a feature"""
        await ctx.send("Click [this link](https://github.com/CursedSen/Kael-bot/issues) to report an issue or request a feature!")

    #################################
    ## Invite Kael
    #################################
    @commands.command()
    async def invite(self, ctx):
        """Invite Kael to your server"""
        await ctx.send("You can click on my profile, or click [this link](https://discord.com/oauth2/authorize?client_id=1293508738036142091) to invite me to your server!")

    #################################
    ## Ping Command
    #################################
    @commands.command()
    async def ping(self, ctx):
        """Check bot's latency"""
        await ctx.send(f"# Pong!\n**Latency**: {round(self.bot.latency * 1000)}ms")
        
    #################################
    ## User Info Command
    #################################
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Get detailed info about a user"""
        member = member or ctx.author
        
        roles = [role.mention for role in member.roles[1:]]
        
        embed = discord.Embed(
            title=f"{member.name}",
            color=member.color,
            timestamp=datetime.utcnow()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="", value=f"```ID: {member.id}```", inline=False)
        embed.add_field(
            name="Created at",
            value=discord.utils.format_dt(member.created_at, 'F'),
            inline=True
        )
        embed.add_field(
            name="Joined at",
            value=discord.utils.format_dt(member.joined_at, 'F'),
            inline=True
        )
        
        if roles:
            embed.add_field(
                name=f"Roles [{len(roles)}]",
                value=" ".join(roles) if len(" ".join(roles)) < 1024 else f"{len(roles)} roles",
                inline=False
            )
        
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(
            name="Status",
            value=str(member.status).title(),
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    #################################
    ## Avatar Command
    #################################
    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        """Get a user's avatar"""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=member.color)
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed)

    #################################
    ## Banner Command
    #################################
    @commands.command()
    async def banner(self, ctx, member: discord.Member = None):
        """Get a user's banner"""
        member = member or ctx.author
        
        user = await self.bot.fetch_user(member.id)
        if not user.banner:
            await ctx.send(f"{member.display_name} doesn't have a banner!")
            return
            
        embed = discord.Embed(title=f"{member.display_name}'s Banner", color=member.color)
        embed.set_image(url=user.banner.url)
        await ctx.send(embed=embed)

    #################################
    ## Reminder Command
    #################################
    @commands.command(aliases=['remind', 'remindme'])
    async def reminder(self, ctx, time_str: str, *, reminder_text: str):
        """Set a reminder
        Example: !reminder 2h30m check the oven"""
        reminder_text = discord.utils.escape_mentions(reminder_text)
        reminder_text = discord.utils.escape_markdown(reminder_text)
        
        if len(reminder_text) > 1000:
            await ctx.send("Reminder text too long! (max 1000 characters)")
            return
        
        total_seconds = 0
        time_parts = re.findall(r'(\d+)([wdhms])', time_str.lower())
        
        if not time_parts:
            await ctx.send("What are you doing?")
            return
            
        for value, unit in time_parts:
            value = int(value)
            if unit == 'w':
                total_seconds += value * 7 * 24 * 60 * 60
            elif unit == 'd':
                total_seconds += value * 24 * 60 * 60
            elif unit == 'h':
                total_seconds += value * 60 * 60
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 's':
                total_seconds += value
            
        if total_seconds == 0:
            await ctx.send("Please specify a valid duration!")
            return
            
        if total_seconds > 2592000:
            await ctx.send("Reminder time too far in the future (max 30 days)")
            return
            
        reminder_time = datetime.now() + timedelta(seconds=total_seconds)
        reminder_id = f"{ctx.author.id}-{int(time.time())}"
        
        if not hasattr(self, 'active_reminders'):
            self.active_reminders = {}
        
        self.active_reminders[reminder_id] = {
            'channel_id': ctx.channel.id,
            'author_id': ctx.author.id,
            'text': reminder_text,
            'time': reminder_time.isoformat()
        }
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        confirm_msg = f"I'll remind you in "
        if hours > 0:
            confirm_msg += f"{int(hours)} hours "
        if minutes > 0:
            confirm_msg += f"{int(minutes)} minutes"
        
        await ctx.reply(confirm_msg, ephemeral=True)
        
        async def remind():
            await asyncio.sleep(total_seconds)
            if reminder_id in self.active_reminders:
                channel = self.bot.get_channel(ctx.channel.id)
                if channel:
                    await channel.send(f"# Reminder! {ctx.author.mention}\n{reminder_text}")
                del self.active_reminders[reminder_id]
                
        self.bot.loop.create_task(remind())

    #################################
    ## Reminders Command
    #################################
    @commands.command()
    async def reminders(self, ctx):
        """List your active reminders"""
        if not hasattr(self, 'active_reminders'):
            self.active_reminders = {}
            
        user_reminders = {k: v for k, v in self.active_reminders.items() 
                         if v['author_id'] == ctx.author.id}
        
        if not user_reminders:
            await ctx.send("You have no active reminders!")
            return
            
        embed = discord.Embed(title="Your active reminders", color=0x2B2D31)
        
        for reminder_id, reminder in user_reminders.items():
            reminder_time = datetime.fromisoformat(reminder['time'])
            time_left = reminder_time - datetime.now()
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            time_str = ""
            if hours > 0:
                time_str += f"{hours}h "
            if minutes > 0:
                time_str += f"{minutes}m"
                
            embed.add_field(
                name=f"In {time_str}",
                value=reminder['text'],
                inline=False
            )
            
        await ctx.send(embed=embed)

    #################################
    ## Stopwatch Command
    #################################
    @commands.command(aliases=['sw'])
    async def stopwatch(self, ctx):
        """Start or stop the stopwatch"""
        if not hasattr(self, 'stopwatches'):
            self.stopwatches = {}
            
        if ctx.author.id not in self.stopwatches:
            self.stopwatches[ctx.author.id] = int(time.time())
            await ctx.send(f"{ctx.author.mention} Stopwatch started!")
        else:
            duration = int(time.time()) - self.stopwatches[ctx.author.id]
            formatted_time = str(timedelta(seconds=duration))
            await ctx.send(f"{ctx.author.mention} Stopwatch stopped!\nTime: **{formatted_time}**")
            self.stopwatches.pop(ctx.author.id, None)

    #################################
    ## Server Info Command
    #################################
    @commands.command()
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """Display detailed server information"""
        guild = ctx.guild
        
        total_members = guild.member_count
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed = discord.Embed(
            title=f"Server Info - {guild.name}",
            color=0x2B2D31,
            timestamp=datetime.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.add_field(
            name="Owner", 
            value=guild.owner.mention,
            inline=True
        )
        embed.add_field(
            name="Created On",
            value=discord.utils.format_dt(guild.created_at, 'F'),
            inline=True
        )
        
        embed.add_field(
            name="Members",
            value=f"Total: {total_members}\nOnline: {online_members}",
            inline=True
        )
        
        embed.add_field(
            name="Channels",
            value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}",
            inline=True
        )
        
        embed.add_field(
            name="Roles",
            value=len(guild.roles),
            inline=True
        )
        
        if guild.features:
            features = "\n".join(f"• {feature.replace('_', ' ').title()}" for feature in guild.features)
            embed.add_field(
                name="Features",
                value=features,
                inline=False
            )
        
        if guild.premium_tier > 0:
            boost_info = f"Level {guild.premium_tier}\nBoosts: {guild.premium_subscription_count}"
            embed.add_field(
                name="Server Boost",
                value=boost_info,
                inline=True
            )
            
        verification = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        embed.add_field(
            name="Security",
            value=f"Verification: {verification[guild.verification_level]}",
            inline=True
        )
        
        embed.set_footer(text=f"ID: {guild.id}")
        await ctx.send(embed=embed)

    #################################
    ## AFK System
    #################################
    @commands.command()
    async def afk(self, ctx, *, message: str = "AFK"):
        """Set your AFK status"""
        if '@everyone' in message or '@here' in message:
            await ctx.send("Nice try!")
            return
        message = discord.utils.escape_mentions(message)
        
        self.afk_users[ctx.author.id] = {
            'message': message,
            'time': datetime.now()
        }
        await ctx.send(f"You are now AFK:\n**{message}**")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid and ctx.command and ctx.command.name == 'afk':
            return

        if message.author.id in self.afk_users:
            del self.afk_users[message.author.id]
            await message.channel.send(f"Welcome back {message.author.mention}, I've removed your AFK status!")
            return

        for mention in message.mentions:
            if mention.id in self.afk_users:
                afk_data = self.afk_users[mention.id]
                time_diff = datetime.now() - afk_data['time']
                hours = time_diff.seconds // 3600
                minutes = (time_diff.seconds % 3600) // 60
                
                time_str = ""
                if hours > 0:
                    time_str += f"{hours}h "
                time_str += f"{minutes}m ago"
                
                await ctx.reply(
                    f"{mention.display_name} is AFK: **{afk_data['message']}**\n**{time_str}**"
                )

    #################################
    ## Steam Command
    #################################
    @commands.command()
    async def steam(self, ctx, *, steam_id: str):
        """Display a Steam profile
        Usage: !steam <steamID/customURL/profileURL>"""
        
        if not STEAM_API_KEY:
            await ctx.send("Steam API key not configured or invalid!")
            return
        
        if "steamcommunity.com" not in steam_id and not steam_id.isdigit():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={steam_id}"
                ) as resp:
                    data = await resp.json()
                    if data['response'].get('success') == 1:
                        steam_id = data['response']['steamid']
                    else:
                        await ctx.send("Could not find Steam profile!")
                        return
        elif "steamcommunity.com" in steam_id:
            if "/id/" in steam_id:
                custom_url = steam_id.split("/id/")[1].split("/")[0]
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={STEAM_API_KEY}&vanityurl={custom_url}"
                    ) as resp:
                        data = await resp.json()
                        if data['response'].get('success') == 1:
                            steam_id = data['response']['steamid']
                        else:
                            await ctx.send("Could not find Steam profile!")
                            return
            elif "/profiles/" in steam_id:
                steam_id = steam_id.split("/profiles/")[1].split("/")[0]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steam_id}"
            ) as resp:
                data = await resp.json()
                
        if not data['response']['players']:
            await ctx.send("Could not find Steam profile!")
            return
        
        player = data['response']['players'][0]
        
        embed = discord.Embed(
            title=player['personaname'],
            url=player['profileurl'],
            color=0x2B2D31
        )
        
        embed.set_thumbnail(url=player['avatarfull'])
        
        status_map = {
            0: "Offline",
            1: "Online",
            2: "Busy",
            3: "Away",
            4: "Snooze",
            5: "Looking to Trade",
            6: "Looking to Play"
        }
        status = status_map.get(player['personastate'], "Unknown")
        
        if player.get('gameextrainfo'):
            status = f"Playing {player['gameextrainfo']}"
        
        embed.add_field(
            name="Status",
            value=status,
            inline=True
        )
        
        if 'timecreated' in player:
            created_at = datetime.fromtimestamp(player['timecreated'])
            embed.add_field(
                name="Account Created",
                value=discord.utils.format_dt(created_at, 'R'),
                inline=True
            )
        
        if player.get('loccountrycode'):
            embed.add_field(
                name="Location",
                value=f":flag_{player['loccountrycode'].lower()}:",
                inline=True
            )
        
        embed.add_field(
            name="Steam ID",
            value=f"```{steam_id}```",
            inline=False
        )

        links = [
            f"[Profile]({player['profileurl']})",
            f"[Add Friend]({player['profileurl']}friends/add)",
            f"[Trade Offers]({player['profileurl']}tradeoffers)",
            f"[Inventory]({player['profileurl']}inventory)",
            f"[Games]({player['profileurl']}games/?tab=all)"
        ]
        
        embed.add_field(
            name="Quick Links",
            value=" • ".join(links),
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Casual(bot))