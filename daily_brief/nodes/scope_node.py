from langchain_core.messages import HumanMessage
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field
from typing import cast
from daily_brief.llm.get_model import get_model
from daily_brief.llm.state import BriefState
from daily_brief.utils.console import console

import os
import json

class ResearchScope(BaseModel):
    situation: str = Field(
        description="2-4 sentence factual summary of what is happening right now."
    )
    world_directive: str = Field(
        description="A single, keyword-rich search query string focusing on global geopolitical, military, or technological developments. Example: '[Topic] effect on global tech supply chains'"
    )
    national_directive: str = Field(
        description="A single, keyword-rich search query string focusing on national policy, economic, or security effects. Example: 'US stock market and economic reaction to [Topic]'"
    )
    local_directive: str = Field(
        description="A single, keyword-rich search query string focusing on direct local impacts. Example: 'Local gas prices and business disruptions in [Location] due to [Topic]'"
    )

async def scope_node(state: BriefState) -> dict:
    console.print("[bold cyan]Scoping...[/bold cyan]")
    cache = state.get("tavily_cache", True)
    location_slug = state["location"].replace(", ", "_").replace(" ", "_")
    topic_slug = state["topic"].replace(" ", "_")
    cache_path = f"cache_tavily/{topic_slug}_{location_slug}_scope.json"

    if cache and os.path.exists(cache_path):
        with open(cache_path) as f:
            tavily_results = json.load(f)
    else:
        tavily = TavilySearch(
            max_results=10,
            topic="news",
            include_answer=True,
            search_depth="basic",
            time_range="week",
        )
        tavily_results = await tavily.ainvoke({"query": f"What is the latest news/updates on {state['topic']}"})
        if cache:
            os.makedirs("cache_tavily", exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(tavily_results, f, indent=2)

    summary = tavily_results['answer']
    context = "\n".join(
        f"- {r.get('content', '')[:300]}"
        for r in tavily_results['results']
    )

    national = state["location"].split(",")[0].strip()
    local = state["location"]

    prompt = f"""You are a news research director. Based on the following current news about "{state['topic']}",
    produce a research scope to guide three Tavily news search gatherers.

    National context: {national}
    Location context: {local}

    Current news summary:
    {summary}

    Current news context:
    {context}

    Each directive is a of keyword-rich Tavily search query topics — the kind a journalist would type into a search engine.
    Directives must be search-oriented: specific actors, events, and angles to query. Do NOT write investigative instructions.

    Return a JSON object with exactly these four fields:
    {{
        "situation": <summary>,
        "world_directive": <world_directive>,
        "national_directive": <national_directive>,
        "local_directive": <local_directive>
    }}
    """

    model = get_model(state["provider"])
    structured_model = model.with_structured_output(schema=ResearchScope, method="json_schema", strict=True)
    research_scope = cast(ResearchScope, await structured_model.ainvoke([HumanMessage(content=prompt)]))
    
    return {
        "situation": research_scope.situation,
        "world_directive": research_scope.world_directive,
        "national_directive": research_scope.national_directive,
        "local_directive": research_scope.local_directive,
    }

if __name__ == "__main__":
    import asyncio
    from daily_brief.llm.state import BriefState
    from daily_brief.utils.phoenix_trace import setup_tracing

    setup_tracing()
    
    state: BriefState = {
        "provider": "openrouter",
        "location": "USA, Ohio",
        "topic": "Iran",
        "situation": "",
        "world_directive": "",
        "national_directive": "",
        "local_directive": "",
        "raw_stories": [],
        "deduped_stories": [],
        "analyzed_stories": [],
        "connections": [],
        "briefing": "",
        "tavily_cache": True
    }

    result = asyncio.run(scope_node(state))
    print(result)
