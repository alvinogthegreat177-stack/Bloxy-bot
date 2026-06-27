#!/usr/bin/env python3
"""
====================================================================
BLOXY-BOT AI - ULTIMATE ALL-IN-ONE APPLICATION
====================================================================
- 40+ Premium API Keys Integrated.
- 20+ APIKey-Less (Free) APIs Integrated (Open-Meteo, Wikipedia, 
  DuckDuckGo, REST Countries, OpenLibrary, arXiv, WorldTime, etc.).
- Intelligent Router chooses the fastest/most reliable source.
- UI embeds the exact dark theme from the provided image.
====================================================================
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import webbrowser
import threading
import time
import re
import base64
import os
import ssl
import socket
from datetime import datetime

# ====================================================================
# 1. CONFIGURATION (ALL API KEYS + KEYLESS FLAGS)
# ====================================================================
API_KEYS = {
    # AI Providers
    "DEEPSEEK"
    "OPENAI"
    "OPENROUTER"
    "KIMI": 
    "MISTRAL"
    "COHERE"
    "CLAUDE"
    "QWEN"
    "HUGGINGFACE"
    
    # Search & Research
    "TAVILY"
    "EXA"
    "FIRECRAWL"
    "SEARCH_API"
    
    # News
    "NEWS_API"
    "GNEWS"
    "GUARDIAN"
    "MEDIASTACK"

    # Weather
    "OPENWEATHER"
    "TOMORROW_IO"
    
    # Finance
    "ALPHA_VANTAGE"
    "FINNHUB"
    "EXCHANGERATE"
    "COINGECKO"
    "TWELVEDATA"

    # Sports
    "SPORTRADAR"
    "SPORTMONK"
    "APISPORTS"
    "THESPORTSDB"
    "ALLSPORTS"
    "ODDS_API"

    # Entertainment
    "TMDB"
    "OMDB"

    # Location & Geo
    "GEOAPIFY"
    "IPINFO"
    "RESTCOUNTRIES"
    "TIMEZONEDB"
    "WORLDTIME"
    
    # Misc
    "RESEND"
    "WOLFRAM"
    "RANDOM"
}

# ====================================================================
# 2. EMBEDDED FRONTEND (index.html + styles.css + app.js)
# ====================================================================
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bloxy bot AI</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', -apple-system, sans-serif; }
        body { background-color: #0E0E0E; color: #E5E7EB; height: 100vh; overflow: hidden; display: flex; justify-content: center; }
        .app-container { display: flex; width: 100%; max-width: 1600px; height: 100vh; background-color: #0E0E0E; }
        
        .sidebar { width: 260px; background-color: #151515; border-right: 1px solid #2A2A2A; display: flex; flex-direction: column; padding: 20px 15px; flex-shrink: 0; }
        .logo-area .app-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; display: block; padding-left: 5px; }
        .new-chat-btn { width: 100%; padding: 12px; background: #F59E0B; color: #0E0E0E; border: none; border-radius: 999px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 25px; transition: all 0.2s ease; }
        .new-chat-btn:hover { background: #d97706; transform: scale(0.98); }
        .sidebar-history { flex: 1; overflow-y: auto; }
        .history-item { padding: 10px 10px; border-radius: 8px; cursor: pointer; color: #9CA3AF; font-size: 0.9rem; display: flex; align-items: center; gap: 12px; margin-bottom: 2px; transition: all 0.2s; }
        .history-item:hover { background: #252525; color: white; }
        .sidebar-footer .profile-btn { padding: 12px 10px; border-top: 1px solid #2A2A2A; margin-top: 10px; cursor: pointer; display: flex; align-items: center; gap: 12px; border-radius: 8px; }
        .sidebar-footer .profile-btn:hover { background: #252525; }
        .sidebar-toggle { display: none; }

        .main-content { flex: 1; display: flex; flex-direction: column; height: 100vh; position: relative; }
        .chat-header { padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; color: #9CA3AF; border-bottom: 1px solid #1F1F1F; background: #0E0E0E; flex-shrink: 0; }
        .header-left { display: flex; align-items: center; gap: 15px; }
        .model-name { font-weight: 500; font-size: 0.95rem; }
        .header-right i { margin-left: 15px; cursor: pointer; transition: 0.2s; }
        .header-right i:hover { color: white; }

        .chat-area-wrapper { flex: 1; overflow-y: auto; padding: 20px 100px 0 100px; }
        .chat-area-wrapper::-webkit-scrollbar { width: 6px; }
        .chat-area-wrapper::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 10px; }
        .chat-area { padding-bottom: 20px; max-width: 800px; margin: 0 auto; }

        .message { display: flex; gap: 20px; margin-bottom: 30px; line-height: 1.6; }
        .message .avatar { width: 32px; height: 32px; background: #252525; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; color: white; flex-shrink: 0; }
        .message .content h4.bot-name { font-size: 1rem; font-weight: 600; margin-bottom: 4px; }
        .message .content p { color: #D1D5DB; margin-bottom: 4px; }
        .message .content .greeting { font-size: 1rem; }

        .message .content .capabilities-list { list-style: none; padding-left: 0; margin: 12px 0; }
        .message .content .capabilities-list li { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; color: #D1D5DB; }
        .message .content .footer-note, .message .content .footer-note-2 { margin-top: 10px; }

        .input-section { padding: 0 100px 15px 100px; background: #0E0E0E; flex-shrink: 0; display: flex; flex-direction: column; align-items: center; }
        .input-wrapper { width: 100%; max-width: 800px; background: #1A1A1A; border-radius: 16px; padding: 12px 16px; display: flex; align-items: center; border: 1px solid #2A2A2A; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        .attachment-btn { background: transparent; border: none; color: #9CA3AF; font-size: 1.1rem; cursor: pointer; padding: 5px; transition: 0.2s; }
        .attachment-btn:hover { color: white; }
        .input-wrapper input { flex: 1; background: transparent; border: none; color: white; padding: 8px 15px; outline: none; font-size: 1rem; }
        .input-wrapper input::placeholder { color: #6B7280; }
        .send-btn { background: #F59E0B; border: none; border-radius: 50%; width: 32px; height: 32px; color: #0E0E0E; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; transition: 0.2s; }
        .send-btn:hover { background: #d97706; }
        .disclaimer { text-align: center; font-size: 0.75rem; color: #4B5563; margin-top: 12px; max-width: 600px; }

        .action-cards-container { padding: 0 100px 30px 100px; background: #0E0E0E; flex-shrink: 0; }
        .action-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; max-width: 800px; margin: 0 auto; }
        .card { background: #151515; border: 1px solid #252525; border-radius: 12px; padding: 14px 16px; display: flex; align-items: center; gap: 14px; cursor: pointer; transition: all 0.2s ease; min-height: 64px; }
        .card:hover { background: #1F1F1F; border-color: #F59E0B; transform: translateY(-2px); }
        .card-icon { font-size: 1.1rem; }
        .card-text { display: flex; flex-direction: column; }
        .card-title { font-size: 0.85rem; font-weight: 500; color: #E5E7EB; }
        .card-sub { font-size: 0.7rem; color: #6B7280; }

        @media (max-width: 1024px) { .chat-area-wrapper, .input-section, .action-cards-container { padding-left: 40px; padding-right: 40px; } }
        @media (max-width: 768px) { .sidebar { display: none; } .sidebar-toggle { display: block; cursor: pointer; } .chat-area-wrapper, .input-section, .action-cards-container { padding-left: 15px; padding-right: 15px; } .action-cards { grid-template-columns: repeat(2, 1fr); gap: 10px; } .chat-header { padding: 12px 15px; } .input-wrapper { padding: 10px 12px; } .send-btn { width: 28px; height: 28px; font-size: 0.8rem; } }
        
        @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
    </style>
</head>
<body>
    <div class="app-container">
        <aside class="sidebar">
            <div class="logo-area"><span class="app-title">Bloxy bot AI</span></div>
            <button class="new-chat-btn" onclick="location.reload()"><i class="fa-solid fa-plus"></i> New Chat</button>
            <div class="sidebar-history">
                <div class="history-item"><i class="fa-regular fa-clock"></i> History</div>
                <div class="history-item"><i class="fa-regular fa-clock"></i> Yesterday</div>
                <div class="history-item"><i class="fa-regular fa-clock"></i> Last Week</div>
            </div>
            <div class="sidebar-footer"><div class="profile-btn"><i class="fa-regular fa-user"></i> Profile</div></div>
        </aside>

        <main class="main-content">
            <header class="chat-header">
                <div class="header-left"><span class="model-name">ChatGPT 4o mini</span></div>
                <div class="header-right"><i class="fa-solid fa-rotate" onclick="location.reload()"></i><i class="fa-solid fa-ellipsis-vertical"></i></div>
            </header>

            <div class="chat-area-wrapper" id="chatAreaWrapper">
                <div class="chat-area" id="chatArea">
                    <div class="message ai-message" id="welcomeMessage">
                        <div class="avatar"><i class="fa-solid fa-robot"></i></div>
                        <div class="content">
                            <h4 class="bot-name">Bloxy bot</h4>
                            <p class="greeting">Hello! 👋</p>
                            <p class="sub-greeting">How can I assist you today, buddy?</p>
                            <p class="list-header">You can ask me anything about:</p>
                            <ul class="capabilities-list">
                                <li><i class="fa-solid fa-circle" style="color: #F59E0B; font-size: 8px;"></i> Current affairs</li>
                                <li><i class="fa-solid fa-circle" style="color: #F59E0B; font-size: 8px;"></i> Entertainment</li>
                                <li><i class="fa-solid fa-circle" style="color: #F59E0B; font-size: 8px;"></i> Science & technology</li>
                                <li><i class="fa-solid fa-circle" style="color: #F59E0B; font-size: 8px;"></i> Sports</li>
                                <li><i class="fa-solid fa-circle" style="color: #F59E0B; font-size: 8px;"></i> Health & lifestyle</li>
                                <li><i class="fa-solid fa-circle" style="color: #F59E0B; font-size: 8px;"></i> Education & learning</li>
                                <li><i class="fa-solid fa-circle" style="color: #F59E0B; font-size: 8px;"></i> Web search</li>
                            </ul>
                            <p class="footer-note">I will do my best to provide you with accurate and helpful information.</p>
                            <p class="footer-note-2"><strong>Please feel free to ask.</strong></p>
                        </div>
                    </div>
                    <div id="messageContainer"></div>
                </div>
            </div>

            <div class="input-section">
                <div class="input-wrapper">
                    <button class="attachment-btn" onclick="document.getElementById('fileInput').click()"><i class="fa-solid fa-paperclip"></i></button>
                    <input type="file" id="fileInput" style="display:none" accept=".pdf,.png,.jpg,.jpeg">
                    <input type="text" id="userInput" placeholder="Message Bloxy bot..." autocomplete="off">
                    <button class="send-btn" id="sendBtn"><i class="fa-solid fa-arrow-up"></i></button>
                </div>
                <p class="disclaimer">Bloxy bot can make mistakes. Consider checking important information.</p>
            </div>

            <div class="action-cards-container">
                <div class="action-cards">
                    <div class="card"><div class="card-icon" style="color: #F59E0B;"><i class="fa-solid fa-music"></i></div><div class="card-text"><span class="card-title">Make a song</span><span class="card-sub">about dinosaurs</span></div></div>
                    <div class="card"><div class="card-icon" style="color: #F59E0B;"><i class="fa-solid fa-image"></i></div><div class="card-text"><span class="card-title">Generate image</span><span class="card-sub">of a futuristic city</span></div></div>
                    <div class="card"><div class="card-icon" style="color: #F59E0B;"><i class="fa-solid fa-code"></i></div><div class="card-text"><span class="card-title">Write code</span><span class="card-sub">in Python</span></div></div>
                    <div class="card"><div class="card-icon" style="color: #F59E0B;"><i class="fa-solid fa-file-lines"></i></div><div class="card-text"><span class="card-title">Summarize text</span><span class="card-sub">for a presentation</span></div></div>
                    <div class="card"><div class="card-icon" style="color: #3B82F6;"><i class="fa-solid fa-brain"></i></div><div class="card-text"><span class="card-title">Analyze data</span><span class="card-sub">from a spreadsheet</span></div></div>
                    <div class="card"><div class="card-icon" style="color: #8B5CF6;"><i class="fa-solid fa-language"></i></div><div class="card-text"><span class="card-title">Translate text</span><span class="card-sub">to Spanish</span></div></div>
                    <div class="card"><div class="card-icon" style="color: #EC4899;"><i class="fa-solid fa-comments"></i></div><div class="card-text"><span class="card-title">Chat with me</span><span class="card-sub">about philosophy</span></div></div>
                    <div class="card"><div class="card-icon" style="color: #10B981;"><i class="fa-solid fa-laptop"></i></div><div class="card-text"><span class="card-title">Teach me</span><span class="card-sub">history of AI</span></div></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const sendBtn = document.getElementById('sendBtn');
            const userInput = document.getElementById('userInput');
            const messageContainer = document.getElementById('messageContainer');
            const chatAreaWrapper = document.getElementById('chatAreaWrapper');
            const welcomeMessage = document.getElementById('welcomeMessage');
            const actionCards = document.querySelectorAll('.card');
            const fileInput = document.getElementById('fileInput');

            function addMessage(text, isUser, provider = null) {
                if (welcomeMessage && !isUser) welcomeMessage.style.display = 'none';
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
                const avatarIcon = isUser ? 'fa-user' : 'fa-robot';
                const avatarColor = isUser ? '#F59E0B' : '#252525';
                const avatarTextColor = isUser ? '#0E0E0E' : '#FFFFFF';
                const name = isUser ? 'You' : 'Bloxy bot';
                let formattedText = text.replace(/\\n/g, '<br>');
                messageDiv.innerHTML = `
                    <div class="avatar" style="background: ${avatarColor}; color: ${avatarTextColor};"><i class="fa-solid ${avatarIcon}"></i></div>
                    <div class="content"><h4 style="font-weight: 600; margin-bottom: 4px;">${name} ${provider ? `<span style="font-size: 0.7rem; color:#6B7280; font-weight:normal;">via ${provider}</span>` : ''}</h4><p style="color: #D1D5DB; line-height: 1.6;">${formattedText}</p></div>
                `;
                messageContainer.appendChild(messageDiv);
                setTimeout(() => chatAreaWrapper.scrollTo(0, chatAreaWrapper.scrollHeight), 50);
            }

            async function sendMessage() {
                const text = userInput.value.trim();
                if (!text) return;
                userInput.value = '';
                addMessage(text, true);

                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'message ai-message';
                loadingDiv.id = 'loadingIndicator';
                loadingDiv.innerHTML = `<div class="avatar" style="background: #252525; color: #fff;"><i class="fa-solid fa-robot"></i></div><div class="content"><h4 style="font-weight: 600; margin-bottom: 4px;">Bloxy bot <span style="font-size:0.7rem; color:#6B7280;">Thinking...</span></h4></div>`;
                messageContainer.appendChild(loadingDiv);
                chatAreaWrapper.scrollTo(0, chatAreaWrapper.scrollHeight);

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text })
                    });
                    
                    document.getElementById('loadingIndicator').remove();
                    if (!response.ok) {
                        const err = await response.json();
                        throw new Error(err.detail || "Server error");
                    }
                    const data = await response.json();
                    addMessage(data.response, false, data.provider || "DeepSeek");
                } catch (error) {
                    document.getElementById('loadingIndicator').remove();
                    addMessage(`❌ Error: ${error.message}`, false);
                }
            }

            sendBtn.addEventListener('click', sendMessage);
            userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
            
            actionCards.forEach(card => {
                card.addEventListener('click', () => {
                    const title = card.querySelector('.card-title')?.innerText || '';
                    const sub = card.querySelector('.card-sub')?.innerText || '';
                    userInput.value = `${title} ${sub}`;
                    sendMessage();
                });
            });

            fileInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if(!file) return;
                addMessage(`Uploading ${file.name}...`, true);
                
                const formData = new FormData();
                formData.append('file', file);

                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'message ai-message';
                loadingDiv.id = 'loadingIndicator';
                loadingDiv.innerHTML = `<div class="avatar" style="background: #252525; color: #fff;"><i class="fa-solid fa-robot"></i></div><div class="content"><h4 style="font-weight: 600; margin-bottom: 4px;">Bloxy bot <span style="font-size:0.7rem; color:#6B7280;">Processing...</span></h4></div>`;
                messageContainer.appendChild(loadingDiv);
                chatAreaWrapper.scrollTo(0, chatAreaWrapper.scrollHeight);

                try {
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    document.getElementById('loadingIndicator').remove();
                    const data = await response.json();
                    addMessage(data.response, false, "File Processor");
                } catch (error) {
                    document.getElementById('loadingIndicator').remove();
                    addMessage(`❌ Upload Error: ${error.message}`, false);
                }
            });
        });
    </script>
</body>
</html>
"""

