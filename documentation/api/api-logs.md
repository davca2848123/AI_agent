# 🌐 Web Interface & Logs API

> **Navigace:** [📂 Dokumentace](../README.md) | [📚 API](../INDEX.md#api) | [Web Interface API](api-logs.md)

Dokumentace pro REST API a WebSocket endpointy webového rozhraní (`agent/web_interface.py`).

<a name="přehled"></a>
## 📋 Přehled

Webové rozhraní běží na Flasku (default port 5001) a poskytuje jak statické stránky (dashboard, dokumentace), tak API endpointy pro monitorování.

**Base URL:** `http://localhost:5001`

---

<a name="rest-api"></a>
## 🔌 REST API Endpointy

<a name="get-apiprocesses"></a>
### `GET /api/processes`
Vrátí seznam běžících procesů a jejich spotřebu zdrojů. Používá se pro modální okno v dashboardu.

**Response (JSON):**
```json
{
    "cpu": [
        {"pid": 1234, "name": "python", "cpu_percent": 12.5},
        ...
    ],
    "memory": [
        {"pid": 1234, "name": "python", "memory_percent": 5.2, "memory_mb": 450},
        ...
    ]
}
```

<a name="get-search"></a>
### `GET /search`
Vyhledávání v dokumentaci.

**Query Parameters:**
- `q`: Hledaný výraz (string)

**Response:**
- HTML stránka s výsledky vyhledávání.

<a name="get-test"></a>
### `GET /test`
Jednoduchý health-check endpoint.

**Response (Text):**
`Flask is running! ✅`

---

<a name="websocket-events"></a>
## 📡 WebSocket Events (Socket.IO)

Web Interface využívá WebSocket pro real-time aktualizace dashboardu (každých 5s).

<a name="status_update"></a>
### Event: `status_update`
Server posílá klientovi komplexní objekt se stavem agenta.

**Structure:**
```javascript
{
    "is_running": true,          // Stav agenta
    "uptime": "1:23:45",         // Doba běhu
    "boredom_score": 0.15,       // Úroveň nudy (0.0 - 1.0)
    "cpu_percent": 45.2,         // Celkové vytížení CPU
    "ram_percent": 60.5,         // Celkové vytížení RAM
    "ram_used": "2.4GB",
    "ram_total": "4.0GB",
    "disk_percent": 55,
    "tools_used": 15,            // Statistiky nástrojů
    "tools_total": 24,
    "log_tail": "...",           // Posledních 100 řádků logu (HTML)
    "action_history": [          // Seznam posledních akcí
        "Executed command: !status",
        "Checked emails"
    ],
    "loop_status": {             // Diagnostika vláken
        "boredom_loop": "Running",
        "observation_loop": "Running",
        ...
    }
}
```

---

<a name="bezpečnost"></a>
## 🛡️ Bezpečnost

- **Content Security Policy (CSP)**: Implementováno via `nonce` pro striktní oddělení skriptů.
- **Port**: 5001 (nebo 5002-5020 pokud je obsazeno).
- **Ngrok**: Volitelné tunelování pro vzdálený přístup (zabezpečeno tokenem v konfiguraci).


<a name="související"></a>
## 🔗 Související

- [🏗️ Architektura](../architecture.md)
- [🧠 Core Documentation](../core/)
- [📂 Source Code](../agent/)
---
Poslední aktualizace: 2025-12-09  
Verze: Beta - CLOSED  
Tip: Použij Ctrl+F pro vyhledávání
