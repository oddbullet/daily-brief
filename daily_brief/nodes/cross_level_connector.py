from daily_brief.llm.get_model import get_model
from daily_brief.llm.state import BriefState
from daily_brief.nodes.story_analyzer import AnalyzedStory
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import cast
from daily_brief.utils.console import console


class Connection(BaseModel):
    world_story_id: str | None = Field(description="story_id of the world-level story in the chain, or null if not applicable")
    national_story_id: str | None = Field(description="story_id of the national-level story in the chain, or null if not applicable")
    local_story_id: str | None = Field(description="story_id of the local-level story in the chain, or null if not applicable")
    chain_description: str = Field(description="Human-readable chain: '<world event> (world, <category>) → <national impact> (national, <category>) → <local impact> (local, <category>)'")

class ConnectionBatch(BaseModel):
    connections: list[Connection] = Field(description="List of identified cross-level connections. Empty list if none found.")

def cross_level_connector_node(state: BriefState) -> dict:
    console.print("[bold cyan]Finding connections...[/bold cyan]")
    stories: list[AnalyzedStory] = state["analyzed_stories"]

    if not stories:
        return {"connections": []}

    stories_text = "\n".join(
        f"[{s.story_id}] ({s.scope}, {', '.join(s.categories)}) {s.summary}"
        for s in stories
    )

    prompt = f"""You are an analyst identifying how world events ripple down through national policy to local community impact.

    You will be given a list of analyzed news stories at world, national, and local scope.
    Your task is to find meaningful causal chains that follow this pattern:
    world event → national event or response → local impact

    The national level can be anything — a market reaction, a corporate decision, a public response, a political development, or any other national-scale event.
    Each connection must span at least two scope levels and follow a logical cause-and-effect path.
    Only include connections where the link is clear and evidence-based from the story summaries.

    Examples of good connections:
    1. "EU carbon tariff imposed on imports (world, economy) → US steel manufacturers face higher export costs (national, economy, manufacturing) → Dayton auto parts suppliers face margin pressure and potential layoffs (local, manufacturing)"
    2. "Federal Reserve raises interest rates to combat inflation (world, finance) → US mortgage lenders tighten lending standards (national, finance, housing) → Columbus first-time homebuyers priced out of market (local, housing, economy)"

    Stories:
    {stories_text}

    Instructions:
    - Identify all valid world → national → local chains
    - A chain does not need all three levels — world → national or national → local are valid if no third story applies
    - If no meaningful connections exist across any scope levels, return an empty connections list

    Return a JSON object in exactly this structure:
    {{
      "connections": [
        {{
          "world_story_id": "<story_id or null>",
          "national_story_id": "<story_id or null>",
          "local_story_id": "<story_id or null>",
          "chain_description": "<world event> (world, <category>) → <national event> (national, <category>) → <local impact> (local, <category>)"
        }}
      ]
    }}
    """

    model = get_model(state["provider"])
    structured_model = model.with_structured_output(schema=ConnectionBatch, method='json_schema', strict=True)
    result = cast(ConnectionBatch, structured_model.invoke([HumanMessage(content=prompt)]))

    return {"connections": result.connections}


if __name__ == "__main__":
    from daily_brief.nodes.story_analyzer import AnalyzedStory
    from daily_brief.utils.phoenix_trace import setup_tracing

    setup_tracing()

    # stories = [
    #     AnalyzedStory(story_id="world_0", scope="world", summary="Iran launched drone strikes against Gulf oil terminals, disrupting Strait of Hormuz shipping lanes.", sentiment="negative", threat_level="high", relevance_score=6, categories=["geopolitics", "energy", "military"]),
    #     AnalyzedStory(story_id="national_0", scope="national", summary="US Congress debates emergency defense supplemental bill as Pentagon requests $200 billion for Iran operations.", sentiment="negative", threat_level="high", relevance_score=9, categories=["politics", "military", "economy"]),
    #     AnalyzedStory(story_id="local_0", scope="local", summary="Ohio defense contractors including Raytheon and L3Harris report increased procurement orders tied to Iran conflict.", sentiment="positive", threat_level="low", relevance_score=9, categories=["economy", "military", "manufacturing"]),
    # ]

    stories = []

    state: BriefState = {
        "provider": "ollama",
        "location": "USA, Ohio",
        "topic": "Iran",
        "situation": "Iran launched drone strikes against Gulf states.",
        "world_directive": "",
        "national_directive": "",
        "local_directive": "",
        "raw_stories": [],
        "deduped_stories": [],
        "analyzed_stories": stories,
        "connections": [],
        "briefing": "",
        'tavily_cache':True
    }

    result = cross_level_connector_node(state)
    print(result, end='\n\n')
    for c in result["connections"]:
        print(c.chain_description)
