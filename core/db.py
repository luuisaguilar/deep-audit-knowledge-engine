"""Central persistence layer for the Deep Audit Knowledge Engine via Supabase.

Provides a unified PostgreSQL connection to record every ingestion
across all source types. Enables cross-project analytics and deduplication.
"""

import json
import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Cliente de Supabase
supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def record_ingestion(
    source_type: str,
    source_url: str,
    title: str | None = None,
    user_id: str | None = None,
    *,
    model_used: str = "gemini-2.0-flash",
    tokens_estimated: int | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    vault_path: str | None = None,
    status: str = "success",
    error_message: str | None = None,
    metadata: dict | None = None,
) -> str | None:
    """Insert a new ingestion record into Supabase."""
    if not supabase:
        return None
    
    data = {
        "user_id": user_id,
        "source_type": source_type,
        "source_url": source_url,
        "title": title,
        "model_used": model_used,
        "tokens_estimated": tokens_estimated,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "vault_path": vault_path,
        "status": status,
        "error_message": error_message,
        "metadata_json": metadata,
    }
    
    try:
        response = supabase.table("ingestions").insert(data).execute()
        if response.data:
            return response.data[0].get("id")
    except Exception as e:
        # Probablemente un error de duplicado (Unique Constraint)
        print(f"Supabase record_ingestion error (likely duplicate): {e}")
        return None
    return None

def has_been_processed(source_url: str, user_id: str | None = None) -> bool:
    """Return True if the URL was already successfully ingested in Supabase for this user."""
    if not supabase:
        return False
    
    try:
        query = supabase.table("ingestions") \
            .select("id") \
            .eq("source_url", source_url) \
            .eq("status", "success")
        
        if user_id:
            query = query.eq("user_id", user_id)
            
        response = query.execute()
        return len(response.data) > 0
    except Exception:
        return False

def get_ingestion_stats(user_id: str | None = None) -> dict:
    """Aggregate statistics for the analytics dashboard from Supabase."""
    if not supabase:
        return {"total": 0, "success": 0, "failed": 0, "by_type": [], "by_date": [], "recent": []}

    try:
        query = supabase.table("ingestions").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
            
        all_data = query.execute()
        rows = all_data.data
        
        total = len(rows)
        success = len([r for r in rows if r["status"] == "success"])
        failed = len([r for r in rows if r["status"] == "failed"])
        
        # Agrupar por tipo
        types = {}
        for r in rows:
            t = r["source_type"]
            types[t] = types.get(t, 0) + 1
        by_type = sorted(types.items(), key=lambda x: x[1], reverse=True)
        
        # Agrupar por fecha (últimos 30 días)
        dates = {}
        for r in rows:
            if not r["processed_at"]: continue
            d = r["processed_at"][:10] # YYYY-MM-DD
            dates[d] = dates.get(d, 0) + 1
        by_date = sorted(dates.items(), key=lambda x: x[0], reverse=True)[:30]
        
        # Calcular costos (Gemini 2.0 Flash: $0.15/1M input, $0.60/1M output)
        total_prompt_tokens = sum(r.get("prompt_tokens") or 0 for r in rows)
        total_completion_tokens = sum(r.get("completion_tokens") or 0 for r in rows)
        estimated_cost_usd = (total_prompt_tokens / 1000000) * 0.15 + (total_completion_tokens / 1000000) * 0.60
        
        # Recientes
        recent = sorted(rows, key=lambda x: x["processed_at"] or "", reverse=True)[:10]
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "by_type": by_type,
            "by_date": by_date,
            "recent": recent,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "estimated_cost_usd": estimated_cost_usd
        }
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return {
            "total": 0, "success": 0, "failed": 0, 
            "by_type": [], "by_date": [], "recent": [],
            "total_prompt_tokens": 0, "total_completion_tokens": 0, "estimated_cost_usd": 0.0
        }

def list_recent_ingestions(limit: int = 50, user_id: str | None = None) -> list[dict]:
    """Return the most recent ingestions from Supabase."""
    if not supabase:
        return []
    try:
        query = supabase.table("ingestions").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
            
        response = query.order("processed_at", desc=True).limit(limit).execute()
        return response.data
    except Exception:
        return []

# --- AUTH FUNCTIONS ---

def signup_user(email: str, password: str):
    """Register a new user in Supabase."""
    return supabase.auth.sign_up({"email": email, "password": password})

def login_user(email: str, password: str):
    """Authenticate a user in Supabase."""
    return supabase.auth.sign_in_with_password({"email": email, "password": password})

def logout_user():
    """Sign out the current user."""
    return supabase.auth.sign_out()

def get_current_user():
    """Get the currently logged in user session."""
    return supabase.auth.get_user()

def reset_password_user(email: str):
    """Trigger a password reset email from Supabase."""
    return supabase.auth.reset_password_for_email(email)

def init_db():
    """No-op for Supabase (schema is managed in Supabase dashboard)."""
    pass
