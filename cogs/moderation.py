import discord
import re

from utils.helpers import PermissionHandler
from discord.ext import commands
from datetime import datetime, timedelta


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_moderation_action(self, ctx, action, member, reason):
        title_map = {
            'Kick': 'Member kicked',
            'Ban': 'Member banned',
            'Unban': 'Member unbanned',
            'Mute': 'Member muted',
            'Unmute': 'Member unmuted',
            'Warn': 'Member warned',
            'Timeout': 'Member timed out',
            'Note': 'Note added'
        }
        
        embed = discord.Embed(
            title=title_map.get(action, f"Member {action}"),
            description=f"**Action:** {action}\n**Target:** {member.mention} (`{member.id}`)\n**Reason:** {reason or 'No reason provided'}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Moderator",
            value=f"{ctx.author.mention} (`{ctx.author.id}`)",
            inline=True
        )
        
        embed.add_field(
            name="Channel",
            value=ctx.channel.mention,
            inline=True
        )

        embed.set_footer(text=f"Action taken in #{ctx.channel.name}")
        embed.set_thumbnail(url=member.display_avatar.url)

        mod_audit_channel_id = self.bot.settings.get_server_setting(ctx.guild.id, "log_channel_modaudit")
        if mod_audit_channel_id:
            channel = ctx.guild.get_channel(int(mod_audit_channel_id))
            if channel:
                await channel.send(embed=embed)

    #################################
    ## Kick Command
    #################################      
    @commands.command(aliases=['slap'])
    @PermissionHandler.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server"""
        try:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot kick someone with a higher or equal role!")
                return

            confirm_view = discord.ui.View()
            confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)

            async def confirm_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You cannot interact with this confirmation.", ephemeral=True)
                    return

                await member.kick(reason=reason)
                await self.log_moderation_action(ctx, "Kick", member, reason)
                await confirm_message.edit(content=f"{member.mention} has been kicked.", view=None)
                await interaction.response.defer()

            async def cancel_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You cannot interact with this confirmation.", ephemeral=True)
                    return

                await confirm_message.edit(content="Kick command cancelled.", view=None)
                await interaction.response.defer()

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)

            confirm_message = await ctx.send(f"Are you sure you want to kick {member.mention}?", view=confirm_view)

        except discord.Forbidden:
            await ctx.send("I don't have permission to kick that member!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Ban Command
    #################################   
    @commands.command(aliases=['kill'])
    @PermissionHandler.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server"""
        try:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot ban someone with a higher or equal role!")
                return

            confirm_view = discord.ui.View()
            confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)

            async def confirm_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You cannot interact with this confirmation.", ephemeral=True)
                    return

                await member.ban(reason=reason)
                await self.log_moderation_action(ctx, "Ban", member, reason)
                await confirm_message.edit(content=f"{member.mention} has been banned.", view=None)
                await interaction.response.defer()

            async def cancel_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You cannot interact with this confirmation.", ephemeral=True)
                    return

                await confirm_message.edit(content="Guess not then.", view=None)
                await interaction.response.defer()

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)

            confirm_message = await ctx.send(f"Are you sure you want to ban {member.global_name}?", view=confirm_view)

        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that member!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Unban Command
    #################################   
    @commands.command(aliases=['pardon'])
    @PermissionHandler.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user_input):
        """Unban a member from the server"""
        try:
            user_id = None
            if user_input.isdigit():
                user_id = int(user_input)
            else:
                mention_match = re.match(r'<@!?(\d+)>', user_input)
                if mention_match:
                    user_id = int(mention_match.group(1))
            
            if not user_id:
                await ctx.send("Please provide a valid user ID or mention.")
                return

            try:
                ban_entry = await ctx.guild.fetch_ban(discord.Object(id=user_id))
                user = ban_entry.user
            except discord.NotFound:
                await ctx.send("That user is not banned.")
                return

            await ctx.guild.unban(user)
            await self.log_moderation_action(ctx, "Unban", user, "No reason provided")
            await ctx.send(f"{user.mention} has been unbanned.")
            
        except discord.Forbidden:
            await ctx.send("I don't have permission to unban members!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Timeout Command
    #################################   
    @commands.command(aliases=['timeout', 'silence'])
    @PermissionHandler.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, time: str = None, *, reason=None):
        """Timeout a member (e.g. 1h, 30m, 1d)"""
        try:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot timeout someone with a higher or equal role!")
                return

            if not time:
                await ctx.send("Please provide a duration (e.g. 1h, 30m, 1d)")
                return

            duration = 0
            if time.endswith('m'): duration = int(time[:-1]) * 60
            elif time.endswith('h'): duration = int(time[:-1]) * 60 * 60
            elif time.endswith('d'): duration = int(time[:-1]) * 24 * 60 * 60
            else:
                await ctx.send("Invalid duration format. Use m (minutes), h (hours), or d (days)")
                return

            if duration <= 0:
                await ctx.send("Duration must be positive")
                return

            await member.timeout(discord.utils.utcnow() + timedelta(seconds=duration), reason=reason)
            await self.log_moderation_action(ctx, "Timeout", member, f"{time} - {reason if reason else 'No reason provided'}")
            await ctx.send(f"{member.mention} has been timed out for {time}")

        except discord.Forbidden:
            await ctx.send("I don't have permission to timeout that member!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Role Command (Fuzzy Search)
    #################################
    def find_best_match(self, input_str, roles):
        """Find the best matching role using fuzzy matching"""
        search_term = input_str.lower()
        best_match = None
        highest_similarity = 0

        for role in roles:
            role_name = role.name.lower()

            if role_name in search_term or search_term in role_name:
                similarity = max(
                    len(role_name) / len(search_term),
                    len(search_term) / len(role_name)
                )
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    best_match = role
                continue

            max_length = max(len(role_name), len(search_term))
            distance = 0
            for i in range(min(len(role_name), len(search_term))):
                if role_name[i] != search_term[i]:
                    distance += 1
            distance += abs(len(role_name) - len(search_term))

            similarity = 1 - (distance / max_length)
            if similarity > highest_similarity and similarity > 0.5:
                highest_similarity = similarity
                best_match = role

        return best_match

    @commands.command()
    @PermissionHandler.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, *, role_input: str):
        """Add or remove a role from a member"""
        try:
            role = None
            if role_input.startswith('<@&') and role_input.endswith('>'):
                role_id = int(role_input[3:-1])
                role = ctx.guild.get_role(role_id)
            elif role_input.isdigit():
                role = ctx.guild.get_role(int(role_input))
            else:
                role = discord.utils.find(
                    lambda r: r.name.lower() == role_input.lower(), 
                    ctx.guild.roles
                )

                if not role:
                    role = self.find_best_match(role_input, ctx.guild.roles)

            if not role:
                await ctx.send("Could not find that role.")
                return

            if role >= ctx.author.top_role and not ctx.author.guild_permissions.administrator:
                await ctx.send("You cannot manage a role equal to or higher than your highest role.")
                return

            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"Removed role **{role.name}** from {member.name}")
            else:
                await member.add_roles(role)
                await ctx.send(f"Added role **{role.name}** to {member.name}")

        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Purge Command
    #################################
    @commands.command()
    @PermissionHandler.has_permissions(manage_messages=True)    
    async def purge(self, ctx, amount: int):
        """Delete a specified number of messages"""
        try:
            await ctx.channel.purge(limit=amount + 1)
            msg = await ctx.send(f"Deleted {amount} messages.")
            await msg.delete(delay=3)

        except discord.Forbidden:
            await ctx.send("I don't have permission to delete messages.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Moderation(bot)) 