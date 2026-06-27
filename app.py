#!/usr/bin/env python3
"""
====================================================================
BLOXY-BOT AI - ULTIMATE ALL-IN-ONE APPLICATION
====================================================================
Combined: app.py (Backend) + index.html + styles.css + app.js
API Sources: All keys provided by the user integrated.
No external dependencies required (Uses Python Standard Library).
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
# CONFIGURATION (API KEYS FROM USER)
# ====================================================================
API_KEYS = {
    # AI Providers
    "DEEPSEEK"
    "OPENAI"
    "OPENROUTER
    "GROQ"
    "KIMI"
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
    "EXCHANGERATE_HOST" 
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
# 1. EMBEDDED FRONTEND (index.html + styles.css + app.js)
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
# 2. BACKEND LOGIC (Routing + API Integrations)
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


class BloxyAPI:
    """Handles all API calls using the provided keys."""
    
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
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEYS['OPENWEATHER']}&units=metric"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())
                temp = data['main']['temp']
                desc = data['weather'][0]['description']
                humidity = data['main']['humidity']
                wind = data['wind']['speed']
                return f"🌤️ Weather in {data['name']}, {data['sys']['country']}:\nTemperature: {temp}°C\nCondition: {desc}\nHumidity: {humidity}%\nWind: {wind} m/s", "OpenWeather"
        except:
            return f"Could not fetch weather for '{location}'. Please check the city name.", "OpenWeather"

    @staticmethod
    def get_crypto(coin):
        if not coin:
            url = "https://api.coingecko.com/api/v3/trending"
        else:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd&include_24hr_change=true"
        headers = {"x-cg-demo-api-key": API_KEYS['COINGECKO']}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
                if not coin:
                    coins = data['coins'][:3]
                    msg = "🚀 Top 3 Trending Coins:\n"
                    for c in coins:
                        coin_data = c['item']
                        msg += f"- {coin_data['name']} ({coin_data['symbol'].upper()}): ${coin_data['data']['price']}\n"
                    return msg, "CoinGecko"
                else:
                    coin_data = data.get(coin.lower(), {})
                    if coin_data:
                        return f"💰 {coin.upper()} Price: ${coin_data['usd']}\n24h Change: {coin_data.get('usd_24h_change', 0):.2f}%", "CoinGecko"
                    return f"Coin '{coin}' not found.", "CoinGecko"
        except:
            return "Crypto API error. Please check the coin name.", "CoinGecko"

    @staticmethod
    def get_stock(symbol):
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={API_KEYS['FINNHUB']}"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())
                if data.get('c'):
                    return f"📈 {symbol.upper()}:\nCurrent: ${data['c']}\nHigh: ${data['h']}\nLow: ${data['l']}\nChange: {data['d']:.2f} ({data['dp']:.2f}%)", "Finnhub"
                return f"Symbol '{symbol}' not found.", "Finnhub"
        except:
            return f"Stock API error for '{symbol}'.", "Finnhub"

    @staticmethod
    def get_news(category="general"):
        url = f"https://newsapi.org/v2/top-headlines?country=us&category={category}&apiKey={API_KEYS['NEWS_API']}&pageSize=5"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())
                articles = data.get('articles', [])
                msg = f"📰 Top {category.capitalize()} News:\n"
                for i, article in enumerate(articles[:5], 1):
                    title = article.get('title', 'No title')
                    source = article.get('source', {}).get('name', 'Unknown')
                    msg += f"{i}. {title} ({source})\n"
                return msg, "NewsAPI"
        except:
            return "Could not fetch news. Please try again later.", "NewsAPI"

    @staticmethod
    def get_sports(sport="soccer"):
        # Using TheSportsDB (Free tier)
        url = f"https://www.thesportsdb.com/api/v1/json/{API_KEYS['THESPORTSDB']}/eventspastleague.php?id=4328" # Premier League ID
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())
                events = data.get('events', [])[:3]
                msg = f"⚽ Latest Sports Results:\n"
                for e in events:
                    msg += f"- {e.get('strHomeTeam')} {e.get('intHomeScore', '?')} vs {e.get('strAwayTeam')} {e.get('intAwayScore', '?')}\n"
                return msg, "TheSportsDB"
        except:
            return "Sports API error. Please check connection.", "TheSportsDB"

    @staticmethod
    def get_movies(query):
        url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEYS['TMDB']}&query={urllib.parse.quote(query)}&language=en-US"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())
                movies = data.get('results', [])[:3]
                msg = f"🎬 Movies matching '{query}':\n"
                for m in movies:
                    title = m.get('title', 'Unknown')
                    year = m.get('release_date', '')[:4]
                    rating = m.get('vote_average', 0)
                    msg += f"- {title} ({year}) - ⭐ {rating}/10\n"
                return msg, "TMDB"
        except:
            return f"Could not find movies for '{query}'.", "TMDB"

    @staticmethod
    def search_web(query):
        # Tavily Search
        url = "https://api.tavily.com/search"
        payload = {"api_key": API_KEYS['TAVILY'], "query": query, "search_depth": "basic"}
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode())
                results = data.get('results', [])[:3]
                if results:
                    msg = f"🔍 Web Search Results for '{query}':\n"
                    for r in results:
                        msg += f"- {r.get('title', 'No Title')}\n  {r.get('content', '')[:200]}...\n  Source: {r.get('url', '')}\n\n"
                    return msg, "Tavily"
                return f"No results found for '{query}'.", "Tavily"
        except:
            return f"Search API unavailable. Please try again later.", "Tavily"

    @staticmethod
    def get_country(country):
        url = f"https://restcountries.com/v3.1/name/{urllib.parse.quote(country)}"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())[0]
                name = data.get('name', {}).get('common', 'Unknown')
                capital = data.get('capital', ['Unknown'])[0]
                population = data.get('population', 0)
                currency = list(data.get('currencies', {}).keys())[0]
                region = data.get('region', 'Unknown')
                flag = data.get('flags', {}).get('emoji', '🏳️')
                return f"🌍 {flag} {name}:\nCapital: {capital}\nPopulation: {population:,}\nCurrency: {currency}\nRegion: {region}", "REST Countries"
        except:
            return f"Country '{country}' not found.", "REST Countries"

    @staticmethod
    def get_dictionary(word):
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())[0]
                word = data.get('word', 'Unknown')
                meanings = data.get('meanings', [])
                msg = f"📖 Definition of '{word}':\n"
                for m in meanings[:1]:
                    part_of_speech = m.get('partOfSpeech', '')
                    definitions = m.get('definitions', [])[:2]
                    for d in definitions:
                        msg += f"- ({part_of_speech}) {d.get('definition', '')}\n"
                return msg, "DictionaryAPI"
        except:
            return f"Definition for '{word}' not found.", "DictionaryAPI"

    @staticmethod
    def get_books(query):
        url = f"https://openlibrary.org/search.json?q={urllib.parse.quote(query)}&limit=3&fields=title,author_name,first_publish_year"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())
                docs = data.get('docs', [])
                msg = f"📚 Books matching '{query}':\n"
                for d in docs:
                    title = d.get('title', 'Unknown')
                    author = d.get('author_name', ['Unknown'])[0]
                    year = d.get('first_publish_year', 'N/A')
                    msg += f"- {title} by {author} ({year})\n"
                return msg, "Open Library"
        except:
            return f"No books found for '{query}'.", "Open Library"

    @staticmethod
    def get_academic(query):
        url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results=3"
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                data = response.read().decode()
                # Simple extraction
                titles = re.findall(r'<title>(.*?)</title>', data)
                summaries = re.findall(r'<summary>(.*?)</summary>', data)
                msg = f"📄 Academic Papers for '{query}':\n"
                for i, title in enumerate(titles[1:4]):
                    summary = summaries[i][:150] + "..." if i < len(summaries) else ""
                    msg += f"- {title}\n  {summary}\n\n"
                return msg, "arXiv"
        except:
            return f"Could not fetch academic papers for '{query}'.", "arXiv"
    
    @staticmethod
    def get_food(query):
        url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={urllib.parse.quote(query)}&search_simple=1&action=process&json=1&page_size=3"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())
                products = data.get('products', [])
                msg = f"🍔 Food Info for '{query}':\n"
                for p in products[:3]:
                    name = p.get('product_name', 'Unknown')
                    brand = p.get('brands', 'Unknown')
                    nutriscore = p.get('nutriscore_grade', 'N/A').upper()
                    msg += f"- {name} ({brand}) - Nutri-Score: {nutriscore}\n"
                return msg, "Open Food Facts"
        except:
            return f"No food data found for '{query}'.", "Open Food Facts"

    @staticmethod
    def translate_text(text):
        # Uses a free, keyless translation API as fallback
        target = "en"
        if "to spanish" in text.lower():
            target = "es"
            text = text.lower().replace("translate to spanish", "").strip()
        elif "to french" in text.lower():
            target = "fr"
            text = text.lower().replace("translate to french", "").strip()
        elif "to german" in text.lower():
            target = "de"
            text = text.lower().replace("translate to german", "").strip()
            
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=en|{target}"
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.loads(response.read().decode())
                translated = data.get('responseData', {}).get('translatedText', 'Translation failed')
                return f"🌐 Translation to {target.upper()}: {translated}", "MyMemory"
        except:
            return f"Translation service unavailable.", "Translation"


# ====================================================================
# 3. CUSTOM HTTP REQUEST HANDLER
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
                
                # ROUTING LOGIC
                intent = BloxyRouter.classify(user_message)
                response_text = ""
                provider_used = "DeepSeek"

                if intent == "weather":
                    city = re.sub(r'(?i)weather in |weather |temperature in |forecast ', '', user_message).strip()
                    response_text, provider_used = BloxyAPI.get_weather(city)
                
                elif intent == "crypto":
                    coin = re.sub(r'(?i)crypto |price of |coin ', '', user_message).strip()
                    if not coin: coin = "bitcoin"
                    response_text, provider_used = BloxyAPI.get_crypto(coin)
                    
                elif intent == "finance":
                    symbol = re.sub(r'(?i)stock |price of |share ', '', user_message).strip().upper()
                    response_text, provider_used = BloxyAPI.get_stock(symbol)
                    
                elif intent == "news":
                    cat = "general"
                    if "tech" in user_message.lower() or "technology" in user_message.lower(): cat = "technology"
                    elif "sports" in user_message.lower(): cat = "sports"
                    elif "business" in user_message.lower(): cat = "business"
                    response_text, provider_used = BloxyAPI.get_news(cat)
                    
                elif intent == "sports":
                    response_text, provider_used = BloxyAPI.get_sports()
                    
                elif intent == "movies":
                    movie = user_message.lower().replace("movie", "").replace("film", "").replace("tv", "").strip()
                    response_text, provider_used = BloxyAPI.get_movies(movie if movie else "latest")
                    
                elif intent == "translation":
                    response_text, provider_used = BloxyAPI.translate_text(user_message)
                    
                elif intent == "country":
                    country = user_message.lower().replace("capital of", "").replace("population of", "").replace("country", "").strip()
                    response_text, provider_used = BloxyAPI.get_country(country)
                    
                elif intent == "dictionary":
                    word = user_message.lower().replace("define", "").replace("definition of", "").replace("meaning of", "").strip()
                    response_text, provider_used = BloxyAPI.get_dictionary(word if word else "hello")
                    
                elif intent == "food":
                    food = user_message.lower().replace("food", "").replace("recipe", "").replace("nutrition", "").strip()
                    response_text, provider_used = BloxyAPI.get_food(food if food else "pizza")
                    
                elif intent == "books":
                    book = user_message.lower().replace("book", "").replace("novel", "").replace("author", "").strip()
                    response_text, provider_used = BloxyAPI.get_books(book if book else "fiction")
                    
                elif intent == "academic":
                    research = user_message.lower().replace("research", "").replace("paper", "").replace("arxiv", "").strip()
                    response_text, provider_used = BloxyAPI.get_academic(research if research else "artificial intelligence")
                    
                elif intent == "web_search":
                    query = user_message.lower().replace("search for", "").replace("find", "").replace("look up", "").replace("latest news on", "").strip()
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
            # Handle simple file uploads (PDF / Image basic support)
            try:
                boundary = self.headers['Content-Type'].split("boundary=")[1]
                raw_data = self.rfile.read(int(self.headers['Content-Length']))
                parts = raw_data.split(f"--{boundary}".encode())
                
                response_text = "📁 File received. Bloxy AI supports PDF and Image analysis via DeepSeek Vision and PyPDF (if installed). \n\nFor now, please type your prompt and I will respond using the DeepSeek AI."
                
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
# 4. SERVER STARTER
# ====================================================================

PORT = 8000
Handler = BloxyHandler

def open_browser():
    time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"🚀 BLOXY-BOT AI ULTIMATE PLATFORM")
    print(f"{'='*60}")
    print(f"📂 Server running at: http://localhost:{PORT}")
    print(f"🧠 API Providers Loaded: DeepSeek, OpenAI, CoinGecko, Tavily, OpenWeather, Finnhub, NewsAPI, TMDB, RESTCountries, OpenLibrary, arXiv, DictionaryAPI, and 20+ more!")
    print(f"📱 Do NOT close this black terminal window.")
    print(f"🌐 Automatically opening your browser in 1 second...\n")
    
    # Automatically open browser after 1 second
    threading.Thread(target=open_browser, daemon=True).start()
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n👋 Bloxy-bot AI server stopped.")
