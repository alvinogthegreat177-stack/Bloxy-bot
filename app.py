import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Biney Bot AI Production Engine", version="1.0.0")

# Global Middleware exception catcher to show you the error in the browser
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return PlainTextResponse(f"Backend Crash Error Traceback:\n\n{error_details}", status_code=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure folders exist before mounting to prevent startup failures
os.makedirs("static", exist_exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

CHATS_FILE = "chats.json"
USERS_FILE = "users.json"

def initialize_json_storage():
    if not os.path.exists(CHATS_FILE) or os.path.getsize(CHATS_FILE) == 0:
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump({"conversations": []}, f, indent=4)
    if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": []}, f, indent=4)

initialize_json_storage()

def read_json_safe(file_path: str) -> Dict:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"conversations": []} if file_path == CHATS_FILE else {"users": []}

class ChatInboundRequest(BaseModel):
    chat_id: Optional[str] = None
    prompt: str

# 23 API Engines Mocks Mapped Cleanly
class BineyBotEngine:
    @staticmethod
    def api_1_google_search(q: str): return {"source": "Google Core", "results": [f"Top search result for {q}"]}
    @staticmethod
    def api_2_wikipedia(q: str): return {"source": "Wikipedia API", "summary": f"Excerpts for {q}"}
    @staticmethod
    def api_3_deep_research(q: str): return {"source": "Deep Web Crawler", "analysis": f"Synthesized data for {q}."}
    @staticmethod
    def api_4_world_news(): return {"source": "Global News Feed", "headlines": ["Breaking updates."]}
    @staticmethod
    def api_5_tech_crunch(): return {"source": "TechNews API", "headlines": ["Silicon Valley changes."]}
    @staticmethod
    def api_6_finance_news(): return {"source": "WallStreet Journal", "headlines": ["Market pulses."]}
    @staticmethod
    def api_7_epl_scores(): return {"source": "Premier League Data", "match": "Arsenal vs Chelsea (2-1)"}
    @staticmethod
    def api_8_nba_stats(): return {"source": "NBA Stats API", "status": "Playoffs scoring active."}
    @staticmethod
    def api_9_ucl_fixtures(): return {"source": "UEFA Champions League", "fixtures": ["Quarter-final brackets."]}
    @staticmethod
    def api_10_current_weather(loc: str): return {"source": "OpenWeather", "temp": "22°C", "condition": "Cloudy"}
    @staticmethod
    def api_11_air_quality(loc: str): return {"source": "AQI Index", "status": "Good", "index": 42}
    @staticmethod
    def api_12_weather_forecast(loc: str): return {"source": "WeatherKit", "forecast": ["7-day trends"]}
    @staticmethod
    def api_13_tmdb_movies(q: str): return {"source": "TMDb Engine", "match": f"Trending for {q}"}
    @staticmethod
    def api_14_tv_shows(q: str): return {"source": "TVMaze API", "schedule": f"Air-time for {q}"}
    @staticmethod
    def api_15_imdb_ratings(q: str): return {"source": "IMDb Scraper", "rating": "8.7/10"}
    @staticmethod
    def api_16_crypto_prices(): return {"source": "CoinGecko Engine", "BTC": "$94,250", "ETH": "$3,420"}
    @staticmethod
    def api_17_solana_tracker(): return {"source": "Solscan API", "TPS": "2,400"}
    @staticmethod
    def api_18_gas_fees(): return {"source": "Etherscan Gas", "standard": "24 Gwei"}
    @staticmethod
    def api_19_dictionary(w: str): return {"source": "Lexicon API", "definition": f"Evaluation for {w}"}
    @staticmethod
    def api_20_currency_converter(): return {"source": "Fixer API", "USD_to_EUR": 0.92}
    @staticmethod
    def api_21_unit_conversion(): return {"source": "MathEngine", "result": "Metric values mapped."}
    @staticmethod
    def api_22_pdf_analyzer(): return {"source": "PyMuPDF Extract", "status": "Parsed successfully."}
    @staticmethod
    def api_23_image_ocr(): return {"source": "Vision AI API", "text_found": "Extracted tokens."}

@app.get("/", response_class=HTMLResponse)
async def render_dashboard_interface(request: Request):
    chats_data = read_json_safe(CHATS_FILE)
    return templates.TemplateResponse("index.html", {"request": request, "recent_chats": chats_data.get("conversations", [])})

@app.post("/api/chat/message", response_class=JSONResponse)
async def post_message_to_session(payload: ChatInboundRequest):
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt text payload cannot be empty.")
        
    chats_data = read_json_safe(CHATS_FILE)
    conversations = chats_data.get("conversations", [])
    
    target_chat_id = payload.chat_id or f"session_{int(datetime.utcnow().timestamp())}"
    current_chat = next((c for c in conversations if c["chat_id"] == target_chat_id), None)
    
    if not current_chat:
        current_chat = {
            "chat_id": target_chat_id,
            "title": payload.prompt[:24] + "..." if len(payload.prompt) > 24 else payload.prompt,
            "messages": [],
            "updated_at": datetime.utcnow().isoformat()
        }
        conversations.insert(0, current_chat)

    current_chat["messages"].append({"role": "user", "content": payload.prompt, "timestamp": datetime.utcnow().isoformat()})
    
    lower_prompt = payload.prompt.lower()
    if "search" in lower_prompt: tool_res = BineyBotEngine.api_1_google_search(payload.prompt)
    elif "news" in lower_prompt: tool_res = BineyBotEngine.api_4_world_news()
    elif "weather" in lower_prompt: tool_res = BineyBotEngine.api_10_current_weather("Default Location")
    elif "crypto" in lower_prompt: tool_res = BineyBotEngine.api_16_crypto_prices()
    else: tool_res = BineyBotEngine.api_3_deep_research(payload.prompt)

    assistant_reply_text = f"Processed request: {json.dumps(tool_res)}"
    current_chat["messages"].append({"role": "assistant", "content": assistant_reply_text, "timestamp": datetime.utcnow().isoformat()})
    
    chats_data["conversations"] = conversations
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(chats_data, f, indent=4)
    
    return {"chat_id": target_chat_id, "title": current_chat["title"], "reply": assistant_reply_text}

@app.get("/health")
async def check_system_liveness():
    return {"status": "healthy", "engines_loaded": 23}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
