import logging
import threading
import os
import markdown
from flask import Flask, render_template_string, send_from_directory, abort, request
from pyngrok import ngrok, conf

logger = logging.getLogger(__name__)


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


# Discord-themed CSS for the documentation
DOCS_CSS = """
    /* Base styles with Discord color scheme */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body { 
        font-family: sans-serif !important; 
        line-height: 1.6; 
        color: #dcddde; 
        background: #2f3136;
        max-width: 1200px; 
        margin: 0 auto; 
        padding: 20px;
    }
    
    /* Navigation bar */
    .nav { 
        background: #202225;
        margin: -20px -20px 30px -20px;
        padding: 20px 40px;
        border-bottom: 2px solid #5865F2;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
    }
    
    .nav a {
        color: #dcddde;
        text-decoration: none;
        font-weight: 500;
        padding: 8px 16px;
        border-radius: 4px;
        transition: all 0.2s;
        display: inline-block;
    }
    
    .nav a:hover {
        background: #5865F2;
        color: white;
        text-decoration: none;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 { 
        color: #ffffff; 
        margin-top: 24px;
        margin-bottom: 16px;
        font-weight: 600;
    }
    
    h1 { 
        color: #5865F2; 
        font-size: 2.5em;
        padding-bottom: 12px;
        border-bottom: 2px solid #40444b;
    }
    
    h2 {
        color: #7289da;
        font-size: 2em;
        padding-bottom: 8px;
        border-bottom: 1px solid #40444b;
    }
    
    h3 {
        color: #b9bbbe;
        font-size: 1.5em;
    }
    
    /* Links */
    a { 
        color: #00aff4; 
        text-decoration: none; 
        transition: color 0.2s;
    }
    
    a:hover { 
        color: #5865F2;
        text-decoration: underline; 
    }
    
    /* Code blocks */
    pre { 
        background: #202225; 
        padding: 16px; 
        border-radius: 8px; 
        overflow-x: auto;
        border-left: 4px solid #5865F2;
        margin: 16px 0;
    }
    
    code { 
        background: #202225; 
        color: #7289da;
        padding: 2px 6px; 
        border-radius: 4px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.9em;
    }
    
    pre code {
        background: transparent;
        padding: 0;
        color: #dcddde;
    }
    
    /* Status cards */
    .status-card { 
        background: linear-gradient(135deg, #36393f 0%, #2f3136 100%);
        padding: 24px; 
        border-radius: 12px; 
        margin-bottom: 24px; 
        border: 1px solid #40444b;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    
    .status-item { 
        margin-bottom: 12px;
        padding: 8px 0;
        border-bottom: 1px solid #40444b;
    }
    
    .status-item:last-child {
        border-bottom: none;
    }
    
    .status-label { 
        font-weight: 600; 
        color: #5865F2;
        margin-right: 8px;
        display: inline-block;
        min-width: 120px;
    }
    
    /* Lists */
    ul, ol {
        margin: 16px 0;
        padding-left: 24px;
    }
    
    li {
        margin: 8px 0;
        color: #dcddde;
    }
    
    /* Tables */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        background: #36393f;
        border-radius: 8px;
        overflow: hidden;
    }
    
    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #40444b;
    }
    
    th {
        background: #202225;
        color: #5865F2;
        font-weight: 600;
    }
    
    tr:hover {
        background: #40444b;
    }
    
    /* Paragraphs */
    p {
        margin: 12px 0;
        color: #dcddde;
    }
    
    /* Blockquotes */
    blockquote {
        border-left: 4px solid #5865F2;
        padding-left: 16px;
        margin: 16px 0;
        color: #b9bbbe;
        font-style: italic;
    }
    
    /* Horizontal rules */
    hr {
        border: none;
        border-top: 2px solid #40444b;
        margin: 24px 0;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: #2f3136;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #202225;
        border-radius: 6px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #5865F2;
    }

    /* Mobile Responsive Styles */
    /* Mobile Responsive Styles */
    @media (max-width: 768px) {
        body {
            padding: 10px;
        }
        
        .nav {
            margin: -10px -10px 20px -10px;
            padding: 10px;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 5px;
        }
        
        .nav a {
            display: inline-block;
            margin: 0;
            padding: 8px 12px;
            background: #36393f;
            font-size: 0.9em;
        }
        
        h1 {
            font-size: 1.5em; /* Reduced from 1.8em */
        }
        
        h2 {
            font-size: 1.3em; /* Reduced from 1.5em */
        }
        
        pre {
            padding: 10px;
            font-size: 0.8em;
        }
        
        .status-card {
            padding: 15px;
        }
        
        table {
            display: block;
            overflow-x: auto;
            white-space: nowrap;
        }
    }
"""

