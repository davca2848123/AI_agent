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
            "tokens": {"input": 0, "output": 0},
            "llm_generations": {"local": 0, "gemini": 0},
            "commands_used": {},
            "active_users": [],
            "tools_used": {},
            "knowledge_acquired": [],
            "errors_count": 0,
            "restarts_planned": 0,
            "restarts_unplanned": 0,
            "boredom_actions": 0,
            "report_sent": False,
            "last_save": time.time()
        }
        self.load()
        # self.check_date() - Removed to prevent auto-reset before reporting

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
            "tokens": {"input": 0, "output": 0},
            "llm_generations": {"local": 0, "gemini": 0},
            "commands_used": {},
            "active_users": [],
            "tools_used": {},
            "knowledge_acquired": [],
            "errors_count": 0,
            "restarts_planned": 0,
            "restarts_unplanned": 0,
            "boredom_actions": 0,
            "report_sent": False,
            "last_save": time.time()
        }
        self.save()

    def increment_message(self):
        self.stats["messages_processed"] += 1
        self.save()

    def record_tokens(self, input_count: int, output_count: int):
        if "tokens" not in self.stats:
            self.stats["tokens"] = {"input": 0, "output": 0}
        self.stats["tokens"]["input"] += input_count
        self.stats["tokens"]["output"] += output_count
        self.save()

    def record_llm_generation(self, provider: str):
        if "llm_generations" not in self.stats:
            self.stats["llm_generations"] = {"local": 0, "gemini": 0}
        if provider in self.stats["llm_generations"]:
            self.stats["llm_generations"][provider] += 1
        else:
            self.stats["llm_generations"][provider] = 1
        self.save()

    def record_command(self, command_name: str):
        if "commands_used" not in self.stats:
            self.stats["commands_used"] = {}
        if command_name not in self.stats["commands_used"]:
            self.stats["commands_used"][command_name] = 0
        self.stats["commands_used"][command_name] += 1
        self.save()

    def record_active_user(self, user_id: int):
        if "active_users" not in self.stats:
            self.stats["active_users"] = []
        if user_id not in self.stats["active_users"]:
            self.stats["active_users"].append(user_id)
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

    def increment_planned_restart(self):
        if "restarts_planned" not in self.stats:
            self.stats["restarts_planned"] = 0
        self.stats["restarts_planned"] += 1
        self.save()

    def increment_unplanned_restart(self):
        if "restarts_unplanned" not in self.stats:
            self.stats["restarts_unplanned"] = 0
        self.stats["restarts_unplanned"] += 1
        self.save()
        
    def increment_boredom_action(self):
        if "boredom_actions" not in self.stats:
            self.stats["boredom_actions"] = 0
        self.stats["boredom_actions"] += 1
        self.save()

    def increment_internet_disconnect(self):
        if "internet_disconnects" not in self.stats:
            self.stats["internet_disconnects"] = 0
        self.stats["internet_disconnects"] += 1
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
        
        # User Stats
        active_users_count = len(self.stats.get("active_users", []))
        embed.add_field(name="👥 Active Users", value=str(active_users_count), inline=True)
        
        # Token Stats
        tokens = self.stats.get("tokens", {"input": 0, "output": 0})
        token_str = f"In: {tokens.get('input', 0)}\nOut: {tokens.get('output', 0)}"
        embed.add_field(name="🪙 Tokens", value=token_str, inline=True)
        
        # LLM Generation Stats
        gens = self.stats.get("llm_generations", {"local": 0, "gemini": 0})
        gen_str = f"Local: {gens.get('local', 0)}\nGemini: {gens.get('gemini', 0)}"
        embed.add_field(name="🤖 Generations", value=gen_str, inline=True)
        
        embed.add_field(name="❌ Errors", value=str(self.stats["errors_count"]), inline=True)
        
        # Restarts & Boredom row
        restarts_str = f"Planned: {self.stats.get('restarts_planned', 0)}\nCrashes: {self.stats.get('restarts_unplanned', 0)}"
        embed.add_field(name="🔄 Restarts", value=restarts_str, inline=True)
        embed.add_field(name="🥱 Boredom Actions", value=str(self.stats.get('boredom_actions', 0)), inline=True)
        embed.add_field(name="📡 Disconnects", value=str(self.stats.get('internet_disconnects', 0)), inline=True)
        
        # Tools
        if self.stats["tools_used"]:
            tools_str = "\n".join([f"• {k}: {v}" for k, v in self.stats["tools_used"].items()])
        else:
            tools_str = "No tools used."
        embed.add_field(name="🛠️ Tools Activity", value=tools_str, inline=False)

        # Commands Stats (Top 3)
        commands = self.stats.get("commands_used", {})
        if commands:
            sorted_commands = sorted(commands.items(), key=lambda item: item[1], reverse=True)[:3]
            cmds_str = "\n".join([f"• {k}: {v}" for k, v in sorted_commands])
        else:
            cmds_str = "No commands used."
        embed.add_field(name="⌨️ Top Commands", value=cmds_str, inline=False)
        
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


class DailyStatsLoggingHandler(logging.Handler):
    """
    Custom logging handler that tracks errors in DailyStats.
    """
    def __init__(self, daily_stats: DailyStats):
        super().__init__()
        self.daily_stats = daily_stats

    def emit(self, record):
        if record.levelno >= logging.ERROR:
            # Avoid recursion if saving stats causes an error
            try:
                self.daily_stats.record_error()
            except Exception:
                pass
