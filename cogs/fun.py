import random
import json

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

    @commands.command()
    async def echo(self, ctx, *, message: str):
        """Echo a message"""
        await ctx.message.delete()
        await ctx.send(message)

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

async def setup(bot):
    await bot.add_cog(Fun(bot)) 