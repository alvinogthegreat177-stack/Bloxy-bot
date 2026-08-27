@@
     async def _anthropic(self, key: str, messages: list[dict[str, str]]) -> str | None:
-        try:
-            headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
-            async with httpx.AsyncClient(timeout=35) as client:
-                models = await client.get("https://api.anthropic.com/v1/models", headers=headers)
-                models.raise_for_status()
-                items = models.json().get("data", [])
-                ids = [item.get("id") for item in items if item.get("id")]
-                model = next((m for m in ids if "haiku" in m.lower()), None) or next((m for m in ids if "sonnet" in m.lower()), None) or (ids[0] if ids else None)
-                if not model:
-                    return None
-                response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json={"model": model, "max_tokens": 1800, "system": messages[0]["content"], "messages": messa[...]
-                response.raise_for_status()
-                return "".join(item.get("text", "") for item in response.json().get("content", []) if item.get("type") == "text") or None
-        except (httpx.HTTPError, KeyError, TypeError, IndexError):
-            return None
+        """
+        Anthropic fallback: convert role-based messages into a single prompt
+        and call the /v1/complete endpoint. Returns the completion text or None.
+        """
+        try:
+            headers = {"x-api-key": key, "Content-Type": "application/json"}
+            # Build a simple prompt from role-based messages
+            parts = []
+            for m in messages:
+                role = m.get("role", "user")
+                content = m.get("content", "") or ""
+                if role == "system":
+                    parts.insert(0, f"SYSTEM: {content}")
+                elif role == "assistant":
+                    parts.append(f"ASSISTANT: {content}")
+                else:
+                    parts.append(f"HUMAN: {content}")
+            prompt = "\n\n".join(parts).strip()
+            payload = {"model": "claude-2.1", "prompt": prompt, "max_tokens_to_sample": 1800}
+            async with httpx.AsyncClient(timeout=35) as client:
+                resp = await client.post("https://api.anthropic.com/v1/complete", headers=headers, json=payload)
+                resp.raise_for_status()
+                data = resp.json()
+                # anthopic-style completion text field (guarded)
+                completion = data.get("completion") or data.get("completion_text") or data.get("text")
+                if isinstance(completion, str) and completion:
+                    return completion
+                return None
+        except (httpx.HTTPError, KeyError, TypeError, IndexError, ValueError):
+            return None
@@
     async def generate(self, query: str, evidence: list[dict[str, Any]], conversation_id: str | None = None, nexus_mode: str = "deep") -> str:
@@
         # Prefer the strongest configured provider and fall back automatically.
         for name, key_name, url, model in self.OPENAI_COMPAT:
             key = os.getenv(key_name)
             if key:
                 answer = await self._openai_compatible(name, key, url, model, messages)
                 if answer:
                     return answer
@@
         key = os.getenv("ANTHROPIC_API_KEY")
         if key:
             answer = await self._anthropic(key, messages)
             if answer:
                 return answer
*** End Patch
