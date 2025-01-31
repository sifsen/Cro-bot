import discord
from datetime import datetime
import json
import time
import random
import base64

class ModLogger:
    def __init__(self, bot):
        self.bot = bot
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

    async def log_action(self, ctx, action, member, reason):
        """Logs a moderation action"""
        embed = discord.Embed(
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        embed.set_author(
            name=f"{action}",
            icon_url=member.display_avatar.url
        )

        duration = None
        if action == "Timeout" and " - " in reason:
            duration, reason = reason.split(" - ", 1)
            embed.description = f"**Duration:** {duration}\n**Reason:** {reason or 'No reason provided'}"
        else:
            embed.description = f"**Reason:** {reason or 'No reason provided'}"

        try:
            with open('data/mod_logs.json', 'r') as f:
                records = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            records = {}

        guild_id = str(ctx.guild.id)
        if guild_id not in records:
            records[guild_id] = {
                'guild_name': ctx.guild.name,
                'users': {},
                'cases': {}
            }

        user_id = str(member.id)
        if user_id not in records[guild_id]['users']:
            records[guild_id]['users'][user_id] = {
                'username': f"{member.name}#{member.discriminator}" if member.discriminator != '0' else member.name,
                'case_ids': []
            }

        case_data = {
            'action': action,
            'user_id': member.id,
            'mod_id': ctx.author.id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
        if duration:
            case_data['duration'] = duration

        case_id = self.generate_case_id()
        
        records[guild_id]['cases'][case_id] = case_data
        records[guild_id]['users'][user_id]['case_ids'].append(case_id)

        with open('data/mod_logs.json', 'w') as f:
            json.dump(records, f, indent=2)

        embed.add_field(
            name="Member",
            value=f"{member.mention} | {member.name}\n```javascript\nID: {member.id}```",
            inline=False
        )

        embed.add_field(
            name="Moderator responsible",
            value=f"{ctx.author.mention} | {ctx.author.name}\n```javascript\nID: {ctx.author.id}```",
            inline=False
        )

        embed.add_field(
            name="Command location",
            value=f"{ctx.channel.mention} | [Direct Link]({ctx.message.jump_url})",
            inline=False
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.set_footer(text=f"Case {case_id}")

        mod_audit_channel_id = self.bot.settings.get_server_setting(ctx.guild.id, "log_channel_mod_audit")
        if mod_audit_channel_id:
            channel = ctx.guild.get_channel(int(mod_audit_channel_id))
            if channel:
                await channel.send(embed=embed)