# Base44 UI + Bloxy Nexus integration

The downloaded Base44 project was reconstructed into a complete frontend export. Chat generation is routed directly from the Base44 frontend to the existing Bloxy Nexus FastAPI service instead of a Base44 AI integration.

## Runtime path

Base44 UI -> `src/lib/bloxyEngine.js` -> `POST /ai/chat` -> Bloxy Nexus -> registered 114-source network -> configured AI provider -> Base44 UI.

## Render URL

The frontend defaults to `https://bloxy-nexus.onrender.com`, inferred from the existing Render service name. Override it with the Vite build variable `VITE_BLOXY_NEXUS_URL` when a custom Render hostname is used.

## Base44 integration credits

The chat generation bridge does not call Base44 `InvokeLLM` or another Base44 AI integration. Existing Base44 integrations used by unrelated features (such as file upload/transcription) remain separate.

## Source count

The backend provider registry in this repository asserts 44 keyed + 20 browser-search + 50 keyless providers = 114 registered sources.

## Secrets

Provider API keys remain server-side in Render environment variables. No provider secrets should be placed in the Base44 frontend.

The Base44 downloader export contained several truncated placeholder source files; those were reconstructed from the surrounding project structure rather than inventing an exact missing Base44 source copy.