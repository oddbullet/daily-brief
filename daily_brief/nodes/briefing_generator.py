from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage
from daily_brief.llm.get_model import get_model
from daily_brief.llm.state import BriefState
from daily_brief.utils.console import console

def briefing_generator_node(state: BriefState):
    console.print("[bold cyan]Creating briefing...[/bold cyan]")
    analyzed_stories = state['analyzed_stories']
    connections = state['connections']
    location = state['location']
    situation = state['situation']

    def stories_by_scope(scope):
        return [s for s in analyzed_stories if s.scope == scope]

    def sentiment_emoji(sentiment):
        return {'positive': '🟢', 'neutral': '🟡', 'negative': '🔴'}.get(sentiment, '🟡')

    def format_stories(stories):
        if not stories:
            return "_No stories at this level._"
        lines = []
        for s in sorted(stories, key=lambda x: -x.relevance_score):
            emoji = sentiment_emoji(s.sentiment)
            threat = s.threat_level.upper()
            cats = ", ".join(s.categories)
            lines.append(
                f"### {s.title}\n"
                f"{emoji} **Sentiment:** {s.sentiment.capitalize()} | "
                f"**Threat:** `{threat}` | "
                f"**Relevance:** {s.relevance_score}/10\n\n"
                f"{s.summary}\n\n"
                f"_Categories: {cats}_"
            )
        return "\n\n---\n\n".join(lines)

    def format_connections(connections):
        if not connections:
            return "_No cross-level connections identified._"
        return "\n\n".join(f"- {c.chain_description}" for c in connections)

    world_block = format_stories(stories_by_scope('world'))
    national_block = format_stories(stories_by_scope('national'))
    local_block = format_stories(stories_by_scope('local'))
    connections_block = format_connections(connections)

    all_stories_text = "\n\n".join(
        f"[{s.story_id}] ({s.scope}) {s.summary}"
        for s in sorted(analyzed_stories, key=lambda x: -x.relevance_score)
    )

    prompt = f"""You are a senior intelligence analyst producing a daily news briefing for a user in {location}.

    User situation context: {situation}

    Your task is to write a structured markdown briefing using the pre-analyzed stories and cross-level connections provided below.

    ---

    OUTPUT FORMAT (strict markdown, use exactly these section headers):

    # Daily Brief

    ## Executive Summary
    Write 3-5 sentences giving a high-level overview of the day's most important developments. Synthesize across all scope levels. Focus on what matters most to this specific user given their location and situation.

    ## Cross-Level Connections
    {connections_block}

    ## World News
    {world_block}

    ## National News
    {national_block}

    ## Local News
    {local_block}

    ## What to Watch
    Identify 2-3 developing stories from any scope level that the user should monitor over the coming days. For each, write one sentence on what to watch for and why it matters. Format as a numbered list.

    ---

    INSTRUCTIONS:
    - Do not invent stories or facts not present in the analyzed data above.
    - The Executive Summary must be written by you — synthesize, don't copy summaries verbatim.
    - Story cards (World/National/Local sections) must be reproduced exactly as formatted above — do not rewrite or reorder the fields.
    - Cross-Level Connections must be reproduced exactly as provided above.
    - Output valid GitHub-flavored markdown only. No preamble, no closing remarks.

    All analyzed stories for your reference:
    {all_stories_text}
    """

    model = get_model(state['provider'])
    result: AIMessage = model.invoke([HumanMessage(content=prompt)])

    return {'briefing': result.content}

if __name__ == "__main__":
    import asyncio
    import json
    from typing import cast, Literal
    from daily_brief.nodes.new_gatherer import RawStory
    from daily_brief.nodes.story_analyzer import make_analyzer_node
    from daily_brief.nodes.cross_level_connector import cross_level_connector_node
    from daily_brief.utils.phoenix_trace import setup_tracing

    setup_tracing()

    scope_files = [
        ('data/tavily_World_Iran.json', 'world'),
        ('data/tavily_USA_Iran.json', 'national'),
        ('data/tavily_Ohio_Iran.json', 'local'),
    ]

    raw_stories = []
    situation_parts = []
    for path, scope in scope_files:
        with open(path) as f:
            data = json.load(f)
        situation_parts.append(data['answer'])
        for i, result in enumerate(data['results']):
            raw_stories.append(RawStory(
                story_id=f"{scope}_{i}",
                title=result['title'],
                url=result['url'],
                content=result['content'][:1000],
                scope=cast(Literal['world', 'national', 'local'], scope),
            ))

    situation = " ".join(situation_parts)

    state: BriefState = {
        "provider": "groq",
        "location": "USA, Ohio",
        "topic": "Iran",
        "situation": situation,
        "world_directive": "",
        "national_directive": "",
        "local_directive": "",
        "raw_stories": raw_stories,
        "deduped_stories": [],
        "analyzed_stories": [],
        "connections": [],
        "briefing": "",
        'tavily_cache': True,
    }

    RATE_LIMIT_WAIT = 90

    async def run():
        for scope in ('world', 'national', 'local'):
            print(f"Waiting {RATE_LIMIT_WAIT}s before {scope} analyzer...")
            await asyncio.sleep(RATE_LIMIT_WAIT)

            node = make_analyzer_node(scope)
            result = await node(state)
            state['analyzed_stories'] = state['analyzed_stories'] + result['analyzed_stories']

        print(f"Waiting {RATE_LIMIT_WAIT}s before cross-level connector...")
        await asyncio.sleep(RATE_LIMIT_WAIT)

        conn_result = cross_level_connector_node(state)
        state['connections'] = conn_result['connections']

        print(f"Waiting {RATE_LIMIT_WAIT}s before briefing generator...")
        await asyncio.sleep(RATE_LIMIT_WAIT)
        
        brief_result = briefing_generator_node(state)

        with open('data/result_3_groq.md', 'w', encoding='utf-8') as file:
            file.write(cast(str, brief_result['briefing']))

        print(brief_result['briefing'])

    asyncio.run(run())