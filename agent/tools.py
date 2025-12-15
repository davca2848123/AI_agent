import os
import logging
import platform
import psutil
import asyncio
import json
import sqlite3
from typing import List, Dict, Any, Callable
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import math as py_math
import config_settings

# Try importing web tools
try:
    from duckduckgo_search import DDGS
    from bs4 import BeautifulSoup
    import aiohttp
    WEB_TOOLS_AVAILABLE = True
except ImportError:
    WEB_TOOLS_AVAILABLE = False

# Try importing additional tools
try:
    import feedparser
    RSS_AVAILABLE = True
except ImportError:
    RSS_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATE_AVAILABLE = True
except ImportError:
    TRANSLATE_AVAILABLE = False

try:
    import wikipediaapi
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False

try:
    from dulwich.repo import Repo
    import dulwich.porcelain
    DULWICH_AVAILABLE = True
except ImportError:
    DULWICH_AVAILABLE = False

logger = logging.getLogger(__name__)

class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        pass
    
    async def _execute_with_logging(self, **kwargs) -> str:
        """Wrapper for execute() with detailed logging and intelligent argument mapping."""
        import time
        start_time = time.time()
        
        # ARGUMENT MAPPING: Handle generic 'query' parameter
        # Map to tool-specific parameters based on tool type
        if 'query' in kwargs and self.name in ['translate_tool', 'math_tool', 'weather_tool', 'file_tool']:
            query_value = kwargs.pop('query')
            
            # Map query to appropriate parameter based on tool
            if self.name == 'translate_tool' and 'text' not in kwargs:
                kwargs['text'] = query_value
            elif self.name == 'math_tool' and 'expression' not in kwargs:
                kwargs['expression'] = query_value
                if 'action' not in kwargs:
                    kwargs['action'] = 'calc'  # Default action
            elif self.name == 'weather_tool' and 'location' not in kwargs:
                kwargs['location'] = query_value
            elif self.name == 'file_tool' and 'filename' not in kwargs:
                # For file_tool, query could be filename for list/read
                kwargs['filename'] = query_value
                if 'action' not in kwargs:
                    kwargs['action'] = 'list_files'  # Default to listing
        
        # Map file_path to filename for file_tool (common hallucination)
        if self.name == 'file_tool' and 'file_path' in kwargs and 'filename' not in kwargs:
            kwargs['filename'] = kwargs.pop('file_path')
        
        # Sanitize kwargs for logging (limit length)
        safe_kwargs = {k: (str(v)[:100] + '...' if len(str(v)) > 100 else v)  
                      for k, v in kwargs.items()}
        
        logger.info(f"{self.name}: Starting with params: {safe_kwargs}")
        
        try:
            result = await self.execute(**kwargs)
            elapsed = time.time() - start_time
            
            # Sanitize result for logging
            result_summary = result[:200] + '...' if len(result) > 200 else result
            is_error = result.startswith("Error:")
            
            if is_error:
                logger.warning(f"{self.name}: Completed in {elapsed:.2f}s - Error: {result_summary}")
            else:
                logger.info(f"{self.name}: Completed in {elapsed:.2f}s - Result: {result_summary}")
            
            return result
        except TypeError as e:
            # Catch unexpected argument errors and provide helpful message
            elapsed = time.time() - start_time
            logger.error(f"{self.name}: Failed after {elapsed:.2f}s - TypeError (likely bad arguments): {e}")
            return f"Error: Tool parameter mismatch. {self.description}"
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{self.name}: Failed after {elapsed:.2f}s - Exception: {type(e).__name__}: {e}")
            return f"Error: {type(e).__name__}: {e}"