TEMPLATE_BASE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - RPI AI Agent</title>
    <style>
        {{ css }}
        .search-form {
            display: inline-block;
            margin-left: auto;
        }
        .search-form input {
            padding: 6px 12px;
            background: #36393f;
            border: 1px solid #40444b;
            border-radius: 4px;
            color: #dcddde;
            font-size: 0.9em;
            width: 250px;
        }
        .search-form input:focus {
            outline: none;
            border-color: #5865F2;
        }
        @media (max-width: 768px) {
            .nav {
                flex-wrap: wrap;
                justify-content: center;
            }
            .search-form {
                width: 100%;
                margin: 10px 0 0 0;
                text-align: center;
            }
            .search-form input {
                width: 80%;
                max-width: 400px;
            }
        }
    </style>
    {{ refresh_meta | safe }}
</head>
<body>
    <div class="nav">
        <a href="/">🏠 Dashboard</a>
        <a href="/docs">📚 Documentation</a>
        <form class="search-form" method="GET" action="/search">
            <input type="text" name="q" placeholder="🔍 Vyhledat v dokumentaci" />
        </form>
    </div>
    {{ content | safe }}
</body>
</html>
"""

class WebServer:
    def __init__(self, agent):
        self.agent = agent
        self.app = Flask(__name__)
        self.port = 5001  # Changed from 5000 due to port conflict
        self.thread = None
        self.public_url = None
        self.manual_stop = False # Track intentional stops
        self.docs_dir = os.path.abspath("documentation")
        
        # Configure routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/docs', 'docs_list', self.docs_list)
        self.app.add_url_rule('/docs/<path:filename>', 'docs_view', self.docs_view)
        self.app.add_url_rule('/search', 'search_docs', self.search_docs)
        self.app.add_url_rule('/test', 'test', lambda: "Flask is running! ✅")
        self.app.add_url_rule('/shutdown', 'shutdown', self._shutdown, methods=['POST'])
        
        # Disable Flask logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
    
    def _shutdown(self):
        """Shutdown Flask server gracefully."""
        from flask import request
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            # Werkzeug 2.1+ doesn't have shutdown function
            import os
            import signal
            os.kill(os.getpid(), signal.SIGINT)
            return 'Server shutting down...'
        func()
        return 'Server shutting down...'

    def index(self):
        """Main dashboard."""
        import psutil
        
        # System Stats
        cpu_percent = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Format bytes to GB
        def to_gb(bytes_val):
            return f"{bytes_val / (1024**3):.1f} GB"
            
        ram_percent = ram.percent
        ram_used = to_gb(ram.used)
        ram_total = to_gb(ram.total)
        
        disk_percent = disk.percent
        disk_used = to_gb(disk.used)
        disk_total = to_gb(disk.total)

        status_html = f"""
        <h1>🤖 Agent Dashboard</h1>
        
        <div class="status-card">
            <div class="status-item">
                <span class="status-label">Status:</span> 
                {'🟢 Running' if self.agent.is_running else '🔴 Stopped'}
            </div>
            <div class="status-item">
                <span class="status-label">Boredom:</span> 
                {self.agent.boredom_score * 100:.1f}%
            </div>
            <div class="status-item">
                <span class="status-label">Uptime:</span> 
                {self._get_uptime()}
            </div>
            <div class="status-item">
                <span class="status-label">Tools Learned:</span> 
                {len([t for t, c in self.agent.tool_usage_count.items() if c > 0])}
            </div>
        </div>

        <div class="status-card">
            <h3>🖥️ System Resources</h3>
            <div class="status-item">
                <span class="status-label">CPU Usage:</span> 
                {cpu_percent}%
            </div>
            <div class="status-item">
                <span class="status-label">RAM Usage:</span> 
                {ram_percent}% ({ram_used} / {ram_total})
            </div>
            <div class="status-item">
                <span class="status-label">Disk Usage:</span> 
                {disk_percent}% ({disk_used} / {disk_total})
            </div>
        </div>
        
        <h3>Recent Activity</h3>
        <ul>
        {''.join([f'<li>{a}</li>' for a in self.agent.action_history[-5:]]) if self.agent.action_history else '<li>No recent activity</li>'}
        </ul>
        """
        import config_settings
        refresh_interval = getattr(config_settings, 'WEB_DASHBOARD_REFRESH_INTERVAL', 10)
        
        return render_template_string(
            TEMPLATE_BASE, 
            title="Dashboard", 
            content=status_html, 
            css=DOCS_CSS,
            refresh_meta=f'<meta http-equiv="refresh" content="{refresh_interval}">'
        )

    def docs_list(self):
        """List available documentation."""
        if not os.path.exists(self.docs_dir):
            return render_template_string(TEMPLATE_BASE, title="Docs", css=DOCS_CSS, content="<p>No documentation directory found.</p>")
            
        files = []
        for root, dirs, filenames in os.walk(self.docs_dir):
            for f in filenames:
                if f.endswith('.md'):
                    rel_path = os.path.relpath(os.path.join(root, f), self.docs_dir)
                    # Replace backslashes with forward slashes for URLs
                    rel_path = rel_path.replace('\\', '/')
                    files.append(rel_path)
        
        list_html = "<h1>📚 Documentation</h1><h3>Všechny soubory</h3><ul>"
        for f in sorted(files):
            list_html += f'<li><a href="/docs/{f}">{f}</a></li>'
        list_html += "</ul>"
        
        return render_template_string(TEMPLATE_BASE, title="Documentation", css=DOCS_CSS, content=list_html)

    def docs_view(self, filename):
        """Render a markdown file."""
        # Security check to prevent directory traversal
        safe_path = os.path.abspath(os.path.join(self.docs_dir, filename))
        if not safe_path.startswith(self.docs_dir) or not os.path.exists(safe_path):
            abort(404)
            
        try:
            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
                html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
                
            return render_template_string(TEMPLATE_BASE, title=filename, css=DOCS_CSS, content=f"<h1>{filename}</h1>{html_content}")
        except Exception as e:
            return f"Error reading file: {e}", 500
    
    def search_docs(self):
        """Search documentation files for a query and link to specific anchors."""
        query = request.args.get('q', '').strip()
        if not query:
            return render_template_string(TEMPLATE_BASE, title="Search", css=DOCS_CSS, 
                                          content="<h1>🔍 Vyhledávání</h1><p>Prázdný dotaz.</p><p><a href='/docs'>← Zpět na dokumentaci</a></p>")
        
        if not os.path.exists(self.docs_dir):
            return render_template_string(TEMPLATE_BASE, title="Search", css=DOCS_CSS, 
                                          content="<h1>🔍 Vyhledávání</h1><p>Dokumentace nenalezena.</p>")
        
        results = []
        query_lower = query.lower()
        
        # Search through all .md files
        for root, dirs, filenames in os.walk(self.docs_dir):
            for f in filenames:
                if f.endswith('.md'):
                    file_path = os.path.join(root, f)
                    rel_path = os.path.relpath(file_path, self.docs_dir).replace('\\', '/')
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            lines = file.readlines()
                            content = ''.join(lines)
                            content_lower = content.lower()
                            
                            # Find all occurrences (exact + fuzzy)
                            import re
                            matches = []
                            
                            # Split query into words for fuzzy matching
                            query_words = query_lower.split()
                            
                            # 1. Exact phrase matching
                            for match in re.finditer(re.escape(query_lower), content_lower):
                                pos = match.start()
                                anchor = self._find_nearest_anchor(lines, pos)
                                start = max(0, pos - 100)
                                end = min(len(content), pos + len(query) + 100)
                                snippet = content[start:end].replace('<', '&lt;').replace('>', '&gt;')
                                
                                # Highlight exact match
                                import re as regex
                                snippet = regex.sub(f'({re.escape(query)})', 
                                                   r'<strong style="background: #43b581; color: white; padding: 2px 4px;">\1</strong>', 
                                                   snippet, flags=regex.IGNORECASE)
                                
                                matches.append({
                                    'anchor': anchor,
                                    'snippet': f'...{snippet}...',
                                    'score': 100  # Exact match gets highest score
                                })
                            
                            # 2. Fuzzy word matching (if query is single word or short)
                            if len(query_words) <= 3:  # Only for short queries
                                content_words = re.findall(r'\b\w+\b', content_lower)
                                for i, word in enumerate(content_words):
                                    for query_word in query_words:
                                        if len(query_word) >= 4:  # Only fuzzy match longer words
                                            distance = levenshtein_distance(query_word, word)
                                            # Allow up to 2 character difference
                                            threshold = 2
                                            
                                            if distance <= threshold and distance > 0:
                                                # Find position of this word in original content
                                                # Reconstruct approximate position
                                                words_before = content_lower[:content_lower.find(word)].split()
                                                approx_pos = sum(len(w) + 1 for w in words_before)
                                                
                                                anchor = self._find_nearest_anchor(lines, approx_pos)
                                                start = max(0, approx_pos - 100)
                                                end = min(len(content), approx_pos + len(word) + 100)
                                                snippet = content[start:end].replace('<', '&lt;').replace('>', '&gt;')
                                                
                                                # Highlight fuzzy match
                                                snippet = snippet.replace(word, f'<strong style="background: #faa61a; color: white; padding: 2px 4px;">{word}</strong>')
                                                
                                                # Score based on distance (closer = better)
                                                score = 80 - (distance * 10)
                                                
                                                matches.append({
                                                    'anchor': anchor,
                                                    'snippet': f'...{snippet}... <em style="color: #b9bbbe; font-size: 0.85em;">(fuzzy: {query_word} → {word})</em>',
                                                    'score': score
                                                })
                            
                            if matches:
                                # Sort by score, then group by anchor
                                matches.sort(key=lambda x: x.get('score', 0), reverse=True)
                                
                                # Group by anchor and take best scored snippet from each
                                anchor_groups = {}
                                for m in matches:
                                    anchor = m['anchor']
                                    if anchor not in anchor_groups:
                                        anchor_groups[anchor] = m['snippet']
                                    # Keep the higher scored match if duplicate anchor
                                
                                for anchor, snippet in anchor_groups.items():
                                    results.append({
                                        'file': rel_path,
                                        'anchor': anchor,
                                        'snippet': snippet
                                    })
                    except Exception as e:
                        logger.error(f"Error searching {file_path}: {e}")
        
        # Build results HTML
        results_html = f"<h1>🔍 Výsledky vyhledávání: '{query}'</h1>"
        results_html += f"<p><a href='/docs'>← Zpět na dokumentaci</a></p>"
        
        # Add legend
        results_html += '''
        <div class="status-card" style="margin-bottom: 20px; padding: 16px;">
            <h3 style="margin-top: 0;">📖 Nápověda</h3>
            <p style="margin: 8px 0;">
                <strong style="background: #43b581; color: white; padding: 2px 6px; border-radius: 3px;">Zelená</strong> 
                = Přesná shoda
            </p>
            <p style="margin: 8px 0;">
                <strong style="background: #faa61a; color: white; padding: 2px 6px; border-radius: 3px;">Oranžová</strong> 
                = Nepřesná shoda (fuzzy)
            </p>
        </div>
        '''
        
        if results:
            results_html += f"<p>Nalezeno <strong>{len(results)}</strong> výsledků.</p>"
            results_html += "<div>"
            for r in results:
                link = f"/docs/{r['file']}"
                if r['anchor']:
                    link += f"#{r['anchor']}"
                    section_name = r['anchor'].replace('-', ' ').title()
                    results_html += f'''
                    <div class="status-card" style="margin-bottom: 16px;">
                        <h3><a href="{link}">{r['file']} → {section_name}</a></h3>
                        <p style="font-size: 0.9em; color: #dcddde; margin-top: 8px;">{r['snippet']}</p>
                    </div>
                    '''
                else:
                    results_html += f'''
                    <div class="status-card" style="margin-bottom: 16px;">
                        <h3><a href="{link}">{r['file']}</a></h3>
                        <p style="font-size: 0.9em; color: #dcddde; margin-top: 8px;">{r['snippet']}</p>
                    </div>
                    '''
            results_html += "</div>"
        else:
            results_html += f"<p>Žádné výsledky pro dotaz: <strong>{query}</strong></p>"
        
        return render_template_string(TEMPLATE_BASE, title="Search Results", css=DOCS_CSS, content=results_html)
    
    def _find_nearest_anchor(self, lines, char_pos):
        """Find the nearest anchor (heading) before a character position."""
        # Convert char position to line number
        current_pos = 0
        target_line = 0
        for i, line in enumerate(lines):
            current_pos += len(line)
            if current_pos >= char_pos:
                target_line = i
                break
        
        # Search backwards for anchor
        import re
        for i in range(target_line, -1, -1):
            line = lines[i].strip()
            # Look for anchor pattern: <a name="anchor-name"></a>
            anchor_match = re.match(r'<a name="([^"]+)"></a>', line)
            if anchor_match:
                return anchor_match.group(1)
        
        return None

    def _get_uptime(self):
        import time
        import datetime
        seconds = int(time.time() - self.agent.start_time)
        return str(datetime.timedelta(seconds=seconds))

    def start(self):
        """Start the Flask server on an available port."""
        self.manual_stop = False # Reset manual stop flag
        if self.thread and self.thread.is_alive():
            return

        # Find an available port starting from 5001
        import socket
        import psutil
        
        found_port = None
        for port in range(5001, 5020): # Increased range
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Set SO_REUSEADDR to avoid TIME_WAIT issues, but we want to know if it's genuinely in use
                # Actually, for the check we want to fail if it's in use.
                sock.bind(('0.0.0.0', port))
                sock.close()
                found_port = port
                logger.info(f"Selected available port: {found_port}")
                break
            except OSError:
                # Try to find what's using it
                try:
                    for conn in psutil.net_connections():
                        if conn.laddr.port == port:
                            logger.warning(f"Port {port} is in use by PID {conn.pid} ({conn.status})")
                except:
                    logger.warning(f"Port {port} is in use (process info unavailable)")
        
        if found_port:
            self.port = found_port
            self.thread = threading.Thread(target=self._run_flask, daemon=True)
            self.thread.start()
        else:
            logger.error("Could not find any available port for Web Interface (5001-5020). Web server will NOT start.")
            # We should probably notify the user via Discord if possible, but this is a synchronous method called during startup.
            # The agent will continue without web interface.

    def _run_flask(self):
        try:
            logger.info(f"Flask server starting on {self.port}...")
            # Disable Flask's default logging to reduce noise
            import logging as flask_logging
            flask_log = flask_logging.getLogger('werkzeug')
            flask_log.setLevel(flask_logging.ERROR)
            
            self.app.run(host='0.0.0.0', port=self.port, use_reloader=False, threaded=True)
        except Exception as e:
            logger.error(f"Web server failed: {e}", exc_info=True)

    def start_ngrok(self):
        """Start ngrok tunnel and return URL. Ensures Flask server is running first."""
        # CRITICAL: Start Flask server if not already running
        if not self.thread or not self.thread.is_alive():
            logger.info("Flask server not running, starting it now...")
            self.start()
            # Give Flask a moment to start
            import time
            time.sleep(1)
        
        if self.public_url:
            return self.public_url
            
        try:
            # Check if ngrok is already running for this port
            tunnels = ngrok.get_tunnels()
            for t in tunnels:
                if t.config['addr'].endswith(str(self.port)):
                    self.public_url = t.public_url
                    logger.info(f"Found existing ngrok tunnel: {self.public_url}")
                    return self.public_url

            # Start new tunnel
            logger.info(f"Starting ngrok tunnel on port {self.port}...")
            # Use http protocol
            tunnel = ngrok.connect(self.port, "http")
            self.public_url = tunnel.public_url
            logger.info(f"Ngrok tunnel established: {self.public_url}")
            return self.public_url
        except Exception as e:
            logger.error(f"Failed to start ngrok: {e}")
            return None


    def disconnect_web_tunnel(self):
        """Stop Flask server and disconnect ONLY the web tunnel (preserves SSH)."""
        # 1. Stop Flask server
        if self.thread and self.thread.is_alive():
            try:
                logger.info(f"Stopping Flask server on port {self.port}...")
                # Try to make a shutdown request to Flask
                import requests
                try:
                    requests.post(f'http://localhost:{self.port}/shutdown', timeout=2)
                    logger.info("Flask shutdown request sent")
                except:
                    pass  # Ignore if shutdown endpoint doesn't respond
                
                # Give it a moment to shut down gracefully
                import time
                time.sleep(1)
                
                self.thread = None
                logger.info("Flask server stopped")
            except Exception as e:
                logger.error(f"Error stopping Flask server: {e}")
        
        # 2. Disconnect web tunnel
        try:
            tunnels = ngrok.get_tunnels()
            for tunnel in tunnels:
                if tunnel.config['addr'].endswith(str(self.port)):
                    try:
                        ngrok.disconnect(tunnel.public_url)
                        logger.info(f"Disconnected web ngrok tunnel: {tunnel.public_url}")
                    except Exception as e:
                        logger.warning(f"Failed to disconnect tunnel {tunnel.public_url}: {e}")
            
            self.public_url = None
        except Exception as e:
            logger.error(f"Error disconnecting web tunnel: {e}")

    def stop(self):
        """Stop ngrok and Flask server - AGGRESSIVE cleanup (closes ALL tunnels)."""
        self.manual_stop = True # Set manual stop flag
        # 1. Gentle stop first
        self.disconnect_web_tunnel()
        
        # 2. Kill ngrok process
        try:
            ngrok.kill()
            logger.info("Ngrok process killed via pyngrok")
        except Exception as e:
            logger.error(f"Error stopping ngrok via pyngrok: {e}")
        
        # 3. FORCE KILL all ngrok processes (brute force cleanup)
        try:
            import subprocess
            if self.agent.is_linux:
                subprocess.run(['pkill', '-9', 'ngrok'], capture_output=True)
            else:
                subprocess.run(['taskkill', '/F', '/IM', 'ngrok.exe'], capture_output=True, shell=True)
            logger.info("Force cleanup of ngrok processes executed")
        except Exception as e:
            logger.warning(f"Could not force-kill ngrok processes: {e}")
        
        logger.info("Web server full stop complete")
