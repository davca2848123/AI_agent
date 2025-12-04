import logging
import threading
import os
import markdown
from flask import Flask, render_template_string, send_from_directory, abort
from pyngrok import ngrok, conf

logger = logging.getLogger(__name__)

# CSS for the documentation
DOCS_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
h1, h2, h3 { color: #2c3e50; }
a { color: #3498db; text-decoration: none; }
a:hover { text-decoration: underline; }
.nav { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
.status-card { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e9ecef; }
.status-item { margin-bottom: 10px; }
.status-label { font-weight: bold; color: #666; }
"""

TEMPLATE_BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - RPI AI Agent</title>
    <style>
        {{ css }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">🏠 Dashboard</a> | 
        <a href="/docs">📚 Documentation</a>
    </div>
    {{ content | safe }}
</body>
</html>
"""

class WebServer:
    def __init__(self, agent):
        self.agent = agent
        self.app = Flask(__name__)
        self.port = 5000
        self.thread = None
        self.public_url = None
        self.docs_dir = os.path.abspath("documentation")
        
        # Configure routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/docs', 'docs_list', self.docs_list)
        self.app.add_url_rule('/docs/<path:filename>', 'docs_view', self.docs_view)
        
        # Disable Flask logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    def index(self):
        """Main dashboard."""
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
        
        <h3>Recent Activity</h3>
        <ul>
        {''.join([f'<li>{a}</li>' for a in self.agent.action_history[-5:]]) if self.agent.action_history else '<li>No recent activity</li>'}
        </ul>
        """
        return render_template_string(TEMPLATE_BASE, title="Dashboard", css=DOCS_CSS, content=status_html)

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
        
        list_html = "<h1>📚 Documentation</h1><ul>"
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

    def _get_uptime(self):
        import time
        import datetime
        seconds = int(time.time() - self.agent.start_time)
        return str(datetime.timedelta(seconds=seconds))

    def start(self):
        """Start the Flask server in a separate thread."""
        if self.thread:
            return
            
        logger.info("Starting Web Interface...")
        self.thread = threading.Thread(target=self._run_flask, daemon=True)
        self.thread.start()

    def _run_flask(self):
        try:
            self.app.run(host='0.0.0.0', port=self.port, use_reloader=False)
        except Exception as e:
            logger.error(f"Web server failed: {e}")

    def start_ngrok(self):
        """Start ngrok tunnel and return URL."""
        if self.public_url:
            return self.public_url
            
        try:
            # Check if ngrok is already running
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

    def stop(self):
        """Stop ngrok and server."""
        if self.public_url:
            try:
                ngrok.disconnect(self.public_url)
                ngrok.kill()
                self.public_url = None
            except:
                pass