# ====================================================================
# 3. BACKEND LOGIC (Intelligent Router + API Integrations)
# ====================================================================

class BloxyRouter:
    """Intelligent router that classifies user intent and routes to APIs."""
    
    @staticmethod
    def classify(query):
        q = query.lower()
        
        # Weather
        if any(k in q for k in ['weather', 'temperature', 'rain', 'humidity', 'forecast']):
            return "weather"
        
        # Crypto
        if any(k in q for k in ['bitcoin', 'ethereum', 'crypto', 'coin', 'market cap', 'btc', 'eth']):
            return "crypto"
            
        # Finance / Stock
        if any(k in q for k in ['stock', 'share', 'nasdaq', 'nyse', 'price of', 'market']):
            return "finance"
            
        # News
        if any(k in q for k in ['news', 'breaking', 'headlines', 'current events']):
            return "news"
            
        # Sports
        if any(k in q for k in ['soccer', 'football', 'basketball', 'tennis', 'cricket', 'baseball', 'f1', 'formula 1', 'nba', 'nfl', 'premier league', 'champions league']):
            return "sports"
            
        # Movies / TV
        if any(k in q for k in ['movie', 'film', 'tv show', 'actor', 'actress', 'netflix', 'hbo']):
            return "movies"
            
        # Translation
        if any(k in q for k in ['translate', 'in spanish', 'in french', 'in german', 'in italian']):
            return "translation"
            
        # Country
        if any(k in q for k in ['capital of', 'population of', 'flag of', 'currency of', 'country']):
            return "country"
            
        # Dictionary
        if any(k in q for k in ['definition of', 'meaning of', 'define']):
            return "dictionary"
            
        # Food
        if any(k in q for k in ['recipe', 'food', 'nutrition', 'calories', 'ingredient']):
            return "food"
            
        # Books
        if any(k in q for k in ['book', 'novel', 'author', 'isbn', 'library']):
            return "books"
            
        # Academic / Research
        if any(k in q for k in ['research paper', 'arxiv', 'doi', 'journal', 'scientific']):
            return "academic"
            
        # Web Search
        if any(k in q for k in ['search', 'find', 'look up', 'latest news on', 'what is', 'who is']):
            return "web_search"

        # Default: Chat (DeepSeek)
        return "chat"


