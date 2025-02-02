import random
import asyncio
import discord
from discord.ext import commands

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @commands.command(aliases=['rr', 'russianroulette'])
    async def roulette(self, ctx, *players: discord.Member):
        """Play Russian Roulette with multiple players"""
        
        if ctx.channel.id in self.active_games:
            await ctx.send("There's already a game in progress in this channel!")
            return

        game_players = []
        if not players:
            game_players = [ctx.author, self.bot.user]
        else:
            game_players = [ctx.author] + list(players)

        game_players = list(dict.fromkeys(game_players))
        if len(game_players) < 2:
            await ctx.send("You need at least one opponent!")
            return

        chamber_count = random.randint(6, 10)
        min_live = 2
        min_blank = 2
        max_live = chamber_count - min_blank
        live_rounds = random.randint(min_live, max_live)
        
        chamber = ([1] * live_rounds) + ([0] * (chamber_count - live_rounds))
        random.shuffle(chamber)
        
        self.active_games[ctx.channel.id] = True
        current_chamber = 0
        current_player_idx = 0

        async def update_game_embed():
            embed = discord.Embed(title="", color=0x2B2D31)
            embed.add_field(name="Setup", value=f"{chamber_count} shells go into a shotgun...", inline=False)
            embed.add_field(name="Players", value="\n".join([p.mention for p in game_players]), inline=False)
            embed.add_field(name="Current Turn", value=f"{game_players[current_player_idx].mention}'s turn", inline=False)
            embed.set_footer(text=f"Live Rounds: {live_rounds} | Chamber Size: {chamber_count}")
            return embed

        async def target_callback(interaction: discord.Interaction, target: discord.Member):
            nonlocal current_chamber, current_player_idx
            
            if interaction.user != game_players[current_player_idx]:
                await interaction.response.send_message("It's not your turn!", ephemeral=True)
                return
                
            if target not in game_players:
                await interaction.response.send_message("That player is already dead!", ephemeral=True)
                return

            embed = discord.Embed(title="", color=0x2B2D31)
            embed.add_field(name="", value=f"{interaction.user.mention} takes aim at {target.mention}...", inline=False)
            await interaction.response.edit_message(embed=embed)
            await asyncio.sleep(2)

            if chamber[current_chamber] == 1:
                embed.description = "*[you hear a loud bang]*"
                await interaction.message.edit(embed=embed)
                await asyncio.sleep(2)
                
                if target != self.bot.user:
                    try:
                        await target.timeout(duration=30)
                    except:
                        pass
                
                game_players.remove(target)
                embed.add_field(name="Result", value=f"{target.mention} has died.", inline=False)
                embed.add_field(name="Status", value=f"{len(game_players)} players remain.", inline=False)
                
                if len(game_players) == 1:
                    embed.add_field(name="Game Over", value=f"{game_players[0].mention} wins!", inline=False)
                    await interaction.message.edit(embed=embed, view=None)
                    del self.active_games[ctx.channel.id]
                    return
            else:
                embed.description = "*[click]*"
                embed.add_field(name="Result", value=f"{target.mention} survived!", inline=False)
            
            current_chamber += 1
            if current_chamber >= len(chamber):
                embed.add_field(name="Game Over", value="All rounds have been fired! Game ends in a draw.", inline=False)
                await interaction.message.edit(embed=embed, view=None)
                del self.active_games[ctx.channel.id]
                return

            current_player_idx = (current_player_idx + 1) % len(game_players)
            new_embed = await update_game_embed()
            await interaction.message.edit(embed=new_embed)

        view = discord.ui.View(timeout=None)
        for player in game_players:
            button = discord.ui.Button(label=player.display_name, style=discord.ButtonStyle.primary)
            button.callback = lambda i, p=player: target_callback(i, p)
            view.add_item(button)

        initial_embed = await update_game_embed()
        await ctx.send(embed=initial_embed, view=view)

    @commands.command()
    async def tictactoe(self, ctx, opponent: discord.Member = None):
        """Play Tic Tac Toe with someone"""
        if opponent is None:
            opponent = self.bot.user
        elif opponent == ctx.author:
            await ctx.send("You can't play against yourself!")
            return

        board = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        current_player = ctx.author
        symbols = {"X": ctx.author, "O": opponent}
        
        def check_winner():
            wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
            for a, b, c in wins:
                if board[a] == board[b] == board[c] in ["❌", "⭕"]:
                    return True
            return False

        def make_board():
            return f"{board[0]}{board[1]}{board[2]}\n{board[3]}{board[4]}{board[5]}\n{board[6]}{board[7]}{board[8]}"

        msg = await ctx.send(f"**Tic Tac Toe**\n{current_player.mention}'s turn (❌)\n\n{make_board()}")

        while not check_winner():
            if current_player == self.bot.user:
                available = [i for i, x in enumerate(board) if x not in ["❌", "⭕"]]
                if not available:
                    break
                move = random.choice(available)
                board[move] = "⭕"
                current_player = ctx.author
            else:
                def check(m):
                    return m.author == current_player and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= 9

                try:
                    move_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                    move = int(move_msg.content) - 1
                    
                    if board[move] in ["❌", "⭕"]:
                        await ctx.send("That spot is taken! Try again.", delete_after=5)
                        continue
                        
                    symbol = "❌" if current_player == ctx.author else "⭕"
                    board[move] = symbol
                    current_player = opponent
                    
                except asyncio.TimeoutError:
                    await ctx.send("Game cancelled due to inactivity!")
                    return

            await msg.edit(content=f"**Tic Tac Toe**\n{current_player.mention}'s turn\n\n{make_board()}")
            await asyncio.sleep(1)

        if check_winner():
            winner = ctx.author if current_player == opponent else opponent
            await msg.edit(content=f"**Tic Tac Toe**\n{winner.mention} wins!\n\n{make_board()}")
        else:
            await msg.edit(content=f"**Tic Tac Toe**\nIt's a tie!\n\n{make_board()}")

    @commands.command()
    async def connect4(self, ctx, opponent: discord.Member = None):
        """Play Connect 4 with someone"""
        if opponent is None:
            opponent = self.bot.user
        elif opponent == ctx.author:
            await ctx.send("You can't play against yourself!")
            return

        board = [[' ' for _ in range(7)] for _ in range(6)]
        current_player = ctx.author
        symbols = {ctx.author: '🔴', opponent: '🟡'}
        numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣']

        def check_winner(board, symbol):
            for row in range(6):
                for col in range(4):
                    if all(board[row][col + i] == symbol for i in range(4)):
                        return True

            for row in range(3):
                for col in range(7):
                    if all(board[row + i][col] == symbol for i in range(4)):
                        return True

            for row in range(3):
                for col in range(4):
                    if all(board[row + i][col + i] == symbol for i in range(4)):
                        return True

            for row in range(3, 6):
                for col in range(4):
                    if all(board[row - i][col + i] == symbol for i in range(4)):
                        return True

            return False

        def make_move(column):
            for row in range(5, -1, -1):
                if board[row][column] == ' ':
                    return row
            return None

        def format_board():
            display = '\n'.join([''.join([(symbols[ctx.author] if cell == symbols[ctx.author] else 
                                         symbols[opponent] if cell == symbols[opponent] else '⚪️') 
                                        for cell in row]) for row in board])
            return f"{display}\n{''.join(numbers)}"

        msg = await ctx.send(f"**Connect 4**\n{current_player.mention}'s turn\n\n{format_board()}")

        while True:
            if current_player == self.bot.user:
                valid_columns = [col for col in range(7) if board[0][col] == ' ']
                if not valid_columns:
                    await msg.edit(content=f"**Connect 4**\nIt's a tie!\n\n{format_board()}")
                    return
                column = random.choice(valid_columns)
            else:
                try:
                    move_msg = await self.bot.wait_for(
                        'message',
                        timeout=30.0,
                        check=lambda m: (
                            m.author == current_player and 
                            m.channel == ctx.channel and 
                            m.content in ['1', '2', '3', '4', '5', '6', '7']
                        )
                    )
                    column = int(move_msg.content) - 1
                except asyncio.TimeoutError:
                    await ctx.send("Game cancelled due to inactivity!")
                    return

            row = make_move(column)
            if row is None:
                if current_player != self.bot.user:
                    await ctx.send("That column is full! Try again.", delete_after=5)
                continue

            board[row][column] = symbols[current_player]
            
            if check_winner(board, symbols[current_player]):
                await msg.edit(content=f"**Connect 4**\n{current_player.mention} wins!\n\n{format_board()}")
                return

            if all(board[0][col] != ' ' for col in range(7)):
                await msg.edit(content=f"**Connect 4**\nIt's a tie!\n\n{format_board()}")
                return

            current_player = opponent if current_player == ctx.author else ctx.author
            await msg.edit(content=f"**Connect 4**\n{current_player.mention}'s turn\n\n{format_board()}")

async def setup(bot):
    await bot.add_cog(Games(bot))
