import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import parsedatetime
import time
import re

class Casual(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cal = parsedatetime.Calendar()
        self.active_reminders = {}
        
    #################################
    ## About Command
    #################################
    @commands.command()
    async def about(self, ctx):
        """About Rei"""
        embed = discord.Embed(
            title="About Rei",
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
        await ctx.send("Click [this link](https://github.com/CursedSen/Rei-bot/issues) to report an issue or request a feature!")

    #################################
    ## Invite Rei
    #################################
    @commands.command()
    async def invite(self, ctx):
        """Invite Rei to your server"""
        await ctx.send("Click [this link](https://discord.com/oauth2/authorize?client_id=1293508738036142091) to invite me to your server!")
        
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
        """Get info about a user"""
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info - {member.tag}", color=member.color)
        embed.add_field(name="ID", value=f"```{member.id}```")
        embed.add_field(name="Joined", value=f"```{member.joined_at.strftime('%Y-%m-%d')}```")
        embed.set_thumbnail(url=member.avatar.url)
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
        
        # verwerk de tijd input
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
            
        # maak de reminder
        reminder_time = datetime.now() + timedelta(seconds=total_seconds)
        reminder_id = f"{ctx.author.id}-{int(time.time())}"
        
        self.active_reminders[reminder_id] = {
            'channel_id': ctx.channel.id,
            'author_id': ctx.author.id,
            'text': reminder_text,
            'time': reminder_time.isoformat()
        }
        
        # laat zien wanneer
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        confirm_msg = f"I'll remind you in "
        if hours > 0:
            confirm_msg += f"{int(hours)} hours "
        if minutes > 0:
            confirm_msg += f"{int(minutes)} minutes"
        
        await ctx.reply(confirm_msg, ephemeral=True)
        
        # start de timer
        async def remind():
            await asyncio.sleep(total_seconds)
            if reminder_id in self.active_reminders:
                channel = self.bot.get_channel(ctx.channel.id)
                if channel:
                    await channel.reply(f"# Reminder! {ctx.author.mention}\n{reminder_text}")
                del self.active_reminders[reminder_id]
                
        self.bot.loop.create_task(remind())

    #################################
    ## Reminders Command
    #################################
    @commands.command()
    async def reminders(self, ctx):
        """List your active reminders"""
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

async def setup(bot):
    await bot.add_cog(Casual(bot))