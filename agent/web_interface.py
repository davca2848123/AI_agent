import logging
import threading
import os
import platform
import markdown
import secrets
from flask import Flask, render_template_string, send_from_directory, abort, request, jsonify, g
from flask_socketio import SocketIO, emit
from pyngrok import ngrok, conf
import config_settings

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



def sanitize_log_line(line: str) -> str:
    """Basic sanitization and colorization for log lines."""
    import html
    import re
    
    # Strip ANSI codes (in case log file contains them)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    line = ansi_escape.sub('', line)
    
    # Escape HTML special characters
    safe_line = html.escape(line.strip())
    
    # regex for standard log format: YYYY-MM-DD HH:MM:SS,mmm - [Host] - Logger - Level - Message
    # Allow dot or comma for milliseconds
    log_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:[,\.]\d{3})?)\s+-\s+(\[.*?\])\s+-\s+(.*?)\s+-\s+(.*?)\s+-\s+(.*)$')
    match = log_pattern.match(safe_line)
    
    if match:
        timestamp, host, logger_name, level, message = match.groups()
        
        # Colorize Level
        level_color = "#dcddde"
        if "ERROR" in level or "CRITICAL" in level:
            level_color = "#f04747"
        elif "WARNING" in level:
            level_color = "#faa61a"
        elif "DEBUG" in level:
            level_color = "#72767d"
        elif "INFO" in level:
            level_color = "#43b581"
            
        # Mask sensitive parts of URLs (path/query) with ****
        # Matches http(s)://domain and captures the rest, preserving domain visibility.
        # Added tcp support
        url_mask_pattern = re.compile(r'((?:[a-zA-Z0-9+\.-]+)://)([^/\s]+)(/[^\s]*)?')
        
        def mask_url_match(m):
            proto = m.group(1)
            domain = m.group(2)
            path = m.group(3)
            
            # Check if domain is an IP address
            ip_match = re.match(r'^(\d{1,3})\.(\d{1,3})\.\d{1,3}\.\d{1,3}$', domain)
            if ip_match:
                # Keep first 2 octets for IPs
                if domain in ['0.0.0.0']: # Keep ignoring 0.0.0.0 for bind addrs if strictly needed, but masking consistent is better. 
                  # User complained about 127... so let's mask 127 too. 
                    masked_domain = f"{ip_match.group(1)}.{ip_match.group(2)}.***.***"
                else:
                    masked_domain = f"{ip_match.group(1)}.{ip_match.group(2)}.***.***"
            else:
                # For regular domains, mask each part but preserve dots
                parts = domain.split('.')
                masked_parts = []
                for part in parts:
                    if len(part) > 3:
                        masked_parts.append(part[:3] + '***')
                    else:
                        masked_parts.append(part)
                masked_domain = '.'.join(masked_parts)
            
            masked_path = ""
            if path and len(path) > 1: # Only mask if there's a path
                # Show first 3 chars of path if possible, then mask
                if len(path) > 5:
                     masked_path = f'{path[:3]}****'
                else:
                     masked_path = '/****'
            
            return f'{proto}{masked_domain}{masked_path}'
            
        message = url_mask_pattern.sub(mask_url_match, message)
        
        # Mask IP addresses (IPv4)
        # Exclude 127.0.0.1 and 0.0.0.0
        ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        
        def mask_ip_match(m):
            ip = m.group(0)
            parts = ip.split('.')
            return f"{parts[0]}.{parts[1]}.***.***"
            return f"{parts[0]}.{parts[1]}.***.***"
            
        message = ip_pattern.sub(mask_ip_match, message)

            
        # Highlight numbers
        number_pattern = re.compile(r'\b\d+\b')
        message = number_pattern.sub(r'<span style="color: #00b0f4;">\g<0></span>', message)

        colored_line = (
             f'<div id="log-{hash(line)}" class="log-entry">'
             f'<span style="color: #43b581;">{timestamp}</span> - '
             f'<span style="color: #ffffff;">{host}</span> - '
             f'<span style="color: #00b0f4;">{logger_name}</span> - '
             f'<span style="color: {level_color}; font-weight: bold;">{level}</span> - '
             f'{message}'
             f'</div>'
        )
        return colored_line
    else:
        # Fallback for non-standard lines
        if "ERROR" in safe_line or "CRITICAL" in safe_line or "Exception" in safe_line:
            return f'<div class="log-entry" style="color: #f04747;">{safe_line}</div>'
        elif "WARNING" in safe_line:
            return f'<div class="log-entry" style="color: #faa61a;">{safe_line}</div>'
        
        return f'<div class="log-entry">{safe_line}</div>'