class FileTool(Tool):
    def __init__(self, workspace_dir: str = "."):
        # Default to current directory to allow access to project files
        self.workspace_dir = os.path.abspath(workspace_dir)
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)

    @property
    def name(self) -> str:
        return "file_tool"

    @property
    def description(self) -> str:
        return "Read/write/list files. Args: action='read'|'write'|'list_files', filename='...', content='...'"

    async def execute(self, action: str, filename: str = None, content: str = None, **kwargs) -> str:
        # Security check: Ensure path is within workspace (which is now root)
        # For 'list_files', filename is optional (defaults to .)
        target_path = filename or "."
        safe_path = os.path.abspath(os.path.join(self.workspace_dir, target_path))
        
        if not safe_path.startswith(self.workspace_dir):
            return "Error: Access denied. Can only access files in project directory."

        try:
            if action == "read":
                if not filename: return "Error: Filename required for read."
                if not os.path.exists(safe_path):
                    return "Error: File not found."
                if os.path.isdir(safe_path):
                    return "Error: Path is a directory, use list_files."
                with open(safe_path, "r", encoding="utf-8") as f:
                    return f.read()
            
            elif action == "write":
                if not filename: return "Error: Filename required for write."
                if content is None:
                    return "Error: Content required for write."
                with open(safe_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"File '{filename}' written successfully."
            
            elif action == "list_files":
                if not os.path.exists(safe_path):
                    return "Error: Path not found."
                if not os.path.isdir(safe_path):
                    return "Error: Path is not a directory."
                
                items = os.listdir(safe_path)
                # Filter out hidden files/dirs and common ignore dirs
                items = [i for i in items if not i.startswith('.') and i not in ['__pycache__', 'venv', 'node_modules']]
                
                result = f"Files in '{target_path}':\n"
                for item in sorted(items):
                    item_path = os.path.join(safe_path, item)
                    if os.path.isdir(item_path):
                        result += f"📁 {item}/\n"
                    else:
                        size = os.path.getsize(item_path)
                        result += f"📄 {item} ({size} bytes)\n"
                return result
            
            else:
                return "Error: Unknown action. Use 'read', 'write', or 'list_files'."
        except Exception as e:
            return f"Error: {e}"

class SystemTool(Tool):
    @property
    def name(self) -> str:
        return "system_tool"

    @property
    def description(self) -> str:
        return "System info (CPU/RAM/Disk). Args: action='info'|'process_list'"

    async def execute(self, action: str = "info", **kwargs) -> str:
        if action == "info":
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            return f"System Info:\nOS: {platform.system()} {platform.release()}\nCPU Usage: {cpu}%\nRAM Usage: {ram}%\nDisk Usage: {disk}%"
        elif action == "process_list":
            # Limit to top 5 by memory to avoid flooding context
            procs = sorted(psutil.process_iter(['name', 'memory_percent']), key=lambda p: p.info['memory_percent'], reverse=True)[:5]
            return "Top 5 Processes:\n" + "\n".join([f"{p.info['name']}: {p.info['memory_percent']:.1f}%" for p in procs])
        else:
            return "Error: Unknown action."

class WebTool(Tool):
    def __init__(self, agent=None):
        self.agent = agent

    @property
    def name(self) -> str:
        return "web_tool"

    @property
    def description(self) -> str:
        return "Search/read web. Args: action='search'|'read', query='...', url='...'"

    async def execute(self, **kwargs) -> str:
        if not WEB_TOOLS_AVAILABLE:
            return "Error: Web tools dependencies not installed."
        
        # Extract arguments safely
        action = kwargs.get('action')
        query = kwargs.get('query')
        url = kwargs.get('url')
        limit = kwargs.get('limit', 1000)

        # Infer action if not provided
        if not action:
            if url:
                action = "read"
            elif query:
                action = "search"
            else:

                # Default behavior: Search for something interesting
                action = "search"
                import random
                import json
                
                # Try to load topics from file
                try:
                    topics_file = getattr(config_settings, 'TOPICS_FILE', 'boredom_topics.json')
                    if os.path.exists(topics_file):
                         with open(topics_file, 'r', encoding='utf-8') as f:
                            topics = json.load(f)
                    else:
                        topics = []
                except Exception as e:
                    logger.warning(f"WebTool: Failed to load topics from file: {e}")
                    topics = []
                
                # Fallback to defaults if file topics are missing or empty
                if not topics:
                    topics = ["latest AI news", "Raspberry Pi projects", "Python programming tips", "SpaceX news", "scientific discoveries"]
                
                query = random.choice(topics)
                logger.info(f"WebTool: Missing arguments. Defaulting to search for: '{query}'")

        # Filter out unexpected arguments (e.g., 'site')
        if kwargs:
            logger.debug(f"web_tool: Ignoring unexpected arguments: {list(kwargs.keys())}")

        try:
            if action == "search":
                if not query: return "Error: Query required."
                
                # Use native query without appended filters to get broad results
                # We fetch more results (10) and filter them client-side to ensure quality
                raw_results = DDGS().text(query, max_results=10)
                
                filtered_results = []
                import re
                
                # Regex to detect CJK (Chinese, Japanese, Korean) characters
                # ranges: 4E00-9FFF (Common), 3400-4DBF (Ext A), 20000-2A6DF (Ext B), ...
                # Simplified check for common ranges
                cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]')
                
                for r in raw_results:
                    title = r.get('title', '')
                    body = r.get('body', '')
                    text_content = title + " " + body
                    
                    # 1. Reject if contains CJK characters (Asian spam filter)
                    if cjk_pattern.search(text_content):
                        continue
                        
                    # 2. Prefer Latin script (European/American)
                    # Check if at least 50% of characters are ASCII/Latin (approximate)
                    # This avoids Russian/Arabic only results if not desired, though user said "European" which includes Cyrillic.
                    # User said "European and American", implying mostly Latin/Cyrillic. 
                    # For now, the CJK rejection is the strongest signal against the spam we saw.
                    
                    filtered_results.append(r)
                    if len(filtered_results) >= 3:
                        break
                
                output = f"Search Results (Query: {query}):\n"
                if not filtered_results:
                    # If strict filtering killed everything, fallback to raw top 3 but warn
                    # Or just return empty to force agent to try different query
                    # Let's return raw first result if available as last resort, or empty
                    if raw_results and not filtered_results:
                         output += "(No European/American matches found, showing best raw result)\n"
                         filtered_results = [raw_results[0]]
                    else:
                         output += "(No results found)\n"
                    
                for i, r in enumerate(filtered_results, 1):
                    output += f"\n{i}. {r['title']}\n"
                    output += f"   URL: {r['href']}\n"
                    output += f"   {r.get('body', 'No description available')}\n"
                return output
            
            elif action == "read":
                if not url: return "Error: URL required."
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as resp:
                        if resp.status != 200: return f"Error: HTTP {resp.status}"
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        # Extract text and limit length
                        text = soup.get_text(separator=' ', strip=True)
                        
                        # Store in memory if agent is available
                        if self.agent:
                            try:
                                logger.info(f"WebTool: Processing content from {url} for memory...")
                                # We pass the full text (or a larger chunk) to the filter
                                # The filter will extract the "core, factual information"
                                await self.agent.add_filtered_memory(
                                    content=text[:5000], # Pass reasonable amount for LLM
                                    metadata={
                                        'type': 'web_knowledge',
                                        'source': url,
                                        'title': soup.title.string if soup.title else 'Webpage'
                                    }
                                )
                            except Exception as e:
                                logger.error(f"WebTool: Failed to process memory: {e}")
                        
                        return text[:limit] + ("..." if len(text) > limit else "") # Limit context
            else:
                return "Error: Unknown action."
        except Exception as e:
            return f"Error: {e}"

