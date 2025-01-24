import discord

from discord.ext import commands

class Casual(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    #################################
    ## About Command
    #################################
    @commands.command()
    async def about(self, ctx):
        """About Nessy"""
        embed = discord.Embed(
            title="✦ About Nessy ✦",
            description=(
                "Work in progress"
            ),
            color=0x2B2D31
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.set_footer(text=f"Buh")
        await ctx.send(embed=embed)
        
    #################################
    ## Ping Command
    #################################
    @commands.command()
    async def ping(self, ctx):
        """Check bot's latency"""
        await ctx.send(f"# Pong!\n**Latency**: {round(self.bot.latency * 1000)}ms")
        
    #################################
    ## User Info Command
    #################################
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Get info about a user"""
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info - {member.tag}", color=member.color)
        embed.add_field(name="ID", value=f"```{member.id}```")
        embed.add_field(name="Joined", value=f"```{member.joined_at.strftime('%Y-%m-%d')}```")
        embed.set_thumbnail(url=member.avatar.url)
        await ctx.send(embed=embed)
    
    #################################
    ## Avatar Command
    #################################
    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        """Get a user's avatar"""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=member.color)
        embed.set_image(url=member.avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def help(self, ctx, command_name=None):
        """Shows all available commands"""
        if command_name:
            command = self.bot.get_command(command_name)
            if not command:
                await ctx.send("That command doesn't exist!")
                return
                
            embed = discord.Embed(
                title=command.name.upper(),
                description=command.help or "No description available",
                color=0x2B2D31
            )
            embed.add_field(name="Usage", value=f"`{ctx.prefix}{command.name} {command.signature}`", inline=False)
            await ctx.send(embed=embed)
            return

        # Group commands by cog (category)
        commands_by_cog = {}
        for command in self.bot.commands:
            if command.cog:
                cog_name = command.cog_name
                if cog_name not in commands_by_cog:
                    commands_by_cog[cog_name] = []
                commands_by_cog[cog_name].append(command)

        # Sort categories
        category_order = {"Casual": 1, "Fun": 2, "Economy": 3, "Levels": 4, "Media": 5, "Moderation": 6, "Admin": 7}
        sorted_categories = sorted(commands_by_cog.keys(), key=lambda x: category_order.get(x, 99))

        pages = []
        current_page = []
        commands_per_page = 8
        
        for category in sorted_categories:
            commands_list = commands_by_cog[category]
            category_text = f"\n**{category.upper()}**\n"
            
            for cmd in commands_list:
                cmd_text = f"`{ctx.prefix}{cmd.name}` → {cmd.help or 'No description available'}\n"
                
                if len('\n'.join(current_page)) + len(category_text) + len(cmd_text) > 2000:
                    pages.append('\n'.join(current_page))
                    current_page = []
                
                if not current_page:
                    current_page.append(category_text)
                elif category_text not in current_page:
                    current_page.append(category_text)
                    
                current_page.append(cmd_text)
                
        if current_page:
            pages.append('\n'.join(current_page))

        if not pages:
            await ctx.send("No commands available!")
            return

        current_page = 0

        view = discord.ui.View()
        previous_button = discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary)
        next_button = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary)
        close_button = discord.ui.Button(label="Close", style=discord.ButtonStyle.danger)

        async def previous_callback(interaction):
            nonlocal current_page
            if interaction.user != ctx.author:
                await interaction.response.send_message("This help menu is not for you!", ephemeral=True)
                return
            current_page = (current_page - 1) % len(pages)
            embed.description = pages[current_page]
            embed.set_footer(text=f"Page {current_page + 1} of {len(pages)} • {sum(len(cmds) for cmds in commands_by_cog.values())} total commands")
            await interaction.response.edit_message(embed=embed)

        async def next_callback(interaction):
            nonlocal current_page
            if interaction.user != ctx.author:
                await interaction.response.send_message("This help menu is not for you!", ephemeral=True)
                return
            current_page = (current_page + 1) % len(pages)
            embed.description = pages[current_page]
            embed.set_footer(text=f"Page {current_page + 1} of {len(pages)} • {sum(len(cmds) for cmds in commands_by_cog.values())} total commands")
            await interaction.response.edit_message(embed=embed)

        async def close_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This help menu is not for you!", ephemeral=True)
                return
            await interaction.message.delete()

        previous_button.callback = previous_callback
        next_button.callback = next_callback
        close_button.callback = close_callback

        view.add_item(previous_button)
        view.add_item(close_button)
        view.add_item(next_button)

        embed = discord.Embed(
            title="Command List",
            description=pages[0],
            color=0x2B2D31
        )
        embed.set_footer(text=f"Page 1 of {len(pages)} • {sum(len(cmds) for cmds in commands_by_cog.values())} total commands")

        message = await ctx.send(embed=embed, view=view)

        # Timeout handler
        async def on_timeout():
            for item in view.children:
                item.disabled = True
            await message.edit(view=view)

        view.on_timeout = on_timeout

async def setup(bot):
    await bot.add_cog(Casual(bot)) 