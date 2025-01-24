import random

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
    ## Choose Command
    #################################
    @commands.command()
    async def choose(self, ctx, *choices: str):
        """Choose between multiple choices"""
        await ctx.send(random.choice(choices))

async def setup(bot):
    await bot.add_cog(Fun(bot)) 