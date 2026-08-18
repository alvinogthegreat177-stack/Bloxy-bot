"""AI model gateway used after Bloxy Nexus gathers source evidence."""
import os
import json
from typing import Any
import httpx

class AIEngine:
    OPENAI_COMPAT = [
        ("OpenAI","OPENAI_API_KEY","https://api.openai.com/v1/chat/completions","gpt-4o-mini"),
        ("DeepSeek","DEEPSEEK_API_KEY","https://api.deepseek.com/chat/completions","deepseek-chat"),
        ("Groq","GROQ_API_KEY","https://api.groq.com/openai/v1/chat/completions","llama-3.3-70b-versatile"),
        ("Mistral","MISTRAL_API_KEY","https://api.mistral.ai/v1/chat/completions","mistral-small-latest"),
        ("OpenRouter","OPENROUTER_API_KEY","https://openrouter.ai/api/v1/chat/completions","openai/gpt-4o-mini"),
        ("Qwen","QWEN_API_KEY","https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions","qwen-plus"),
        ("Kimi","KIMI_API_KEY","https://api.moonshot.cn/v1/chat/completions","moonshot-v1-8k"),
    ]

    def __init__(self):
        self.providers = self.OPENAI_COMPAT

    async def search_web(self, query: str):
        for name, key_name, url, _ in [("Tavily","TAVILY_API_KEY","","") , ("Exa","EXA_API_KEY","","")]:
            key=os.getenv(key_name)
            if not key: continue
            try:
                async with httpx.AsyncClient(timeout=12) as c:
                    if name=="Tavily":
                        r=await c.post("https://api.tavily.com/search",json={"api_key":key,"query":query,"search_depth":"advanced","max_results":5})
                    else:
                        r=await c.post("https://api.exa.ai/search",headers={"x-api-key":key},json={"query":query,"numResults":5,"contents":{"text":{"maxCharacters":3000}}})
                    r.raise_for_status(); return r.json().get("results",[])
            except Exception: pass
        return []

    async def _openai_compatible(self, name, key, url, model, messages):
        try:
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"}
            if name=="OpenRouter": headers.update({"HTTP-Referer":"https://bloxy-bot.base44.app","X-Title":"Bloxy-bot"})
            async with httpx.AsyncClient(timeout=35) as c:
                r=await c.post(url,headers=headers,json={"model":model,"messages":messages,"temperature":0.2})
                r.raise_for_status(); data=r.json()
                return data["choices"][0]["message"]["content"]
        except Exception: return None

    async def _anthropic(self, key, messages):
        try:
            async with httpx.AsyncClient(timeout=35) as c:
                r=await c.post("https://api.anthropic.com/v1/messages",headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},json={"model":"claude-3-5-haiku-latest","max_tokens":1800,"system":messages[0]["content"],"messages":messages[1:]})
                r.raise_for_status(); return "".join(x.get("text","") for x in r.json().get("content",[]) if x.get("type")=="text")
        except Exception:return None

    async def _cohere(self, key, messages):
        try:
            async with httpx.AsyncClient(timeout=35) as c:
                r=await c.post("https://api.cohere.com/v2/chat",headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"model":"command-r7b-12-2024","messages":messages})
                r.raise_for_status(); return r.json().get("message",{}).get("content",[{}])[0].get("text")
        except Exception:return None

    async def _huggingface(self, key, messages):
        try:
            prompt=messages[0]["content"]+"\n\n"+messages[-1]["content"]
            async with httpx.AsyncClient(timeout=35) as c:
                r=await c.post("https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",headers={"Authorization":f"Bearer {key}"},json={"inputs":prompt,"parameters":{"max_new_tokens":1200,"return_full_text":False}})
                r.raise_for_status(); data=r.json(); return data[0].get("generated_text") if isinstance(data,list) else None
        except Exception:return None

    async def generate(self, query: str, evidence: list[dict[str, Any]], conversation_id: str | None = None):
        context=json.dumps(evidence,ensure_ascii=False,default=str)[:30000]
        system=("You are Bloxy-bot, powered by Bloxy Nexus. Answer clearly, accurately and directly. "
                "Use supplied evidence when relevant. Do not invent source results. If evidence conflicts, explain the uncertainty.")
        messages=[{"role":"system","content":system},{"role":"user","content":f"Question: {query}\n\nBloxy Nexus evidence:\n{context}"}]
        # Preferred multi-model fallback chain.
        for name,key_name,url,model in self.OPENAI_COMPAT:
            key=os.getenv(key_name)
            if key:
                answer=await self._openai_compatible(name,key,url,model,messages)
                if answer: return answer
        key=os.getenv("ANTHROPIC_API_KEY")
        if key:
            answer=await self._anthropic(key,messages)
            if answer:return answer
        key=os.getenv("COHERE_API_KEY")
        if key:
            answer=await self._cohere(key,messages)
            if answer:return answer
        key=os.getenv("HUGGINGFACE_API_KEY")
        if key:
            answer=await self._huggingface(key,messages)
            if answer:return answer
        raise RuntimeError("No configured AI provider completed the request")
