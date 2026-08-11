/**
 * Bloxy Nexus — Unified AI API Gateway
 *
 * One API. 30+ models. Automatic failover. Zero errors.
 *
 * The Nexus key below is a shared secret between the platform owner and admin only.
 * It gates access to the unified cloud routing layer that load-balances across
 * every configured provider (Groq, DeepSeek, Mistral, OpenRouter, OpenAI, Claude, Cohere)
 * — each offering multiple models for a combined knowledge base of 30+ AI models.
 *
 * Configuration is admin-locked. Normal users cannot access or modify API keys.
 *
 * ⚠️  Do not share this key publicly.
 */

export const NEXUS_NAME = 'Bloxy Nexus';
export const NEXUS_TAGLINE = 'Unified AI API Gateway';
export const NEXUS_KEY = 'nx_bloxy_7K9mP4x8Q3wZ2vR6';

// Failover priority: fast + cheap providers first, premium models as fallback
export const NEXUS_PRIORITY = [
  'groq',
  'deepseek',
  'mistral',
  'openrouter',
  'openai',
  'claude',
  'cohere',
];

/**
 * Validates a key against the Nexus secret.
 * Only the platform owner and admin know this key.
 */
export function validateNexusKey(key) {
  return key === NEXUS_KEY;
}
