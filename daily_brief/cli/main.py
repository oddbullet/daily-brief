from daily_brief.llm.router import init_model
import click

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--location', '-l', default="USA, Ohio", help="Set national and local location")
@click.option('--provider', '-m', default="groq", type=click.Choice(["groq", 'ollama']), help="LLM Provider")
@click.option('--focus', '-f', default='AI', help="Topics to focus on. Each topic is separated by a comma. e.g. AI, Energy, Food")
@click.option('--save/--no-save', default=True, help="Save results to file ./save")
@click.option('--verbose', '-v', is_flag=True, help="Show progess")
def dailybrief(ctx, location, provider, focus, save, verbose):
    init_model(provider)


if __name__ == "__main__":
    dailybrief()
