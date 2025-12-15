# Changelog

## [Beta - Ongoing] - 2025-12-15

### Fixed
- **Web Interface Version**: Updated the web dashboard "System Info" to display the correct project version dynamically from `config_settings.AGENT_VERSION` instead of a hardcoded string.
- **Web Log Viewer**: Fixed log line sanitization to preserve indentation (using `rstrip` instead of `strip`). This ensures that stack traces and formatted logs are displayed correctly in the web dashboard.
- **Daily Stats Pinning**: Implemented automatic pinning of Daily Reports in the Admin DM. The agent now automatically unpins previous reports and pins the new one, keeping the latest stats easily accessible.
- **Agent Tools Error**: Fixed a critical `TypeError` in `WebTool` where missing optional arguments caused crashes during autonomous execution. The tool now safely handles dynamic arguments.
- **LLM Initialization**: Downgraded "llama-cpp-python not installed" from ERROR to WARNING when Gemini is successfully configured, preventing false alarms for users relying on cloud models.
- **Restart Notification**: Fixed "Channel not found" error during restart. The agent now validates the channel existence before attempting to send the "Restarted successfully" message.
- **Network Resilience**: Enhanced Discord client stability by adding specific handling and exponential backoff for `ClientConnectorDNSError` and `ConnectionClosed` events, preventing crash loops during temporary network outages.
- **WebTool Search**: Improved result consistency. Removed broken `lang:xx` filters and implemented Python-side content filtering. We now fetch a broader result set (10 items) and actively reject Asian (CJK) spam while focusing on European/American (Latin script) content.
 

## [Beta - Ongoing] - 2025-12-14

### Added
- **Enhanced Daily Statistics**:
    - **Restart Tracking**: Daily reports now distinguish between "Planned Restarts" (user-initiated) and "Unplanned Restarts" (crashes/power loss).
    - **Boredom Tracking**: Added a counter for "Boredom Actions" to track how many times the agent autonomously triggered an activity.
    - **Disconnect Tracking**: Added a counter for "Internet Disconnects" to track network stability events.
    - **Daily Report**: Discord embed updated to display these new metrics in a dedicated "Restarts" row and alongside tools usage.
    - **Cost & Usage**: Added tracking for LLM Tokens (Input/Output), Generations (Local vs Cloud), Command Usage, and Active Users.
- **Admin DM Auto-Pin**: The agent now automatically pins the latest message it sends in the Admin DM channel and unpins its previous messages, ensuring the most recent context is always prominent.


### Fixed
- **Log Cleanup Logic**: Refactored `cleanup_logs` script to properly handle log files. It now uses a checkpoint system to identify the first valid log entry older than the cutoff date and keeps everything after it, ensuring that undated lines (e.g., stack traces) from old logs are correctly deleted while preserving those from recent logs.
- **WebTool Robustness**: Fixed issue where autonomous `web_tool` calls failed with missing arguments. Tool now defaults to a random generic search if no query/URL is provided.
- **WebTool Topics**: The default search topics for `web_tool` fallback are now loaded from `boredom_topics.json` instead of being hardcoded.
- **Gitignore Update**: Added `daily_stats.json` and `*.tmp` files to `.gitignore` to prevent committing runtime statistics and prevent frequent restart loops.
- **Diagnostic Crash**: Fixed `Undefined variable 'genai'` in `!debug` command by removing the unused variable alias and refactoring the import check to catch `ImportError`.

## [Beta - CLOSED] - 2025-12-13

### Fixed
- **WebTool Crash**: Fixed a critical `TypeError` where `WebTool.execute()` failed when the `action` argument was missing. Modified the tool to be robust: it now automatically infers the action (`read` if URL is present, otherwise `search`) if not explicitly provided, resolving failures during autonomous operation.
- **Restart Notification**: Fixed race condition where post-restart notification failed because Discord channel cache wasn't ready. Added retry mechanism and API fetch fallback.

### Added
- **Crash Notification**: Implemented "Runtime Lock" crash detection. The agent now creates a lock file at startup and removes it only on graceful shutdown. This allows detection of ALL types of crashes, including power loss or kill commands, and notifies the admin via DM upon the next successful restart.

## [Beta - CLOSED] - 2025-12-11

### Added
- **Gemini API Integration**: Integrated Google Gemini models (`gemini-1.5-flash`, `gemini-1.5-pro`) for handling complex queries and image processing.
- **Autonomous Fallback**: Implemented Gemini fallback for autonomous actions (boredom system) when local LLM is unavailable. Agent can now "think" and act on its own using the cloud model if the local brain is missing.
- **Smart Routing**: Added `!ask` routing logic. Complex query (>50 chars, keywords, images) -> Gemini (High/Fast). Simple query -> Local LLM.
- **Auto Fallback**: If Local LLM is unavailable (e.g., on RPi without binaries), `!ask` automatically falls back to Gemini Fast model.
- **Gemini Integration**:
    - **Models**: Configured to use `gemini-flash-latest` and `gemini-pro-latest` aliases for maximum compatibility.
    - **Long Responses**: Responses >1900 chars are automatically saved to a file (`.txt` or `.md`) and sent as an attachment to keep chat clean.
    - **Logging**: Added logging of the specific Gemini model used for each request.
