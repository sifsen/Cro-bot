import discord
from discord.ext import commands
from wand.image import Image
from wand.drawing import Drawing
from wand.color import Color
import io
import aiohttp
import random
import textwrap
import os

class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'fonts', 'impact.ttf')
        
    async def get_image(self, url):
        """Helper function to get image from URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                image_data = await response.read()
                return image_data
                
    @commands.command()
    async def caption(self, ctx, *, text: str = None):
        """Add a white box caption to an image
        Either attach an image or reply to one"""
        
        if not text:
            await ctx.send("You need to provide text for the caption!")
            return
            
        if ctx.message.attachments and ctx.message.attachments[0].content_type.startswith('image/'):
            image_data = await ctx.message.attachments[0].read()
        elif ctx.message.reference:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if ref_msg.attachments and ref_msg.attachments[0].content_type.startswith('image/'):
                image_data = await ref_msg.attachments[0].read()
            else:
                await ctx.send("The replied message doesn't have an image!")
                return
        else:
            await ctx.send("You need to attach an image or reply to a message with an image!")
            return
            
        with Image(blob=image_data) as img:
            font_size = int(img.width / 12)
            font_size = max(40, min(font_size, 120))
            
            padding = 20
            
            with Drawing() as draw:
                draw.font = self.font_path
                draw.font_size = font_size
                draw.text_alignment = 'center'
                draw.fill_color = Color('black')
                
                max_width = img.width - (padding * 2)
                metrics = draw.get_font_metrics(img, text.upper(), multiline=False)
                
                if metrics.text_width > max_width:
                    chars_per_line = int(len(text) * (max_width / metrics.text_width))
                    text = textwrap.fill(text, width=chars_per_line)
                    line_count = len(text.split('\n'))
                else:
                    line_count = 1
                
            caption_height = (font_size * line_count) + (padding * 2)
            
            with Image(width=img.width, height=caption_height, background=Color('white')) as caption:
                with Drawing() as draw:
                    draw.font = self.font_path
                    draw.font_size = font_size
                    draw.text_alignment = 'center'
                    draw.fill_color = Color('black')
                    
                    x = img.width // 2
                    y = int(padding + (font_size * 0.9))
                    draw.text(x, y, text.upper())
                    draw(caption)
                
                with Image(width=img.width, height=img.height + caption_height) as final:
                    final.composite(caption, 0, 0)
                    final.composite(img, 0, caption_height)
                    
                    output = io.BytesIO()
                    final.format = 'png'
                    final.save(output)
                    output.seek(0)
            
        await ctx.send(file=discord.File(output, 'caption.png'))

    @commands.command()
    async def deepfry(self, ctx):
        """Deep fry an image"""
        
        if ctx.message.attachments and ctx.message.attachments[0].content_type.startswith('image/'):
            image_data = await ctx.message.attachments[0].read()
        elif ctx.message.reference:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if ref_msg.attachments and ref_msg.attachments[0].content_type.startswith('image/'):
                image_data = await ref_msg.attachments[0].read()
            else:
                await ctx.send("The replied message doesn't have an image!")
                return
        else:
            await ctx.send("You need to attach an image or reply to a message with an image!")
            return
            
        with Image(blob=image_data) as img:
            img.modulate(brightness=150, saturation=300, hue=random.randint(50, 150))
            img.noise("gaussian", attenuate=0.2)
            img.contrast = True
            img.sharpen(radius=15, sigma=8)
            img.compression_quality = 1
            
            img.noise("impulse", attenuate=0.1)
            img.sharpen(radius=20, sigma=10)
            
            output = io.BytesIO()
            img.format = 'jpeg'
            img.save(output)
            output.seek(0)
            
        await ctx.send(file=discord.File(output, 'deepfried.jpg'))

async def setup(bot):
    await bot.add_cog(Images(bot)) 
