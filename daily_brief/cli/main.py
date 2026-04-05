import asyncio
import datetime as dt
import os
import click
from daily_brief.llm.build_graph import build_graph
from daily_brief.llm.state import BriefState
from daily_brief.utils.sanitize_output import sanitize_output
from daily_brief.utils.phoenix_trace import setup_tracing
from daily_brief.utils.load_config import _load_config
from daily_brief.utils.console import console


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--location', '-l', help="Set national and local location. Format: Country, Local")
@click.option('--provider', '-p', type=click.Choice(["groq", 'ollama', 'openrouter']), help="LLM Provider")
@click.option('--focus', '-f', help="Topics to focus on. Each topic is separated by a comma. e.g. AI, Energy, Food")
@click.option('--save/--no-save', default=True, help="Save results to file ./save")
@click.option('--cache/--no-cache', default=True, help="Cache Tavily API calls to cache_tavily/")
@click.option('--verbose', '-v', is_flag=True, help="Show progess")
def dailybrief(ctx, location: str, provider: str, focus: str, save: bool, cache: bool, verbose):
    if ctx.invoked_subcommand:
        return

    setup_tracing()

    config = _load_config()

    provider = provider or config['defaults']['provider']
    location = location or config['defaults']['location']
    focus = focus or config['defaults']['topic']

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

    console.print(f"[bold cyan]Generating briefing on {focus} for {location}...[/bold cyan]")
    
    async def run():
        graph = build_graph()
        result = await graph.ainvoke(initial_state)
        brief_result = result['briefing']

        if save:
            date = dt.datetime.now()

            safe_location = sanitize_output(location)
            safe_focus = sanitize_output(focus)

            filename = f"save/{provider}_{safe_location}_{safe_focus}_{date.year}_{date.month}_{date.day}.md"
            os.makedirs("save", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(brief_result)

        print(brief_result)
    
    asyncio.run(run())

@dailybrief.command(help="Edit the configuration file.")
def config():
    click.edit(filename="daily_brief/config.yaml")

if __name__ == "__main__":
    dailybrief()
