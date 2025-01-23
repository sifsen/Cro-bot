import discord
from typing import Union

################################
## Check Permissions
################################
async def check_permissions(ctx, member: discord.Member, permission: str) -> bool:
    """Check if user has required permissions"""
    return getattr(ctx.author.guild_permissions, permission)

################################
## Format Time
################################    
def format_time(seconds: int) -> str:
    """Convert seconds to readable time format"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {seconds}s" 