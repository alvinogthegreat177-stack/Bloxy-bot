# Bloxy-bot Base44 + Bloxy Nexus integration

This export preserves the Base44 frontend structure and routes chat generation directly to the Bloxy Nexus backend instead of a Base44 AI/integration call.

## Chat path

Base44 UI -> `src/lib/bloxyEngine.js` -> `POST /ai/chat` -> Bloxy Nexus -> 114-source provider network -> configured AI provider -> Base44 UI.

## Render endpoint

Default endpoint: `https://bloxy-nexus.onrender.com`

Override it at build time with:

`VITE_BLOXY_NEXUS_URL=https://YOUR-RENDER-HOST`

## Backend

The existing `alvinogthegreat177-stack/Bloxy-bot` repository contains the Bloxy Nexus FastAPI service. Its provider registry asserts 44 keyed + 20 browser-search + 50 keyless = 114 registered sources.

## Important

No provider API keys belong in the Base44 frontend. Keep them in Render environment variables.

The downloaded Base44 export contained several placeholder/truncated files. Those were reconstructed where necessary so the project has a coherent source tree; exact visual behavior of those repaired files may differ slightly from the original Base44 editor state.
