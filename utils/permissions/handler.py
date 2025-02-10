from functools import wraps
from discord.ext import commands
from typing import Callable, Any
from config import BOT_MASTERS

class PermissionHandler:
    @staticmethod
    def has_permissions(**permissions: bool) -> Callable:
        """
        A decorator that checks if a user has all the required permissions
        Usage: @PermissionHandler.has_permissions(manage_messages=True)
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(self: Any, ctx: commands.Context, *args: Any, **kwargs: Any) -> Any:
                if str(ctx.author.id) in BOT_MASTERS or ctx.author == ctx.guild.owner:
                    return await func(self, ctx, *args, **kwargs)

                missing_perms = []
                for perm, required in permissions.items():
                    if required and not getattr(ctx.author.guild_permissions, perm, False):
                        formatted_perm = ' '.join(word.capitalize() for word in perm.split('_'))
                        missing_perms.append(formatted_perm)

                if missing_perms:
                    if len(missing_perms) == 1:
                        await ctx.send("You can't do that.")
                    else:
                        perms_list = '`, `'.join(missing_perms)
                        await ctx.send(f"You need the following permissions:\n`{perms_list}`")
                    return None

                return await func(self, ctx, *args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def is_bot_master() -> Callable:
        """Decorator to check if user is a bot master"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(self: Any, ctx: commands.Context, *args: Any, **kwargs: Any) -> Any:
                if str(ctx.author.id) not in BOT_MASTERS:
                    await ctx.send("This command is only available to bot masters.")
                    return None
                return await func(self, ctx, *args, **kwargs)
            return wrapper
        return decorator 