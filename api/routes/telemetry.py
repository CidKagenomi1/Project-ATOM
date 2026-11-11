import os
import csv
from datetime import datetime
from fastapi import APIRouter, HTTPException
from api.schemas import TelemetryEntry
from api.utils import safe_print

try:
    from modules.core.database import db, MONGODB_CONNECTED
except Exception as e:
    db = None
    MONGODB_CONNECTED = False

TELEMETRY_FILE = "data/atom_telemetry.csv"

router = APIRouter()

@router.get("/telemetry")
async def get_telemetry_endpoint():
    if MONGODB_CONNECTED:
        try:
            cursor = db["telemetry"].find().sort("timestamp", -1)
            telemetry_list = []
            for row in cursor:
                row.pop("_id", None)
                telemetry_list.append(row)
            return telemetry_list
        except Exception as e:
            safe_print(f"[DB ERROR] get_telemetry failed: {e}. Using local.")
            
    if not os.path.exists(TELEMETRY_FILE):
        return []
    try:
        with open(TELEMETRY_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading telemetry: {e}")

@router.post("/telemetry")
async def post_telemetry_endpoint(entry: TelemetryEntry):
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if MONGODB_CONNECTED:
        try:
            db["telemetry"].insert_one({
                "timestamp": timestamp_str,
                "user_input": entry.user_input,
                "model_used": entry.model_used,
                "response_time": entry.response_time,
                "status": entry.status,
                "ai_response": entry.ai_response
            })
            return {"status": "success"}
        except Exception as e:
            safe_print(f"[DB ERROR] post_telemetry failed: {e}. Writing locally.")
            
    # Local fallback
    try:
        os.makedirs(os.path.dirname(TELEMETRY_FILE), exist_ok=True)
        write_header = not os.path.exists(TELEMETRY_FILE)
        with open(TELEMETRY_FILE, mode="a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["timestamp", "user_input", "model_used", "response_time", "status", "ai_response"])
            writer.writerow([
                timestamp_str,
                entry.user_input,
                entry.model_used,
                entry.response_time,
                entry.status,
                entry.ai_response
            ])
        return {"status": "success"}
    except Exception as e:
        safe_print(f"[WARN] Local telemetry write failed (expected on read-only environments like Vercel): {e}")
        return {"status": "success", "info": "read_only_fallback"}

@router.delete("/telemetry")
async def delete_telemetry_endpoint():
    if MONGODB_CONNECTED:
        try:
            db["telemetry"].delete_many({})
            return {"status": "success"}
        except Exception as e:
            safe_print(f"[DB ERROR] delete_telemetry failed: {e}. Clearing locally.")
            
    try:
        os.makedirs(os.path.dirname(TELEMETRY_FILE), exist_ok=True)
        with open(TELEMETRY_FILE, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "user_input", "model_used", "response_time", "status"])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing telemetry: {e}")