class TimeTool(Tool):
    @property
    def name(self) -> str:
        return "time_tool"

    @property
    def description(self) -> str:
        return "Current time/diff. Args: action='now'|'diff', time1='...', time2='...'"

    async def execute(self, action: str = "now", format_str: str = None, time1: str = None, time2: str = None, **kwargs) -> str:
        try:
            if action == "now":
                now = datetime.now()
                fmt = format_str or "%Y-%m-%d %H:%M:%S"
                return f"Current time: {now.strftime(fmt)}"
            
            elif action == "format":
                now = datetime.now()
                fmt = format_str or "%A, %B %d, %Y at %I:%M %p"
                return now.strftime(fmt)
            
            elif action == "diff":
                # Simple time difference (expects ISO format)
                if not time1 or not time2:
                    return "Error: Both time1 and time2 required"
                t1 = datetime.fromisoformat(time1)
                t2 = datetime.fromisoformat(time2)
                diff = abs((t2 - t1).total_seconds())
                hours = int(diff // 3600)
                minutes = int((diff % 3600) // 60)
                return f"Time difference: {hours}h {minutes}m"
            
            else:
                return "Error: Unknown action"
        except Exception as e:
            return f"Error: {e}"

class MathTool(Tool):
    @property
    def name(self) -> str:
        return "math_tool"

    @property
    def description(self) -> str:
        return "Calc/convert. Args: action='calc'|'convert', expression='...', value='...', unit='...', to_unit='...'"

    async def execute(self, action: str, expression: str = None, value: float = None, unit: str = None, to_unit: str = None, base: float = None, exponent: float = None, **kwargs) -> str:
        try:
            if action == "calc":
                if not expression:
                    return "Error: Expression required"
                # Safe eval with limited scope
                allowed = {"abs": abs, "round": round, "min": min, "max": max, "sum": sum,
                          "sqrt": py_math.sqrt, "sin": py_math.sin, "cos": py_math.cos, "tan": py_math.tan}
                result = eval(expression, {"__builtins__": {}}, allowed)
                return f"Result: {result}"
            
            elif action == "sqrt":
                if value is None:
                    return "Error: Value required"
                return f"sqrt({value}) = {py_math.sqrt(value)}"
            
            elif action == "pow":
                if base is None or exponent is None:
                    return "Error: Base and exponent required"
                return f"{base}^{exponent} = {pow(base, exponent)}"
            
            elif action == "convert":
                # Simple temperature conversion
                if not value or not unit or not to_unit:
                    return "Error: value, unit, and to_unit required"
                
                if unit == "C" and to_unit == "F":
                    result = (value * 9/5) + 32
                    return f"{value}°C = {result:.2f}°F"
                elif unit == "F" and to_unit == "C":
                    result = (value - 32) * 5/9
                    return f"{value}°F = {result:.2f}°C"
                else:
                    return "Error: Only C<->F conversion supported"
            
            else:
                return "Error: Unknown action"
        except Exception as e:
            return f"Error: {e}"

class WeatherTool(Tool):
    @property
    def name(self) -> str:
        return "weather_tool"

    @property
    def description(self) -> str:
        return "Get weather. Args: location='...'"

    async def execute(self, location: str = None, **kwargs) -> str:
        # Use DEFAULT_LOCATION from config if no location specified
        if location is None:
            location = config_settings.DEFAULT_LOCATION
        
        try:
            # Use wttr.in - free, no API key needed
            url = f"http://wttr.in/{location}?format=%l:+%C+%t+%h+%w"
            # Increased timeout to 30s as wttr.in can be slow
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return f"Error: HTTP {resp.status} - Weather service unavailable"
                    text = await resp.text()
                    if not text or not text.strip():
                        return "Error: Weather service returned empty response"
                    return f"Weather: {text.strip()}"
        except asyncio.TimeoutError:
            return f"Error: Weather service timeout - try again later"
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e) or 'Unknown error'}"

