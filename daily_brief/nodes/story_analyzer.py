from daily_brief.llm.get_model import get_model
from daily_brief.nodes.new_gatherer import RawStory
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import Literal, cast
from daily_brief.llm.state import BriefState

class AnalyzedStory(BaseModel):
    story_id: str = Field(description="Id of the story")
    summary: str = Field(description="Two to three sentence summary of the story")
    sentiment: Literal['positive', 'neutral', 'negative'] = Field(description="Overall sentiment of the news story")
    threat_level: Literal['none', 'low', 'medium', 'high'] = Field(description="Threat level based on how urgent action should be taken")
    relevance_score: int = Field(description="1-10 score for how relevant the story is to the user based on their location and situation")
    categories: list[str] = Field(description="Category or categories that the story falls into (e.g. geopolitics, economy, military, health)")

class AnalyzedStoryBatch(BaseModel):
    stories: list[AnalyzedStory] = Field(description="List of analyzed stories")

async def make_analyzer_node(scope: Literal['world', 'national', 'local']):
    async def story_analyzer_node(state: BriefState) -> dict:
        scope_stories: list[RawStory] = [
            s for s in state["raw_stories"] if s.scope == scope
        ]

        if not scope_stories:
            return {"analyzed_stories": []}

        stories = state['raw_stories']
        location = state['location']
        situation = state['situation']

        stories_text = "\n\n".join(
            f"[{s.story_id}] {s.title}\n{s.content}"
            for s in stories
        )

        prompt = f"""You are an analyst preparing a {scope}-level news briefing covering all areas of news.

        User location: {location}
        Current situation: {situation}

        Analyze each of the following {scope} news stories. For each story provide:

        - summary: 2-3 sentences capturing who, what, and why it matters.

        - sentiment: the real-world impact of the story on citizens and society.
          - positive: improvement, gains, agreements, breakthroughs, de-escalation
          - neutral: informational or procedural with no clear positive or negative outcome yet
          - negative: harm, instability, losses, breakdown, or escalation
          Do NOT use neutral simply because the reporting tone is objective — judge the underlying events.

        - threat_level: how urgently this story could affect the user's safety, finances, community, or daily life.
          - none: no foreseeable personal or local impact
          - low: possible indirect or long-term impact (policy shifts, distant events, early-stage developments)
          - medium: tangible impact likely within weeks or months (market moves, supply disruptions, regulatory changes)
          - high: immediate or near-term impact on safety, jobs, cost of living, or essential services
          Apply consistently — stories with similar stakes should share the same threat level regardless of topic.

        - relevance_score: 1-10, how directly this story affects the user given their location and situation.
          - 1-3: broad global or national story with no plausible local connection
          - 4-6: national story with indirect local effects (industry trends, policy downstream effects)
          - 7-8: story with direct local effects (regional employers, state policy, nearby infrastructure)
          - 9-10: story directly involves or immediately impacts the user's community or region

        - categories: list of applicable categories (e.g. geopolitics, economy, military, diplomacy, legislation, energy, health, technology, security, environment, finance, labor, education)

        Stories:
        {stories_text}

        Return a JSON object with a "stories" array containing one object per story, preserving the story_id.
        """

        model = get_model(state["provider"])
        structured_model = model.with_structured_output(schema=AnalyzedStoryBatch, method='json_schema')
        result = cast(AnalyzedStoryBatch, await structured_model.ainvoke([HumanMessage(content=prompt)]))

        return {"analyzed_stories": result.stories}

    return story_analyzer_node


if __name__ == "__main__":
    import asyncio
    import json
    from phoenix.otel import register
    from daily_brief.nodes.new_gatherer import RawStory

    tracer_provider = register(
        project_name="daily-brief",
        protocol="http/protobuf",
        auto_instrument=True
    )

    with open('data/tavily2_ollama_USA_Iran.json') as f:
        data = json.load(f)

    raw_stories = []
    i = 0
    for result in data['results']:
        raw_stories.append(RawStory(story_id=f"story_{i}", title=result['title'], content=result['content'], scope='national'))
        i += 1

    state: BriefState = {
        "provider": "groq",
        "location": "USA, Ohio",
        "topic": "Iran",
        "situation": data['answer'],
        "world_directive": "",
        "national_directive": "",
        "local_directive": "",
        "raw_stories": raw_stories,
        "analyzed_stories": [],
        "connections": [],
        "briefing": "",
    }

    node = asyncio.run(make_analyzer_node("national"))
    result = asyncio.run(node(state))
    print(result, end='\n')
    for r in result['analyzed_stories']:
        print(r.summary)
        print(r.sentiment)
        print(r.threat_level)
        print(r.relevance_score, end='\n')
