# Web Interface

> **Navigace:** [📂 Dokumentace](../README.md) | [🧠 Core](../README.md#core-jádro) | [Web Interface](web-interface.md)

> Webový dashboard pro monitorování stavu agenta a prohlížení logů.
> **Verze:** Beta - CLOSED

---

<a name="přehled"></a>
## 📋 Přehled

`WebInterface` poskytuje lokální webový server (Flask) s real-time dashboardem. Umožňuje sledovat stav agenta, systémové prostředky, logy a dokumentaci.

---

<a name="přístup"></a>
## 🔐 Přístup

- **URL:** `http://localhost:5001` (nebo jiný volný port)
- **Status:** Automaticky spuštěno při startu agenta.
- **Port Finding:** Pokud je port obsazen, zkouší další v rozsahu 5001-5050.

---

<a name="funkce"></a>
## 🚀 Hlavní Funkce

<a name="dashboard"></a>
### 📊 Dashboard (`/`)

Hlavní stránka zobrazuje klíčové metriky:
- **Status Agenta:** (Running/Stopped, Boredom Score, Uptime)
- **Loops Status:** Stav jednotlivých smyček (Observation, Action, etc.)
- **System Resources:** CPU, RAM, Disk usage.
- **Recent Activity:** Posledních 5 akcí agenta.
- **Log Viewer:** Real-time stream logů (posledních 100 řádků).

<a name="dokumentace"></a>
### 📚 Dokumentace (`/docs`)

- Prohlížeč Markdown dokumentace.
- Podpora pro vyhledávání (Search).

<a name="api"></a>
### 🔌 API Endpoints

- **`/api/processes`** - Vrací seznam běžících procesů a jejich spotřebu (pro modal okno).
- **`/api/stats`** - (Internal) WebSocket používá vlastní event `status_update`.

<a name="search"></a>
### 🔍 Vyhledávání (`/search`)

- Fulltexové vyhledávání v dokumentaci.
- Zvýrazňování výsledků (přesná vs fuzzy shoda).
- Odkazy přímo na kotvy (anchors) v textu.

---

<a name="technická-implementace"></a>
## ⚙️ Technická Implementace

<a name="websocket"></a>
### WebSocket Updates
Server používá `Flask-SocketIO` pro real-time aktualizace dashboardu bez nutnosti obnovování stránky.

- **Interval:** 2 sekundy (konfigurovatelné).
- **Event:** `status_update`

<a name="ui-ux"></a>
### 🎨 UI/UX Vylepšení
Webové rozhraní obsahuje řadu moderních vizuálních prvků:
- **Animace:**
  - Hover scaling efekty na navigačních odkazech a tlačítkách.
  - Smooth entry/exit animace pro modální okna.
  - Staggered content loading (postupné načítání) pro dokumentaci.
  - Sliding underline animace pro textové odkazy.
- **Interaktivita:**
  - Hover efekty pro code blocky, citace a tabulky.
  - "Live" status indikátor s pulzující animací (ukotven vpravo).
  - Flashing red animace pro stav "Disconnected".
- **Header:**
  - Sdružený kontejner pro status připojení a čas poslední aktualizace.
  - Zobrazení intervalu obnovení a počtu připojených klientů (na desktopu).

<a name="automatické-vypnutí"></a>
### Auto-Shutdown
Web server obsahuje bezpečnostní pojistku:

- Automatické vypnutí po **1 hodině** běhu (default, konfigurovatelné přes `WEB_INTERFACE_TIMEOUT`).
- **Client Tracking:** Server sleduje počet připojených uživatelů skrze WebSocket eventy (`connect`/`disconnect`).
- **Resource Saver:** Automatická pauza aktualizací stavu, pokud není připojen žádný klient (šetření CPU).

---

<a name="konfigurace"></a>
## 🔧 Konfigurace

V `config_settings.py`:

```python
WEB_WEBSOCKET_UPDATE_INTERVAL = 2  # Interval aktualizací (s)
WEB_ENABLED = True                 # Povolení/Zákaz webu
```

---

<a name="související"></a>
## 🔗 Související

- [📖 Autonomous Behavior](autonomous-behavior.md)
- [`!web`](../commands/admin.md#web) - Příkaz pro správu webu (start/stop)
- [📚 API Reference](../api/api-logs.md)
- [🏗️ Architektura](../architecture.md)

---
Poslední aktualizace: 2025-12-08
Verze: Beta - CLOSED
Tip: Použij Ctrl+F pro vyhledávání