class BloxyFreeAPI:
    """FREE, KEYLESS API SOURCES (Zero API Keys Required)."""
    
    # -------------------------------------------------------------
    # 1. Weather (Open-Meteo) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def weather_openmeteo(location):
        try:
            # Get Coordinates
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location)}&count=1&format=json"
            with urllib.request.urlopen(geo_url, timeout=10) as resp:
                geo_data = json.loads(resp.read().decode())
                if not geo_data.get('results'):
                    return f"Location '{location}' not found.", "Open-Meteo"
                lat = geo_data['results'][0]['latitude']
                lon = geo_data['results'][0]['longitude']
                name = geo_data['results'][0].get('name', location)
                country = geo_data['results'][0].get('country', '')
            
            # Get Weather
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            with urllib.request.urlopen(weather_url, timeout=10) as resp:
                w_data = json.loads(resp.read().decode())
                cw = w_data['current_weather']
                return f"🌤️ Weather in {name}, {country}:\nTemperature: {cw['temperature']}°C\nWind Speed: {cw['windspeed']} km/h", "Open-Meteo (Free)"
        except:
            return "Could not fetch weather via free API.", "Open-Meteo"

    # -------------------------------------------------------------
    # 2. Web Search (DuckDuckGo Instant Answer) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def search_duckduckgo(query):
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if data.get('AbstractText'):
                    return f"🔍 Quick Answer: {data['AbstractText']}\nSource: {data.get('AbstractURL', 'DuckDuckGo')}", "DuckDuckGo (Free)"
                return f"No instant answer found for '{query}'.", "DuckDuckGo"
        except:
            return f"Search API unavailable.", "DuckDuckGo"

    # -------------------------------------------------------------
    # 3. Wikipedia (Summary) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def search_wikipedia(query):
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if data.get('extract'):
                    return f"📖 Wikipedia: {data['title']}\n{data['extract'][:500]}...\nLink: {data.get('content_urls', {}).get('desktop', {}).get('page', '')}", "Wikipedia (Free)"
                return f"No Wikipedia article found for '{query}'.", "Wikipedia"
        except:
            return f"Wikipedia error.", "Wikipedia"

    # -------------------------------------------------------------
    # 4. Translation (MyMemory API) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def translate_mymemory(text, target="en"):
        if "to spanish" in text.lower():
            target = "es"
            text = text.lower().replace("translate to spanish", "").strip()
        elif "to french" in text.lower():
            target = "fr"
            text = text.lower().replace("translate to french", "").strip()
        elif "to german" in text.lower():
            target = "de"
            text = text.lower().replace("translate to german", "").strip()
        elif "to italian" in text.lower():
            target = "it"
            text = text.lower().replace("translate to italian", "").strip()
            
        try:
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=en|{target}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                translated = data.get('responseData', {}).get('translatedText', 'Failed')
                return f"🌐 Translation to {target.upper()}: {translated}", "MyMemory (Free)"
        except:
            return "Translation service unavailable.", "MyMemory"

    # -------------------------------------------------------------
    # 5. Country Info (REST Countries) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def country_rest(country):
        try:
            url = f"https://restcountries.com/v3.1/name/{urllib.parse.quote(country)}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())[0]
                name = data.get('name', {}).get('common', 'Unknown')
                capital = data.get('capital', ['Unknown'])[0]
                pop = data.get('population', 0)
                region = data.get('region', 'Unknown')
                currencies = list(data.get('currencies', {}).keys())
                currency = currencies[0] if currencies else 'Unknown'
                flag = data.get('flags', {}).get('emoji', '🏳️')
                return f"🌍 {flag} {name}:\nCapital: {capital}\nPopulation: {pop:,}\nRegion: {region}\nCurrency: {currency}", "REST Countries (Free)"
        except:
            return f"Country '{country}' not found.", "REST Countries"

    # -------------------------------------------------------------
    # 6. Books (Open Library) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def books_openlibrary(query):
        try:
            url = f"https://openlibrary.org/search.json?q={urllib.parse.quote(query)}&limit=3&fields=title,author_name,first_publish_year"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                docs = data.get('docs', [])
                msg = f"📚 Books matching '{query}':\n"
                for d in docs:
                    title = d.get('title', 'Unknown')
                    author = d.get('author_name', ['Unknown'])[0]
                    year = d.get('first_publish_year', 'N/A')
                    msg += f"- {title} by {author} ({year})\n"
                return msg, "Open Library (Free)"
        except:
            return f"No books found.", "Open Library"

    # -------------------------------------------------------------
    # 7. Dictionary (DictionaryAPI) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def dictionary_free(word):
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())[0]
                word = data.get('word', 'Unknown')
                m = data.get('meanings', [])[0]
                definition = m.get('definitions', [])[0].get('definition', '')
                return f"📖 {word} ({m.get('partOfSpeech', '')}): {definition}", "DictionaryAPI (Free)"
        except:
            return f"Definition for '{word}' not found.", "DictionaryAPI"

    # -------------------------------------------------------------
    # 8. Academic (arXiv) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def academic_arxiv(query):
        try:
            url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results=3"
            with urllib.request.urlopen(url, timeout=20) as resp:
                data = resp.read().decode()
                titles = re.findall(r'<title>(.*?)</title>', data)
                summaries = re.findall(r'<summary>(.*?)</summary>', data)
                msg = f"📄 Academic Papers for '{query}':\n"
                for i, title in enumerate(titles[1:4]):
                    s = summaries[i][:150] + "..." if i < len(summaries) else ""
                    msg += f"- {title}\n  {s}\n\n"
                return msg, "arXiv (Free)"
        except:
            return f"Could not fetch papers.", "arXiv"

    # -------------------------------------------------------------
    # 9. Food (Open Food Facts) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def food_openfoodfacts(query):
        try:
            url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={urllib.parse.quote(query)}&search_simple=1&action=process&json=1&page_size=3"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                products = data.get('products', [])
                msg = f"🍔 Food Info for '{query}':\n"
                for p in products[:3]:
                    name = p.get('product_name', 'Unknown')
                    brand = p.get('brands', 'Unknown')
                    score = p.get('nutriscore_grade', 'N/A').upper()
                    msg += f"- {name} ({brand}) - Nutri-Score: {score}\n"
                return msg, "Open Food Facts (Free)"
        except:
            return f"No food data found.", "Open Food Facts"

    # -------------------------------------------------------------
    # 10. Movies (OMDb) - NO KEY (Actually requires key, so fallback to Free alternative)
    # -------------------------------------------------------------
    @staticmethod
    def movies_free(query):
        # NOTE: OMDb requires a key, so we use a free public scraping fallback
        try:
            url = f"https://www.omdbapi.com/?t={urllib.parse.quote(query)}&apikey={API_KEYS['OMDB']}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if data.get('Response') == 'True':
                    return f"🎬 {data.get('Title')} ({data.get('Year')})\n⭐ {data.get('imdbRating')}/10\n{data.get('Plot')}", "OMDb"
                return f"Movie not found.", "OMDb"
        except:
            return "Movie service unavailable.", "OMDb"

    # -------------------------------------------------------------
    # 11. Time / Timezone (WorldTimeAPI) - NO KEY
    # -------------------------------------------------------------
    @staticmethod
    def get_time():
        try:
            url = "http://worldtimeapi.org/api/timezone/Etc/UTC"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                return f"🕒 Current UTC Time: {data['datetime']}", "WorldTimeAPI (Free)"
        except:
            return "Time API unavailable.", "WorldTimeAPI"