# Discord-themed CSS for the documentation
DOCS_CSS = """
    /* Base styles with Discord color scheme */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.1); }
        100% { opacity: 1; transform: scale(1); }
    }

    @keyframes modalAppear {
        from { opacity: 0; transform: scale(0.95) translateY(-20px); }
        to { opacity: 1; transform: scale(1) translateY(0); }
    }

    @keyframes modalDisappear {
        from { opacity: 1; transform: scale(1) translateY(0); }
        to { opacity: 0; transform: scale(0.95) translateY(-20px); }
    }

    @keyframes flashRed {
        0% { opacity: 1; text-shadow: 0 0 5px rgba(240, 71, 71, 0.5); }
        50% { opacity: 0.4; text-shadow: none; }
        100% { opacity: 1; text-shadow: 0 0 5px rgba(240, 71, 71, 0.5); }
    }

    .modal.closing .modal-content {
        animation: modalDisappear 0.3s ease-in forwards;
    }

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
        background-image: none;
    }
    
    .nav a:hover {
        background: #5865F2; /* Overrides background-image if it was set, but being explicit is good */
        color: white;
        text-decoration: none;
        transform: scale(1.05);
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
        transition: color 0.2s, background-size 0.3s;
        background-image: linear-gradient(#5865F2, #5865F2);
        background-position: 0% 100%;
        background-repeat: no-repeat;
        background-size: 0% 2px;
    }
    
    a:hover { 
        color: #5865F2;
        background-size: 100% 2px;
    }
    
    /* Code blocks */
    pre { 
        background: #202225; 
        padding: 16px; 
        border-radius: 8px; 
        overflow-x: auto;
        border-left: 4px solid #5865F2;
        margin: 16px 0;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    pre:hover {
        transform: scale(1.01);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
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
    
    /* Search highlighting */
    .highlight-exact {
        background: #43b581;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-weight: 600;
    }
    
    .highlight-fuzzy {
        background: #faa61a;
        color: white;
        padding: 2px 6px;
        border-radius: 3px;
        font-weight: 600;
    }
    
    /* Status cards */
    .status-card { 
        background: linear-gradient(135deg, #36393f 0%, #2f3136 100%);
        padding: 24px; 
        border-radius: 12px; 
        margin-bottom: 24px; 
        border: 1px solid #40444b;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        animation: fadeIn 0.6s ease-out forwards;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .status-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.5);
    }
    
    .status-item { 
        min-height: 45px;
        display: flex;
        align-items: center;
        border-bottom: 1px solid #40444b;
        padding: 5px 0;
        margin: 0;
    }
    
    .status-item:last-child {
        border-bottom: none;
    }
    
    .status-label { 
        font-weight: 600; 
        color: #5865F2;
        margin-right: 8px;
        display: inline-block;
        min-width: 160px;
    }
    
    .status-row {
        display: flex;
        flex-wrap: wrap;
    }
    
    .status-col {
        width: 50%;
        box-sizing: border-box;
    }
    
    .status-col:first-child {
        padding-right: 25px;
        border-right: 1px solid #40444b;
    }
    
    .status-col:last-child {
        padding-left: 25px;
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
        transition: background-color 0.1s;
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
        transition: border-left-color 0.3s, background 0.3s;
        padding-top: 5px;
        padding-bottom: 5px;
    }

    blockquote:hover {
        border-left-color: #00aff4;
        background: rgba(88, 101, 242, 0.05); /* Very subtle tint */
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
    /* Modal Styles */
    .modal {
        display: none; 
        position: fixed; 
        z-index: 100; 
        left: 0;
        top: 0;
        width: 100%; 
        height: 100%; 
        overflow: auto; 
        background-color: rgba(0,0,0,0.6); 
    }
    .modal-content {
        background-color: #2f3136;
        margin: 5% auto; /* Less top margin on mobile */
        padding: 15px;
        border: 1px solid #40444b;
        width: 95%; /* Wider on mobile */
        max-width: 600px;
        border-radius: 8px;
        color: #dcddde;
        max-height: 90vh; /* Prevent overflow on small screens */
        overflow-y: auto; /* Scrollable content */
        animation: modalAppear 0.3s ease-out forwards;
    }
    .proc-table { width: 100%; border-collapse: collapse; font-size: 0.8em; margin-bottom: 20px; table-layout: fixed; }
    .proc-table th { text-align: left; border-bottom: 1px solid #40444b; padding: 8px 4px; color: #b9bbbe; }
    .proc-table td { border-bottom: 1px solid #2f3136; padding: 6px 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    /* Column widths */
    .proc-table th:nth-child(1), .proc-table td:nth-child(1) { width: 20%; } /* PID */
    .proc-table th:nth-child(2), .proc-table td:nth-child(2) { width: 50%; } /* Name */
    .proc-table th:nth-child(3), .proc-table td:nth-child(3) { width: 30%; text-align: right; } /* Value */
    .close {
        color: #aaa;
        float: right;
        font-size: 28px;
        font-weight: bold;
        cursor: pointer;
    }
    .close:hover,
    .close:focus {
        color: #fff;
        text-decoration: none;
        cursor: pointer;
    }
    .detail-btn {
        background-color: #5865F2;
        border: none;
        color: white;
        padding: 8px 15px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        border-radius: 4px;
        cursor: pointer;
        transition: transform 0.2s, background-color 0.2s;
    }
    .detail-btn:hover { 
        background-color: #4752c4; 
        transform: scale(1.05);
    }
    .proc-table { width: 100%; font-size: 0.9em; margin-bottom: 20px; }
    .proc-table th { text-align: left; border-bottom: 1px solid #40444b; padding: 5px; color: #b9bbbe; }
    .proc-table td { border-bottom: 1px solid #2f3136; padding: 5px; }

    /* Dashboard */
    .dashboard-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #40444b;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .dashboard-title {
        font-size: 2.5em;
        font-weight: 600;
        color: #5865F2;
    }
    .status-wrapper {
        text-align: right;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .connection-status {
        font-weight: bold;
        font-size: 1.1em;
        color: #faa61a;
        animation: pulse 2s infinite;
        transform-origin: right center;
    }
    .connection-status.disconnected {
        color: #f04747;
        animation: flashRed 1.5s infinite;
    }
    .stats-info {
        font-size: 0.8em; 
        color: #72767d; 
        margin-top: 5px;
    }

    .resources-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .resources-title {
        margin: 0;
    }

    /* Mobile Responsive Styles */
    @media (max-width: 768px) {
        .stats-info {
            display: none;
        }
        .status-label {
             min-width: 80px;
        }
        body {
            padding: 10px;
        }

        .detail-btn {
            padding: 5px 10px;
            font-size: 12px;
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
        
        h1, .dashboard-title {
            font-size: 1.5em; /* Reduced from 1.8em */
        }

        .connection-status {
            font-size: 0.9em;
            white-space: nowrap;
            margin-left: 10px;
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
        
        .status-col {
            width: 100%;
        }
        .status-col:first-child {
            border-right: none;
            padding-right: 0;
            border-bottom: 1px solid #40444b;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }
        .status-col:last-child {
            padding-left: 0;
        }

        table {
            display: block;
            overflow-x: auto;
            white-space: nowrap;
        }
    }

    /* Staggered animation for content elements */
    #content > h1, #content > h2, #content > h3, 
    #content > p, #content > ul, #content > ol, 
    #content > pre, #content > table, #content > blockquote {
        animation: fadeIn 0.5s ease-out forwards;
        opacity: 0;
    }

    #content > *:nth-child(1) { animation-delay: 0.1s; }
    #content > *:nth-child(2) { animation-delay: 0.15s; }
    #content > *:nth-child(3) { animation-delay: 0.2s; }
    #content > *:nth-child(4) { animation-delay: 0.25s; }
    #content > *:nth-child(n+5) { animation-delay: 0.3s; }
"""

