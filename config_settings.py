# Configuration Settings

# Core Settings
ADMIN_USER_IDS = [512658574875557889]  # Discord user IDs with admin access
MODEL_CACHE_DIR = "./models/"

# Location Settings
DEFAULT_LOCATION = "Frýdek-Místek"  # Default location for weather, time queries, etc.

# Resource Management
RESOURCE_TIER_1_THRESHOLD = 80  # Warning & Cleanup %
RESOURCE_TIER_2_THRESHOLD = 90  # Active mitigation %
RESOURCE_TIER_3_THRESHOLD = 95  # Emergency mode %

# Dynamic SWAP Configuration
ENABLE_DYNAMIC_SWAP = True
SWAP_MIN_SIZE_GB = 2
SWAP_MAX_SIZE_GB = 8

# LLM Resource Adaptation
LLM_CONTEXT_NORMAL = 2048
LLM_CONTEXT_TIER1 = 2048
LLM_CONTEXT_TIER2 = 1024
LLM_CONTEXT_TIER3 = 1024

# Boredom System
BOREDOM_INTERVAL = 300  # Time in seconds between boredom checks (5 minutes)
TOPICS_FILE = "boredom_topics.json"  # Path to topics JSON file

# Memory Scoring System
MEMORY_CONFIG = {
    "MIN_SCORE_TO_SAVE": 70,           # Minimum score required to save memory
    "KEYWORDS": ["def", "class", "api", "návod", "fix", "tool", "python", "code"],
    "KEYWORD_BONUS": 10,                # Points per matching keyword
    "BLACKLIST": ["error", "chyba"],
    "ERROR_PENALTY": -20,               # Penalty for error-containing content
    "UNIQUENESS_BONUS": 30,             # Bonus for unique content
    "UNIQUENESS_THRESHOLD": 0.90        # Similarity threshold for uniqueness check
}

# GitHub Release Management
GITHUB_UPLOAD_MIN_INTERVAL = 2 * 60 * 60  # Minimum 2 hours between uploads (in seconds)
GITHUB_REPO_NAME = "davca2848123/AI_agent"

# Error Recovery System
STARTUP_RETRY_LIMIT = 3  # Maximum consecutive startup failures before long wait
STARTUP_FAILURE_WAIT = 6 * 60 * 60  # 6 hours wait after exceeding retry limit (in seconds)

# Documentation
DOCUMENTATION_WEB_URL = "http://localhost:5001/docs"  # URL for web documentation (will be ngrok URL when available)

# Web Interface
WEB_DASHBOARD_REFRESH_INTERVAL = 10
WEB_SERVER_AUTO_RESTART = True  # Seconds between dashboard auto-refreshes

# Web Interface
WEB_INTERFACE_TIMEOUT = 1 * 60 * 60  # Auto-shutdown after 1 hour of inactivity (in seconds)

# Fuzzy Command Matching
FUZZY_MATCH_DISTANCE_BASE_COMMANDS = 2      # Max Levenshtein distance for base commands (e.g., !help → !helps)
FUZZY_MATCH_DISTANCE_SUBCOMMANDS = 4        # Max Levenshtein distance for subcommands (e.g., !web strat → !web start)

# Security - IP Address Sanitization
IP_SANITIZATION_ENABLED = True  # Enable global IP masking in console/Discord output

# Admin Restricted Shell Commands
# These commands are blocked even for admins unless explicitly allowed in code
ADMIN_RESTRICTED_COMMANDS = ["sudo", "shutdown", "reboot", "kill", "rm -rf", "mkfs", "dd", ":(){ :|:& };:"]
