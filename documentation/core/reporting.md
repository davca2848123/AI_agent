# Daily Reporting System

<nav>
<a href="../../INDEX.md">Home</a> &gt; <a href="../README.md">Core Documentation</a> &gt; Reporting
</nav>

## Overview
The Daily Reporting System provides the administrator with a regular summary of the agent's activities ensuring visibility into its automated operations.

## Schedule
Arguments:
- **Time**: 23:59 (Server Local Time)
- **Frequency**: Once per day
- **Recipient**: Admin User (DM)

## Content
The report is sent as a Discord Embed containing:
1.  **Uptime**: Total accumulated uptime (in hours/minutes, persists across restarts).
2.  **Messages Processed**: Total number of messages seen by the agent.
3.  **Errors**: Count of critical errors logged (includes Startup & Runtime errors).
4.  **Tools Activity**: Breakdown of which tools were used and how many times.
5.  **Restarts**: Count of Planned (manual) vs Unplanned (crash) restarts.
6.  **Boredom Actions**: Number of times the agent autonomously triggered an action due to boredom.
7.  **Disconnects**: Number of times the internet connection was lost and recovered.
8.  **Knowledge Acquired**: Summary of new skills or facts learned during the day.
9.  **Active Users**: Number of unique users who interacted with the agent.
10. **Tokens**: Total LLM tokens processed (Input/Output).
11. **Generations**: Count of LLM generations by provider (Local vs Gemini).
12. **Top Commands**: The top 3 most frequently used commands.

## Auto-Pinning
To ensure the administrator always sees the latest status:
- The agent automatically **pins** the newly sent Daily Report in the Admin DM channel.
- It scans for and **unpins** any previous "Daily Report" messages to keep the pinned messages clean.

## Error Tracking
The system now tracks critical errors:
- **Startup Errors**: Failures occurring during agent initialization.
- **Runtime Errors**: Exceptions caught during normal operation.
- **Global Counter**: Increments daily error stats automatically when `logger.error` or `logger.critical` is called.

## Crash Detection (Runtime Lock)
The system implements a robust mechanisms to detect ALL types of crashes (including power loss or `kill -9`):

1.  **Runtime Lock**: On startup, a lock file is created.
2.  **Graceful Shutdown**: The lock file is removed only when the agent shuts down gracefully (`!shutdown` or systemctl stop).
3.  **Crash Detection**: If the agent starts and finds an existing lock file, it assumes the previous run crashed.
4.  **Notification**: A DM is sent to the admin upon successful restart: "⚠️ **Agent Crashed!** Detected runtime lock from previous session...".

## Technical Details
- **Class**: `agent.reports.DailyStats`
- **Persistence**: Stats are saved to `daily_stats.json` to ensure continuity across agent restarts.
- **Reset**: Stats are reset automatically when the date changes.
- **Missed Reports**: Logic detects if a report was missed (e.g., due to downtime) and sends it immediately upon the next restart before resetting statistics.
---
---
Poslední aktualizace: 2025-12-15
Verze: Beta - Ongoing  
Tip: Použij Ctrl+F pro vyhledávání
