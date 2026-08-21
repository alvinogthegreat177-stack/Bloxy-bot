# Bloxy-bot Base44 UI + Bloxy Nexus

This branch is the integration layer for the Base44-derived frontend and the existing Bloxy Nexus backend.

## Chat engine

The frontend chat bridge uses `src/lib/bloxyEngine.js` and sends user messages directly to `POST /ai/chat` on Render. It does not call Base44 AI integrations for answer generation.

The Render backend remains the 11-file Bloxy Nexus engine with the 114-source registry: 44 keyed sources, 20 browser/search sources, and 50 keyless/public sources.

## Read Aloud

`src/lib/aiVoices.js` provides the browser speech voices and sanitizes assistant text before speech. It removes emojis, URLs, email addresses, markdown markers, list markers, slashes, brackets, code blocks, and other formatting noise while keeping the underlying prose and natural sentence pauses.

## Response quality

The backend AI prompt is intended to produce mature, diplomatic, calm, professional answers and to answer general questions, coding requests, research, planning, writing, explanations, comparisons, and everyday requests while using Nexus evidence when relevant.

## Verification

The backend files pass Python compilation. The Render configuration parses successfully. JavaScript syntax checks pass for the voice and Nexus bridge modules. A successful live `/ai/chat` request still depends on the deployed Render service being reachable and having at least one configured AI provider secret.
