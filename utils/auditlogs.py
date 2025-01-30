import discord
from datetime import datetime

class ModLogger:
    def __init__(self, bot):
        self.bot = bot
        
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

        case_data = {
            'action': action,
            'user_id': member.id,
            'mod_id': ctx.author.id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }
    
        if duration:
            case_data['duration'] = duration

        embed.description = f"**Reason:** {reason or 'No reason provided'}"

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

        case_id = await ctx.cog.save_mod_action(ctx.guild.id, {
            'action': action,
            'user_id': member.id,
            'mod_id': ctx.author.id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        })

        embed.set_footer(text=f"Case {case_id}")

        mod_audit_channel_id = self.bot.settings.get_server_setting(ctx.guild.id, "log_channel_mod_audit")
        if mod_audit_channel_id:
            channel = ctx.guild.get_channel(int(mod_audit_channel_id))
            if channel:
                await channel.send(embed=embed)