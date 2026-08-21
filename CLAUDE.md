# Bloxy-bot project notes

- Preserve the existing Base44-inspired UI, sidebar, chat controls, account pages, settings, verified badge, and conversation features.
- Chat generation must use the direct Bloxy Nexus HTTPS endpoint, not Base44 AI/integration credits.
- The Render Bloxy Nexus service is `bloxy-nexus` and exposes `POST /ai/chat`.
- Keep chat renaming available directly from the sidebar.
- Never commit API keys or other secrets to the frontend repository.
- Keep provider credentials server-side in Render environment variables.