class CodeTool(Tool):
    @property
    def name(self) -> str:
        return "code_tool"

    @property
    def description(self) -> str:
        return "Run Python code. Args: code='...'"

    async def execute(self, code: str = None, **kwargs) -> str:
        if not code:
            return "Error: Code required"
        
        try:
            # Very restricted sandbox
            safe_globals = {
                "__builtins__": {
                    "print": print, "len": len, "range": range, "str": str,
                    "int": int, "float": float, "list": list, "dict": dict,
                    "sum": sum, "max": max, "min": min, "abs": abs
                }
            }
            
            # Capture output
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            
            try:
                exec(code, safe_globals, {})
                output = buffer.getvalue()
            finally:
                sys.stdout = old_stdout
            
            return f"Output:\n{output if output else '(no output)'}"
        except Exception as e:
            return f"Error: {e}"

class NoteTool(Tool):
    def __init__(self, notes_file: str = "workspace/notes.json"):
        # Ensure absolute path
        self.notes_file = os.path.abspath(notes_file)
        os.makedirs(os.path.dirname(self.notes_file), exist_ok=True)
        if not os.path.exists(self.notes_file):
            with open(self.notes_file, 'w') as f:
                json.dump([], f)

    @property
    def name(self) -> str:
        return "note_tool"

    @property
    def description(self) -> str:
        return "Manage notes. Args: action='add'|'list'|'search', content='...'"

    async def execute(self, action: str, content: str = None, tag: str = None, **kwargs) -> str:
        try:
            with open(self.notes_file, 'r') as f:
                notes = json.load(f)
            
            if action == "add":
                if not content:
                    return "Error: Content required"
                note = {
                    "id": len(notes) + 1,
                    "content": content,
                    "tag": tag or "general",
                    "timestamp": datetime.now().isoformat()
                }
                notes.append(note)
                with open(self.notes_file, 'w') as f:
                    json.dump(notes, f, indent=2)
                return f"Note added (ID: {note['id']})"
            
            elif action == "list":
                if not notes:
                    return "No notes found"
                return "\n".join([f"[{n['id']}] ({n['tag']}) {n['content'][:50]}..." for n in notes[-10:]])
            
            elif action == "search":
                if not content:
                    return "Error: Search query required"
                found = [n for n in notes if content.lower() in n['content'].lower()]
                if not found:
                    return "No matching notes"
                return "\n".join([f"[{n['id']}] {n['content']}" for n in found[:5]])
            
            else:
                return "Error: Unknown action"
        except Exception as e:
            return f"Error: {e}"

