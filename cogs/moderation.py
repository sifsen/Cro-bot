import discord
import random
import json
import re
import base64
import time
from typing import Union
import asyncio

from utils.helpers import PermissionHandler
from discord.ext import commands
from datetime import datetime, timedelta
from utils.helpers.formatting import TextFormatter, EmbedBuilder
from utils.helpers.time import TimeParser


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mod_log_file = "data/mod_logs.json"
        self.last_case_time = 0
        self.case_counter = 0

    def generate_case_id(self) -> str:
        """Generate a unique case ID based on timestamp"""
        current_time = int(time.time())
        
        if current_time == self.last_case_time:
            self.case_counter += 1
        else:
            self.last_case_time = current_time
            self.case_counter = 0
        
        unique_num = (current_time << 16) | (self.case_counter << 8) | random.randint(0, 255)
        
        case_id = base64.b32encode(unique_num.to_bytes(8, 'big')).decode('utf-8').rstrip('=')[:8]
        return case_id

    async def save_mod_action(self, guild_id: int, action: dict):
        """Save a moderation action to the records"""
        try:
            with open(self.mod_log_file, 'r') as f:
                records = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            records = {}

        guild_id = str(guild_id)
        if guild_id not in records:
            records[guild_id] = {
                'cases': {},
                'users': {}
            }

        case_id = self.generate_case_id()
        action['case_id'] = case_id
        action['timestamp'] = datetime.utcnow().isoformat()
        
        records[guild_id]['cases'][case_id] = action
        
        user_id = str(action['user_id'])
        user = await self.bot.fetch_user(action['user_id'])
        
        if user_id not in records[guild_id]['users']:
            records[guild_id]['users'][user_id] = {
                'username': f"{user.name}#{user.discriminator}" if user.discriminator != '0' else user.name,
                'case_ids': []
            }
        else:
            records[guild_id]['users'][user_id]['username'] = f"{user.name}#{user.discriminator}" if user.discriminator != '0' else user.name
                
        records[guild_id]['users'][user_id]['case_ids'].append(case_id)

        with open(self.mod_log_file, 'w') as f:
            json.dump(records, f, indent=2)
            
        return case_id

    @commands.command(aliases=['history', 'infractions'])
    @PermissionHandler.has_permissions(kick_members=True)
    async def records(self, ctx, user: Union[discord.Member, discord.User, str]):
        """View a member's moderation record"""
        try:
            if isinstance(user, str):
                if user.isdigit():
                    user = await self.bot.fetch_user(int(user))
                else:
                    mention_match = re.match(r'<@!?(\d+)>', user)
                    if mention_match:
                        user = await self.bot.fetch_user(int(mention_match.group(1)))
                    else:
                        await ctx.send("Please provide a valid user ID or mention.")
                        return

            with open(self.mod_log_file, 'r') as f:
                records = json.load(f)

            guild_records = records.get(str(ctx.guild.id), {})
            user_data = guild_records.get('users', {}).get(str(user.id))

            if not user_data or not user_data.get('case_ids', []):
                await ctx.send(f"No moderation records found for {user.mention}")
                return

            embed = discord.Embed(
                title=f"Member records | Page 1/1",
                color=0x2B2D31,
                timestamp=datetime.utcnow()
            )
            
            embed.description = f"**{user.name}**\nMention: {user.mention}\n```javascript\nID: {user.id}```\n**Total records:** {len(user_data['case_ids'])}"
            embed.set_thumbnail(url=user.display_avatar.url)

            cases = guild_records.get('cases', {})
            cases_to_show = user_data['case_ids'][-10:]
            cases_to_show.reverse()
            
            for case_id in cases_to_show:
                if case_id not in cases:
                    continue
                    
                record = cases[case_id]
                action_time = datetime.fromisoformat(record['timestamp'])
                moderator = ctx.guild.get_member(record['mod_id'])
                mod_name = moderator.name if moderator else "Unknown moderator"

                embed.add_field(
                    name=f"**{record['action']}**",
                    value=(
                        f"**Case ID:** `{case_id}`\n"
                        f"**Moderator:** {moderator.mention if moderator else mod_name}\n"
                        f"When: {discord.utils.format_dt(action_time)}\n"
                        f"> **Reason:**\n> {record['reason'] or 'No reason provided'}"
                        + (f"\n> **Duration:** {record['duration']}" if 'duration' in record else "")
                    ),
                    inline=False
                )

            embed.set_footer(text=f"Most recent {min(len(user_data['case_ids']), 10)} of {len(user_data['case_ids'])} records")
            await ctx.send(embed=embed)

        except FileNotFoundError:
            await ctx.send("No moderation records exist yet")
        except json.JSONDecodeError:
            await ctx.send("Error reading moderation records")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(aliases=['editcase'])
    @PermissionHandler.has_permissions(kick_members=True)
    async def editrecord(self, ctx, case_id: str, *, new_reason: str):
        """Edit the reason for a moderation case"""
        try:
            with open(self.mod_log_file, 'r') as f:
                records = json.load(f)
                
            guild_records = records.get(str(ctx.guild.id), {})
            case = guild_records.get('cases', {}).get(case_id)
            
            if not case:
                await ctx.send(f"Case ID `{case_id}` not found.")
                return
            
            case['reason'] = new_reason
            case['edited_by'] = ctx.author.id
            case['edited_at'] = datetime.utcnow().isoformat()
            
            with open(self.mod_log_file, 'w') as f:
                json.dump(records, f, indent=2)
            
            user = ctx.guild.get_member(case['user_id']) or await ctx.guild.fetch_member(case['user_id'])
            mod = ctx.guild.get_member(case['mod_id'])
            
            embed = discord.Embed(
                title=f"Case updated",
                description=f"**Case:** {case_id}\n**Action:** {case['action']}\n**Target:** {user.mention}\n**New reason:** {new_reason}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Original moderator", value=mod.mention if mod else "Unknown")
            embed.add_field(name="Edited by", value=ctx.author.mention)
            
            await ctx.send("Done 👍")
            
            mod_audit_channel_id = self.bot.settings.get_server_setting(ctx.guild.id, "log_channel_mod_audit")
            if mod_audit_channel_id:
                channel = ctx.guild.get_channel(int(mod_audit_channel_id))
                if channel:
                    await channel.send(embed=embed)
                    
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Kick Command
    #################################      
    @commands.command(aliases=['punch'])
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
                    await interaction.response.send_message("This is not for you!", ephemeral=True)
                    return

                try:
                    await member.kick(reason=reason)
                    
                    case_id = await self.save_mod_action(ctx.guild.id, {
                        'user_id': member.id,
                        'mod_id': ctx.author.id,
                        'action': 'Kick',
                        'reason': reason
                    })
                    
                    await self.log_mod_action(ctx, "Kicked", member, case_id, reason=reason)
                    
                    await ctx.send(f"**{member.name}** was kicked")
                    await interaction.message.delete()
                except discord.Forbidden:
                    await ctx.send("I don't have permission to kick that user!")
                except Exception as e:
                    await ctx.send(f"An error occurred: {str(e)}")

            async def cancel_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This is not for you!", ephemeral=True)
                    return
                await interaction.message.delete()

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)

            await ctx.send(
                f"Are you sure you want to kick **{member.name}**?" + 
                (f"\nReason: {reason}" if reason else ""), 
                view=confirm_view
            )


        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Ban Command
    #################################   
    async def get_or_fetch_user(self, ctx, user_input: str) -> Union[discord.Member, discord.User, None]:
        """Helper function to get a user from various input formats"""
        user = None
        
        if user_input.startswith('<@') and user_input.endswith('>'):
            user_id = int(user_input[2:-1].replace('!', ''))
            user = ctx.guild.get_member(user_id) or await self.bot.fetch_user(user_id)
        
        elif user_input.isdigit():
            user_id = int(user_input)
            user = ctx.guild.get_member(user_id) or await self.bot.fetch_user(user_id)
            
        else:
            user = discord.utils.find(
                lambda m: str(m) == user_input or m.name == user_input,
                ctx.guild.members
            )
            
            if not user and '#' in user_input:
                try:
                    user = await self.bot.fetch_user(user_input)
                except:
                    pass

        return user

    @commands.command(aliases=['kill'])
    @PermissionHandler.has_permissions(ban_members=True)
    async def ban(self, ctx, user_input: str, *, reason=None):
        """Ban a user from the server (can ban users not in the server)"""
        try:
            user = await self.get_or_fetch_user(ctx, user_input)
            if not user:
                await ctx.reply("Could not find that user. Please provide a valid user ID, mention, or username#discriminator.")
                return

            if isinstance(user, discord.Member):
                if user.top_role >= ctx.author.top_role:
                    await ctx.reply("You cannot ban someone with a higher or equal role!")
                    return

            confirm_view = discord.ui.View()
            confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
            compromised_button = discord.ui.Button(label="Compromised account", style=discord.ButtonStyle.primary)

            async def confirm_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This is not for you!", ephemeral=True)
                    return

                try:
                    await ctx.guild.ban(user, reason=reason)
                    
                    case_id = await self.save_mod_action(ctx.guild.id, {
                        'user_id': user.id,
                        'mod_id': ctx.author.id,
                        'action': 'Ban',
                        'reason': reason
                    })

                    embed = discord.Embed(
                        title=f"You were banned from {ctx.guild.name}",
                        color=discord.Color.red()
                    )
                    if reason:
                        embed.add_field(name="Reason", value=reason)

                    await user.send(embed=embed)
                    
                    await self.log_mod_action(ctx, "Ban", user, case_id, reason=reason)
                    
                    with open('data/strings.json', 'r') as f:
                        strings = json.load(f)
                        action = random.choice(strings['user_was_x'])
                    
                    await confirm_message.edit(content=f"**{user}** was {action}", view=None)
                    await interaction.response.defer()
                except Exception as e:
                    await confirm_message.edit(content=f"Error: {str(e)}", view=None)

            async def compromised_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This is not for you!", ephemeral=True)
                    return

                try:
                    await interaction.response.defer()
                    
                    dm_message = (
                        f"You were banned from {ctx.guild.name} because your account showed signs of being compromised.\n\n"
                        "For your security, please:\n"
                        "1. Change your Discord password\n"
                        "2. Enable 2-factor authentication\n"
                        "3. Remove any suspicious authorized apps\n"
                        "4. Check for suspicious login locations\n\n"
                        "You have been automatically unbanned and can re-join once you've secured your account."
                    )
                    try:
                        await user.send(dm_message)
                    except:
                        pass

                    await user.ban(reason="Compromised account", delete_message_days=1)
                    
                    case_id = await self.save_mod_action(ctx.guild.id, {
                        'user_id': user.id,
                        'mod_id': ctx.author.id,
                        'action': 'Ban',
                        'reason': "Compromised account"
                    })
                    
                    await self.log_mod_action(ctx, "Ban", user, case_id, reason="Compromised account")
                    
                    await asyncio.sleep(2)
                    await ctx.guild.unban(user)
                    
                    await interaction.message.edit(f"**{user}** was banned for compromised account")
                except Exception as e:
                    await interaction.message.edit(f"Error handling compromised account: {str(e)}")

            async def cancel_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This is not for you!", ephemeral=True)
                    return
                await interaction.message.delete()

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            compromised_button.callback = compromised_callback
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)
            confirm_view.add_item(compromised_button)

            confirm_message = await ctx.reply(f"Are you sure you want to ban **{user}**?", view=confirm_view)

        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that user!")
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
                await ctx.send("That user is not banned")
                return

            await ctx.guild.unban(user)
            await ctx.send(f"**{user.name}** has been unbanned")

        except discord.Forbidden:
            await ctx.send("I don't have permission to unban users!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Mute Command
    #################################   
    @commands.command(aliases=['silence'])
    @PermissionHandler.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: str = None, *, reason=None):
        """Mute a member (e.g. 1h, 30m, 1d). Default: 1 hour"""
        try:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot mute someone with a higher or equal role!")
                return

            if duration is None:
                duration = "1h"
                
            seconds = TimeParser.parse_time_string(duration)
            if not seconds:
                await ctx.send("Invalid duration format. Use combinations of w/d/h/m/s (e.g., 1d12h)")
                return

            if seconds > 2419200:
                await ctx.send("Timeout duration cannot exceed 28 days.")
                return

            await member.timeout(
                discord.utils.utcnow() + timedelta(seconds=seconds),
                reason=f"{ctx.author}: {reason}" if reason else f"{ctx.author}: no reason provided"
            )

            case_id = await self.save_mod_action(ctx.guild.id, {
                'user_id': member.id,
                'mod_id': ctx.author.id,
                'action': 'Mute',
                'reason': reason,
                'duration': TimeParser.format_duration(seconds)
            })

            future_timestamp = int((datetime.utcnow() + timedelta(seconds=seconds)).timestamp())
            await self.log_mod_action(
                ctx, 
                "Mute",
                member,
                case_id,
                reason=reason,
                duration=TimeParser.format_duration(seconds),
                expires_at=future_timestamp
            )

            await ctx.send(f"**{member.name}** has been muted for {TimeParser.format_duration(seconds)}")

        except discord.Forbidden:
            await ctx.send("I don't have permission to mute that user!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Unmute Command
    #################################   
    @commands.command(aliases=['unsilence', 'untimeout'])
    @PermissionHandler.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        """Remove timeout from a member"""
        try:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot unmute someone with a higher or equal role!")
                return

            if not member.is_timed_out():
                mute_role_id = self.bot.settings.get_server_setting(ctx.guild.id, "mute_role")
                if not mute_role_id:
                    await ctx.send("This user is not muted")
                    return
                
                mute_role = ctx.guild.get_role(int(mute_role_id))
                if not mute_role or mute_role not in member.roles:
                    await ctx.send("This user is not muted")
                    return
                
                await member.remove_roles(mute_role, reason=reason)
            else:
                await member.timeout(None, reason=reason)

            await ctx.send(f"**{member.name}** has been unmuted")

        except discord.Forbidden:
            await ctx.send("I don't have permission to unmute that user!")
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

    #################################
    ## Role Command
    ################################
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
                await ctx.send("Could not find that role")
                return

            if role >= ctx.author.top_role and not ctx.author.guild_permissions.administrator:
                await ctx.send("You cannot manage a role equal to or higher than your highest role.")
                return

            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(f"Removed role **{role.name}** from **{member.name}**")
            else:
                await member.add_roles(role)
                await ctx.send(f"Added role **{role.name}** to **{member.name}**")

        except discord.Forbidden:
            await ctx.send("I don't have permission to manage roles.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Purge Command
    #################################
    @commands.group(invoke_without_command=True)
    @PermissionHandler.has_permissions(manage_messages=True)
    async def purge(self, ctx, search: int = 100, member: discord.Member = None):
        """Purge messages. If member is specified, only purge their messages"""
        if search > 1000:
            await ctx.send("Cannot delete more than 1000 messages at once")
            return
            
        def check(message):
            if message.pinned:
                return False
            if member:
                return message.author == member
            return True

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, member)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @purge.command(name='bot')
    @PermissionHandler.has_permissions(manage_messages=True)
    async def purge_bot(self, ctx, search: int = 100, prefix: str = None):
        """Purge bot messages and messages with prefix"""
        def check(message):
            if message.pinned:
                return False
            if message.author.bot:
                return True
            if prefix and message.content.startswith(prefix):
                return True
            return False

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, None, f"Bot messages {f'with prefix {prefix}' if prefix else ''}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @purge.command(name='contains')
    @PermissionHandler.has_permissions(manage_messages=True)
    async def purge_contains(self, ctx, search: int = 100, *, substring: str):
        """Purge messages containing substring"""
        def check(message):
            return not message.pinned and substring.lower() in message.content.lower()

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, None, f"Messages containing: {substring}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command()
    @PermissionHandler.has_permissions(manage_messages=True)
    async def cleanup(self, ctx, search: int = 100):
        """Cleanup bot messages"""
        def check(message):
            return message.author == ctx.bot.user

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, ctx.bot.user)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @purge.command(name='embeds')
    @PermissionHandler.has_permissions(manage_messages=True)
    async def purge_embeds(self, ctx, search: int = 100):
        """Purge messages with embeds"""
        def check(message):
            return not message.pinned and (message.embeds or message.attachments)

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, None, "Messages with embeds")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @purge.command(name='emoji')
    @PermissionHandler.has_permissions(manage_messages=True)
    async def purge_emoji(self, ctx, search: int = 100):
        """Purge messages containing custom emoji"""
        def check(message):
            return not message.pinned and re.search(r'<a?:\w+:\d+>', message.content)

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, None, "Messages with custom emoji")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @purge.command(name='files')
    @PermissionHandler.has_permissions(manage_messages=True)
    async def purge_files(self, ctx, search: int = 100):
        """Purge messages with attachments"""
        def check(message):
            return not message.pinned and message.attachments

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, None, "Messages with attachments")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @purge.command(name='links')
    @PermissionHandler.has_permissions(manage_messages=True)
    async def purge_links(self, ctx, search: int = 100):
        """Purge messages containing links"""
        def check(message):
            return not message.pinned and re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content)

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, None, "Messages with links")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @purge.command(name='mentions', aliases=['pings'])
    @PermissionHandler.has_permissions(manage_messages=True)
    async def purge_mentions(self, ctx, search: int = 100):
        """Purge messages containing mentions"""
        def check(message):
            return not message.pinned and (message.mentions or message.role_mentions or message.mention_everyone)

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, None, "Messages with mentions")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @purge.command(name='humans')
    @PermissionHandler.has_permissions(manage_messages=True)
    async def purge_humans(self, ctx, search: int = 100):
        """Purge messages by humans"""
        def check(message):
            return not message.pinned and not message.author.bot

        try:
            deleted = await ctx.channel.purge(limit=search + 1, check=check)
            await self.log_bulk_delete(ctx, len(deleted) - 1, None, "Human messages")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    async def log_bulk_delete(self, ctx, count: int, target: discord.Member = None, filter_info: str = None):
        """Helper function to log bulk message deletions"""
        log_channel_id = self.bot.settings.get_server_setting(ctx.guild.id, "log_channel_mod_audit")
        if not log_channel_id:
            return
        
        await ctx.send(f"Deleted {count} messages")

    #################################
    ## Add Note Command
    #################################
    @commands.command(aliases=['setnote'])
    @PermissionHandler.has_permissions(kick_members=True)
    async def note(self, ctx, member: Union[discord.Member, discord.User], *, note: str):
        """Add a note to a user's record"""
        case_id = await self.save_mod_action(
            ctx.guild.id,
            {
                'action': 'Note',
                'user_id': member.id,
                'mod_id': ctx.author.id,
                'reason': note
            }
        )
        
        await self.log_mod_action(ctx, "Note", member, case_id, reason=note)
        await ctx.reply(f"Added note to **{member.name}**'s record")

    #################################
    ## Lock Command
    #################################
    @commands.command()
    @PermissionHandler.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Lock a channel"""
        try:
            channel = channel or ctx.channel
            overwrites = channel.overwrites_for(ctx.guild.default_role)
            
            if not overwrites.send_messages is False:
                overwrites.send_messages = False
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)

                await ctx.send(f"{channel.mention} has been locked.")
            else:
                await ctx.send(f"{channel.mention} is already locked.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to manage channel permissions!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Unlock Command
    #################################
    @commands.command()
    @PermissionHandler.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlock a channel"""
        try:
            channel = channel or ctx.channel
            overwrites = channel.overwrites_for(ctx.guild.default_role)
            
            if overwrites.send_messages is False:
                overwrites.send_messages = None
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
                
                await ctx.send(f"{channel.mention} has been unlocked.")
            else:
                await ctx.send(f"{channel.mention} is not locked.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to manage channel permissions!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Warn Command
    #################################   
    @commands.command()
    @PermissionHandler.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Warn a member"""
        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You cannot warn someone with a higher or equal role!")
            return
        
        case_id = await self.save_mod_action(
            ctx.guild.id,
            {
                'action': 'Warn',
                'user_id': member.id,
                'mod_id': ctx.author.id,
                'reason': reason
            }
        )
        
        try:
            embed = discord.Embed(
                title=f"You were warned in {ctx.guild.name}",
                color=discord.Color.yellow()
            )
            if reason:

                embed.add_field(name="Reason", value=reason)
            await member.send(embed=embed)
        except:
            pass
        
        await self.log_mod_action(ctx, "Warn", member, case_id, reason=reason)
        await ctx.reply(f"Warned **{member.name}**" + (f" for: **{reason}**" if reason else ""))

    #################################
    ## Nickname Command
    #################################
    @commands.command(aliases=['nick'])
    async def nickname(self, ctx: commands.Context, member: discord.Member, *, new_nick: str = None):
        """Change a member's nickname"""
        old_nick = member.display_name
        
        try:
            await member.edit(nick=new_nick)
            if new_nick is None:
                await ctx.send(f"Reset **{member.name}**'s nickname")
            else:
                await ctx.send(f"Changed **{member.name}**'s nickname from **{old_nick}** to **{new_nick}**")
        except discord.Forbidden:
            await ctx.send("I don't have permission to change that user's nickname")

    #################################
    ## Softban Command
    #################################   
    @commands.command()
    @PermissionHandler.has_permissions(ban_members=True)
    async def softban(self, ctx, member: discord.Member, days: int = 2, *, reason=None):
        """Ban and immediately unban to clear message history"""
        try:
            if member.top_role >= ctx.author.top_role:
                await ctx.reply("You cannot softban someone with a higher or equal role!")
                return

            confirm_view = discord.ui.View()
            confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)

            async def confirm_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This is not for you!", ephemeral=True)
                    return

                try:
                    await member.ban(reason=reason, delete_message_days=days)
                    case_id = await self.save_mod_action(ctx.guild.id, {
                        'user_id': member.id,
                        'mod_id': ctx.author.id,
                        'action': 'Softban',
                        'reason': reason
                    })
                    
                    await self.log_mod_action(ctx, "Softbanned", member, case_id, reason=reason)
                    await ctx.guild.unban(member)
                    
                    with open('data/strings.json', 'r') as f:
                        strings = json.load(f)
                        action = random.choice(strings['user_was_x'])
                    
                    await confirm_message.edit(content=f"**{member.name}** was {action}", view=None)
                    await interaction.response.defer()
                except Exception as e:
                    await confirm_message.edit(content=f"Error: {str(e)}", view=None)
                    await interaction.response.defer()

            async def cancel_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("This is not for you!", ephemeral=True)
                    return
                await interaction.message.delete()

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)

            confirm_message = await ctx.send(
                f"Are you sure you want to softban **{member.name}**?" +
                (f"\nReason: {reason}" if reason else ""),
                view=confirm_view
            )

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Tempban Command
    #################################   
    @commands.command()
    @PermissionHandler.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: discord.Member, duration: str, days: int = 2, *, reason=None):
        """Temporarily ban a member"""
        try:
            if member.top_role >= ctx.author.top_role:
                await ctx.reply("You cannot tempban someone with a higher or equal role!")
                return
                
            seconds = TimeParser.parse_time_string(duration)
            if not seconds:
                await ctx.send("Invalid duration format. Use combinations of w/d/h/m/s (e.g., 1d12h)")
                return

            await member.ban(reason=reason, delete_message_days=days)
            case_id = await self.save_mod_action(ctx.guild.id, {
                'user_id': member.id,
                'mod_id': ctx.author.id,
                'action': 'Tempban',
                'reason': reason,
                'duration': TimeParser.format_duration(seconds),
                'expires_at': int((datetime.utcnow() + timedelta(seconds=seconds)).timestamp())
            })
            
            await self.log_mod_action(
                ctx, 
                "Tempban", 
                member, 
                case_id, 
                reason=reason,
                duration=TimeParser.format_duration(seconds)
            )

            await asyncio.sleep(seconds)
            try:
                await ctx.guild.unban(member)
                await self.log_mod_action(ctx, "Tempban expired", member, case_id)
            except:
                pass

            await ctx.reply(f"**{member.name}** was tempbanned for {TimeParser.format_duration(seconds)}")

        except discord.Forbidden:
            await ctx.send("I don't have permission to ban that user!")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    #################################
    ## Massban Command
    #################################   
    @commands.command()
    @PermissionHandler.has_permissions(ban_members=True)
    async def massban(self, ctx, days: int = 2, *, args):
        """Ban multiple members at once"""
        members = []
        reason = None
        
        parts = args.split()
        for part in parts:
            if part.startswith('<@') and part.endswith('>'):
                try:
                    member_id = int(part[2:-1].replace('!', ''))
                    member = ctx.guild.get_member(member_id)
                    if member:
                        members.append(member)
                except:
                    continue
            elif part.isdigit():
                try:
                    member = ctx.guild.get_member(int(part))
                    if member:
                        members.append(member)
                except:
                    continue
            else:
                reason_start = args.find(part)
                if reason_start != -1:
                    reason = args[reason_start:]
                break

        if not members:
            await ctx.send("No valid members provided!")
            return

        confirm_view = discord.ui.View()
        confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
        cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)

        async def confirm_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return

            success = []
            failed = []
            for member in members:
                try:
                    if member.top_role >= ctx.author.top_role:
                        failed.append(f"{member.name} (higher role)")
                        continue
                        
                    await member.ban(reason=reason, delete_message_days=days)
                    case_id = await self.save_mod_action(ctx.guild.id, {
                        'user_id': member.id,
                        'mod_id': ctx.author.id,
                        'action': 'Massban',
                        'reason': reason
                    })
                    await self.log_mod_action(ctx, "Massban", member, case_id, reason=reason)
                    success.append(member.name)
                except:
                    failed.append(member.name)

            report = f"Banned {len(success)} members"
            if success:
                report += f"\nSuccess: {', '.join(success[:10])}" + ("..." if len(success) > 10 else "")
            if failed:
                report += f"\nFailed: {', '.join(failed[:10])}" + ("..." if len(failed) > 10 else "")
                
            await confirm_message.edit(content=report, view=None)
            await interaction.response.defer()

        async def cancel_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("This is not for you!", ephemeral=True)
                return
            await interaction.message.delete()

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        confirm_view.add_item(confirm_button)
        confirm_view.add_item(cancel_button)

        confirm_message = await ctx.send(
            f"Are you sure you want to ban {len(members)} members?\n" +
            "\n".join(f"- {member.name} ({member.id})" for member in members[:10]) +
            ("\n..." if len(members) > 10 else "") +
            (f"\nReason: {reason}" if reason else ""),
            view=confirm_view
        )

    #################################
    ## Warning Management Commands
    #################################
    @commands.group(invoke_without_command=True)
    @PermissionHandler.has_permissions(kick_members=True)
    async def warns(self, ctx, member: discord.Member = None):
        """List warnings for a member or the whole server"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        mod_logs = settings.get('mod_logs', {})
        
        if member:
            warnings = [
                log for log in mod_logs.values()
                if log.get('action') == 'Warn' and log.get('user_id') == member.id
            ]
            if not warnings:
                return await ctx.send(f"**{member.name}** has no warnings.")
                
            embed = discord.Embed(title=f"Warnings for {member.name}", color=discord.Color.yellow())
        else:
            warnings = [log for log in mod_logs.values() if log.get('action') == 'Warn']
            if not warnings:
                return await ctx.send("No warnings in this server.")
                
            embed = discord.Embed(title="Server Warnings", color=discord.Color.yellow())
            
        for warn in warnings[-10:]:
            mod = ctx.guild.get_member(warn.get('mod_id'))
            embed.add_field(
                name=f"Case {warn.get('case_id')}",
                value=f"**Moderator:** {mod.mention if mod else 'Unknown'}\n"
                      f"**Reason:** {warn.get('reason') or 'No reason provided'}",
                inline=False
            )
            
        await ctx.send(embed=embed)

    @warns.command(name='remove')
    @PermissionHandler.has_permissions(kick_members=True)
    async def remove_warn(self, ctx, case_id: str):
        """Remove a warning by its case ID"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        mod_logs = settings.get('mod_logs', {})
        
        if case_id not in mod_logs or mod_logs[case_id].get('action') != 'Warn':
            return await ctx.send("Warning not found.")
            
        warning = mod_logs[case_id]
        del mod_logs[case_id]
        
        self.bot.settings.set_server_setting(ctx.guild.id, 'mod_logs', mod_logs)
        await ctx.send(f"Removed warning case **{case_id}**")
        
        member = ctx.guild.get_member(warning.get('user_id'))
        if member:
            await self.log_mod_action(ctx, "Warning Removed", member, case_id)

    @warns.command(name='clear')
    @PermissionHandler.has_permissions(kick_members=True)
    async def clear_warns(self, ctx, member: discord.Member):
        """Clear all warnings from a member"""
        settings = self.bot.settings.get_all_server_settings(ctx.guild.id)
        mod_logs = settings.get('mod_logs', {})
        
        removed = 0
        new_logs = {}
        for case_id, log in mod_logs.items():
            if log.get('action') == 'Warn' and log.get('user_id') == member.id:
                removed += 1
            else:
                new_logs[case_id] = log
                
        if removed == 0:
            return await ctx.send(f"**{member.name}** has no warnings to clear.")
            
        self.bot.settings.set_server_setting(ctx.guild.id, 'mod_logs', new_logs)
        await ctx.send(f"Cleared {removed} warning(s) from **{member.name}**")
        
        await self.log_mod_action(ctx, "Warnings Cleared", member, self.generate_case_id())

    async def log_mod_action(self, ctx, action: str, target: Union[discord.Member, discord.User], case_id: str, *, reason: str = None, duration: str = None, expires_at: int = None):
        """Log a moderation action to the audit log channel"""
        log_channel_id = self.bot.settings.get_server_setting(ctx.guild.id, "log_channel_mod_audit")
        if not log_channel_id:
            return
            
        channel = ctx.guild.get_channel(int(log_channel_id))
        if not channel:
            return

        embed = EmbedBuilder(
            title=f"{action}",
            description=(
                f"**User:** {target.mention}\n`{target.id}`\n"
                f"**Moderator:** {ctx.author.mention}\n`{ctx.author.id}`\n"
                f"**Case ID:** `{case_id}`"
                + (f"\n**Duration:** {duration}" if duration else "")


                + (f"\n**Expires:** <t:{expires_at}:R>" if expires_at else "")
                + (f"\n\n**Reason:**\n> {reason}" if reason else "\n\n**Reason:** No reason provided")
            )
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed = embed.build()
        embed.color = 0x2B2D31
        await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))