- **Diagnostics**:
    - **!debug**: Added Gemini library and API key status checks.
    - **Service**: Fixed `rpi_ai.service` to correctly use virtual environment (`venv`) instead of system Python.
- **Image Processing**: `!ask` now supports image attachments using Gemini Vision.
- **Typing Animation**: Added dynamic "Thinking..." animation (editing message) while the agent processes long requests.
- **Configuration**: Added `config_settings.py` support for Gemini model selection and difficulty thresholds.
- **Documentation**: Added guide for obtaining Gemini API keys in `tests/gemini_guide.md`.

### Fixed
- **Network Resilience**: Implemented active SSH tunnel recovery. The agent now detects if the tunnel is down after network restoration and automatically attempts to restart it.
- **SSH Stability**: Added retry logic (3 attempts with backoff) to the SSH tunnel startup process to handle transient connection failures.
- **Discord Connectivity**: Wrapped the Discord client in a permanent reconnection loop to automatically recover from fatal errors (e.g., `ClientConnectionResetError`) without crashing the agent.



## [Beta - CLOSED] - 2025-12-10

### Fixed
- **Critical Resource Instability**: Fixed system freezing/Discord disconnects by making Linux swap expansion idempotent (smart checking) and non-shrinking.
- **Resource Monitoring Sensitivity**: Increased CPU measurement interval from 0.1s to 1.0s to prevent false "Emergency" triggers.
- **Log Cleanliness**: Filtered "Thinking..." and "Reasoning..." animation updates from `!live logs` and dashboard to prevent spam.
- **Diagnostics**: Enhanced post-restart diagnostics (`quick` mode) to include `resources`, `filesystem`, `loops`, and `tools` checks for better health assessment.



## [Beta - CLOSED] - 2025-12-09

### Added
- **Dashboard Activity Feed**: Added a real-time "Recent Activity" list to the Web Dashboard, displaying the last 5 actions performed by the agent.
- **Startup Error Tracking**: Critical errors occurring during early startup (before full agent initialization) are now captured in daily statistics.

### Changed
- **SSH Notification**: Startup SSH messages now wrap commands in code blocks for easier copying.
- **Activity History**: Refined "Recent Activity" logging to focus on tool usage and autonomous actions, excluding generic user commands (!help, !status) to reduce noise.
- **Tool Logging**: Autonomous actions and `!ask` command now log detailed tool usage (including arguments) to the activity history.

### Fixed
- **Dashboard Activity Feed**: Fixed `[object Object]` display issue in Recent Activity list by properly formatting action objects with timestamps on both server and client side.
- **Daily Reporting Logic**: Implemented the missing scheduler loop to trigger daily reports at 23:59. Added logic to detect missed reports (e.g., due to downtime) and send them upon restart before resetting statistics, ensuring data continuity.
- **Uptime Calculation**: Enable real-time uptime accumulation in daily stats (previously static 0).
- **Error Tracking**: Implemented global error tracking. All internal errors (logged as ERROR/CRITICAL) now automatically increment the daily error count in reports.



## [Beta - CLOSED] - 2025-12-08

### Added
- **Daily Reporting System**: Agent now sends a summary DM to admin at 23:59 with uptime, message counts, and tools used.
- **UI Animations**: Added hover scaling animations to navigation links, detail buttons, and the scroll button in the web interface, smooth entry and exit animations for the modal window, staggered content loading for documentation pages, interactive hover effects for code blocks, blockquotes, and tables, plus a sliding underline animation for text links.
- **Dashboard Header**: Redesigned to group connection status and update time into a single container, with the "Live" status pulsing independently (anchored to the right) to indicate activity, and a flashing red animation for the "Disconnected" state.
- **Dashboard Stats**: Added "Last update" timestamp, "Interval" display, and active "Clients" count to the dashboard header (hidden on mobile devices).
- **Raw Memory Logging**: All memory write attempts are now logged to `memory.log` for debugging purposes.
- **Persistent Daily Stats**: Daily statistics are saved to `daily_stats.json` to survive restarts.

### Changed
- **Log Noise Reduction**: Reduced log levels for `discord.gateway`, `pyngrok`, and `httpcore` to WARNING.
- **Boredom Logging**: "Boredom" status updates are now less frequent to reduce channel spam.
- **Documentation Hub**: The web interface `/docs` page is now organized into categories (Commands, Core, Tools, etc.) for better navigation.
- **LLM Resource Config**: Updated resource tier settings to maintain 1024 context context (limit) and 3 threads for all high-load tiers (1, 2, 3), preventing excessive degradation.

### Fixed
- **Enhanced Memory Logging**: Updated `memory.log` to include the status (SAVED/REJECTED) and reason for each memory attempt, providing better visibility into the memory filtering process.
- **!ask Search Parsing**: Fixed case sensitivity issue where `Need_SEARCH` from LLM was treated as text instead of a search command.
- **Stability Fix**: Reverted LLM Threads for Tier 2 (2) and Tier 3 (1) to prevent system freeze (Discord heartbeat timeout) observed during high load. Context remains 1024.
