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
    "ERROR_PENALTY": -20,               # Penalty for error-containing content
    "KEYWORDS": ["def", "class", "api", "návod", "fix", "tool", "python", "code"],
    "KEYWORD_BONUS": 10,                # Points per matching keyword
    "BLACKLIST": ["error", "chyba"],
    "UNIQUENESS_BONUS": 30,             # Bonus for unique content
    "UNIQUENESS_THRESHOLD": 0.90        # Similarity threshold for uniqueness check
}

# Security - IP Address Sanitization
IP_SANITIZATION_ENABLED = True  # Enable global IP masking in console/Discord output
