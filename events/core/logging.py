import discord
from discord.ext import commands
from datetime import datetime
from utils.helpers.formatting import EmbedBuilder

class LoggingEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recent_deletions = {}

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
    ## Member Events
    #################################
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(
            title="Member joined",
            description=f"{member.mention} `{member.id}`",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        created_ago = discord.utils.format_dt(member.created_at, style='R')
        created_at = discord.utils.format_dt(member.created_at, style='D')
        
        embed.add_field(
            name="Account created",
            value=f"{created_at}\n{created_ago}",
            inline=False
        )
        
        embed.set_author(
            name=str(member),
            icon_url=member.display_avatar.url
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await self.log_to_channel(member.guild.id, "join_leave", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(
            title="Member left",
            description=f"{member.mention} `{member.id}`",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        joined_ago = discord.utils.format_dt(member.joined_at, style='R')
        joined_at = discord.utils.format_dt(member.joined_at, style='D')
        
        embed.add_field(
            name="Joined server",
            value=f"{joined_at}\n{joined_ago}",
            inline=False
        )
        
        roles = [role.mention for role in member.roles[1:]]
        if roles:
            embed.add_field(
                name="Roles",
                value=" ".join(roles),
                inline=False
            )
        
        embed.set_author(
            name=str(member),
            icon_url=member.display_avatar.url
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await self.log_to_channel(member.guild.id, "join_leave", embed)

    #################################
    ## Message Events
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

        await self.log_to_channel(before.guild.id, "messages", embed)

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

        if message.attachments:
            attachments = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
            embed.add_field(name="Attachments", value=attachments, inline=False)

        current_time = datetime.utcnow()
        embed.set_footer(text=current_time.strftime("%d/%m/%Y %H:%M"))

        await self.log_to_channel(message.guild.id, "messages", embed)

    #################################
    ## Member Update Events
    #################################
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.nick != after.nick:
            embed = EmbedBuilder(
                title="Nickname changed",
                color=discord.Color.blue()
            ).add_field(
                name="Member", 
                value=f"{after.mention} ({after})", 
                inline=True
            ).add_field(
                name="Before", 
                value=before.nick or "None", 
                inline=True
            ).add_field(
                name="After", 
                value=after.nick or "None", 
                inline=True
            )

            await self.log_to_channel(after.guild.id, "profiles", embed.build())

        added_roles = set(after.roles) - set(before.roles)
        removed_roles = set(before.roles) - set(after.roles)

        if added_roles or removed_roles:
            embed = EmbedBuilder(
                title="Member roles updated",
                color=discord.Color.blue()
            ).add_field(
                name="Member", 
                value=f"{after.mention} ({after})", 
                inline=False
            )

            if added_roles:
                embed.add_field(
                    name="Added roles", 
                    value=" ".join(role.mention for role in added_roles), 
                    inline=False
                )

            if removed_roles:
                embed.add_field(
                    name="Removed roles", 
                    value=" ".join(role.mention for role in removed_roles), 
                    inline=False
                )

            await self.log_to_channel(after.guild.id, "profiles", embed.build())

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
            name=after.name
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