import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, command_name=None):
        """Shows command help and documentation"""
        if command_name:
            command = self.bot.get_command(command_name)
            if not command:
                await ctx.send("That command doesn't exist!")
                return
                
            admin_commands = {
                'automod': {
                    'description': 'Automoderation system',
                    'requires': 'Administrator',
                    'usage': [
                        ('automod', 'Show current configuration'),
                        ('automod toggle', 'Enable/disable the automod system'),
                        ('automod add <name> <action> <pattern>', 'Add a new pattern\n- Actions: delete, timeout\n- Pattern: regex pattern\n- Optional: duration=1w/1d/1h/1m/1s'),
                        ('automod remove <name>', 'Remove a pattern'),
                        ('automod exclude #channel/@role', 'Exclude channel/role from automod'),
                        ('automod include #channel/@role', 'Re-include channel/role in automod')
                    ],
                    'examples': [
                        '`automod add nword delete (?i)n+[i1]+[g6]+[g6]+[e3]+(r+|a+)`',
                        '`automod add spam timeout (?i)(discord\.gg|discordapp\.com\/invite) duration=1d`',
                        '`automod exclude #bot-commands`',
                        '`automod exclude @Moderator`'
                    ]
                }
            }

            if command.name in admin_commands:
                if not ctx.author.guild_permissions.administrator:
                    await ctx.send("You don't have permission to view admin command documentation.")
                    return
                    
                cmd_info = admin_commands[command.name]
                embed = discord.Embed(
                    title=f"{command.name.upper()} Command guide",
                    description=cmd_info['description'],
                    color=0x2B2D31
                )
                
                embed.add_field(
                    name="Permission required",
                    value=cmd_info['requires'],
                    inline=False
                )
                
                usage_text = ""
                for cmd, desc in cmd_info['usage']:
                    usage_text += f"`{ctx.prefix}{cmd}`\n{desc}\n\n"
                embed.add_field(
                    name="Usage",
                    value=usage_text,
                    inline=False
                )
                
                if 'examples' in cmd_info:
                    embed.add_field(
                        name="💡 Examples",
                        value="\n".join(cmd_info['examples']),
                        inline=False
                    )
                    
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title=command.name.upper(),
                description=command.help or "No description available",
                color=0x2B2D31
            )
            usage = f"`{ctx.prefix}{command.name} {command.signature}`"
            embed.add_field(name="Usage", value=usage, inline=False)
            
            if command.aliases:
                aliases = ", ".join(f"`{alias}`" for alias in command.aliases)
                embed.add_field(name="Aliases", value=aliases, inline=False)
                
            await ctx.send(embed=embed)
            return

        commands_by_cog = {}
        for command in self.bot.commands:
            if command.cog:
                cog_name = command.cog_name
                if cog_name not in commands_by_cog:
                    commands_by_cog[cog_name] = []
                commands_by_cog[cog_name].append(command)

        category_order = {
            "Casual": 1,
            "Fun": 2, 
            "Games": 3,
            "AutoMod": 4,
            "Moderation": 5,
            "Admin": 6
        }
        
        sorted_categories = sorted(
            commands_by_cog.keys(),
            key=lambda x: category_order.get(x, 99)
        )

        pages = []
        current_categories = []
        current_page = []
        categories_per_page = 2
        
        for category in sorted_categories:
            commands_list = commands_by_cog[category]
            category_text = f"\n**{category.upper()}**\n"
            category_commands = []
            
            for cmd in commands_list:
                cmd_text = f"`{ctx.prefix}{cmd.name}` → {cmd.help or 'No description available'}\n"
                category_commands.append(cmd_text)
            
            current_categories.append((category_text, category_commands))
            
            if len(current_categories) >= categories_per_page or category == sorted_categories[-1]:
                page_content = []
                
                for cat_text, cmd_list in current_categories:
                    page_content.append(cat_text)
                    page_content.extend(cmd_list)
                
                if len('\n'.join(page_content)) > 2000:
                    temp_page = []
                    for line in page_content:
                        if len('\n'.join(temp_page + [line])) > 2000:
                            pages.append('\n'.join(temp_page))
                            temp_page = [line]
                        else:
                            temp_page.append(line)
                    if temp_page:
                        pages.append('\n'.join(temp_page))
                else:
                    pages.append('\n'.join(page_content))
                
                current_categories = []
        
        if not pages:
            await ctx.send("No commands available!")
            return

        current_page = 0

        view = discord.ui.View()
        prev_button = discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary)
        next_button = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary)
        close_button = discord.ui.Button(label="Close", style=discord.ButtonStyle.danger)

        async def prev_callback(interaction):
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

        prev_button.callback = prev_callback
        next_button.callback = next_callback
        close_button.callback = close_callback

        view.add_item(prev_button)
        view.add_item(close_button)
        view.add_item(next_button)

        embed = discord.Embed(
            title="Command list",
            description=pages[0],
            color=0x2B2D31
        )
        embed.set_footer(text=f"Page 1 of {len(pages)} • {sum(len(cmds) for cmds in commands_by_cog.values())} total commands")

        message = await ctx.send(embed=embed, view=view)

        async def on_timeout():
            for item in view.children:
                item.disabled = True
            await message.edit(view=view)

        view.on_timeout = on_timeout

async def setup(bot):
    await bot.add_cog(Help(bot))