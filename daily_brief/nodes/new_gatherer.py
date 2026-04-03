import json
import os
from langchain_core.messages import HumanMessage
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field
from typing import Literal, cast
from daily_brief.llm.get_model import get_model
from daily_brief.llm.state import BriefState
from daily_brief.utils.console import console

class Query(BaseModel):
    query: str = Field(description="The query to find news with.")

class RawStory(BaseModel):
    story_id: str = Field(description="Id of the story")
    title: str = Field(description="Title of the news story")
    content: str = Field(description="Content of the news story")
    scope: Literal['world', 'national', 'local'] = Field(description="World scope of the news story")

def make_gatherer_node(scope: Literal['world', 'national', 'local']):
    async def news_gatherer_node(state: BriefState) -> dict:
        console.print(f"[bold cyan]Gathering [green]{scope}[/green] stories...[/bold cyan]")
        directive_map = {
            "world": state["world_directive"],
            "national": state["national_directive"],
            "local": state["local_directive"],
        }
        
        directive = directive_map[scope]

        prompt = f"""Generate 1 query question based on the directive:

        Directive: {directive}

        Rules:
        - Use specific nouns and keywords a journalist would search
        - Do NOT use filler phrases like "latest news" or "recent developments"
        - Target a specific angle: actors, events, consequences, policy responses

        Return a JSON object with exactly these four fields:
        {{
            "query": <query>,
        }}
        """

        model = get_model(state['provider'])
        structured_model = model.with_structured_output(schema=Query, method='json_schema', strict=True)
        results = cast(Query, await structured_model.ainvoke([HumanMessage(content=prompt)]))

        cache = state.get("tavily_cache", True)
        location_slug = state["location"].replace(", ", "_").replace(" ", "_")
        topic_slug = state["topic"].replace(" ", "_")
        cache_path = f"cache_tavily/{topic_slug}_{location_slug}_{scope}.json"

        if cache and os.path.exists(cache_path):
            with open(cache_path) as f:
                tavily_results = json.load(f)
        else:
            tavily = TavilySearch(
                max_results=5,
                topic="news",
                include_answer=True,
                include_raw_content=True,
                include_usage=True,
                search_depth="advanced",
                time_range="week"
            )
            tavily_results = await tavily.ainvoke({"query": results.query})
            if cache:
                os.makedirs("cache_tavily", exist_ok=True)
                with open(cache_path, "w") as f:
                    json.dump(tavily_results, f, indent=2)

        raw_stories = [
            RawStory(
                story_id=f"{scope}_{i}",
                title=result['title'],
                content=result["content"],
                scope=scope
            )
            for i, result in enumerate(tavily_results.get("results") or [])
        ]

        return {"raw_stories": raw_stories}

    return news_gatherer_node


if __name__ == "__main__":
    import asyncio
    from daily_brief.llm.state import BriefState
    from daily_brief.utils.phoenix_trace import setup_tracing

    setup_tracing()

    node_world = make_gatherer_node("world")
    node_national = make_gatherer_node("national")
    node_local = make_gatherer_node("local")

    state: BriefState = {
        "provider": "ollama",
        "location": "USA, Ohio",
        "situation":"Iran launched drone strikes against Gulf states. The US has responded with new sanctions and military posturing.",
        "world_directive":"Iran Israel IDF strikes Marine Industries Organization Parchin, Iran President Pezeshkian IRGC chief power struggle, G7 Strait of Hormuz security plan, Saudi UAE intercept Iranian drones, Pakistan regional powers Mideast meeting",
        "national_directive":"US Congress Iran sanctions enforcement military authorization defense spending",
        "local_directive":"Ohio defense contractors Iran conflict procurement jobs manufacturing impact",
        "topic": "Iran",
        "raw_stories": [],
        "analyzed_stories": [],
        "connections": [],
        "briefing": "",
        "tavily_cache": True
    }

    # asyncio.run(node_world(state))
    # asyncio.run(node_national(state))
    asyncio.run(node_local(state))
