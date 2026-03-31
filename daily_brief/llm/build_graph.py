from daily_brief.nodes.scope_node import scope_node
from daily_brief.nodes.new_gatherer import make_gatherer_node
from daily_brief.nodes.briefing_generator import briefing_generator_node
from daily_brief.nodes.cross_level_connector import cross_level_connector_node
from daily_brief.nodes.story_analyzer import make_analyzer_node
from daily_brief.llm.state import BriefState
from langgraph.graph import START, END, StateGraph
from typing import Literal


def build_graph(scope: list[Literal['world', 'national', 'local']]):
    graph = StateGraph(BriefState)

    graph.add_node("scope_node", scope_node)

    for location in scope:
        graph.add_node(f"new_gatherer_node_{location}", make_gatherer_node(location))
        graph.add_node(f"story_analyzer_node_{location}", make_analyzer_node(location))

    graph.add_node(cross_level_connector_node)
    graph.add_node(briefing_generator_node)

    graph.add_edge(START, "scope_node")

    for location in scope:
        graph.add_edge("scope_node", f"new_gatherer_node_{location}")
        graph.add_edge(f"new_gatherer_node_{location}", f"story_analyzer_node_{location}")
        graph.add_edge(f"story_analyzer_node_{location}", "cross_level_connector_node")

    graph.add_edge("cross_level_connector_node", "briefing_generator_node")
    graph.add_edge("briefing_generator_node", END)

    return graph.compile()

if __name__ == "__main__":
    import asyncio
    from phoenix.otel import register

    tracer_provider = register(
        project_name="daily-brief",
        protocol="http/protobuf",
        auto_instrument=True
    )

    initial_state: BriefState = {
        "provider": "ollama",
        "location": "USA, Ohio",
        "topic": "AI development",
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
        graph = build_graph(["world", "national", "local"])
        result = await graph.ainvoke(initial_state)

        output_path = "data/result_AI_development.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["briefing"])

        print(f"Briefing saved to {output_path}")
        print(result["briefing"])

    asyncio.run(run())
