import json
import os
from langchain_core.messages import HumanMessage
from langchain_tavily import TavilySearch
from pydantic import BaseModel, Field
from typing import Literal, cast
from daily_brief.llm.get_model import get_model
from daily_brief.llm.state import BriefState

class Query(BaseModel):
    query: str = Field(description="The query to find news with.")

class RawStory(BaseModel):
    story_id: str = Field(description="Id of the story")
    title: str = Field(description="Title of the news story")
    content: str = Field(description="Content of the news story")
    scope: Literal['world', 'national', 'local'] = Field(description="World scope of the news story")

def make_gatherer_node(scope: Literal['world', 'national', 'local'], cache: bool = False):
    async def news_gatherer_node(state: BriefState) -> dict:
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
        structured_model = model.with_structured_output(schema=Query, method='json_schema')
        results = cast(Query, await structured_model.ainvoke([HumanMessage(content=prompt)]))

        tavily = TavilySearch(
            max_results=10,
            topic="news",
            include_answer=True,
            include_raw_content=True,
            include_usage=True,
            search_depth="advanced",
            time_range="week"
        )

        tavily_results = await tavily.ainvoke({"query": results.query})

        if cache:
            os.makedirs("data", exist_ok=True)
            filename = f"data/tavily2_ollama_{scope}_{state['topic']}.json".replace(" ", "_")
            with open(filename, "w") as f:
                json.dump(tavily_results, f, indent=2)

        raw_stories = [
            RawStory(
                story_id=f"{scope}_{i}",
                title=result['title'],
                content=result["content"],
                scope=scope
            )
            for i, result in enumerate(tavily_results["results"])
        ]

        return {"raw_stories": raw_stories}

    return news_gatherer_node


if __name__ == "__main__":
    import asyncio
    from daily_brief.llm.state import BriefState
    from phoenix.otel import register

    tracer_provider = register(
        project_name="daily-brief",
        protocol="http/protobuf",
        auto_instrument=True
    )

    node_world = make_gatherer_node("world", True)
    node_national = make_gatherer_node("national", True)
    node_local = make_gatherer_node("local", True)

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
    }

    # asyncio.run(node_world(state))
    # asyncio.run(node_national(state))
    asyncio.run(node_local(state))
