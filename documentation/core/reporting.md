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
5.  **Knowledge Acquired**: Summary of new skills or facts learned during the day.

## Error Tracking
The system now tracks critical errors:
- **Startup Errors**: Failures occurring during agent initialization.
- **Runtime Errors**: Exceptions caught during normal operation.
- **Global Counter**: Increments daily error stats automatically when `logger.error` or `logger.critical` is called.

## Technical Details
- **Class**: `agent.reports.DailyStats`
- **Persistence**: Stats are saved to `daily_stats.json` to ensure continuity across agent restarts.
- **Reset**: Stats are reset automatically when the date changes.
- **Missed Reports**: Logic detects if a report was missed (e.g., due to downtime) and sends it immediately upon the next restart before resetting statistics.
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
