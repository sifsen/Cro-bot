import discord
from typing import Union
from discord.ext import commands
from functools import wraps

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

class PermissionHandler:
    @staticmethod
    def has_permissions(**permissions):
        """
        A decorator that checks if a user has all the required permissions
        Usage: @PermissionHandler.has_permissions(manage_messages=True)
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(self, ctx: commands.Context, *args, **kwargs):
                # Check if user is the server owner
                if ctx.author == ctx.guild.owner:
                    return await func(self, ctx, *args, **kwargs)

                # Check all required permissions
                missing_perms = []
                for perm, required in permissions.items():
                    if required and not getattr(ctx.author.guild_permissions, perm, False):
                        missing_perms.append(perm)

                if missing_perms:
                    formatted_perms = ", ".join(perm.replace("_", " ").title() for perm in missing_perms)
                    await ctx.send(f"You're missing the following permissions: {formatted_perms}")
                    return

                return await func(self, ctx, *args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def has_role(*role_names: str):
        """
        A decorator that checks if a user has at least one of the specified roles
        Usage: @PermissionHandler.has_role("Admin", "Moderator")
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(self, ctx: commands.Context, *args, **kwargs):
                if ctx.author == ctx.guild.owner:
                    return await func(self, ctx, *args, **kwargs)

                user_roles = [role.name for role in ctx.author.roles]
                
                if not any(role in user_roles for role in role_names):
                    formatted_roles = ", ".join(role_names)
                    await ctx.send(f"You need one of these roles to use this command: {formatted_roles}")
                    return

                return await func(self, ctx, *args, **kwargs)
            return wrapper
        return decorator 