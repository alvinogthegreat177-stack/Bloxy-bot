import os
import json
from typing import Any
import httpx

class AIEngine:
    def __init__(self):
        self.providers = [
            ("OpenAI", os.getenv("OPENAI_API_KEY"), "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
            ("DeepSeek", os.getenv("DEEPSEEK_API_KEY"), "https://api.deepseek.com/chat/completions", "deepseek-chat"),
            ("Groq", os.getenv("GROQ_API_KEY"), "https://api.groq.com/openai/v1/chat/completions", "llama-3.3-70b-versatile"),
            ("Mistral", os.getenv("MISTRAL_API_KEY"), "https://api.mistral.ai/v1/chat/completions", "mistral-small-latest"),
            ("OpenRouter", os.getenv("OPENROUTER_API_KEY"), "https://openrouter.ai/api/v1/chat/completions", "openai/gpt-4o-mini"),
            ("Qwen", os.getenv("QWEN_API_KEY"), "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions", "qwen-plus"),
        ]

    async def search_web(self, query: str):
        tavily = os.getenv("TAVILY_API_KEY")
        if tavily:
            try:
                async with httpx.AsyncClient(timeout=12) as c:
                    r = await c.post("https://api.tavily.com/search", json={"api_key":tavily,"query":query,"search_depth":"basic","max_results":5})
                    r.raise_for_status()
                    return r.json().get("results", [])
            except Exception:
                pass
        exa = os.getenv("EXA_API_KEY")
        if exa:
            try:
                async with httpx.AsyncClient(timeout=12) as c:
                    r = await c.post("https://api.exa.ai/search", headers={"x-api-key":exa,"Content-Type":"application/json"}, json={"query":query,"numResults":5,"contents":{"text":{"maxCharacters":3000}}})
                    r.raise_for_status()
                    return r.json().get("results", [])
            except Exception:
                pass
        return []

    async def generate(self, query: str, evidence: list[dict[str, Any]], conversation_id: str | None = None):
        context = json.dumps(evidence, ensure_ascii=False)[:30000]
        system = ("You are Bloxy-bot, powered by Bloxy Nexus. Answer clearly and accurately. "
                  "Use the supplied evidence when relevant. If evidence is uncertain or conflicting, say so. "
                  "Do not claim to have used a source that is not represented in the evidence. Keep the answer useful and direct.")
        messages = [{"role":"system","content":system},{"role":"user","content":f"Question: {query}\n\nEvidence from Bloxy Nexus:\n{context}"}]
        for name, key, url, model in self.providers:
            if not key:
                continue
            try:
                async with httpx.AsyncClient(timeout=30) as c:
                    r = await c.post(url, headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}, json={"model":model,"messages":messages,"temperature":0.2})
                    r.raise_for_status()
                    data = r.json()
                    return data["choices"][0]["message"]["content"]
            except Exception:
                continue
        raise RuntimeError("No configured AI provider completed the request")
