# Changelog

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

## [Beta - CLOSED] - 2025-12-06

### Added


### Changed


