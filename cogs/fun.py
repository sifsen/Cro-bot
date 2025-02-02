import random
import json
import discord
from datetime import datetime, timedelta
from typing import Union
import urllib.parse
import aiohttp
import re

from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ###########################
    ## Game Commands
    ###########################
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
    async def rps(self, ctx, choice: str):
        """Play Rock Paper Scissors"""
        choice = choice.lower()
        if choice not in ['rock', 'paper', 'scissors']:
            await ctx.send("Please choose rock, paper, or scissors!")
            return
        if not choice:
            await ctx.send("Please choose rock, paper, or scissors!")
            return
        
        bot_choice = random.choice(['rock', 'paper', 'scissors'])
        
        wins = {
            'rock': 'scissors',
            'paper': 'rock', 
            'scissors': 'paper'
        }
        
        if choice == bot_choice:
            await ctx.send(f"I chose **{bot_choice}**! It's a tie!")
        elif wins[choice] == bot_choice:
            await ctx.send(f"I chose **{bot_choice}**! You win!")
        else:
            await ctx.send(f"I chose **{bot_choice}**! You lose!")

    @commands.command(aliases=['cf', 'flip'])
    async def coinflip(self, ctx):
        """Flip a coin"""
        result = random.choice(['Heads', 'Tails'])
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
    async def bonk(self, ctx, member: discord.Member = None):
        """Bonk someone"""
        if member is None:
            await ctx.send("You need to specify someone to bonk!")
            return
            
        if member == ctx.author:
            await ctx.send("You bonked yourself... why would you do that?")
            return
            
        bonks = [
            "bonk! Go to horny jail",
            "*bonks with newspaper*",
            "**BONK**",
            "*tactical bonk incoming*",
            "B O N K"
        ]
        await ctx.send(f"{member.mention} {random.choice(bonks)}")

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
    async def poke(self, ctx, member: discord.Member = None):
        """Poke someone"""
        if member is None:
            await ctx.send("You need to specify someone to poke!")
            return
            
        if member == ctx.author:
            await ctx.send("You poked yourself... why?")
            return
            
        pokes = [
            "*poke*",
            "**POKE**",
            "*aggressive poke*",
            "*gentle poke*",
            "*sneaky poke*",
            "*pokes repeatedly*"
        ]
        await ctx.send(f"{member.mention} {random.choice(pokes)}")

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
    ## Food & Drink Commands
    ###########################
    @commands.command()
    async def sandwich(self, ctx, member: discord.Member = None):
        """Make a sandwich for someone"""
        member = member or ctx.author
        
        breads = ["🍞", "🥖", "🥯", "🥪"]
        fillings = ["🧀", "🥓", "🥚", "🥬", "🍅", "🥕", "🥩", "🥑"]
        
        sandwich = (
            f"{random.choice(breads)} "
            f"{' '.join(random.sample(fillings, k=random.randint(2, 4)))} "
            f"{random.choice(breads)}"
        )
        
        if member == ctx.author:
            await ctx.send(f"You made yourself a sandwich: {sandwich}")
        else:
            await ctx.send(f"You made {member.mention} a sandwich: {sandwich}")

    @commands.command()
    async def soup(self, ctx, member: discord.Member = None):
        """Give someone some soup"""
        member = member or ctx.author
        
        soups = ["🥣", "🍜", "🍲"]
        temps = ["hot", "warm", "lukewarm", "cold"]
        types = [
            "tomato", "chicken noodle", "mushroom", 
            "mystery", "void", "cosmic", "potato",
            "debugger's", "binary", "quantum"
        ]
        
        soup = f"{random.choice(temps)} {random.choice(types)} soup {random.choice(soups)}"
        
        if member == ctx.author:
            await ctx.send(f"You made yourself some {soup}")
        else:
            await ctx.send(f"You gave {member.mention} some {soup}")

    @commands.command()
    async def sip(self, ctx):
        """Take a sip"""
        sips = [
            "*sips tea*",
            "*sips coffee aggressively*",
            "*slurps loudly*",
            "*sips in judgement*",
            "*takes a long sip*",
            "*sips awkwardly*"
        ]
        await ctx.send(f"{ctx.author.name} {random.choice(sips)}")

    @commands.command()
    async def nom(self, ctx, member: discord.Member = None, *, thing: str = None):
        """Nom something or someone"""
        noms = [
            "*nom nom nom*",
            "*aggressive nomming*",
            "*nibble*",
            "*monch*",
            "*cronch*",
            "*happy nomming sounds*"
        ]
        
        if member:
            if member == ctx.author:
                await ctx.send("You tried to nom yourself... how does that even work?")
                return
                
            if member.bot:
                await ctx.send("You can't nom bots! You might chip a tooth!")
                return
                
            await ctx.send(f"{member.mention} *{ctx.author.name} noms you* {random.choice(noms)}")
        elif thing:
            if '@everyone' in thing or '@here' in thing:
                await ctx.send("Nice try!")
                return
            thing = discord.utils.escape_mentions(thing)
            await ctx.send(f"*{ctx.author.name} noms {thing}* {random.choice(noms)}")
        else:
            await ctx.send(f"*{ctx.author.name} noms the air*")

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
    ## Expression Commands
    ###########################
    @commands.command()
    async def stare(self, ctx, member: discord.Member = None):
        """Stare at someone"""
        if member is None:
            await ctx.send("You need to specify someone to stare at!")
            return
            
        if member == ctx.author:
            await ctx.send("You stare at yourself in the mirror...")
            return
            
        stares = [
            "ಠ_ಠ",
            "ಠ_ರೃ",
            "ಠ▃ಠ",
            "ಠ╮╮ಠ",
            "(╬ಠ益ಠ)",
            "(｀_´)ゞ"
        ]
        await ctx.send(f"{member.mention} *{ctx.author.name} stares at you* {random.choice(stares)}")

    @commands.command()
    async def squint(self, ctx, member: discord.Member = None):
        """Squint suspiciously at someone"""
        if member is None:
            await ctx.send("You need to specify someone to squint at!")
            return
            
        if member == ctx.author:
            await ctx.send("You squint at yourself in confusion...")
            return
            
        squints = [
            "눈_눈",
            "-᷅_-᷄",
            "≖_≖",
            "( ⚆ _ ⚆ )",
            "(-_-;)"
        ]
        await ctx.send(f"{member.mention} *{ctx.author.name} squints suspiciously* {random.choice(squints)}")

    @commands.command()
    async def flail(self, ctx):
        """Flail around"""
        flails = [
            "ヽ(°〇°)ﾉ",
            "༼ノ◕ヮ◕༽ノ",
            "(ノ°□°)ノ",
            "┗(｀Дﾟ┗(｀ﾟДﾟ´)┛ﾟД´)┛",
            "ヽ(。_°)ノ",
            "ヽ(ﾟДﾟ)ﾉ"
        ]
        await ctx.send(f"*{ctx.author.name} flails around* {random.choice(flails)}")

    @commands.command()
    async def lurk(self, ctx):
        """Lurk in the shadows"""
        lurks = [
            "┬┴┬┴┤(･_├┬┴┬┴",
            "┬┴┬┴┤ ͜ʖ ͡°) ├┬┴┬┴",
            "┬┴┬┴┤･ω･)ﾉ├┬┴┬┴",
            "┬┴┬┴┤(･_├┬┴┬┴",
            "┬┴┬┴┤(･_├┬┴┬┴",
            "┬┴┬┴┤ ͡° ͜ʖ ͡°)├┬┴┬┴"
        ]
        await ctx.send(f"*{ctx.author.name} lurks menacingly* {random.choice(lurks)}")

    @commands.command()
    async def wiggle(self, ctx):
        """Wiggle wiggle wiggle"""
        wiggles = [
            "~(˘▾˘~)",
            "(~˘▾˘)~",
            "⊂((・▽・))⊃",
            "└[∵┌]└[ ∵ ]┘[┐∵]┘",
            "(〜￣△￣)〜",
            "♪～(´ε｀ )"
        ]
        await ctx.send(f"*{ctx.author.name} wiggles* {random.choice(wiggles)}")

    @commands.command()
    async def panic(self, ctx):
        """PANIC!!!"""
        panics = [
            "(ノ°Д°）ノ︵ ┻━┻",
            "┻━┻ ︵ヽ(`Д´)ﾉ︵ ┻━┻",
            "(╯°□°）╯︵ ┻━┻",
            "┻━┻ミ＼(≧ﾛ≦＼)",
            "(┛◉Д◉)┛彡┻━┻",
            "(┛ಸ_ಸ)┛彡┻━┻"
        ]
        await ctx.send(f"*{ctx.author.name} panics* {random.choice(panics)}")

    @commands.command()
    async def unflip(self, ctx):
        """Restore order to the tables"""
        unflips = [
            "┬─┬ノ( º _ ºノ)",
            "┬─┬ノ(ಠ_ಠノ)",
            "┬─┬ノ( º _ ºノ)",
            "┬──┬◡ﾉ(° -°ﾉ)",
            "┬━┬ ノ( ゜-゜ノ)",
            "┬──┬ ¯\\_(ツ)"
        ]
        await ctx.send(f"*{ctx.author.name} restores order* {random.choice(unflips)}")

    @commands.command()
    async def smug(self, ctx):
        """Be smug"""
        smugs = [
            "（￣～￣）",
            "(￣⊙￣)",
            "(-‿◦☀)",
            "(｀ω´)",
            "(￣ω￣)",
            "(｀∀´)Ψ"
        ]
        await ctx.send(f"*{ctx.author.name} looks smug* {random.choice(smugs)}")

    @commands.command()
    async def confused(self, ctx):
        """Express confusion"""
        confusions = [
            "(⊙_⊙)？",
            "⊙.☉",
            "(⊙.⊙)",
            "( ・◇・)？",
            "(●__●)",
            "ಠಿ_ಠ"
        ]
        await ctx.send(f"*{ctx.author.name} is confused* {random.choice(confusions)}")

    @commands.command()
    async def yawn(self, ctx):
        """*yawns contagiously*"""
        yawns = [
            "(๑ᵕ⌓ᵕ̤)",
            "（´≧Д≦）",
            "(∙ө∙)",
            "(˶ᵔ ᵕ ᵔ˶)",
            "( ⚈̥̥̥̥̥́⌢⚈̥̥̥̥̥̀)",
            "(◞ ‸ ◟)"
        ]
        await ctx.send(f"*{ctx.author.name} yawns* {random.choice(yawns)}")

    @commands.command()
    async def nap(self, ctx):
        """Take a quick nap"""
        naps = [
            "(-, - )…zzzZZZ",
            "(∪｡∪)｡｡｡zzz",
            "(-_-) zzz",
            "(ᴗ˳ᴗ)",
            "✾(〜 ☌ω☌)〜✾",
            "(⊃◜⌓◝⊂)"
        ]
        await ctx.send(f"*{ctx.author.name} takes a nap* {random.choice(naps)}")

    @commands.command()
    async def grump(self, ctx):
        """Be grumpy"""
        grumps = [
            "( ╯°□°)╯",
            "(｀Д´)",
            "( ͠° ͟ʖ ͡°)",
            "(⋋▂⋌)",
            "(≖︿≖ )",
            "( ง ᵒ̌皿ᵒ̌)ง⁼³₌₃"
        ]
        await ctx.send(f"*{ctx.author.name} is grumpy* {random.choice(grumps)}")

    @commands.command()
    async def sparkle(self, ctx, *, thing: str = None):
        """Make something sparkle"""
        if thing:
            if '@everyone' in thing or '@here' in thing:
                await ctx.send("Nice try!")
                return
            thing = discord.utils.escape_mentions(thing)
            await ctx.send(f"*{ctx.author.name} sprinkles sparkles on {thing}* ✧･ﾟ: *✧･ﾟ♡*(◕‿◕✿)*♡･ﾟ✧*:･ﾟ✧")
        else:
            await ctx.send(f"*{ctx.author.name} sparkles* ✧･ﾟ: *✧･ﾟ♡*(◕‿◕✿)*♡･ﾟ✧*:･ﾟ✧")

    ###########################
    ## Text Manipulation Commands
    ###########################
    @commands.command()
    async def emojify(self, ctx, *, text: str):
        """Convert text to regional indicators"""
        if '@everyone' in text or '@here' in text:
            await ctx.send("Nice try!")
            return
        text = discord.utils.escape_mentions(text)
        
        char_map = {
            ' ': '   ',
            '!': ':exclamation:',
            '?': ':question:',
            '#': ':hash:',
            '*': ':asterisk:'
        }
        
        output = ''
        for char in text.lower():
            if char.isalpha():
                output += f":regional_indicator_{char}: "
            elif char in char_map:
                output += char_map[char] + ' '
            else:
                output += char + ' '
                
        await ctx.send(output)

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
        """UwU-ify text (can reply to a message)"""
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
    async def choose(self, ctx, *choices: str):
        """Choose between multiple options"""
        clean_choices = [
            discord.utils.escape_mentions(discord.utils.escape_markdown(choice))
            for choice in choices
        ]
        
        if len(clean_choices) < 2:
            await ctx.send("I need at least 2 choices to pick from!")
            return
            
        await ctx.send(f"I choose: **{random.choice(clean_choices)}**")

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

    @commands.command(aliases=['google'])
    async def lmgtfy(self, ctx, *, search_terms: str):
        """Create a Let Me Google That For You link"""
        clean_terms = discord.utils.escape_mentions(search_terms)
        clean_terms = discord.utils.escape_markdown(clean_terms)
        encoded_terms = urllib.parse.quote_plus(clean_terms)
        
        if len(encoded_terms) > 500:
            await ctx.send("Search query too long!")
            return
            
        await ctx.send(f"<https://letmegooglethat.com/?q={encoded_terms}>")

    ###########################
    ## Fun Rating Commands
    ###########################
    @commands.command()
    async def rate(self, ctx, *, thing: str):
        """Rate anything out of 10"""
        if '@everyone' in thing or '@here' in thing:
            await ctx.send("Nice try!")
            return
        thing = discord.utils.escape_mentions(thing)
        
        seed = sum(ord(char) for char in thing.lower())
        random.seed(seed)
        
        rating = random.randint(0, 10)
        emoji = "💫" if rating >= 8 else "⭐" if rating >= 5 else "💢"
        
        await ctx.send(f"I rate {thing} a **{rating}/10** {emoji}")
        
        random.seed()

    @commands.command()
    async def judge(self, ctx, *, thing: str):
        """Get judged"""
        if '@everyone' in thing or '@here' in thing:
            await ctx.send("Nice try!")
            return
        thing = discord.utils.escape_mentions(thing)
        
        judgements = [
            "seems kinda sus",
            "pretty based ngl",
            "cringe",
            "absolutely cursed",
            "needs to touch grass",
            "certified classic",
            "wouldn't recommend",
            "literally me",
            "peak content",
            "mid"
        ]
        
        seed = sum(ord(char) for char in thing.lower())
        random.seed(seed)
        judgement = random.choice(judgements)
        random.seed()
        
        await ctx.send(f"**{thing}** {judgement}")

    @commands.command(aliases=['vibe'])
    async def vibecheck(self, ctx, member: discord.Member = None):
        """Perform a totally scientific vibe check"""
        member = member or ctx.author
        
        data = {
            "username_length": len(member.name),
            "avatar_hash": hash(str(member.display_avatar.url)),
            "created_at": int(member.created_at.timestamp()),
            "discriminator": int(member.discriminator) if member.discriminator != '0' else 0,
            "roles": len(member.roles),
            "color": member.color.value if member.color != discord.Color.default() else 0,
            "status": hash(str(member.status)),
            "activities": len(member.activities) if member.activities else 0
        }
        
        day_seed = int(datetime.now().strftime("%Y%m%d"))
        random.seed(sum(data.values()) + day_seed)
        
        vibes = {
            "chaos": random.randint(0, 100),
            "swag": random.randint(0, 100),
            "gaming": random.randint(0, 100),
            "touch_grass": random.randint(0, 100),
            "sleep": random.randint(0, 100),
            "meme": random.randint(0, 100),
            "productivity": random.randint(0, 100),
            "creativity": random.randint(0, 100)
        }
        
        def get_meter(value):
            blocks = ["░", "▒", "▓", "█"]
            meter = ""
            segments = 10
            for i in range(segments):
                threshold = (i + 1) * (100 / segments)
                if value >= threshold:
                    block_index = min(3, int((value - threshold) / (100 / segments / 1.5)))
                    meter += blocks[block_index]
                else:
                    meter += blocks[0]
            return meter
        
        avg_vibe = sum(vibes.values()) / len(vibes)
        if avg_vibe >= 90:
            grade = "S+"
            conclusion = "Vibes have transcended reality ✨"
        elif avg_vibe >= 80:
            grade = "S"
            conclusion = "Elite vibes detected"
        elif avg_vibe >= 70:
            grade = "A"
            conclusion = "Certified fresh vibes"
        elif avg_vibe >= 60:
            grade = "B"
            conclusion = "Vibing respectfully"
        elif avg_vibe >= 50:
            grade = "C"
            conclusion = "Vibes are a bit sus"
        elif avg_vibe >= 40:
            grade = "D"
            conclusion = "Vibes need maintenance"
        else:
            grade = "F"
            conclusion = "Vibe check failed successfully"
        
        embed = discord.Embed(
            title=f"Vibe Check: {member.display_name}",
            description=f"Overall Grade: **{grade}** ({avg_vibe:.1f}%)",
            color=member.color if member.color != discord.Color.default() else 0x2B2D31
        )
        
        for name, value in vibes.items():
            embed.add_field(
                name=name.replace('_', ' ').title(),
                value=f"`{get_meter(value)}` {value}%",
                inline=False
            )
        
        embed.set_footer(text=conclusion)
        embed.set_thumbnail(url=member.display_avatar.url)
        
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

        await ctx.send(f"{member.display_name} was {action}")

    @commands.command(name="8ball", aliases=['8'])
    async def _8ball(self, ctx, *, question: str):
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
        
        if not question.endswith('?'):
            await ctx.send("That doesn't look like a question!")
            return
            
        await ctx.send(f"{random.choice(responses)}")

    @commands.command()
    async def f(self, ctx, *, reason: str = None):
        """Pay respects"""
        if reason:
            if '@everyone' in reason or '@here' in reason:
                await ctx.send("Nice try!")
                return
            reason = discord.utils.escape_mentions(reason)
            
        hearts = ['❤️', '💛', '💚', '💙', '💜', '🤎', '🖤', '🤍']
        reason_text = f" for {reason}" if reason else ""
        await ctx.send(f"**{ctx.author.name}** has paid their respects{reason_text} {random.choice(hearts)}")

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
    async def emote(self, ctx, emote: str):
        """Get info about an emote"""
        try:
            emoji = await commands.EmojiConverter().convert(ctx, emote)
            
            embed = discord.Embed(title="Emoji Info", color=0x2B2D31)
            embed.add_field(name="Name", value=f"`{emoji.name}`", inline=True)
            embed.add_field(name="ID", value=f"`{emoji.id}`", inline=True)
            embed.add_field(name="Server", value=discord.utils.escape_markdown(emoji.guild.name), inline=True)
            embed.add_field(name="Created", value=discord.utils.format_dt(emoji.created_at, 'R'), inline=True)
            embed.add_field(name="URL", value=f"[Link]({emoji.url})", inline=True)
            embed.set_thumbnail(url=emoji.url)
            
            await ctx.send(embed=embed)
            
        except commands.BadArgument:
            if len(emote) == 1 or emote.startswith('\\U'):
                await ctx.send("That's a unicode emoji! I can only get info about custom server emotes.")
            else:
                await ctx.send("That's not a valid emoji!")

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

    @commands.command()
    async def conspiracy(self, ctx):
        """Generate a random conspiracy theory"""
        
        subjects = [
            "Discord light theme users",
            "People who don't use dark mode",
            "Users who read the TOS",
            "People who touch grass",
            "Discord developers",
            "Bot developers",
            "People who sleep properly",
            "Offline status users",
            "People who don't use emojis",
            "Users with perfect ping",
            "People who never misclick"
        ]
        
        actions = [
            "are secretly plotting to",
            "have been working for years to",
            "don't want you to know they",
            "have formed an alliance to",
            "have discovered how to",
            "are hiding the truth about how they",
            "have been pretending to",
            "are using bots to",
            "have created an algorithm to",
            "have been spending millions to"
        ]
        
        objects = [
            "replace all emojis with comic sans",
            "make everyone use light theme",
            "delete all the memes",
            "force everyone to touch grass",
            "turn off everyone's RGB lighting",
            "make ping permanently 999ms",
            "remove all keyboard shortcuts",
            "implement mandatory grass touching",
            "make sleep schedules actually healthy",
            "fix all the bugs (suspicious)",
            "make everyone read the terms of service",
            "eliminate copy-paste functionality",
            "replace all servers with book clubs",
            "make everyone go outside",
            "enforce proper posture at desks"
        ]
        
        evidence = [
            "I saw it in a meme once",
            "Source: trust me bro",
            "My cat told me",
            "It was revealed to me in a dream",
            "A random Discord status told me",
            "The loading screen tips confirmed it",
            "My RGB lights flickered in morse code",
            "My high ping is proof",
            "The bugs are actually features",
            "The discord loading messages speak the truth",
            "A bot whispered it to me",
            "The server hamsters leaked this info",
            "I made it the fuck up!"
        ]
        
        theory = (
            f"{random.choice(subjects)} {random.choice(actions)} "
            f"{random.choice(objects)}!\n\n"
            f"*Evidence: {random.choice(evidence)}*"
        )
        
        embed = discord.Embed(
            title="CONSPIRACY ALERT",
            description=theory,
            color=0x2B2D31
        )
        embed.set_footer(text="Wake up sheeple!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot)) 