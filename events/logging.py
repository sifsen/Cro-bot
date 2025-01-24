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
            title="Message Edited",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(
            name=before.author.name,
            icon_url=before.author.display_avatar.url
        )
        
        embed.add_field(name="Before", value=before.content[:1024] or "*Empty*", inline=False)
        embed.add_field(name="After", value=after.content[:1024] or "*Empty*", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Author", value=before.author.mention, inline=True)
        embed.add_field(name="Message ID", value=before.id, inline=True)
        embed.add_field(name="Jump to Message", value=f"[Click Here]({before.jump_url})", inline=True)

        await self.log_to_channel(before.guild.id, "edits", embed)

    #################################
    ## Message Delete
    #################################
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or message.id in self.recent_deletions:
            return

        embed = discord.Embed(
            title="Message Deleted",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Content", value=message.content[:1024] or "*Empty*", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Author", value=message.author.mention, inline=True)
        embed.add_field(name="Message ID", value=message.id, inline=True)

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
        embed.add_field(name="ID", value=member.id, inline=True)
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
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)

        await self.log_to_channel(member.guild.id, "join_leave", embed)

    #################################
    ## Member Update
    #################################
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick or before.roles != after.roles:
            embed = discord.Embed(
                title="Member Updated",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Member", value=f"{after.mention} ({after})", inline=True)
            
            if before.nick != after.nick:
                embed.add_field(name="Nickname Change", value=f"Before: {before.nick or '*None*'}\nAfter: {after.nick or '*None*'}", inline=False)
            
            if before.roles != after.roles:
                added_roles = set(after.roles) - set(before.roles)
                removed_roles = set(before.roles) - set(after.roles)
                
                if added_roles:
                    embed.add_field(name="Roles Added", value=", ".join(role.mention for role in added_roles), inline=False)
                if removed_roles:
                    embed.add_field(name="Roles Removed", value=", ".join(role.mention for role in removed_roles), inline=False)

            embed.set_thumbnail(url=after.display_avatar.url)
            await self.log_to_channel(after.guild.id, "profiles", embed)

async def setup(bot):
    await bot.add_cog(LoggingEvents(bot)) 