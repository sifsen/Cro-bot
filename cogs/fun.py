import random
import json
import discord

from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #################################
    ## Roll Command
    #################################   
    @commands.command()
    async def roll(self, ctx, dice: str):
        """Roll a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
            result = [random.randint(1, limit) for r in range(rolls)]
            await ctx.send(f"Results: {', '.join(map(str, result))}")
        except Exception:
            await ctx.send("Format has to be in NdN!")
    
    #################################
    ## Coinflip Command
    #################################
    @commands.command(aliases=['cf', 'flip'])
    async def coinflip(self, ctx):
        """Flip a coin"""
        result = random.choice(['Heads', 'Tails'])
        await ctx.send(f"You got **{result}**!")

    #################################
    ## Echo Command
    #################################
    @commands.command()
    async def echo(self, ctx, *, message: str):
        """Echo a message"""
        await ctx.message.delete()
        await ctx.send(message)

    #################################
    ## Bean Command
    #################################
    @commands.command(aliases=['punish', 'troll', 'bange', 'jail'])
    @commands.has_permissions(ban_members=True)
    async def bean(self, ctx, member: commands.MemberConverter = None):
        """Bean a user (totally real ban command)"""
        if not member:
            return

        if member.id == ctx.author.id:
            await ctx.send("Nice try.")
            return

        with open('data/strings.json', 'r') as f:
            strings = json.load(f)
            action = random.choice(strings['user_was_x'])

        await ctx.send(f"{member.display_name} was {action}")

    #################################
    ## Choose Command
    #################################
    @commands.command()
    async def choose(self, ctx, *choices: str):
        """Choose between multiple choices"""
        await ctx.send(random.choice(choices))

    #################################
    ## Snipe Command
    #################################
    @commands.command()
    async def snipe(self, ctx):
        """Shows the last deleted message in the channel"""
        handlers = self.bot.get_cog('EventHandlers')
        if not handlers:
            return
            
        guild_deletes = handlers.deleted_messages.get(ctx.guild.id, {})
        deleted_msg = guild_deletes.get(ctx.channel.id)
        
        if not deleted_msg:
            await ctx.send("There's nothing to snipe!")
            return
            
        embed = discord.Embed(
            description=deleted_msg['content'] or "*No text content*",
            color=0x2B2D31,
            timestamp=deleted_msg['timestamp']
        )
        
        embed.set_author(
            name=deleted_msg['author'].name,
            icon_url=deleted_msg['author'].display_avatar.url
        )
        
        if deleted_msg['reference']:
            embed.description += f"\n\nReplying to [this message]({ctx.channel.jump_url}/{deleted_msg['reference']})"
            
        if deleted_msg['attachments']:
            embed.set_image(url=deleted_msg['attachments'][0])
            
        embed.set_footer(text=f"Sniped by {ctx.author.name}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot)) 