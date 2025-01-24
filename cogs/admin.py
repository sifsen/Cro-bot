import discord

from discord.ext import commands
from datetime import datetime

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.guild_permissions.administrator
        
    #################################
    ## Purge Command
    #################################
    @commands.command()
    async def purge(self, ctx, amount: int):
        """Delete a specified number of messages"""
        try:
            await ctx.channel.purge(limit=amount + 1)
            msg = await ctx.send(f"Deleted {amount} messages.")
            await msg.delete(delay=3)
        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Role Command
    #################################
    @commands.command()
    async def role(self, ctx, member: discord.Member, role: discord.Role):
        """Add or remove a role from a member"""
        try:
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"Removed role **{role.name}** from {member.mention}")
            else:
                await member.add_roles(role)
                await ctx.send(f"Added role **{role.name}** to {member.mention}")
        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Nickname Command
    #################################
    @commands.command()
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

async def setup(bot):
    await bot.add_cog(Admin(bot))