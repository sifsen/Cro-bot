import re
from typing import List, Dict, Any
import discord

class TextFormatter:
    @staticmethod
    def truncate(text: str, max_length: int = 2000) -> str:
        """Truncate text to max_length, accounting for markdown"""
        if len(text) <= max_length:
            return text
            
        truncated = text[:max_length-3] + "..."
        
        unclosed_bold = truncated.count('**') % 2
        unclosed_italic = truncated.count('*') % 2
        unclosed_code = truncated.count('`') % 2
        
        if unclosed_bold:
            truncated += "**"
        if unclosed_italic:
            truncated += "*"
        if unclosed_code:
            truncated += "`"
            
        return truncated

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean text of mentions and markdown"""
        text = discord.utils.escape_mentions(text)
        text = discord.utils.escape_markdown(text)
        return text

    @staticmethod
    def parse_flags(text: str) -> Dict[str, Any]:
        """Parse command flags from text
        Example: 'hello --user @someone --contains test' ->
        {'user': '@someone', 'contains': 'test'}
        """
        flags = {}
        current_flag = None
        parts = text.split()
        
        for part in parts:
            if part.startswith('--'):
                current_flag = part[2:]
                flags[current_flag] = True
            elif current_flag:
                if flags[current_flag] is True:
                    flags[current_flag] = part
                else:
                    flags[current_flag] = f"{flags[current_flag]} {part}"
                    
        return flags

class EmbedBuilder:
    def __init__(self, title=None, description=None, color=None):
        self.embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )

    def add_field(self, name: str, value: str, inline: bool = True) -> 'EmbedBuilder':
        """Add a field to the embed"""
        if value:
            self.embed.add_field(
                name=name,
                value=TextFormatter.truncate(str(value), 1024),
                inline=inline
            )
        return self

    def set_author(self, name: str, icon_url: str = None) -> 'EmbedBuilder':
        """Set the author of the embed"""
        self.embed.set_author(name=name, icon_url=icon_url)
        return self

    def set_footer(self, text: str, icon_url: str = None) -> 'EmbedBuilder':
        """Set the footer of the embed"""
        self.embed.set_footer(text=text, icon_url=icon_url)
        return self

    def set_thumbnail(self, url: str) -> 'EmbedBuilder':
        """Set the thumbnail of the embed"""
        self.embed.set_thumbnail(url=url)
        return self

    def build(self) -> discord.Embed:
        """Return the built embed"""
        return self.embed