class GitTool(Tool):
    @property
    def name(self) -> str:
        return "git_tool"

    @property
    def description(self) -> str:
        return "Git status/log. Args: action='status'|'log'"

    async def execute(self, action: str = "status", repo_path: str = ".", **kwargs) -> str:
        if not DULWICH_AVAILABLE:
            return "Error: dulwich not installed"
        
        try:
            # Check if repo exists
            try:
                Repo(repo_path)
            except:
                return f"Error: No git repository found at {repo_path}"

            import io
            output = io.StringIO()
            
            if action == "status":
                dulwich.porcelain.status(repo=repo_path, outstream=output)
                return output.getvalue() or "No changes."
            
            elif action == "log":
                dulwich.porcelain.log(repo=repo_path, max_entries=5, outstream=output)
                return output.getvalue()
            
            else:
                return "Error: Unknown action"
        except Exception as e:
            return f"Error: {e}"

class DatabaseTool(Tool):
    def __init__(self, db_path: str = "workspace/agent.db"):
        # Ensure absolute path
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @property
    def name(self) -> str:
        return "database_tool"

    @property
    def description(self) -> str:
        return "SQLite SELECT. Args: query='...'"

    async def execute(self, query: str = None, **kwargs) -> str:
        if not query:
            return "Error: Query required"
        
        # Only allow SELECT queries for safety
        if not query.strip().upper().startswith("SELECT"):
            return "Error: Only SELECT queries allowed"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return "No results"
            
            return "\n".join([str(row) for row in rows[:10]])
        except Exception as e:
            return f"Error: {e}"

class RSSTool(Tool):
    @property
    def name(self) -> str:
        return "rss_tool"

    @property
    def description(self) -> str:
        return "Read RSS. Args: url='...'"

    async def execute(self, url: str = None, **kwargs) -> str:
        if not RSS_AVAILABLE:
            return "Error: feedparser not installed"
        
        if not url:
            return "Error: URL required"
        
        try:
            # Use run_in_executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            if not feed.entries:
                return "No entries found"
            
            result = f"Feed: {feed.feed.get('title', 'Unknown')}\n\n"
            for entry in feed.entries[:5]:
                result += f"• {entry.get('title', 'No title')}\n"
                result += f"  {entry.get('link', '')}\n\n"
            
            return result
        except Exception as e:
            return f"Error: {e}"

