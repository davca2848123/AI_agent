import json
import time
import os
import logging
import datetime
from typing import Dict, List, Any
import discord

logger = logging.getLogger(__name__)

class DailyStats:
    def __init__(self, filepath: str = "daily_stats.json"):
        self.filepath = filepath
        self.stats = {
            "date": datetime.date.today().isoformat(),
            "uptime_seconds": 0,
            "messages_processed": 0,
            "tools_used": {},
            "knowledge_acquired": [],
            "errors_count": 0,
            "report_sent": False,
            "last_save": time.time()
        }
        self.load()
        self.check_date()

    def load(self):
        """Loads stats from file if it exists."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats.update(data)
                logger.info("Daily stats loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load daily stats: {e}")

    def save(self):
        """Saves current stats to file."""
        try:
            self.stats["last_save"] = time.time()
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save daily stats: {e}")

    def check_date(self):
        """Checks if date changed, if so, resets stats (unless report wasn't sent?).
        Actually, we want to reset ONLY after report is sent or if it's a new day and we don't care about old report?
        The user wants report at 23:59. So fast forward to next day 00:00 -> new stats.
        If we restart at 10:00 next day, we should probably start fresh if date mismatch.
        """
        current_date = datetime.date.today().isoformat()
        if self.stats["date"] != current_date:
            logger.info(f"Date changed ({self.stats['date']} -> {current_date}). Resetting stats.")
            self._reset_stats(current_date)

    def _reset_stats(self, new_date: str):
        self.stats = {
            "date": new_date,
            "uptime_seconds": 0,
            "messages_processed": 0,
            "tools_used": {},
            "knowledge_acquired": [],
            "errors_count": 0,
            "report_sent": False,
            "last_save": time.time()
        }
        self.save()

    def increment_message(self):
        self.stats["messages_processed"] += 1
        self.save()

    def record_tool_usage(self, tool_name: str):
        if tool_name not in self.stats["tools_used"]:
            self.stats["tools_used"][tool_name] = 0
        self.stats["tools_used"][tool_name] += 1
        self.save()

    def record_knowledge(self, knowledge: str):
        if knowledge not in self.stats["knowledge_acquired"]:
            self.stats["knowledge_acquired"].append(knowledge)
            self.save()

    def record_error(self):
        self.stats["errors_count"] += 1
        self.save()
    
    def add_uptime(self, seconds: float):
        self.stats["uptime_seconds"] += int(seconds)
        # Don't save on every uptime tick, expensive. Save externally or periodically.

    def generate_report_embed(self) -> discord.Embed:
        """Generates a Discord Embed for the daily report."""
        
        # Calculate uptime string
        uptime_sec = self.stats["uptime_seconds"]
        hours = uptime_sec // 3600
        minutes = (uptime_sec % 3600) // 60
        uptime_str = f"{hours}h {minutes}m"

        embed = discord.Embed(
            title=f"📅 Daily Report: {self.stats['date']}",
            color=0x00ff00, # Green
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="⏱️ Uptime", value=uptime_str, inline=True)
        embed.add_field(name="📩 Messages", value=str(self.stats["messages_processed"]), inline=True)
        embed.add_field(name="❌ Errors", value=str(self.stats["errors_count"]), inline=True)
        
        # Tools
        if self.stats["tools_used"]:
            tools_str = "\n".join([f"• {k}: {v}" for k, v in self.stats["tools_used"].items()])
        else:
            tools_str = "No tools used."
        embed.add_field(name="🛠️ Tools Activity", value=tools_str, inline=False)
        
        # Knowledge
        if self.stats["knowledge_acquired"]:
            # Limit to last 5 or summary if too long
            knowledge_list = self.stats["knowledge_acquired"]
            if len(knowledge_list) > 10:
                knowledge_str = "\n".join([f"• {k}" for k in knowledge_list[:10]]) + f"\n...and {len(knowledge_list)-10} more."
            else:
                knowledge_str = "\n".join([f"• {k}" for k in knowledge_list])
        else:
            knowledge_str = "No new major knowledge acquired."
        embed.add_field(name="🧠 Knowledge Acquired", value=knowledge_str, inline=False)
        
        return embed

    @property
    def report_sent_today(self) -> bool:
        return self.stats["report_sent"]

    def mark_report_sent(self):
        self.stats["report_sent"] = True
        self.save()
