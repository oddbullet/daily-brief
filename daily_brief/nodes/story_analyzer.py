from daily_brief.llm.get_model import get_model
from daily_brief.nodes.new_gatherer import RawStory
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import Literal, cast
from daily_brief.llm.state import BriefState

class AnalyzedStory(BaseModel):
    story_id: str = Field(description="Id of the story")
    title: str = Field(description="Title of the story")
    scope: Literal['world', 'national', 'local'] = Field(description="Scope level of the story")
    summary: str = Field(description="Two to three sentence summary of the story")
    sentiment: Literal['positive', 'neutral', 'negative'] = Field(description="Overall sentiment of the news story")
    threat_level: Literal['none', 'low', 'medium', 'high'] = Field(description="Threat level based on how urgent action should be taken")
    relevance_score: int = Field(description="1-10 score for how relevant the story is to the user based on their location and situation")
    categories: list[str] = Field(description="Category or categories that the story falls into (e.g. geopolitics, economy, military, health)")

class LLMAnalyzedStory(BaseModel):
    summary: str
    sentiment: Literal['positive', 'neutral', 'negative']
    threat_level: Literal['none', 'low', 'medium', 'high']
    relevance_score: int
    categories: list[str]

def make_analyzer_node(scope: Literal['world', 'national', 'local']):
    async def story_analyzer_node(state: BriefState) -> dict:
        scope_stories: list[RawStory] = [
            s for s in state["raw_stories"] if s.scope == scope
        ]

        if not scope_stories:
            return {"analyzed_stories": []}

        location = state['location']
        situation = state['situation']
        model = get_model(state["provider"])
        structured_model = model.with_structured_output(schema=LLMAnalyzedStory, method='json_schema')

        analyzed = []
        for raw in scope_stories:
            prompt = f"""You are an analyst preparing a {scope}-level news briefing. Analyze the story below and return a JSON object.

            IMPORTANT: You must respond with ONLY a valid JSON object. No explanation, no markdown, no code fences. Raw JSON only.

            User location: {location}
            Current situation: {situation}

            Story:
            Title: {raw.title}
            Content: {raw.content}

            Return this exact JSON structure with no extra fields:
            {{
            "summary": "<2-3 sentences: who, what, and why it matters>",
            "sentiment": "<exactly one of: positive | neutral | negative>",
            "threat_level": "<exactly one of: none | low | medium | high>",
            "relevance_score": <integer 1-10>,
            "categories": ["<category>", ...]
            }}

            Field rules:
            - summary: 2-3 sentences. Be factual and concise.
            - sentiment: judge the real-world impact on citizens, not the reporting tone.
            positive = improvement, agreements, de-escalation
            neutral = procedural or unclear outcome
            negative = harm, instability, escalation
            - threat_level: how urgently this affects the user's safety, finances, or daily life.
            none = no foreseeable personal impact
            low = possible indirect or long-term impact
            medium = tangible impact within weeks or months
            high = immediate impact on safety, jobs, or essential services
            - relevance_score: 1-3 = no local connection, 4-6 = indirect national effects, 7-8 = direct local effects, 9-10 = directly impacts the user's community
            - categories: choose from geopolitics, economy, military, diplomacy, legislation, energy, health, technology, security, environment, finance, labor, education
            """

            llm_result = cast(LLMAnalyzedStory, await structured_model.ainvoke([HumanMessage(content=prompt)]))
            analyzed.append(AnalyzedStory(
                story_id=raw.story_id,
                title=raw.title,
                scope=scope,
                **llm_result.model_dump()
            ))

        return {"analyzed_stories": analyzed}

    return story_analyzer_node

if __name__ == "__main__":
    import asyncio
    import json
    from phoenix.otel import register

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
        "provider": "ollama",
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

    node = make_analyzer_node("national")
    result = asyncio.run(node(state))
    print(result, end='\n')
    for r in result['analyzed_stories']:
        print(r.scope)
        print(r.summary)
        print(r.sentiment)
        print(r.threat_level)
        print(r.relevance_score, end='\n')
