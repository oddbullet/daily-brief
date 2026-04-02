# Daily Brief

AI-powered daily news briefings that trace how global events ripple down to your local community.

## What It Does

Daily Brief fetches and analyzes news across three scopes, **world**, **national**, and **local**, then generates a structured markdown briefing. The **key feature** is the causal chain analysis: it identifies how a geopolitical event at the world level creates ripple effects at the national policy level, and what that ultimately means for your local area.

## Key Features

- **Causal chain tracing** — global news → national → local impact
- **Structured story analysis** — each story tagged with sentiment, threat level (none/low/medium/high), relevance score (1–10), and topic categories
- **Swappable LLM providers** — Groq, Ollama, or OpenRouter
- **Tavily response caching** — reduces API calls and costs during repeated runs
- **Markdown output** — saved to `./output/` with structured filenames

## Quick Start

**Requirements:** Python 3.13 and [uv](https://docs.astral.sh/uv/)

```bash
# 1. Clone and install
git clone https://github.com/your-username/daily-brief
cd daily-brief
uv sync

uv pip install -e .

# 2. Configure API keys
cp .env.example .env

# 3. Run
brief
```

## Configuration

Copy `.env.example` to `.env` and fill in your keys:

| Variable                     | Required            | Description                                           |
| ---------------------------- | ------------------- | ----------------------------------------------------- |
| `TAVILY_API_KEY`             | Yes                 | [Tavily](https://tavily.com) search API key           |
| `GROQ_API_KEY`               | If using Groq       | [Groq](https://console.groq.com) API key              |
| `OPENROUTER_API_KEY`         | If using OpenRouter | [OpenRouter](https://openrouter.ai/) API key          |
| `OLLAMA_URL`                 | If using Ollama     | Ollama server URL (default: `http://localhost:11434`) |
| `PHOENIX_API_KEY`            | No                  | Use for AI tracing and token tracking                 |
| `PHOENIX_COLLECTOR_ENDPOINT` | No                  | Use for AI tracing and token tracking                 |

## Usage

```
brief [OPTIONS]
```

| Flag                     | Default       | Description                                     |
| ------------------------ | ------------- | ----------------------------------------------- |
| `--location`, `-l`       | `"USA, Ohio"` | Location as `"Country, Local Area"`             |
| `--focus`, `-f`          | `"AI"`        | Topic(s) to research, comma-separated           |
| `--provider`, `-m`       | `groq`        | LLM provider: `groq`, `ollama`, or `openrouter` |
| `--save` / `--no-save`   | save          | Save output to `./output/`                      |
| `--cache` / `--no-cache` | cache         | Cache Tavily API responses to `./cache_tavily/` |

```bash
# Default: AI news in Ohio using Groq
brief

# Oil and energy briefing for London
brief -l "UK, London" -f "Oil, Energy" -m groq

# Self-hosted model, verbose, no cache
brief -f "Geopolitics" -m ollama -v --no-cache
```

## LLM Providers

| Provider       | Best For                                 | Setup                                |
| -------------- | ---------------------------------------- | ------------------------------------ |
| **Groq**       | Fast inference, free tier available      | Set `GROQ_API_KEY` in `.env`         |
| **Ollama**     | Fully local or cloud (with account)      | Run Ollama locally, set `OLLAMA_URL` |
| **OpenRouter** | Access to many models (some free models) | Set `OPENROUTER_API_KEY` in `.env`   |

## Output Format

Briefings are saved to `./output/`

Each briefing contains:

- **Executive Summary** — 3–5 sentence synthesis across all scope levels
- **Cross-Level Connections** — explicit world → national → local causal chains
- **World / National / Local News** — stories with sentiment, threat level, relevance, and categories
- **What to Watch** — 2–3 developing stories to monitor

## How It Works

The pipeline is built on [LangGraph](https://github.com/langchain-ai/langgraph):

![Graph Layout](images/image.png)

1. **Scope Node** — runs an initial search to define tailored research directives for each scope level
2. **News Gatherer** — fetches stories via Tavily for each scope in parallel
3. **Story Analyzer** — analyzes each story for sentiment, threat level, relevance, and categories
4. **Cross-Level Connector** — identifies causal chains linking world events to national and local impacts
5. **Briefing Generator** — synthesizes everything into the final markdown briefing