TEMPLATE_BASE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - RPI AI Agent</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js" nonce="{{ nonce }}"></script>
    <style nonce="{{ nonce }}">
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
        .log-viewer {
            background: #202225;
            color: #b9bbbe;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85em;
            padding: 10px;
            border-radius: 8px;
            height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            border: 1px solid #40444b;
            animation: fadeIn 0.8s ease-out forwards;
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
</head>
<body>
    <div class="nav">
        <a href="/">🏠 Dashboard</a>
        <a href="/docs">📚 Documentation</a>
        <form class="search-form" method="GET" action="/search">
            <input type="text" name="q" placeholder="🔍 Vyhledat v dokumentaci" />
        </form>
    </div>
    <div id="content">
        {{ content | safe }}
    </div>
    
    <script nonce="{{ nonce }}">
        // Process Modal Functions (Moved here to avoid CSP issues)
        function openProcessModal() {
            document.getElementById('processModal').style.display = 'block';
            fetchProcesses();
        }
        function closeProcessModal() {
            var modal = document.getElementById('processModal');
            modal.classList.add('closing');
            setTimeout(function() {
                modal.style.display = 'none';
                modal.classList.remove('closing');
            }, 280); 
        }
        window.onclick = function(event) {
            var modal = document.getElementById('processModal');
            if (event.target == modal) {
                closeProcessModal();
            }
        }
        
        function updateProcessTable(data) {
            if (!data) return;
            
            let cpuRows = '<tr><th>PID</th><th>Name</th><th>CPU %</th></tr>';
            if (data.cpu) {
                data.cpu.forEach(p => {
                    cpuRows += `<tr><td>${p.pid}</td><td>${p.name}</td><td style="text-align: right;">${p.cpu_percent.toFixed(2)}%</td></tr>`;
                });
            }
            document.getElementById('cpu-table').innerHTML = cpuRows;
            
            let ramRows = '<tr><th>PID</th><th>Name</th><th>RAM</th></tr>';
            if (data.memory) {
                data.memory.forEach(p => {
                    let memText = p.memory_mb + ' MB';
                    if (p.memory_percent !== undefined) {
                        memText = `${p.memory_percent.toFixed(1)}% (${p.memory_mb} MB)`;
                    }
                    ramRows += `<tr><td>${p.pid}</td><td>${p.name}</td><td style="text-align: right;">${memText}</td></tr>`;
                });
            }
            document.getElementById('ram-table').innerHTML = ramRows;
        }
        
        function fetchProcesses() {
            fetch('/api/processes')
            .then(response => response.json())
            .then(data => {
                if (data.error) { console.error('Error:', data.error); return; }
                updateProcessTable(data);
            })
            .catch(err => console.error('Fetch error:', err));
        }

        var socket = io();
        window.autoScrollEnabled = true;

        // Attach event listeners (CSP compliance)
        (function() {
            var detailsBtn = document.getElementById('details-btn');
            if(detailsBtn) detailsBtn.addEventListener('click', openProcessModal);
            
            var closeBtn = document.getElementById('modal-close-btn');
            if(closeBtn) closeBtn.addEventListener('click', closeProcessModal);
            
            var scrollBtn = document.getElementById('scroll-btn');
            if(scrollBtn) scrollBtn.addEventListener('click', resumeAutoScroll);
        })();

        function resumeAutoScroll() {
            var logViewer = document.getElementById('log-viewer');
            logViewer.scrollTop = logViewer.scrollHeight;
            window.autoScrollEnabled = true;
            document.getElementById('scroll-btn').style.display = 'none';
        }
        
        socket.on('connect', function() {
            // Init log viewer scroll listener
            var logViewer = document.getElementById('log-viewer');
            if (logViewer) {
                logViewer.addEventListener('scroll', function() {
                    // Check if user scrolled up (threshold 50px)
                    var isAtBottom = logViewer.scrollHeight - logViewer.scrollTop - logViewer.clientHeight < 50;
                    
                    if (!isAtBottom) {
                         window.autoScrollEnabled = false;
                         var btn = document.getElementById('scroll-btn');
                         if(btn) btn.style.display = 'block';
                    } else {
                         window.autoScrollEnabled = true;
                         var btn = document.getElementById('scroll-btn');
                         if(btn) btn.style.display = 'none';
                    }
                });
            }

            console.log('Connected to WebSocket');
            var el = document.getElementById('connection-status');
            if(el) {
                el.innerText = '● Live';
                el.classList.remove('disconnected');
                el.style.color = '#43b581';
            }
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from WebSocket');
            var el = document.getElementById('connection-status');
            if(el) {
                el.innerText = '● Disconnected';
                el.classList.add('disconnected');
                el.style.color = ''; // Let CSS class handle color
            }
        });
        
        socket.on('status_update', function(data) {
            // Update Status Card
            document.getElementById('status-running').innerHTML = data.is_running ? '🟢 Running' : '🔴 Stopped';
            document.getElementById('status-boredom').innerText = (data.boredom_score * 100).toFixed(1) + '%';
            document.getElementById('status-uptime').innerText = data.uptime;
            document.getElementById('status-tools').innerText = data.tools_used + ' / ' + data.tools_total;
            
            // Update Connection Stats
            var now = new Date();
            var timeString = now.toLocaleTimeString();
            var interval = {{ update_interval }};
            var clients = data.connected_clients !== undefined ? data.connected_clients : '?';
            document.getElementById('stats-info').innerText = 'Last update: ' + timeString + ' (Interval: ' + interval + 's) | Clients: ' + clients;
            
            // Update Loops
            if (data.loop_status) {
                var loopBoredom = document.getElementById('loop-boredom');
                if(loopBoredom) loopBoredom.innerText = data.loop_status.boredom_loop || 'N/A';
                
                var loopObs = document.getElementById('loop-observation');
                if(loopObs) loopObs.innerText = data.loop_status.observation_loop || 'N/A';
                
                var loopAct = document.getElementById('loop-action');
                if(loopAct) loopAct.innerText = data.loop_status.action_loop || 'N/A';
                
                var loopBack = document.getElementById('loop-backup');
                if(loopBack) loopBack.innerText = data.loop_status.backup_loop || 'N/A';
            }
            
            // Update Resources
            document.getElementById('res-cpu').innerText = data.cpu_percent + '%';
            document.getElementById('res-ram').innerText = data.ram_percent + '% (' + data.ram_used + ' / ' + data.ram_total + ')';
            document.getElementById('res-disk').innerText = data.disk_percent + '% (' + data.disk_used + ' / ' + data.disk_total + ')';
            
            // Update Activity
            var activityList = document.getElementById('activity-list');
            activityList.innerHTML = '';
            if (data.action_history.length > 0) {
                // Reverse to show newest first
                var reversedHistory = [...data.action_history].reverse();
                reversedHistory.forEach(function(action) {
                    var li = document.createElement('li');
                    
                    if (typeof action === 'object' && action !== null && action.timestamp) {
                         var date = new Date(action.timestamp * 1000);
                         var timeStr = date.toLocaleTimeString([], { hour12: false });
                         li.innerHTML = '<span style="color: #72767d; font-size: 0.9em;">[' + timeStr + ']</span> ' + (action.action || 'Unknown');
                    } else {
                         li.innerText = action;
                    }
                    
                    activityList.appendChild(li);
                });
            } else {
                activityList.innerHTML = '<li>No recent activity</li>';
            }
            
            // Update Log
            var logViewer = document.getElementById('log-viewer');
            
            // Set content
            var isAtBottom = logViewer.scrollHeight - logViewer.scrollTop - logViewer.clientHeight < 50;

            // Only update if content changed prevents heavy DOM updates/selection loss
            // Only update if content changed prevents heavy DOM updates/selection loss
            if (logViewer.innerHTML !== data.log_tail) {
                // Find visible element to anchor to
                var savedElementId = null;
                var savedOffset = 0;
                
                if (!window.autoScrollEnabled) {
                     var children = logViewer.children;
                     for (var i = 0; i < children.length; i++) {
                         var el = children[i];
                         // Find first element that is within or below the top of container (visible)
                         if (el.offsetTop >= logViewer.scrollTop) {
                             savedElementId = el.id;
                             savedOffset = el.offsetTop - logViewer.scrollTop;
                             break;
                         }
                     }
                }
                
                logViewer.innerHTML = data.log_tail;
                
                // Auto-scroll logic
                if (window.autoScrollEnabled) {
                    logViewer.scrollTop = logViewer.scrollHeight;
                } else if (savedElementId) {
                    // Try to restore position to exact element
                    var el = document.getElementById(savedElementId);
                    if (el) {
                        logViewer.scrollTop = el.offsetTop - savedOffset;
                    } else {
                        // Element fell off, maintain bottom distance as fallback
                         // (Actually strictly speaking if element fell off we can't scroll to it, 
                         //  so we might just stay where we are or let browser handle it.
                         //  Since browser reset scrollTop might happen, let's trust scrollTop 
                         //  adjustment isn't needed or handle via relative bottom if we tracked it.)
                         //  
                         // Simpler fallback: If reading history and that history is gone, 
                         // we probably end up at top.
                    }
                }
            }
            
            // On Scroll Event to detect manual scroll up
            logViewer.onscroll = function() {
                // If user scrolls up (is not at bottom), disable auto-scroll
                if (logViewer.scrollHeight - logViewer.scrollTop - logViewer.clientHeight > 50) {
                    window.autoScrollEnabled = false;
                    document.getElementById('scroll-btn').style.display = 'block';
                } else {
                    // If user scrolls back to bottom, re-enable auto-scroll
                    window.autoScrollEnabled = true;
                    document.getElementById('scroll-btn').style.display = 'none';
                }
            };
            
            // Update Info Stats if present
            if (data.info) {
                 // We might want to render this dynamically or just update specific fields if we add them to the DOM
            }
            
            // Update Processes via WS if modal is open (data.processes provided by backend now)
            if (data.processes) {
                updateProcessTable(data.processes);
            }
        });
    </script>
</body>
</html>
"""

class WebServer:
    def __init__(self, agent):
        self.agent = agent
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        self.port = 5001  # Changed from 5000 due to port conflict
        self.thread = None
        self.public_url = None
        self.manual_stop = False # Track intentional stops
        self.docs_dir = os.path.abspath("documentation")
        self.connected_clients = 0 # Track active WS connections
        self.start_time = 0 # Track server start time for auto-shutdown
        
        # Cache for process objects to get accurate CPU % (needs state)
        self.process_cache = {}
        
        # Configure routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/docs', 'docs_list', self.docs_list)
        self.app.add_url_rule('/docs/<path:filename>', 'docs_view', self.docs_view)
        self.app.add_url_rule('/search', 'search_docs', self.search_docs)
        self.app.add_url_rule('/api/processes', 'get_processes', self.get_processes)
        self.app.add_url_rule('/test', 'test', lambda: "Flask is running! ✅")
        
        # Endpoint /shutdown removed per user request.
        # Shutdown is now handled via manual_stop flag checked in _emit_updates loop.
        
        # SocketIO Event Handlers
        @self.socketio.on('connect')
        def handle_connect():
            self.connected_clients += 1
            logger.info(f"Client connected. Active clients: {self.connected_clients}")
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            if self.connected_clients > 0:
                self.connected_clients -= 1
            logger.info(f"Client disconnected. Active clients: {self.connected_clients}")
        
        # Disable Flask logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        @self.app.before_request
        def generate_nonce():
            g.nonce = secrets.token_hex(16)

        @self.app.context_processor
        def inject_nonce():
            return dict(nonce=g.nonce)

        @self.app.after_request
        def add_security_headers(response):
            # CVE-2025-XSS Mitigation - Best Practice
            # Strict CSP with Nonce (Blocking unsafe-inline)
            # allow cdnjs for socket.io if nonce fails (but nonce should work)
            nonce = getattr(g, 'nonce', '')
            csp = (
                f"default-src 'self'; "
                f"script-src 'self' 'nonce-{nonce}' https://cdnjs.cloudflare.com; "
                f"style-src 'self' 'nonce-{nonce}'; "
                f"connect-src 'self'; "
                f"img-src 'self' data:; "
                f"font-src 'self'; "
                f"object-src 'none'; "
                f"base-uri 'self';"
            )
            response.headers['Content-Security-Policy'] = csp
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            return response
    
    def index(self):
        """Main dashboard."""
        import psutil
        
        # System Stats
        cpu_percent = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get consistent RAM usage from processes
        proc_data = self.get_processes_data()
        total_mem_from_procs = proc_data.get('total_mem_bytes', 0)
        
        if total_mem_from_procs > 0:
            ram_used_val = total_mem_from_procs
            ram_percent_val = (total_mem_from_procs / ram.total) * 100
        else:
            ram_used_val = ram.used
            ram_percent_val = ram.percent
        
        # Format bytes to GB
        def to_gb(bytes_val):
            return f"{bytes_val / (1024**3):.1f} GB"
            
        ram_percent = f"{ram_percent_val:.1f}"
        ram_used = to_gb(ram_used_val)
        ram_total = to_gb(ram.total)
        
        disk_percent = disk.percent
        disk_used = to_gb(disk.used)
        disk_total = to_gb(disk.total)

        # Prepare Activity List HTML
        import datetime
        activity_items = []
        if self.agent.action_history:
            for item in reversed(self.agent.action_history[-5:]):
                if isinstance(item, dict):
                    ts = datetime.datetime.fromtimestamp(item.get('timestamp', 0)).strftime('%H:%M:%S')
                    act = item.get('action', 'Unknown')
                    activity_items.append(f'<li><span style="color: #72767d; font-size: 0.9em;">[{ts}]</span> {act}</li>')
                else:
                    activity_items.append(f'<li>{item}</li>')
            activity_list_html = "".join(activity_items)
        else:
            activity_list_html = '<li>No recent activity</li>'

        status_html = f"""
        <div class="dashboard-header">
            <div class="dashboard-title">🤖 Agent Dashboard</div>
            <div class="status-wrapper">
                <div id="connection-status" class="connection-status">● Connecting...</div>
                <div id="stats-info" class="stats-info"></div>
            </div>
        </div>
        
        <div class="status-card">
            <div class="status-row">
                <div class="status-col">
                    <div class="status-item">
                        <span class="status-label">Status:</span> 
                        <span id="status-running">{'🟢 Running' if self.agent.is_running else '🔴 Stopped'}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Boredom:</span> 
                        <span id="status-boredom">{self.agent.boredom_score * 100:.1f}%</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Uptime:</span> 
                        <span id="status-uptime">{self._get_uptime()}</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Tools Learned:</span> 
                        <span id="status-tools">{len([t for t, c in self.agent.tool_usage_count.items() if c > 0])} / {len(self.agent.tools.tools)}</span>
                    </div>
                </div>
                <div class="status-col">
                    <div class="status-item"><span class="status-label">Boredom loop:</span> <span id="loop-boredom">Loading...</span></div>
                    <div class="status-item"><span class="status-label">Observation loop:</span> <span id="loop-observation">Loading...</span></div>
                    <div class="status-item"><span class="status-label">Action loop:</span> <span id="loop-action">Loading...</span></div>
                    <div class="status-item"><span class="status-label">Backup loop:</span> <span id="loop-backup">Loading...</span></div>
                </div>
            </div>
        </div>

        <div class="status-card">
            <div class="resources-header">
                <h3 class="resources-title">🖥️ System Resources</h3>
                <button id="details-btn" class="detail-btn">🔍 Details</button>
            </div>
            <div class="status-item">
                <span class="status-label">CPU Usage:</span> 
                <span id="res-cpu">{cpu_percent}%</span>
            </div>
            <div class="status-item">
                <span class="status-label">RAM Usage:</span> 
                <span id="res-ram">{ram_percent}% ({ram_used} / {ram_total})</span>
            </div>
            <div class="status-item">
                <span class="status-label">Disk Usage:</span> 
                <span id="res-disk">{disk_percent}% ({disk_used} / {disk_total})</span>
            </div>
        </div>
        
        <div class="status-card">
            <h3>ℹ️ System Info</h3>
            <div class="status-item"><span class="status-label">OS:</span> {self._get_os_info()} running on {self._get_hardware_info()}</div>
            <div class="status-item"><span class="status-label">Python:</span> {platform.python_version()}</div>
            <div class="status-item"><span class="status-label">LLM Model:</span> {self._get_llm_display_name()}</div>
            <div class="status-item"><span class="status-label">Project Version:</span> Beta - CLOSED</div>
        </div>
        
        <h3>Recent Activity</h3>

        <ul id="activity-list">
        {activity_list_html}
        </ul>
        
        <h3>📜 Log Viewer</h3>
        <div class="log-wrapper">
            <div id="log-viewer" class="log-viewer">Loading logs...</div>
            <button id="scroll-btn" style="display: none;">⬇️ Resume Auto-scroll</button>
        </div>
        
        <!-- Modal -->
        <div id="processModal" class="modal">
            <div class="modal-content">
                <span id="modal-close-btn" class="close">&times;</span>
                <h2>📊 Resource Details</h2>
                
                <h3>🔥 Top CPU</h3>
                <table class="proc-table" id="cpu-table">
                    <tr><th>PID</th><th>Name</th><th>CPU %</th></tr>
                    <tr><td colspan="3">Loading...</td></tr>
                </table>
                
                <h3>💾 Top RAM</h3>
                <table class="proc-table" id="ram-table">
                    <tr><th>PID</th><th>Name</th><th>RAM (MB)</th></tr>
                    <tr><td colspan="3">Loading...</td></tr>
                </table>
            </div>
        </div>


        """
        
        return render_template_string(
            TEMPLATE_BASE, 
            title="Dashboard", 
            update_interval=config_settings.WEB_WEBSOCKET_UPDATE_INTERVAL,
            content=status_html, 
            css=DOCS_CSS + """
            .log-wrapper { position: relative; }
            .log-viewer { width: 100%; }
            #scroll-btn { 
                position: absolute; 
                top: 10px; 
                right: 20px; 
                background: rgba(88, 101, 242, 0.8); /* 80% opacity */
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 4px; 
                cursor: pointer; 
                z-index: 10;
                transition: transform 0.2s, background-color 0.2s;
            }
            #scroll-btn:hover {
                background: rgba(88, 101, 242, 1.0);
                transform: scale(1.05);
            }
            @media (max-width: 768px) {
                #scroll-btn { 
                    padding: 12px 18px; /* Larger padding for mobile */
                    font-size: 1.1em;   /* Larger text for mobile */
                }
            }
            """
        )

    def docs_list(self):
        """List available documentation organized by category and subcategory."""
        if not os.path.exists(self.docs_dir):
            return render_template_string(TEMPLATE_BASE, title="Docs", css=DOCS_CSS, content="<p>No documentation directory found.</p>")
            
        # Define categories structure
        # Key: Category Title
        # Value: Dict with 'paths' (list of folders/files) and optional 'subgroups' (dict of Subgroup Title -> list of filenames)
        structure = {
            "🏁 Start Here (Hlavní)": {
                "paths": ["", "README.md", "INDEX.md", "OVERVIEW.md", "SUMMARY.md", "architecture.md", "troubleshooting.md"],
                "priority_files": ["README.md", "INDEX.md", "OVERVIEW.md"] # Sort order
            },
            "💬 Discord Příkazy": {
                "paths": ["commands"],
                # Just flat list is fine for commands, but we could map filenames to nice names if we wanted
            },
            "🧠 Core Systémy": {
                "paths": ["core"],
                "subgroups": {
                    "Intelligence & Chování": ["autonomous-behavior.md", "llm-integration.md"],
                    "Paměť a Data": ["memory-system.md", "reporting.md"],
                    "Infrastruktura": ["resource-manager.md", "discord-client.md", "web-interface.md"]
                }
            },
            "🛠️ Nástroje": {
                "paths": ["tools"]
            },
            "⚙️ Konfigurace": {
                "paths": ["configuration"]
            },
            "💻 Developer API": {
                "paths": ["api"],
                "subgroups": {
                    "Core Components": ["agent-core.md", "memory-system.md", "tools-api.md"],
                    "Integrations": ["discord-client.md", "llm-integration.md"],
                    "System & Utils": ["error-tracker.md", "hardware-monitor.md", "utils-sanitizer.md", "utils-startup.md", "api-logs.md", "entry-point.md"]
                }
            },
            "📝 Skripty a Utility": {
                "paths": ["scripts"]
            },
            "🔍 Pokročilé": {
                "paths": ["advanced"]
            }
        }
        
        # Collect all files first
        all_files = []
        for root, dirs, filenames in os.walk(self.docs_dir):
            for f in filenames:
                if f.endswith('.md'):
                    rel_path = os.path.relpath(os.path.join(root, f), self.docs_dir).replace('\\', '/')
                    all_files.append(rel_path)
        
        categorized_files = set()
        html_content = "<h1>📚 Dokumentace</h1>"
        html_content += "<p>Procházejte dokumentaci podle kategorií.</p>"
        
        for category, config in structure.items():
            cat_paths = config.get("paths", [])
            subgroups = config.get("subgroups", {})
            priority = config.get("priority_files", [])
            
            # Find files belonging to this category
            files_in_cat = []
            if "" in cat_paths: # Root files
                for f in all_files:
                     if "/" not in f and f in cat_paths:
                         files_in_cat.append(f)
            else: # Folder based
                for folder in cat_paths:
                    for f in all_files:
                        if f.startswith(f"{folder}/"):
                            files_in_cat.append(f)
            
            if not files_in_cat:
                continue

            inner_html = ""
            
            # If subgroups are defined, group files
            if subgroups:
                # Track which files are in subgroups
                grouped_files = set()
                
                for group_name, filenames in subgroups.items():
                    group_files_found = []
                    for f in files_in_cat:
                        fname = os.path.basename(f)
                        if fname in filenames:
                            group_files_found.append(f)
                            grouped_files.add(f)
                            categorized_files.add(f)
                    
                    if group_files_found:
                        # Sort by defined order in subgroups
                        group_files_found.sort(key=lambda x: filenames.index(os.path.basename(x)))
                        
                        group_list = ""
                        for f in group_files_found:
                            display_name = os.path.basename(f)
                            group_list += f'<li><a href="/docs/{f}">{display_name}</a></li>'
                        
                        inner_html += f'<h4 style="margin-top: 10px; margin-bottom: 5px; color: #b9bbbe; border-bottom: 1px solid #40444b; padding-bottom: 2px;">{group_name}</h4>'
                        inner_html += f'<ul style="margin-top: 5px;">{group_list}</ul>'
                
                # Handle leftovers in this category that weren't in a subgroup
                leftovers = [f for f in files_in_cat if f not in grouped_files]
                if leftovers:
                    leftovers.sort()
                    leftover_list = ""
                    for f in leftovers:
                         display_name = os.path.basename(f)
                         leftover_list += f'<li><a href="/docs/{f}">{display_name}</a></li>'
                         categorized_files.add(f)
                    
                    if inner_html: # If we had groups, label the others
                        inner_html += f'<h4 style="margin-top: 10px; margin-bottom: 5px; color: #b9bbbe; border-bottom: 1px solid #40444b; padding-bottom: 2px;">Ostatní</h4>'
                    inner_html += f'<ul style="margin-top: 5px;">{leftover_list}</ul>'

            else:
                # No subcategories, just list them
                # Sort logic
                if priority:
                    files_in_cat.sort(key=lambda x: priority.index(x) if x in priority else 999)
                else:
                    files_in_cat.sort()
                    
                list_html = ""
                for f in files_in_cat:
                    display_name = os.path.basename(f)
                    if display_name == f: # It's a root file or full path view
                        display_name = f
                    else:
                        display_name = display_name # Show just filename for cleanness
                        
                    list_html += f'<li><a href="/docs/{f}">{display_name}</a></li>'
                    categorized_files.add(f)
                inner_html = f'<ul>{list_html}</ul>'
            
            html_content += f'''
            <div class="status-card" style="margin-bottom: 20px;">
                <h3>{category}</h3>
                {inner_html}
            </div>
            '''

        # Catch-all for uncategorized
        uncategorized = [f for f in all_files if f not in categorized_files]
        if uncategorized:
             uncategorized.sort()
             other_html = ""
             for f in uncategorized:
                 other_html += f'<li><a href="/docs/{f}">{f}</a></li>'
             
             html_content += f'''
                <div class="status-card" style="margin-bottom: 20px;">
                    <h3>📂 Ostatní soubory</h3>
                    <ul>{other_html}</ul>
                </div>
                '''
        
        return render_template_string(TEMPLATE_BASE, title="Documentation", css=DOCS_CSS, content=html_content)

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
        
        # Joke XSS Detection
        import re
        xss_detected = False
        # Detects tags, protocols, event handlers (on...), and dangerous functions
        xss_pattern = re.compile(r'(<(script|iframe|object|embed|svg|style|link|meta)|(javascript|vbscript):|\bon\w+\s*=| (alert|prompt|confirm|eval|setTimeout|setInterval)\s*\()', re.IGNORECASE)
        if xss_pattern.search(query):
            query = "dobrý pokus 😉"
            xss_detected = True
        
        results = []
        query_lower = query.lower()
        
        # Search through all .md files (Skip if XSS detected)
        search_iter = os.walk(self.docs_dir) if not xss_detected else []
        for root, dirs, filenames in search_iter:
            for f in filenames:
                if f.endswith('.md'):
                    file_path = os.path.join(root, f)
                    rel_path = os.path.relpath(file_path, self.docs_dir).replace('\\', '/')
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            original_lines = file.readlines()
                            content = ''.join(original_lines)
                            
                            # Remove navigation blocks (all lines starting with >)
                            # Filter out blockquote lines (navigation, metadata, etc.)
                            content_lines = content.split('\n')
                            
                            # Debug: count removed lines
                            removed_lines = [line for line in content_lines if line.strip().startswith('>')]
                            if removed_lines:
                                logger.info(f"Filtering {len(removed_lines)} navigation lines from {rel_path}")
                            
                            filtered_content_lines = [line for line in content_lines if not line.strip().startswith('>')]
                            content_cleaned = '\n'.join(filtered_content_lines)
                            
                            # Create filtered lines for anchor detection (with newlines)
                            filtered_lines = [line + '\n' for line in filtered_content_lines]
                            
                            content_lower = content_cleaned.lower()
                            
                            # Find all occurrences (exact + fuzzy)
                            import re
                            matches = []
                            
                            # Split query into words for fuzzy matching
                            query_words = query_lower.split()
                            
                            # 1. Exact phrase matching
                            import html
                            # Escape query for regex to match against HTML-escaped snippet
                            escaped_query_for_regex = re.escape(html.escape(query))
                            
                            for match in re.finditer(re.escape(query_lower), content_lower):
                                pos = match.start()
                                
                                # Check if this match is inside a markdown link or anchor
                                # Find the line containing this match
                                line_start = content_cleaned.rfind('\n', 0, pos) + 1
                                line_end = content_cleaned.find('\n', pos)
                                if line_end == -1:
                                    line_end = len(content_cleaned)
                                match_line = content_cleaned[line_start:line_end]
                                
                                # Skip if line contains markdown link with query: [text](url)
                                link_pattern = r'\[([^\]]*' + re.escape(query_lower) + r'[^\]]*)\]\([^\)]+\)'
                                if re.search(link_pattern, match_line, re.IGNORECASE):
                                    continue
                                
                                # Skip if line contains HTML anchor with query: <a name="...query..."></a>
                                anchor_pattern = r'<a\s+name="[^"]*' + re.escape(query_lower) + r'[^"]*"[^>]*></a>'
                                if re.search(anchor_pattern, match_line, re.IGNORECASE):
                                    continue
                                
                                anchor = self._find_nearest_anchor(filtered_lines, pos)
                                # Show small context before, match, and text after
                                start = max(0, pos - 30)
                                end = min(len(content_cleaned), pos + len(query) + 120)
                                snippet = content_cleaned[start:end].replace('<', '&lt;').replace('>', '&gt;')
                                
                                # Highlight exact match
                                import re as regex
                                snippet = regex.sub(f'({escaped_query_for_regex})', 
                                                   r'<strong class="highlight-exact">\1</strong>', 
                                                   snippet, flags=regex.IGNORECASE)
                                
                                matches.append({
                                    'anchor': anchor,
                                    'snippet': f'...{snippet}...',
                                    'score': 100  # Exact match gets highest score
                                })
                            
                            # 2. Fuzzy word matching (if query is single word or short)
                            if len(query_words) <= 3:  # Only for short queries
                                # Track word positions for accurate snippet extraction
                                word_positions = []
                                for match in re.finditer(r'\b\w+\b', content_lower):
                                    word_positions.append((match.group(), match.start()))
                                
                                for word, word_pos in word_positions:
                                    for query_word in query_words:
                                        if len(query_word) >= 4:  # Only fuzzy match longer words
                                            distance = levenshtein_distance(query_word, word)
                                            # Allow up to 2 character difference
                                            threshold = 2
                                            
                                            if distance <= threshold and distance > 0:
                                                # Check if this match is inside a markdown link or anchor
                                                # Find the line containing this match
                                                line_start = content_cleaned.rfind('\n', 0, word_pos) + 1
                                                line_end = content_cleaned.find('\n', word_pos)
                                                if line_end == -1:
                                                    line_end = len(content_cleaned)
                                                match_line = content_cleaned[line_start:line_end]
                                                
                                                # Skip if line contains markdown link with query word
                                                link_pattern = r'\[([^\]]*' + re.escape(query_word) + r'[^\]]*)\]\([^\)]+\)'
                                                if re.search(link_pattern, match_line, re.IGNORECASE):
                                                    continue
                                                
                                                # Skip if line contains HTML anchor with query word
                                                anchor_pattern = r'<a\s+name="[^"]*' + re.escape(query_word) + r'[^"]*"[^>]*></a>'
                                                if re.search(anchor_pattern, match_line, re.IGNORECASE):
                                                    continue
                                                
                                                # Use the actual word position from regex match
                                                anchor = self._find_nearest_anchor(filtered_lines, word_pos)
                                                # Show small context before, match, and text after
                                                start = max(0, word_pos - 30)
                                                end = min(len(content_cleaned), word_pos + len(word) + 120)
                                                snippet = content_cleaned[start:end].replace('<', '&lt;').replace('>', '&gt;')
                                                
                                                # Highlight fuzzy match (case-insensitive replacement)
                                                snippet = re.sub(re.escape(word), f'<strong class="highlight-fuzzy">{word}</strong>', snippet, flags=re.IGNORECASE)
                                                
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
        import html
        safe_query = html.escape(query)
        results_html = f"<h1>🔍 Výsledky vyhledávání: '{safe_query}'</h1>"
        results_html += f"<p><a href='/docs'>← Zpět na dokumentaci</a></p>"
        
        # Add legend
        results_html += '''
        <div class="status-card" style="margin-bottom: 20px; padding: 16px;">
            <h3 style="margin-top: 0;">📖 Nápověda</h3>
            <p style="margin: 8px 0;">
                <strong class="highlight-exact">Zelená</strong> 
                = Přesná shoda
            </p>
            <p style="margin: 8px 0;">
                <strong class="highlight-fuzzy">Oranžová</strong> 
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

    def _get_log_tail(self, lines=100):
        """Get the last N lines of the agent log."""
        log_file = "agent.log"
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Seek to end and read back a bit to save memory if file is huge, 
                    # but for now simple readlines is fine for < 100MB logs
                    all_lines = f.readlines()
                    last_lines = all_lines[-lines:]
                    
                    # Filter out spammy/verbose logs
                    ignored_phrases = ['msg="join connections"', 'navigation lines from']
                    filtered_lines = [l for l in last_lines if not any(phrase in l for phrase in ignored_phrases)]
                    
                    # Sanitize and colorize each line
                    processed_lines = [sanitize_log_line(line) for line in filtered_lines]
                    return "".join(processed_lines)
            except Exception as e:
                return f"Error reading log: {e}"
        return "Log file not found."

    def _get_llm_display_name(self):
        """Parses model filename to friendly name."""
        import re
        filename = getattr(self.agent.llm, 'model_filename', 'Unknown')
        if filename == 'Unknown':
             # Try to fallback to model_repo if filename missing
             return getattr(self.agent.llm, 'model_repo', 'Unknown')
            
        # Example: qwen2.5-0.5b-instruct-q4_k_m.gguf -> QWEN 2.5 0.5b - instruct
        try:
            name = filename.lower()
            if 'qwen' in name:
                # Remove extension and quantization tag
                clean_name = name.replace('.gguf', '').replace('-q4_k_m', '')
                
                # Split qwen2.5 -> qwen, 2.5
                if 'qwen' in clean_name:
                    # qwen2.5-0.5b-instruct -> ['qwen2.5', '0.5b', 'instruct']
                    parts = clean_name.split('-')
                    base = parts[0] # qwen2.5
                    
                    # Extract version from base (2.5 from qwen2.5)
                    version_match = re.search(r'qwen([\d\.]+)', base)
                    ver = version_match.group(1) if version_match else ""
                    
                    # Join specific parts e.g. "0.5b - instruct"
                    rest = " - ".join(parts[1:])
                    
                    return f"QWEN {ver} {rest}".strip()
                    
            return filename
        except Exception as e:
            logger.error(f"Error parsing LLM name: {e}")
            return filename

    def _get_hardware_info(self):
        """Attempts to get specific hardware model."""
        try:
            # Raspberry Pi specific check
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().strip()
                    # Simplify model name: "Raspberry Pi 4 Model B Rev 1.5" -> "Raspberry Pi 4B"
                    import re
                    # Replace " Model X Rev Y.Y" with "X"
                    # Capture "Raspberry Pi N" and "Model X"
                    simple_model = re.sub(r' Model ([A-Z]) Rev [\d\.]+', r'\1', model)
                    
                    # Get RAM
                    import psutil
                    total_ram_gb = round(psutil.virtual_memory().total / (1024**3))
                    
                    return f"{simple_model} ({total_ram_gb}GB)"
            
            # Fallback
            return platform.machine()
        except:
            return "Unknown Hardware"

    def _get_os_info(self):
        """Returns formatted OS string: Linux (debian) <version>"""
        sys_name = platform.system() # Linux
        release = platform.release().replace("+rpt-rpi-v8", "") # 6.12...
        
        distro = ""
        if sys_name == "Linux":
            try:
                # Try to get distribution ID
                import re
                if os.path.exists('/etc/os-release'):
                    with open('/etc/os-release') as f:
                        content = f.read()
                        # Look for ID=debian or ID="debian"
                        match = re.search(r'^ID=["\']?([^"\'\n\r]+)["\']?', content, re.MULTILINE)
                        if match:
                            distro = f"({match.group(1)}) "
            except:
                pass
                
        return f"{sys_name} {distro}{release}"

    def _emit_updates(self):
        """Background task to emit status updates via WebSocket."""
        import config_settings
        import time
        import psutil
        import platform
        
        interval = getattr(config_settings, 'WEB_WEBSOCKET_UPDATE_INTERVAL', 2)
        logger.info(f"WebSocket update loop started (interval: {interval}s)")
        
        while True:
            # Check for manual stop signal
            if self.manual_stop:
                logger.info("Manual stop signal received in background task. Stopping SocketIO...")
                self.socketio.stop()
                break
                
            # 1. Check Auto-Shutdown (Configurable timeout)
            timeout = getattr(config_settings, 'WEB_INTERFACE_TIMEOUT', 3600)
            if self.start_time > 0 and (time.time() - self.start_time) > timeout:
                logger.info(f"⏱️ Web server auto-shutdown: {timeout/3600:.1f} hour limit reached.")
                self.stop()
                continue # loop will catch manual_stop on next iter
                
            # 2. Check Active Clients (Pause if 0)
            if self.connected_clients <= 0:
                # Wait a bit and continue to save resources
                time.sleep(1)
                continue

            try:
                # Get Process Data First (includes total mem sum)
                proc_data = self.get_processes_data()
                total_mem_from_procs = proc_data.get('total_mem_bytes', 0)
                
                # Gather stats
                cpu_percent = psutil.cpu_percent()
                ram = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Override RAM stats with sum of processes (for consistency)
                # Keep total from system, but used/percent from sum
                if total_mem_from_procs > 0:
                     ram_used_val = total_mem_from_procs
                     ram_percent_val = (total_mem_from_procs / ram.total) * 100
                else:
                     ram_used_val = ram.used
                     ram_percent_val = ram.percent

                def to_gb(bytes_val):
                    return f"{bytes_val / (1024**3):.1f} GB"
                
                # Check Loop Status
                loop_status = {}
                loop_names = ['boredom_loop', 'observation_loop', 'action_loop', 'backup_loop']
                if hasattr(self.agent, 'loop_tasks'):
                    for i, task in enumerate(self.agent.loop_tasks):
                        name = loop_names[i] if i < len(loop_names) else f'loop_{i}'
                        if not task.done():
                            loop_status[name] = '🟢 Running'
                        else:
                            loop_status[name] = '🔴 Stopped'
                else:
                    for name in loop_names:
                        loop_status[name] = '❌ Not Init'

                stats = {
                    'is_running': self.agent.is_running,
                    'loop_status': loop_status,
                    'boredom_score': self.agent.boredom_score,
                    'uptime': self._get_uptime(),
                    'tools_used': len([t for t, c in self.agent.tool_usage_count.items() if c > 0]),
                    'tools_total': len(self.agent.tools.tools),
                    'cpu_percent': cpu_percent,
                    'ram_percent': round(ram_percent_val, 1),
                    'ram_used': to_gb(ram_used_val),# Format bytes to GB
                    'ram_total': to_gb(ram.total),
                    'disk_percent': disk.percent,
                    'disk_used': to_gb(disk.used),
                    'disk_total': to_gb(disk.total),
                    'action_history': self.agent.action_history[-20:] if self.agent.action_history else [],
                    'log_tail': self._get_log_tail(),
                    'connected_clients': self.connected_clients,
                    'info': {
                        'os': self._get_os_info(),
                        'python': platform.python_version(),
                        'agent_version': getattr(config_settings, 'AGENT_VERSION', 'Unknown')
                    },
                    'processes': proc_data
                }
                
                self.socketio.emit('status_update', stats)
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error emitting updates: {e}")
                time.sleep(5)

    def start(self):
        """Start the Flask server on an available port."""
        import time
        self.manual_stop = False # Reset manual stop flag
        self.start_time = time.time() # Start timer for auto-shutdown
        self.connected_clients = 0 # Reset client count
        
        if self.thread and self.thread.is_alive():
            return

        # Find an available port starting from 5001
        import socket
        import psutil
        
        found_port = None
        for port in range(5001, 5051): # Expanded range to match cleanup
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
            logger.error("Could not find any available port for Web Interface (5001-5051). Web server will NOT start.")
            # We should probably notify the user via Discord if possible, but this is a synchronous method called during startup.
            # The agent will continue without web interface.

    def _run_flask(self):
        try:
            logger.info(f"Flask SocketIO server starting on {self.port}...")
            # Disable Flask's default logging to reduce noise
            import logging as flask_logging
            flask_log = flask_logging.getLogger('werkzeug')
            flask_log.setLevel(flask_logging.ERROR)
            
            # Start background task
            self.socketio.start_background_task(self._emit_updates)
            
            self.socketio.run(self.app, host='0.0.0.0', port=self.port, use_reloader=False, allow_unsafe_werkzeug=True)
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
            # Check if ngrok is already running for this port
            # Add retry logic for get_tunnels as it might timeout during heavy load/startup
            tunnels = []
            for attempt in range(3):
                try:
                    tunnels = ngrok.get_tunnels()
                    break
                except Exception as e:
                    logger.warning(f"ngrok.get_tunnels failed (attempt {attempt+1}/3): {e}")
                    time.sleep(1 * (attempt + 1))
            
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
        # Signal background loop to stop
        self.manual_stop = True
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

    def get_processes_data(self):
        """Internal helper to get process data using cache for accurate CPU."""
        import psutil
        import os
        try:
            # 1. Update cache with current processes
            current_pids = set()
            procs_info = []
            total_mem_usage = 0
            
            # Get totals for normalization
            cpu_count = psutil.cpu_count() or 1
            total_mem = psutil.virtual_memory().total
            
            for p in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    pid = p.info['pid']
                    current_pids.add(pid)
                    
                    # Get or Create Process Object in Cache
                    if pid not in self.process_cache:
                        self.process_cache[pid] = p
                    
                    proc_obj = self.process_cache[pid]
                    
                    # Ensure process is still running with this PID
                    if not proc_obj.is_running():
                        continue
                        
                    # Get Stats
                    # cpu_percent(interval=None) calculates % since last call.
                    # This returns value summed across cores (can be > 100%).
                    raw_cpu = proc_obj.cpu_percent(interval=None)
                    
                    # Normalize to 0-100% System Scale
                    normalized_cpu = raw_cpu / cpu_count
                    
                    # Memory: PSS (Proportional) is best for summing up to Total.
                    # USS (Unique) is strict private. RSS is total resident (includes shared).
                    mem_bytes = 0
                    metric_used = "unknown"
                    try:
                        # memory_full_info is expensive but needed for PSS/USS
                        mem_info = proc_obj.memory_full_info()
                        # Try PSS first, then USS, then fallback to RSS
                        if hasattr(mem_info, 'pss'):
                            mem_bytes = mem_info.pss
                            metric_used = "pss"
                        elif hasattr(mem_info, 'uss'):
                            mem_bytes = mem_info.uss
                            metric_used = "uss"
                        else:
                            mem_bytes = mem_info.rss
                            metric_used = "rss"
                    except (psutil.AccessDenied, AttributeError):
                        # Fallback for permission errors or missing attrs
                        mem_info = proc_obj.memory_info()
                        mem_bytes = mem_info.rss
                        # Try to subtract shared memory to approximate private/USS
                        if hasattr(mem_info, 'shared'):
                            mem_bytes -= mem_info.shared
                            metric_used = "rss_minus_shared"
                        else:
                            metric_used = "rss_fallback"

                    if pid == os.getpid() and not hasattr(self, '_mem_debug_logged'):
                        logger.debug(f"Process Memory Metric: {metric_used} | Val: {mem_bytes/1024/1024:.1f}MB")
                        self._mem_debug_logged = True
                        
                    mem_mb = round(mem_bytes / (1024 * 1024), 1)
                    mem_percent = (mem_bytes / total_mem) * 100
                    
                    total_mem_usage += mem_bytes
                    
                    procs_info.append({
                        'pid': pid,
                        'name': p.info['name'],
                        'cpu_percent': normalized_cpu,
                        'memory_mb': mem_mb,
                        'memory_percent': mem_percent
                    })
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Clean up cache
            cached_pids = list(self.process_cache.keys())
            for old_pid in cached_pids:
                if old_pid not in current_pids:
                    del self.process_cache[old_pid]
                    
            # Sort Top 5 (Sort by Percent)
            top_cpu = sorted(procs_info, key=lambda x: x['cpu_percent'], reverse=True)[:5]
            top_mem = sorted(procs_info, key=lambda x: x['memory_percent'], reverse=True)[:5]
            
            return {'cpu': top_cpu, 'memory': top_mem, 'total_mem_bytes': total_mem_usage}
            
        except Exception as e:
            logger.error(f"Error getting process data: {e}")
            return {'cpu': [], 'memory': [], 'total_mem_bytes': 0}

    def get_processes(self):
        """API Endpoint."""
        return jsonify(self.get_processes_data())
