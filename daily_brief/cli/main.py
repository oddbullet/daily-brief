import click
import asyncio
import datetime as dt
from daily_brief.llm.build_graph import build_graph
from daily_brief.llm.state import BriefState
from phoenix.otel import register

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--location', '-l', default="USA, Ohio", help="Set national and local location. Format Country, Local")
@click.option('--provider', '-m', default="groq", type=click.Choice(["groq", 'ollama', 'openrouter']), help="LLM Provider")
@click.option('--focus', '-f', default='AI', help="Topics to focus on. Each topic is separated by a comma. e.g. AI, Energy, Food")
@click.option('--save/--no-save', default=True, help="Save results to file ./save")
@click.option('--cache/--no-cache', default=True, help="Cache Tavily API calls to cache_tavily/")
@click.option('--verbose', '-v', is_flag=True, help="Show progess")
def dailybrief(ctx, location, provider, focus, save, cache, verbose):
    
    tracer_provider = register(
        project_name="daily-brief",
        protocol="http/protobuf",
        auto_instrument=True
    )

    initial_state: BriefState = {
        "provider": provider,
        "location": location,
        "topic": focus,
        "tavily_cache": cache,
        "situation": "",
        "world_directive": "",
        "national_directive": "",
        "local_directive": "",
        "raw_stories": [],
        "analyzed_stories": [],
        "connections": [],
        "briefing": "",
    }
    
    async def run():
        graph = build_graph()
        result = await graph.ainvoke(initial_state)
        brief_result = result['briefing']

        if save:
            date = dt.datetime.now()
            filename = f"output/{provider}_{location}_{focus}_{date.year}_{date.day}.md"
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(brief_result)

        print(brief_result)
    
    asyncio.run(run())

if __name__ == "__main__":
    dailybrief()
