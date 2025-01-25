from discord.ext import commands
import discord
import random
import json
import re

class EventHandlers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.starboard_cache = {}
        self.starboard_emoji_cache = {}

    #################################
    ## Message Hook
    #################################   
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.guild:
            self.bot.settings.set_server_setting(message.guild.id, "server_name", message.guild.name)

        if self.bot.user.mentioned_in(message) and not any(m in message.content for m in ['@everyone', '@here']):
            if not message.reference and message.type != discord.MessageType.reply:
                try:
                    with open('data/strings.json', 'r') as f:
                        strings = json.load(f)
                        responses = strings['ping_responses']
                        await message.channel.send(random.choice(responses))
                except Exception as e:
                    print(f"Error handling ping response: {e}")

    #################################
    ## Command Error Hook
    #################################   
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("That command doesn't exist.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You can't do that.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("I couldn't find that member.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I can't do that.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide an arg.")
        else:
            await ctx.send(f"An error occurred: {str(error)}")

    #################################
    ## Starboard
    #################################
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.handle_starboard(payload)
    
    #################################
    ## Starboard Remove
    #################################
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.handle_starboard(payload)
        
    #################################
    ## Starboard Handler
    #################################
    async def handle_starboard(self, payload):
        if payload.member and payload.member.bot:
            return
            
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
            
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return
            
        server_config = self.bot.settings.get_all_server_settings(payload.guild_id)
            
        starboard_channel_id = server_config.get('starboard_channel')
        threshold = server_config.get('starboard_threshold', 3)
        
        if not starboard_channel_id:
            return
            
        starboard_channel = channel.guild.get_channel(int(starboard_channel_id))
        if not starboard_channel:
            return
            
        valid_emojis = ['⭐', '🌟', '✨', '🔥']
        
        if str(payload.emoji) not in valid_emojis:
            return
            
        for emoji in valid_emojis:
            reaction = discord.utils.get(message.reactions, emoji=emoji)
            if reaction:
                star_count = reaction.count
                active_emoji = emoji
                break
        else:
            return
            
        existing_star_message_id = self.starboard_cache.get(message.id)
        
        if star_count < threshold and not existing_star_message_id:
            return
            
        if star_count < threshold and existing_star_message_id:
            try:
                star_message = await starboard_channel.fetch_message(existing_star_message_id)
                await star_message.delete()
                self.starboard_cache.pop(message.id, None)
            except:
                pass
            return
            
        embed = discord.Embed(
            description=message.content or "*No text content*",
            color=0xFFAC33,
            timestamp=message.created_at
        )
        embed.add_field(name="", value=f"[Jump to message]({message.jump_url})")
        embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
        embed.set_footer(text=f"ID: {message.id}")
        
        if message.attachments and message.attachments[0].content_type.startswith('image/'):
            embed.set_image(url=message.attachments[0].url)
        elif message.embeds and any(e.provider and e.provider.name == "Tenor" for e in message.embeds):
            tenor_embed = next(e for e in message.embeds if e.provider and e.provider.name == "Tenor")
            if tenor_embed.thumbnail and tenor_embed.thumbnail.url:
                tenor_match = re.match(r'^https://media\.tenor\.com/([a-zA-Z0-9_-]+)e/[a-zA-Z0-9_-]+\.png$', tenor_embed.thumbnail.url)
                if tenor_match:
                    gif_url = f"https://c.tenor.com/{tenor_match.group(1)}C/tenor.gif"
                    embed.set_image(url=gif_url)
        elif message.content:
            cdn_match = re.search(r'https?://(?:cdn|media)\.discordapp\.(?:com|net)/attachments/\d+/\d+/[^\s]+(?:\.gif|\.png|\.jpg|\.jpeg|\.webp)', message.content)
            if cdn_match:
                embed.set_image(url=cdn_match.group(0))
        
        content = f"{active_emoji} **{star_count}** {message.channel.mention}"
        
        try:
            if existing_star_message_id:
                star_message = await starboard_channel.fetch_message(existing_star_message_id)
                await star_message.edit(content=content, embed=embed)
            else:
                star_message = await starboard_channel.send(content=content, embed=embed)
                self.starboard_cache[message.id] = star_message.id
        except Exception as e:
            print(f"Error handling starboard message: {e}")

async def setup(bot):
    await bot.add_cog(EventHandlers(bot)) 