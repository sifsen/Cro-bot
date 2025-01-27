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

async def setup(bot):
    await bot.add_cog(Games(bot))