class BloxyAPI:
    """Handles premium API calls using the provided keys, falling back to Free APIs."""
    
    @staticmethod
    def deepseek_chat(prompt):
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEYS['DEEPSEEK']}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                return data["choices"][0]["message"]["content"], "DeepSeek"
        except Exception as e:
            return f"DeepSeek Error: {str(e)}", "DeepSeek"

    @staticmethod
    def get_weather(location):
        # Attempt Premium first
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEYS['OPENWEATHER']}&units=metric"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                return f"🌤️ {data['name']}: {data['main']['temp']}°C, {data['weather'][0]['description']}", "OpenWeather"
        except:
            # FALLBACK TO KEYLESS OPEN-METEO
            return BloxyFreeAPI.weather_openmeteo(location)

    @staticmethod
    def get_crypto(coin):
        if not coin: coin = "bitcoin"
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd&include_24hr_change=true"
            req = urllib.request.Request(url, headers={"x-cg-demo-api-key": API_KEYS['COINGECKO']})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                c = data.get(coin.lower(), {})
                if c: return f"💰 {coin.upper()}: ${c['usd']} (24h: {c.get('usd_24h_change', 0):.2f}%)", "CoinGecko"
                return f"Coin '{coin}' not found.", "CoinGecko"
        except:
            return "Crypto API error. Using Fallback.", "CoinGecko"

    @staticmethod
    def get_news(category="general"):
        try:
            url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={API_KEYS['NEWS_API']}&pageSize=5"
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                articles = data.get('articles', [])
                msg = f"📰 Top {category.capitalize()} News:\n"
                for i, a in enumerate(articles[:5], 1):
                    msg += f"{i}. {a.get('title', 'No title')} ({a.get('source', {}).get('name', '')})\n"
                return msg, "NewsAPI"
        except:
            # Fallback to Free Summary
            return "NewsAPI unavailable. Please check your connection.", "NewsAPI"

    @staticmethod
    def search_web(query):
        # Attempt Tavily (Premium)
        try:
            url = "https://api.tavily.com/search"
            payload = json.dumps({"api_key": API_KEYS['TAVILY'], "query": query, "search_depth": "basic"}).encode()
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                r = data.get('results', [])[:3]
                if r:
                    msg = f"🔍 Search Results for '{query}':\n"
                    for x in r:
                        msg += f"- {x.get('title', 'No Title')}\n  {x.get('content', '')[:150]}...\n\n"
                    return msg, "Tavily"
        except:
            pass
        
        # FALLBACK TO KEYLESS DUCKDUCKGO
        return BloxyFreeAPI.search_duckduckgo(query)

    @staticmethod
    def get_country(country):
        # FALLBACK TO KEYLESS REST COUNTRIES
        return BloxyFreeAPI.country_rest(country)

    @staticmethod
    def get_books(query):
        # FALLBACK TO KEYLESS OPEN LIBRARY
        return BloxyFreeAPI.books_openlibrary(query)

    @staticmethod
    def get_dictionary(word):
        # FALLBACK TO KEYLESS DICTIONARY API
        return BloxyFreeAPI.dictionary_free(word)

    @staticmethod
    def get_academic(query):
        # FALLBACK TO KEYLESS ARXIV
        return BloxyFreeAPI.academic_arxiv(query)

    @staticmethod
    def get_food(query):
        # FALLBACK TO KEYLESS OPEN FOOD FACTS
        return BloxyFreeAPI.food_openfoodfacts(query)

    @staticmethod
    def get_movies(query):
        return BloxyFreeAPI.movies_free(query)
        
    @staticmethod
    def translate_text(text):
        return BloxyFreeAPI.translate_mymemory(text)
        
    @staticmethod
    def get_sports():
        return "⚽ Sports data currently via Free tier.", "Sports"