class TranslateTool(Tool):
    @property
    def name(self) -> str:
        return "translate_tool"

    @property
    def description(self) -> str:
        return "Translate. Args: text='...', source='auto', target='en'"

    async def execute(self, text: str = None, source: str = "auto", target: str = "en", **kwargs) -> str:
        if not TRANSLATE_AVAILABLE:
            return "Error: deep-translator not installed"
        
        if not text:
            return "Error: Text required"
        
        try:
            translator = GoogleTranslator(source=source, target=target)
            result = translator.translate(text)
            return f"Translation ({source}->{target}): {result}"
        except Exception as e:
            return f"Error: {e}"

class WikipediaTool(Tool):
    @property
    def name(self) -> str:
        return "wikipedia_tool"

    @property
    def description(self) -> str:
        return "Search Wikipedia. Args: query='...', lang='en'"

    async def execute(self, query: str = None, lang: str = "en", **kwargs) -> str:
        if not WIKIPEDIA_AVAILABLE:
            return "Error: wikipedia-api not installed"
        
        if not query:
            return "Error: Query required"
        
        try:
            wiki = wikipediaapi.Wikipedia('RpiAI/1.0 (bot@example.com)', lang)
            page = wiki.page(query)
            
            if not page.exists():
                return f"No Wikipedia page found for '{query}'"
            
            # Return summary (first 500 chars)
            summary = page.summary[:500]
            return f"Wikipedia: {page.title}\n\n{summary}...\n\nURL: {page.fullurl}"
        except Exception as e:
            return f"Error: {e}"

class DiscordActivityTool(Tool):
    def __init__(self, agent):
        self.agent = agent

    @property
    def name(self) -> str:
        return "discord_activity_tool"

    @property
    def description(self) -> str:
        return "Check Discord activities. No args."

    async def execute(self, **kwargs) -> str:
        if not self.agent.network_monitor.is_online:
            return "Error: No internet connection. Cannot check activities or research them."

        if not self.agent.discord.is_ready:
            return "Error: Discord client is not ready."

        try:
            activities = await self.agent.discord.get_online_activities()
            
            # Filter ignored users
            import config_settings
            ignored_users = getattr(config_settings, 'DISCORD_ACTIVITY_IGNORE_USERS', [])
            
            filtered_activities = []
            for act in activities:
                user_id = act.get('user_id')
                try:
                    user_id_int = int(user_id) if user_id else 0
                except:
                    user_id_int = 0
                    
                if user_id_int not in ignored_users:
                    filtered_activities.append(act)
            
            if not filtered_activities:
                return "No users are currently performing any public activities."
            
            # Process activities to ensure learning
            for activity in filtered_activities:
                asyncio.create_task(self.agent._process_activity(activity))
            
            # Format output
            output = "Current User Activities:\n"
            for act in filtered_activities:
                output += f"- {act['user_name']} is playing/doing: {act['name']}\n"
            
            return output
        except Exception as e:
            return f"Error checking activities: {e}"

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.usage_stats: Dict[str, int] = {}
        
    def register(self, tool: Tool):
        self.tools[tool.name] = tool
        self.usage_stats[tool.name] = 0
        logger.info(f"Registered tool: {tool.name}")
        
    def get_tool(self, name: str) -> Tool:
        return self.tools.get(name)
    
    def increment_usage(self, name: str):
        if name in self.usage_stats:
            self.usage_stats[name] += 1
            
    def get_usage_stats(self) -> Dict[str, int]:
        return self.usage_stats
        
    def get_descriptions(self) -> str:
        return "\n".join([f"- {t.name}: {t.description}" for t in self.tools.values()])
