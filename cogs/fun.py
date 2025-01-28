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

    #################################
    ## Cookies
    #################################
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if not (message.reference or message.mentions):
            return
        
        content = message.content.lower()
        thank_variants = ['thank', 'thanks', 'thx', 'ty', 'tysm', 'tyvm']
        
        if not any(variant in content for variant in thank_variants):
            return
        
        thanked_user = None
        if message.reference:
            try:
                reply_msg = await message.channel.fetch_message(message.reference.message_id)
                thanked_user = reply_msg.author
            except:
                return
        elif message.mentions:
            thanked_user = message.mentions[0]
        
        if not thanked_user or thanked_user.bot or thanked_user == message.author:
            return
        
        cookie_file = 'data/cookies.json'
        try:
            with open(cookie_file, 'r') as f:
                cookie_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cookie_data = {}
        
        if str(thanked_user.id) not in cookie_data:
            cookie_data[str(thanked_user.id)] = 0
        
        cookie_data[str(thanked_user.id)] += 1
        
        with open(cookie_file, 'w') as f:
            json.dump(cookie_data, f, indent=2)
        
        await message.channel.send(f"{thanked_user.display_name} gained a cookie!")

    @commands.command()
    async def cookies(self, ctx, member: discord.Member = None):
        """Check how many cookies someone has"""
        member = member or ctx.author
        
        try:
            with open('data/cookies.json', 'r') as f:
                cookie_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cookie_data = {}
        
        cookie_count = cookie_data.get(str(member.id), 0)
        cookie_text = "cookie" if cookie_count == 1 else "cookies"
        await ctx.send(f"{member.mention} has **{cookie_count}** {cookie_text}! 🍪")

    @commands.command()
    async def eat(self, ctx, amount: int = 1):
        """Eat some of your cookies"""
        try:
            with open('data/cookies.json', 'r') as f:
                cookie_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cookie_data = {}
        
        user_cookies = cookie_data.get(str(ctx.author.id), 0)
        
        if user_cookies < amount:
            cookie_text = "cookie" if user_cookies == 1 else "cookies"
            await ctx.send(f"You have **{user_cookies}** {cookie_text}")
            return
        
        cookie_data[str(ctx.author.id)] = user_cookies - amount
        
        with open('data/cookies.json', 'w') as f:
            json.dump(cookie_data, f, indent=2)
        
        remaining = user_cookies - amount
        remaining_text = "cookie" if remaining == 1 else "cookies"
        amount_text = "cookie" if amount == 1 else "cookies"
        
        if amount == 1:
            await ctx.send(f"You ate a cookie!\nYou have **{remaining}** {remaining_text} left")
        else:
            await ctx.send(f"You ate **{amount}** {amount_text}!\nYou have **{remaining}** {remaining_text} left")

    @commands.command()
    async def give(self, ctx, member: discord.Member, amount: int = 1):
        """Give someone some of your cookies"""
        if member.bot:
            await ctx.send("You can't give cookies to bots!")
            return
        
        if member == ctx.author:
            await ctx.send("You can't give cookies to yourself!")
            return
        
        try:
            with open('data/cookies.json', 'r') as f:
                cookie_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cookie_data = {}
        
        user_cookies = cookie_data.get(str(ctx.author.id), 0)
        
        if user_cookies < amount:
            await ctx.send(f"You have **{user_cookies}** cookies")
            return
        
        if str(member.id) not in cookie_data:
            cookie_data[str(member.id)] = 0
        
        cookie_data[str(ctx.author.id)] = user_cookies - amount
        cookie_data[str(member.id)] += amount
        
        with open('data/cookies.json', 'w') as f:
            json.dump(cookie_data, f, indent=2)
        
        if amount == 1:
            await ctx.send(f"You gave a cookie to {member.display_name}")
        else:
            await ctx.send(f"You gave **{amount}** cookies to {member.display_name}!")

async def setup(bot):
    await bot.add_cog(Fun(bot)) 