BEGIN TRANSACTION;

-- 1. Vytvoření čisté tabulky
DROP TABLE IF EXISTS memories;
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Uživatelská výuka (User Teachings) - Opraveno kódování a odstraněny duplicity
-- Původní: "Automation is key to efficiency." (nalezeno vícekrát)
INSERT INTO memories (content, metadata, created_at) VALUES 
('User taught me: Automation is key to efficiency.', 
 '{"type": "user_teaching", "importance": "high"}', 
 '2025-11-27 10:22:03');

-- Původní: "python je programovacÃ­ jazyk" (opraveno na čitelné znaky)
INSERT INTO memories (content, metadata, created_at) VALUES 
('User taught me: python je programovací jazyk', 
 '{"type": "user_teaching", "importance": "high"}', 
 '2025-11-26 10:25:42');

-- Původní: "hitler je hodnÃ½" (zachováno jako vstup uživatele)
INSERT INTO memories (content, metadata, created_at) VALUES 
('User taught me: hitler je hodný', 
 '{"type": "user_teaching", "importance": "high"}', 
 '2025-11-28 11:24:34');

-- 3. Úspěšné použití nástrojů (Tool Executions) - Pouze relevantní výsledky
-- Výsledek hledání o Machine Learning
INSERT INTO memories (content, metadata, created_at) VALUES 
('Tool web_tool executed. Result: Search Results: Machine learning: o que é e qual sua importância? | SAS', 
 '{"type": "tool_execution", "tool": "web_tool"}', 
 '2025-11-25 21:49:30');

-- Výsledek hledání o Raspberry Pi
INSERT INTO memories (content, metadata, created_at) VALUES 
('Tool web_tool executed. Result: Search Results: Teach, learn, and make with the Raspberry Pi Foundation', 
 '{"type": "tool_execution", "tool": "web_tool"}', 
 '2025-11-25 22:15:40');

-- Výsledek hledání zpráv (SCMP)
INSERT INTO memories (content, metadata, created_at) VALUES 
('Tool web_tool executed. Result: Search Results: Latest and Breaking News | South China Morning Post', 
 '{"type": "tool_execution", "tool": "web_tool"}', 
 '2025-11-29 19:02:01');

-- Výsledek analýzy slova "počasí" (Translate Tool)
INSERT INTO memories (content, metadata, created_at) VALUES 
('Q: počasí -> A: The term "počasí" in Czech can be interpreted as a contraction of "počas" (for "day"). In this context, "počasí" refers to "the day" or "the time".', 
 '{"type": "qa_search", "query": "latest and breaking news"}', 
 '2025-11-30 09:56:03');

-- 4. Aktuální stav agenta (Status) - Pouze nejnovější relevantní cíl
INSERT INTO memories (content, metadata, created_at) VALUES 
('Context: My goal is to learn how to use the ''translate_tool'' tool. I MUST use the ''translate_tool'' tool now to test its functionality.', 
 '{"type": "autonomous_decision"}', 
 '2025-11-30 10:19:38');

COMMIT;