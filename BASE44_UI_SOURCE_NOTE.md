# Base44 UI integration boundary

The Base44 export remains the source of truth for the visual application layer: pages, components, navigation, chat layout, account/settings UI, conversations, buttons, styling, and other frontend behavior.

This repository branch adds only the engine boundary needed to connect that UI to Bloxy Nexus:

- `src/lib/bloxyEngine.js` sends chat requests directly to Render `/ai/chat`.
- `src/lib/aiVoices.js` cleans assistant prose before Read Aloud.
- `ai_engine.py` gives the model a mature, diplomatic response policy.

The 114-source engine remains the existing Render backend and is not replaced by Base44 frontend code.
