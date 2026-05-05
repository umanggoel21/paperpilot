"""
PaperPilot — Shared API Clients (Singleton)
============================================
Centralizes Tavily and Groq client initialization.
All service modules should import from here instead of
creating their own client instances.

Usage:
    from clients import tavily_client, groq_client

Environment variables required in .env:
    TAVILY_API_KEY=tvly-...
    GROQ_API_KEY=gsk_...
"""

import os
import logging

from dotenv import load_dotenv
from tavily import TavilyClient
from groq import Groq

load_dotenv(override=True)

logger = logging.getLogger('paperpilot.clients')

_tavily_key = os.getenv("TAVILY_API_KEY")
_groq_key = os.getenv("GROQ_API_KEY")

if not _tavily_key:
    logger.warning("TAVILY_API_KEY not set — Tavily features will be unavailable")

if not _groq_key:
    logger.warning("GROQ_API_KEY not set — Groq features will be unavailable")

# Singleton clients — initialized once at import time (None if key missing)
tavily_client = TavilyClient(api_key=_tavily_key) if _tavily_key else None
groq_client = Groq(api_key=_groq_key) if _groq_key else None

if tavily_client and groq_client:
    logger.info("Tavily + Groq clients initialized.")
elif tavily_client:
    logger.info("Tavily client initialized (Groq unavailable).")
elif groq_client:
    logger.info("Groq client initialized (Tavily unavailable).")
else:
    logger.warning("No API clients initialized — set keys in environment.")