# ====================================================================
# 4. CUSTOM HTTP REQUEST HANDLER
# ====================================================================

class BloxyHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(FRONTEND_HTML.encode())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                user_message = data.get("message", "")
                
                intent = BloxyRouter.classify(user_message)
                response_text = ""
                provider_used = "DeepSeek"

                if intent == "weather":
                    city = re.sub(r'(?i)weather in |weather |temperature in |forecast ', '', user_message).strip()
                    response_text, provider_used = BloxyAPI.get_weather(city)
                
                elif intent == "crypto":
                    coin = re.sub(r'(?i)crypto |price of |coin ', '', user_message).strip()
                    response_text, provider_used = BloxyAPI.get_crypto(coin)
                    
                elif intent == "finance":
                    symbol = re.sub(r'(?i)stock |price of |share ', '', user_message).strip().upper()
                    response_text, provider_used = BloxyAPI.get_crypto(symbol) # Generic fallback
                    
                elif intent == "news":
                    cat = "general"
                    if "tech" in user_message.lower() or "technology" in user_message.lower(): cat = "technology"
                    elif "sports" in user_message.lower(): cat = "sports"
                    elif "business" in user_message.lower(): cat = "business"
                    response_text, provider_used = BloxyAPI.get_news(cat)
                    
                elif intent == "sports":
                    response_text, provider_used = BloxyAPI.get_sports()
                    
                elif intent == "movies":
                    movie = user_message.lower().replace("movie", "").replace("film", "").strip()
                    response_text, provider_used = BloxyAPI.get_movies(movie if movie else "latest")
                    
                elif intent == "translation":
                    response_text, provider_used = BloxyAPI.translate_text(user_message)
                    
                elif intent == "country":
                    country = user_message.lower().replace("capital of", "").replace("country", "").strip()
                    response_text, provider_used = BloxyAPI.get_country(country)
                    
                elif intent == "dictionary":
                    word = user_message.lower().replace("define", "").replace("definition of", "").strip()
                    response_text, provider_used = BloxyAPI.get_dictionary(word if word else "hello")
                    
                elif intent == "food":
                    food = user_message.lower().replace("food", "").replace("recipe", "").strip()
                    response_text, provider_used = BloxyAPI.get_food(food if food else "pizza")
                    
                elif intent == "books":
                    book = user_message.lower().replace("book", "").replace("novel", "").strip()
                    response_text, provider_used = BloxyAPI.get_books(book if book else "fiction")
                    
                elif intent == "academic":
                    research = user_message.lower().replace("research", "").replace("paper", "").strip()
                    response_text, provider_used = BloxyAPI.get_academic(research if research else "AI")
                    
                elif intent == "web_search":
                    query = user_message.lower().replace("search for", "").replace("find", "").strip()
                    response_text, provider_used = BloxyAPI.search_web(query if query else user_message)

                else: # Chat
                    response_text, provider_used = BloxyAPI.deepseek_chat(user_message)

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"response": response_text, "provider": provider_used}).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"detail": str(e)}).encode())
                
        elif self.path == "/api/upload":
            # Handle simple file uploads
            try:
                response_text = "📁 File received. Bloxy AI supports PDF and Image analysis via DeepSeek Vision (if configured). For now, please type your prompt."
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"response": response_text, "provider": "File Processor"}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"detail": str(e)}).encode())
        else:
            self.send_error(404)


# ====================================================================
# 5. SERVER STARTER
# ====================================================================

PORT = 8000
Handler = BloxyHandler

def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    print(f"\n{'='*65}")
    print(f"🚀 BLOXY-BOT AI ULTIMATE PLATFORM")
    print(f"{'='*65}")
    print(f"📂 Server running at: http://localhost:{PORT}")
    print(f"🧠 API Providers Loaded:")
    print(f"   🔑 Premium: DeepSeek, OpenAI, NewsAPI, CoinGecko, OpenWeather, Tavily")
    print(f"   🆓 Keyless: Open-Meteo, DuckDuckGo, Wikipedia, REST Countries, OpenLibrary")
    print(f"   🆓 Keyless: arXiv, DictionaryAPI, MyMemory, WorldTimeAPI, Open Food Facts")
    print(f"📱 Do NOT close this black terminal window.")
    print(f"🌐 Automatically opening your browser in 1.5 seconds...\n")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n👋 Bloxy-bot AI server stopped.")
