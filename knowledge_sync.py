import os
import sqlite3
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DEFAULT_VAULT_PATH = os.getenv("VAULT_PATH", "/mnt/obsidian-vault")
AGENTS_PATH = os.getenv("AGENTS_PATH", "/opt/agents")


def get_auctionbot_summary():
    db_path = os.path.join(AGENTS_PATH, "auctionbot", "data", "auctionbot.db")
    if not os.path.exists(db_path):
        return "Database not found."
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT * FROM auctions ORDER BY id DESC LIMIT 10"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error leyendo AuctionBot: {e}"


def get_dexscreener_summary():
    db_path = os.path.join(AGENTS_PATH, "dexscreener_bot", "dexscreener_data.db")
    if not os.path.exists(db_path):
        return "Database not found."
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if not tables:
            return "No tables found."
        main_table = tables[0][0]
        df = pd.read_sql_query(f"SELECT * FROM {main_table} LIMIT 10", conn)
        conn.close()
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Error leyendo DexScreener: {e}"


def sync_all_to_obsidian(vault_path: str = DEFAULT_VAULT_PATH, consolidated: bool = True, user_id: str = None) -> dict:
    """Sincroniza los datos de los agentes al vault de Obsidian.

    Args:
        vault_path: Ruta al vault. Por defecto usa DEFAULT_VAULT_PATH.
        consolidated: True → una sola nota con todo. False → una nota por agente.
        user_id: Si se provee, escribe en users/<user_id>/40_Agente_Sync/
    """
    results = {
        'AuctionBot': get_auctionbot_summary(),
        'DexScreener': get_dexscreener_summary(),
    }

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base = os.path.join(vault_path, "users", user_id) if user_id else vault_path
    sync_dir = os.path.join(base, "40_Agente_Sync")
    os.makedirs(sync_dir, exist_ok=True)

    stats = {"synced": 0, "new": 0, "updated": 0}

    if consolidated:
        content = f"---\ntipo: reporte_agentes\nfecha_sincro: {now}\n---\n\n# 🧠 Reporte Consolidado de Agentes\n\n"
        for agent, data in results.items():
            content += f"## 🤖 {agent}\n\n{data}\n\n"

        filename = f"Reporte_Agentes_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = os.path.join(sync_dir, filename)
        
        if os.path.exists(filepath):
            stats["updated"] += 1
        else:
            stats["new"] += 1
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        stats["synced"] = stats["new"] + stats["updated"]
        return stats
    else:
        for agent, data in results.items():
            content = (
                f"---\ntipo: reporte_agente\nagente: {agent}\nfecha_sincro: {now}\n---\n\n"
                f"# 🤖 {agent}\n\n{data}\n"
            )
            filename = f"{agent}_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = os.path.join(sync_dir, filename)
            
            if os.path.exists(filepath):
                stats["updated"] += 1
            else:
                stats["new"] += 1
                
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        
        stats["synced"] = stats["new"] + stats["updated"]
        return stats


if __name__ == "__main__":
    print(sync_all_to_obsidian())
