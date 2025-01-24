import discord

from discord.ext import commands
from datetime import datetime

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_moderation_action(self, ctx, action, member, reason):
        embed = discord.Embed(
            title=f"Moderation Action: {action}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Target", value=f"{member.name}#{member.discriminator}")
        embed.add_field(name="Moderator", value=f"{ctx.author.name}#{ctx.author.discriminator}")
        embed.add_field(name="Reason", value=reason or "No reason provided", inline=False)
        
        log_channel = ctx.guild.system_channel
        if log_channel:
            await log_channel.send(embed=embed)

    #################################
    ## Kick Command
    #################################      
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server"""
        try:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot kick someone with a higher or equal role!")
                return
                
            confirm = await ctx.send(f"Are you sure you want to kick {member.mention}?")
            await confirm.add_reaction('✅')
            await confirm.add_reaction('❌')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except TimeoutError:
                await ctx.send("Kick command timed out.")
                return

            if str(reaction.emoji) == '✅':
                await member.kick(reason=reason)
                await self.log_moderation_action(ctx, "Kick", member, reason)
                await ctx.send(f"{member.mention} has been kicked.")
            else:
                await ctx.send("Kick command cancelled.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to kick that member!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Ban Command
    #################################   
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server"""
        try:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot ban someone with a higher or equal role!")
                return

            confirm = await ctx.send(f"Are you sure you want to ban {member.mention}?")
            await confirm.add_reaction('✅')
            await confirm.add_reaction('❌')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            except TimeoutError:
                await ctx.send("Ban command timed out.")
                return

            if str(reaction.emoji) == '✅':
                await member.ban(reason=reason)
                await self.log_moderation_action(ctx, "Ban", member, reason)
                await ctx.send(f"{member.mention} has been banned.")
            else:
                await ctx.send("Ban command cancelled.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that member!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Moderation(bot)) 