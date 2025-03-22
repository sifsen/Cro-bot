import random
import json
import discord
from datetime import datetime, timedelta
from typing import Union
import urllib.parse
import aiohttp
import re

from discord.ext import commands
from utils.helpers.formatting import EmbedBuilder, TextFormatter
from utils.permissions.handler import PermissionHandler

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.eight_ball_responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
            "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]

    @commands.command()
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice in NdN format"""
        try:
            match = re.match(r"(\d+)d(\d+)", dice.lower())
            if not match:
                await ctx.send("Format must be in NdN! (e.g., 2d6)")
                return

            number, sides = map(int, match.groups())
            
            if number > 100:
                await ctx.send("Cannot roll more than 100 dice!")
                return
                
            if sides > 100:
                await ctx.send("Cannot roll dice with more than 100 sides!")
                return

            rolls = [random.randint(1, sides) for _ in range(number)]
            total = sum(rolls)
            
            embed = EmbedBuilder(
                title="🎲 Dice Roll",
                color=discord.Color.blue()
            ).add_field(
                name="Roll",
                value=f"`{dice}`",
                inline=True
            ).add_field(
                name="Results",
                value=f"`{', '.join(map(str, rolls))}`",
                inline=True
            ).add_field(
                name="Total",
                value=f"**{total}**",
                inline=True
            )
            
            await ctx.send(embed=embed.build())
            
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(aliases=['cf', 'flip'])
    async def coinflip(self, ctx):
        """Flip a coin"""
        result = random.choice(['heads', 'tails'])
        await ctx.send(f"You got **{result}**!")

    ###########################
    ## Social Commands
    ###########################
    @commands.command()
    async def hug(self, ctx, member: discord.Member = None, intensity: int = 1):
        """Give someone a hug!
        
        Intensity levels 1-10"""
        if member is None:
            await ctx.send("You need to specify someone to hug!")
            return
        
        if intensity <= 0:
            msg = f"(っ˘̩╭╮˘̩)っ {member.mention}"
        elif intensity <= 3:
            msg = f"(っ´▽｀)っ {member.mention}"
        elif intensity <= 6:
            msg = f"╰(*´︶`*)╯ {member.mention}"
        elif intensity <= 9:
            msg = f"(つ≧▽≦)つ {member.mention}"
        else:
            msg = f"(づ￣ ³￣)づ {member.mention} ⊂(´・ω・｀⊂)"
        
        await ctx.send(msg)

    @commands.command()
    async def pat(self, ctx, member: discord.Member = None):
        """Pat someone on the head"""
        if member is None:
            await ctx.send("You need to specify someone to pat!")
            return
            
        if member == ctx.author:
            await ctx.send("You pat yourself... weird flex but ok")
            return
            
        pats = ['(´･ω･`)ノ', '(ｏ・_・)ノ"', '(づ｡◕‿‿◕｡)づ', '(っ´ω`)ﾉ']
        await ctx.send(f"{random.choice(pats)} *pats {member.mention}*")

    @commands.command()
    async def boop(self, ctx, member: discord.Member = None):
        """Boop someone's nose"""
        if member is None:
            await ctx.send("You need to specify someone to boop!")
            return
            
        if member == ctx.author:
            await ctx.send("You booped your own nose... weird flex but ok")
            return
            
        if member.bot:
            await ctx.send("You tried to boop a bot... *boop processing error*")
            return
            
        boops = [
            "*boop!*", 
            "**BOOP!**", 
            "*sneaky boop*", 
            "*tactical boop incoming!*",
            "*boops aggressively*",
            "*gentle boop*"
        ]
        
        await ctx.send(f"{member.mention} {random.choice(boops)}")

    @commands.command()
    async def slap(self, ctx, member: discord.Member = None):
        """Slap someone with a random object"""
        if member is None:
            await ctx.send("You need to specify someone to slap!")
            return
            
        if member == ctx.author:
            await ctx.send("You slapped yourself. Why would you do that?")
            return
            
        if member.bot:
            await ctx.send("You can't slap a bot! Your hand would break!")
            return
            
        items = [
            "a wet noodle",
            "a large trout",
            "a physics textbook",
            "a rubber chicken",
            "a slice of pizza",
            "the ban hammer",
            "a keyboard",
            "a cactus",
            "the communist manifesto",
            "a bug report"
        ]
        await ctx.send(f"{ctx.author.name} slaps {member.mention} with {random.choice(items)}")

    @commands.command()
    async def throw(self, ctx, member: discord.Member = None):
        """Throw something at someone"""
        if member is None:
            await ctx.send("You need to specify someone to throw at!")
            return
            
        if member == ctx.author:
            await ctx.send("You threw something at yourself... why?")
            return
            
        if member.bot:
            await ctx.send("You can't throw things at bots! They'll throw them back harder!")
            return
            
        items = [
            "a potato 🥔",
            "an error message",
            "a stack trace",
            "some spaghetti code",
            "a rubber duck 🦆",
            "a merge conflict",
            "a bug fix",
            "the documentation",
            "a feature request",
            "undefined behavior"
        ]
        await ctx.send(f"{ctx.author.name} throws {random.choice(items)} at {member.mention}")

    ###########################
    ## Cookie System Commands
    ###########################
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if not (message.reference or message.mentions):
            return
        
        content = message.content.lower()
        thank_variants = ['thank', 'thanks', 'thx', 'ty', 'tysm', 'tyvm', 'thank you', 'thankyou', 'thnks']
        
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
        
        if str(thanked_user.id) in cookie_data:
            if isinstance(cookie_data[str(thanked_user.id)], int):
                cookie_data[str(thanked_user.id)] = [cookie_data[str(thanked_user.id)], 0]
        else:
            cookie_data[str(thanked_user.id)] = [0, 0]
        
        cookie_data[str(thanked_user.id)][0] += 1
        
        with open(cookie_file, 'w') as f:
            json.dump(cookie_data, f, indent=2)
        
        await message.channel.send(f"{thanked_user.display_name} gained a cookie!")

    @commands.command(aliases=['cookie'])
    async def cookies(self, ctx, member: discord.Member = None):
        """Check how many cookies someone has"""
        member = member or ctx.author
        
        try:
            with open('data/cookies.json', 'r') as f:
                cookie_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cookie_data = {}
        
        if str(member.id) in cookie_data:
            if isinstance(cookie_data[str(member.id)], int):
                cookie_data[str(member.id)] = [cookie_data[str(member.id)], 0]
                with open('data/cookies.json', 'w') as f:
                    json.dump(cookie_data, f, indent=2)
        
        user_data = cookie_data.get(str(member.id), [0, 0])
        cookie_count, eaten_count = user_data
        
        cookie_text = "cookie" if cookie_count == 1 else "cookies"
        eaten_text = "cookie" if eaten_count == 1 else "cookies"
        
        await ctx.send(f"{member.mention} has **{cookie_count}** {cookie_text}! 🍪\nThey have eaten **{eaten_count}** {eaten_text} in total.")

    @commands.command(aliases=['chomp'])
    async def eat(self, ctx, amount: int = 1):
        """Eat some of your cookies"""
        try:
            with open('data/cookies.json', 'r') as f:
                cookie_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cookie_data = {}
        
        user_data = cookie_data.get(str(ctx.author.id), [0, 0])
        user_cookies, eaten_cookies = user_data
        
        if user_cookies < amount:
            cookie_text = "cookie" if user_cookies == 1 else "cookies"
            await ctx.send(f"You have **{user_cookies}** {cookie_text}")
            return
        
        cookie_data[str(ctx.author.id)] = [user_cookies - amount, eaten_cookies + amount]
        
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
        
        if str(ctx.author.id) in cookie_data:
            if isinstance(cookie_data[str(ctx.author.id)], int):
                cookie_data[str(ctx.author.id)] = [cookie_data[str(ctx.author.id)], 0]
        else:
            cookie_data[str(ctx.author.id)] = [0, 0]
        
        if str(member.id) in cookie_data:
            if isinstance(cookie_data[str(member.id)], int):
                cookie_data[str(member.id)] = [cookie_data[str(member.id)], 0]
        else:
            cookie_data[str(member.id)] = [0, 0]
        
        user_cookies = cookie_data[str(ctx.author.id)][0]
        
        if user_cookies < amount:
            cookie_text = "cookie" if user_cookies == 1 else "cookies"
            await ctx.send(f"You have **{user_cookies}** {cookie_text}")
            return
        
        cookie_data[str(ctx.author.id)][0] = user_cookies - amount
        cookie_data[str(member.id)][0] += amount
        
        with open('data/cookies.json', 'w') as f:
            json.dump(cookie_data, f, indent=2)
        
        if amount == 1:
            await ctx.send(f"You gave a cookie to {member.display_name}")
        else:
            await ctx.send(f"You gave **{amount}** cookies to {member.display_name}!")

    ###########################
    ## Text Manipulation Commands
    ###########################
    @commands.command()
    async def reverse(self, ctx, *, text: str):
        """Reverse any text"""
        if '@everyone' in text or '@here' in text:
            await ctx.send("Nice try!")
            return
        text = discord.utils.escape_mentions(text)
        await ctx.send(text[::-1])

    @commands.command()
    async def mock(self, ctx, *, text: str):
        """MoCk TeXt LiKe ThIs"""
        if '@everyone' in text or '@here' in text:
            await ctx.send("Nice try!")
            return
        text = discord.utils.escape_mentions(text)
        
        output = ''
        last_upper = False
        
        for char in text:
            if char.isalpha():
                if not last_upper:
                    output += char.upper()
                    last_upper = True
                else:
                    output += char.lower()
                    last_upper = False
            else:
                output += char
                
        await ctx.send(output)

    @commands.command()
    async def uwu(self, ctx, *, text: str = None):
        """UwU-ify text"""
        if text is None:
            if not ctx.message.reference:
                await ctx.send("Please provide text or reply to a message!")
                return
            try:
                ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                text = ref_msg.content
            except:
                await ctx.send("Couldn't fetch the replied message!")
                return
        
        if '@everyone' in text or '@here' in text:
            await ctx.send("Nice try!")
            return
            
        text = discord.utils.escape_mentions(text)
        text = discord.utils.escape_markdown(text)
        
        uwu_map = {
            'r': 'w',
            'l': 'w',
            'R': 'W',
            'L': 'W',
            'th': 'd',
            'Th': 'D',
            'TH': 'D',
            'this': 'dis',
            'This': 'Dis',
            'THIS': 'DIS',
            'that': 'dat',
            'That': 'Dat',
            'THAT': 'DAT',
            'the': 'da',
            'The': 'Da',
            'THE': 'DA',
            'yes': 'yus',
            'Yes': 'Yus',
            'YES': 'YUS',
            'you': 'u',
            'You': 'U',
            'YOU': 'U',
            'what': 'wat',
            'What': 'Wat',
            'WHAT': 'WAT'
        }
        
        words = text.split()
        for i, word in enumerate(words):
            for old, new in uwu_map.items():
                if len(old) > 1:
                    words[i] = re.sub(f'\\b{old}\\b', new, words[i])
        
        text = ' '.join(words)
        for old, new in uwu_map.items():
            if len(old) == 1:
                text = text.replace(old, new)
        
        words = text.split()
        for i, word in enumerate(words):
            if len(word) > 2 and random.random() < 0.2:
                words[i] = f"{word[0]}-{word}"
        text = ' '.join(words)
        
        quirks = [
            lambda t: t.replace('!', '!!1'),
            lambda t: t.replace('.', '...'),
            lambda t: t + ' >w<',
            lambda t: t + ' uwu',
            lambda t: t + ' owo',
            lambda t: t + ' :3',
            lambda t: t + ' nyaa~',
            lambda t: t + ' >_<',
            lambda t: t + ' ^-^',
            lambda t: t
        ]
        
        for _ in range(random.randint(1, 2)):
            text = random.choice(quirks)(text)
        
        kaomoji = [
            '(◕ᴗ◕✿)',
            '(｡♡‿♡｡)',
            '(◠‿◠✿)',
            '(≧◡≦)',
            '(●´ω｀●)',
            '(◕‿◕✿)',
            '(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧',
            '(｡◕‿‿◕｡)'
        ]
        
        if random.random() < 0.3:
            text = f"{random.choice(kaomoji)} {text}"
        
        await ctx.send(text)

    ###########################
    ## Utility Commands
    ###########################
    @commands.command()
    @PermissionHandler.has_permissions(Administrator=True)
    async def echo(self, ctx, *, message: str):
        """Echo a message"""
        if '@everyone' in message or '@here' in message:
            await ctx.send("Nice try.")
            return
            
        message = discord.utils.escape_mentions(message)
        message = discord.utils.escape_markdown(message)
        
        await ctx.message.delete()
        await ctx.send(message)

    @commands.command()
    async def choose(self, ctx, *, choices: str):
        """Choose between multiple options"""
        options = [opt.strip() for opt in choices.split(',') if opt.strip()]
        
        if len(options) < 2:
            await ctx.send("Please provide at least 2 options separated by commas!")
            return

        choice = random.choice(options)
        
        await ctx.send(f"**{choice}**")

    @commands.command()
    async def snipe(self, ctx):
        """Shows the last deleted message in the channel"""
        message_events = self.bot.get_cog('MessageEvents')
        if not message_events:
            return
            
        guild_deletes = message_events.deleted_messages.get(ctx.guild.id, {})
        deleted_msg = guild_deletes.get(ctx.channel.id)
        
        if not deleted_msg:
            await ctx.send("There's nothing to snipe!")
            return
            
        embed = discord.Embed(
            description=deleted_msg['content'] or "*No text content*",
            color=0x2B2D31
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

    ###########################
    ## Miscellaneous Commands
    ###########################
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

        await ctx.send(f"**{member.display_name}** was {action}")

    @commands.command(name='8ball', aliases=['8'])
    async def _8ball(self, ctx):
        """Ask the magic 8ball a question"""

        responses = [
            "It is certain", "Without a doubt", "You may rely on it",
            "Yes definitely", "It is decidedly so", "As I see it, yes",
            "Most likely", "Yes", "Signs point to yes", 
            "Reply hazy try again", "Ask again later",
            "Better not tell you now", "Cannot predict now",
            "Concentrate and ask again", "Don't count on it",
            "My reply is no", "My sources say no",
            "Outlook not so good", "Very doubtful"
        ]
            
        await ctx.send(f"{random.choice(responses)}")

    @commands.command(aliases=['ud', 'define'])
    async def urban(self, ctx, *, word: str):
        """Search Urban Dictionary for a word"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.urbandictionary.com/v0/define?term={urllib.parse.quote(word)}"
                ) as resp:
                    data = await resp.json()
                    
            if not data['list']:
                await ctx.send("No results found!")
                return
                
            entry = data['list'][0]
            
            embed = discord.Embed(
                title=f"{entry['word']}",
                url=entry['permalink'],
                color=0x2B2D31
            )
            
            definition = entry['definition'][:2048] + '...' if len(entry['definition']) > 2048 else entry['definition']
            embed.add_field(name="Definition", value=definition, inline=False)
            
            if entry['example']:
                example = entry['example'][:1024] + '...' if len(entry['example']) > 1024 else entry['example']
                embed.add_field(name="Example", value=example, inline=False)
                
            embed.set_footer(
                text=f"👍 {entry['thumbs_up']} | 👎 {entry['thumbs_down']} | By {entry['author']}"
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send("An error occurred while fetching the definition.")

    @commands.command()
    async def patch(self, ctx, member: discord.Member = None):
        """Generate patch notes for a user"""
        member = member or ctx.author
        
        data = {
            "username_length": len(member.name),
            "avatar_hash": hash(str(member.display_avatar.url)),
            "created_at": int(member.created_at.timestamp()),
            "roles": len(member.roles),
            "status": hash(str(member.status)),
            "activities": len(member.activities) if member.activities else 0
        }
        
        day_seed = int(datetime.now().strftime("%Y%m%d"))
        random.seed(sum(data.values()) + day_seed)
        
        changes = [
            "- Fixed bug where user wasn't touching grass",
            "- Improved sleep schedule efficiency by 3%",
            "- Added new coffee dependency",
            "- Removed Herobrine",
            "- Patched exploit that allowed multiple dinners",
            "- Updated localization files",
            "- Nerfed gaming skills (was too OP)",
            "- Fixed typo in user.brain",
            "- Optimized meme processing",
            "- Deprecated old excuses.dll",
            "- Added support for more snacks",
            "- Fixed infinite loop in sleep.exe",
            "- Updated terms of procrastination",
            "- Patched memory leak in caffeine.sys",
            "- Added new bugs to fix later",
            "- Improved random number generation by making it more random",
            "- Fixed bug where touching grass caused crash",
            "- Added more RGB (improves performance)",
            "- Removed unnecessary sleep calls",
            "- Fixed exploit where work was being finished too quickly"
        ]
        
        selected_changes = random.sample(changes, k=random.randint(4, 6))
        
        embed = discord.Embed(
            title=f"Patch Notes v{day_seed}.{random.randint(1, 9)}.{random.randint(0, 9)}",
            description=f"# {member.display_name}.exe\nLatest changes:",
            color=member.color if member.color != discord.Color.default() else 0x2B2D31
        )
        
        embed.description += "\n\n" + "\n".join(selected_changes)
        embed.set_footer(text="Known issues: Everything")
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
