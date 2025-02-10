from datetime import datetime, timedelta
import re
from typing import Tuple, Optional

class TimeParser:
    TIME_REGEX = re.compile(r'(\d+)([wdhms])')
    TIME_UNITS = {
        'w': 7 * 24 * 60 * 60,
        'd': 24 * 60 * 60,
        'h': 60 * 60,
        'm': 60,
        's': 1
    }
    
    @classmethod
    def parse_time_string(cls, time_str: str) -> Optional[int]:
        """
        Parse a time string into seconds
        Example: '1d2h30m' -> 95400 (seconds)
        """
        if not time_str:
            return None
            
        total_seconds = 0
        matches = cls.TIME_REGEX.findall(time_str.lower())
        
        if not matches:
            return None
            
        for value, unit in matches:
            try:
                total_seconds += int(value) * cls.TIME_UNITS[unit]
            except (ValueError, KeyError):
                return None
                
        return total_seconds

    @classmethod
    def format_duration(cls, seconds: int) -> str:
        """
        Format a duration in seconds to a human readable string
        Example: 95400 -> '1d 2h 30m'
        """
        if seconds < 60:
            return f"{seconds}s"
            
        parts = []
        for unit, div in [('d', 86400), ('h', 3600), ('m', 60)]:
            if seconds >= div:
                val = seconds // div
                seconds %= div
                parts.append(f"{val}{unit}")
                
        if seconds > 0:
            parts.append(f"{seconds}s")
            
        return "".join(parts)

    @staticmethod
    def get_future_timestamp(seconds: int) -> Tuple[datetime, str]:
        """
        Get future timestamp and discord timestamp string
        Example: 3600 -> (datetime, '<t:1234567890:R>')
        """
        future = datetime.utcnow() + timedelta(seconds=seconds)
        discord_timestamp = f"<t:{int(future.timestamp())}:R>"
        return future, discord_timestamp 