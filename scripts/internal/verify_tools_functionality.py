import unittest
import asyncio
import os
import sys
import shutil
import json
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path (scripts/internal/ -> ../.. -> rpi_ai)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.tools import (
    FileTool, SystemTool, TimeTool, MathTool, WebTool, WeatherTool,
    CodeTool, NoteTool, GitTool, DatabaseTool, RSSTool, TranslateTool,
    WikipediaTool, DiscordActivityTool
)
import agent.tools

import unittest
import asyncio
import os
import sys
import shutil
import json
from unittest.mock import MagicMock, patch, mock_open, AsyncMock

# Add project root to path (scripts/internal/ -> ../.. -> rpi_ai)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent.tools import (
    FileTool, SystemTool, TimeTool, MathTool, WebTool, WeatherTool,
    CodeTool, NoteTool, GitTool, DatabaseTool, RSSTool, TranslateTool,
    WikipediaTool, DiscordActivityTool
)
import agent.tools

class TestToolsFunctionality(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Use a temp dir within the project to avoid permission issues, but ensure cleanup
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'temp_test_workspace'))
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    # 1. FileTool
    async def test_file_tool(self):
        tool = FileTool(workspace_dir=self.test_dir)
        
        # Write
        res = await tool.execute(action="write", filename="test.txt", content="Hello")
        self.assertIn("written successfully", res)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "test.txt")))
        
        # Read
        res = await tool.execute(action="read", filename="test.txt")
        self.assertEqual(res, "Hello")
        
        # List
        res = await tool.execute(action="list_files")
        self.assertIn("test.txt", res)

    # 2. SystemTool
    async def test_system_tool(self):
        tool = SystemTool()
        res = await tool.execute(action="info")
        self.assertIn("CPU Usage", res)
        self.assertIn("RAM Usage", res)

    # 3. TimeTool
    async def test_time_tool(self):
        tool = TimeTool()
        res = await tool.execute(action="now")
        self.assertIn("Current time", res)
        
        res = await tool.execute(action="diff", time1="2023-01-01T12:00:00", time2="2023-01-01T14:30:00")
        self.assertIn("2h 30m", res)

    # 4. MathTool
    async def test_math_tool(self):
        tool = MathTool()
        res = await tool.execute(action="calc", expression="2 + 2")
        self.assertIn("4", res)
        
        res = await tool.execute(action="sqrt", value=16)
        self.assertIn("4.0", res)

    # 5. WebTool
    async def test_web_tool_search(self):
        # Force mock DDGS
        agent.tools.DDGS = MagicMock()
        
        # Mock DDGS instance
        mock_ddgs_instance = agent.tools.DDGS.return_value
        mock_ddgs_instance.text.return_value = [{'title': 'Test', 'href': 'http://test.com', 'body': 'Content'}]
        
        tool = WebTool()
        # Force available
        with patch('agent.tools.WEB_TOOLS_AVAILABLE', True):
            res = await tool.execute(action="search", query="test")
            self.assertIn("Test", res)
            self.assertIn("http://test.com", res)

    # 6. WeatherTool
    async def test_weather_tool(self):
        # Force mock aiohttp
        agent.tools.aiohttp = MagicMock()
            
        # Mock response
        mock_resp = MagicMock()
        mock_resp.status = 200
        # Use AsyncMock for awaitable text()
        mock_resp.text = AsyncMock(return_value="Sunny +25C")
        
        mock_ctx = MagicMock()
        mock_ctx.__aenter__.return_value = mock_resp
        mock_ctx.__aexit__.return_value = None
        
        # Mock ClientSession
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get.return_value = mock_ctx
        
        agent.tools.aiohttp.ClientSession.return_value = mock_session

        tool = WeatherTool()
        res = await tool.execute(location="Prague")
        self.assertIn("Sunny +25C", res)

    # 7. CodeTool
    async def test_code_tool(self):
        tool = CodeTool()
        res = await tool.execute(code="print(2+3)")
        self.assertIn("5", res)

    # 8. NoteTool
    async def test_note_tool(self):
        notes_file = os.path.join(self.test_dir, "notes.json")
        tool = NoteTool(notes_file=notes_file)
        
        res = await tool.execute(action="add", content="Remember this")
        self.assertIn("Note added", res)
        
        res = await tool.execute(action="list")
        self.assertIn("Remember this", res)

    # 9. GitTool
    async def test_git_tool(self):
        # Force mocks
        agent.tools.dulwich = MagicMock()
        agent.tools.Repo = MagicMock()
            
        tool = GitTool()
        # Force available
        with patch('agent.tools.DULWICH_AVAILABLE', True):
            # Mock status
            agent.tools.dulwich.porcelain.status = MagicMock()
            
            res = await tool.execute(action="status")
            self.assertIn("No changes", res)

    # 10. DatabaseTool
    async def test_database_tool(self):
        db_path = os.path.join(self.test_dir, "test.db")
        tool = DatabaseTool(db_path=db_path)
        
        # Create dummy table for test (DatabaseTool only allows SELECT, so we need to setup first)
        import sqlite3
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("CREATE TABLE test (id int, name text)")
        c.execute("INSERT INTO test VALUES (1, 'Alice')")
        conn.commit()
        conn.close()
        
        res = await tool.execute(query="SELECT * FROM test")
        self.assertIn("(1, 'Alice')", res)

    # 11. RSSTool
    async def test_rss_tool(self):
        # Force mock feedparser
        agent.tools.feedparser = MagicMock()
            
        mock_feed = MagicMock()
        mock_feed.feed.get.return_value = "Test Feed"
        # Ensure entries is a list
        mock_feed.entries = [{'title': 'News 1', 'link': 'http://news.com/1'}]
        
        agent.tools.feedparser.parse.return_value = mock_feed
        
        tool = RSSTool()
        with patch('agent.tools.RSS_AVAILABLE', True):
            res = await tool.execute(url="http://feed.com")
            self.assertIn("Test Feed", res)
            self.assertIn("News 1", res)

    # 12. TranslateTool
    async def test_translate_tool(self):
        # Force mock GoogleTranslator
        agent.tools.GoogleTranslator = MagicMock()
            
        mock_instance = agent.tools.GoogleTranslator.return_value
        mock_instance.translate.return_value = "Ahoj"
        
        tool = TranslateTool()
        with patch('agent.tools.TRANSLATE_AVAILABLE', True):
            res = await tool.execute(text="Hello", target="cs")
            self.assertIn("Ahoj", res)

    # 13. WikipediaTool
    async def test_wikipedia_tool(self):
        # Force mock wikipediaapi
        agent.tools.wikipediaapi = MagicMock()
            
        mock_wiki = agent.tools.wikipediaapi.Wikipedia.return_value
        mock_page = MagicMock()
        mock_page.exists.return_value = True
        mock_page.title = "Python"
        mock_page.summary = "Python is a language."
        mock_page.fullurl = "http://wiki/Python"
        mock_wiki.page.return_value = mock_page
        
        tool = WikipediaTool()
        with patch('agent.tools.WIKIPEDIA_AVAILABLE', True):
            res = await tool.execute(query="Python")
            self.assertIn("Python is a language", res)

    # 14. DiscordActivityTool
    async def test_discord_activity_tool(self):
        mock_agent = MagicMock()
        mock_agent.network_monitor.is_online = True
        mock_agent.discord.is_ready = True
        
        # Use AsyncMock for coroutines
        mock_agent.discord.get_online_activities = AsyncMock(return_value=[{'user_name': 'User1', 'name': 'Game1'}])
        mock_agent._process_activity = AsyncMock(return_value=None)
        
        tool = DiscordActivityTool(mock_agent)
        res = await tool.execute()
        self.assertIn("User1 is playing/doing: Game1", res)

if __name__ == '__main__':
    unittest.main()
