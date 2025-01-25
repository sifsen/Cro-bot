import discord
from discord.ext import commands
from datetime import datetime

class LoggingEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recent_deletions = {}

    #################################
    ## Logchannel Helper
    #################################
    async def log_to_channel(self, guild_id: int, log_type: str, embed: discord.Embed):
        """Logs to the appropriate channel"""
        try:
            setting_name = f"log_channel_{log_type}"
            settings = self.bot.settings.get_all_server_settings(guild_id)
            channel_id = settings.get(setting_name)
            
            if not channel_id:
                return
                
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return
                
            permissions = channel.permissions_for(channel.guild.me)
            if not permissions.send_messages or not permissions.embed_links:
                return

            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error in log_to_channel: {str(e)}")

    #################################
    ## Message Edit
    #################################   
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return

        embed = discord.Embed(
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(
            name=before.author.name,
            icon_url=before.author.display_avatar.url
        )
        
        embed.add_field(name="Before", value=before.content[:1024] or "*Empty*", inline=False)
        embed.add_field(name="After", value=after.content[:1024] or "*Empty*", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="User ID", value=f"```{before.author.id}```", inline=False)
        embed.add_field(name="", value=f"[Jump to message]({before.jump_url})", inline=True)

        await self.log_to_channel(before.guild.id, "edits", embed)

    #################################
    ## Message Delete
    #################################
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or message.id in self.recent_deletions:
            return

        embed = discord.Embed(
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        embed.set_author(
            name=message.author.name,
            icon_url=message.author.display_avatar.url
        )
        
        embed.add_field(name="Content", value=message.content[:1024] or "*Empty*", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="User ID", value=f"```{message.author.id}```", inline=False)

        await self.log_to_channel(message.guild.id, "deletions", embed)

    #################################
    ## Member Join
    #################################
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(
            title="Member Joined",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Member", value=f"{member.mention} ({member})", inline=True)
        embed.add_field(name="ID", value=f"```{member.id}```", inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)

        await self.log_to_channel(member.guild.id, "join_leave", embed)

    #################################
    ## Member Leave
    #################################
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(
            title="Member Left",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Member", value=f"{member.mention} ({member})", inline=True)
        embed.add_field(name="ID", value=f"```{member.id}```", inline=True)
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)

        await self.log_to_channel(member.guild.id, "join_leave", embed)


    #################################
    ## User Update
    #################################   
    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if (before.avatar == after.avatar and 
            before.name == after.name and 
            before.global_name == after.global_name):
            return
            
        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(
            name=after.name,
            icon_url=after.display_avatar.url
        )
        
        embed.set_thumbnail(url=after.display_avatar.url)
        
        embed.add_field(
            name="", 
            value=f"<@{after.id}> `{after.id}`",
            inline=False
        )
        
        if before.name != after.name:
            embed.add_field(
                name="",
                value=f"{before.name} → {after.name}",
                inline=False
            )
        
        if before.global_name != after.global_name:
            embed.add_field(
                name="",
                value=f"{before.global_name or '*None*'} → {after.global_name or '*None*'}",
                inline=False
            )

        if before.avatar != after.avatar:
            embed.add_field(
                name="",
                value=f"[View avatar]({after.display_avatar.url})",
                inline=False
            )
        
        for guild in self.bot.guilds:
            if guild.get_member(after.id):
                await self.log_to_channel(guild.id, "profiles", embed)

async def setup(bot):
    await bot.add_cog(LoggingEvents(bot)) 