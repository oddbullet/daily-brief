from daily_brief.nodes.scope_node import scope_node
from daily_brief.nodes.new_gatherer import make_gatherer_node
from daily_brief.nodes.briefing_generator import briefing_generator_node
from daily_brief.nodes.cross_level_connector import cross_level_connector_node
from daily_brief.nodes.story_analyzer import story_analyzer_node
from daily_brief.llm.state import BriefState
from langgraph.graph import START, END, StateGraph


def build_graph(scope: list[str]):
    graph = StateGraph(BriefState)

    graph.add_node("scope_node", scope_node)

    for location in scope:
        graph.add_node(f"new_gatherer_node_{location}", make_gatherer_node(location))

    graph.add_node("story_analyzer_node", story_analyzer_node)
    graph.add_node(cross_level_connector_node)
    graph.add_node(briefing_generator_node)

    graph.add_edge(START, "scope_node")

    for location in scope:
        graph.add_edge("scope_node", f"new_gatherer_node_{location}")
        graph.add_edge(f"new_gatherer_node_{location}", "story_analyzer_node")

    graph.add_edge("story_analyzer_node", "cross_level_connector_node")
    graph.add_edge("cross_level_connector_node", "briefing_generator_node")
    graph.add_edge("briefing_generator_node", END)

    return graph.compile()

if __name__ == "__main__":
    graph = build_graph(["World", "USA", "Ohio"])
    print(graph.get_graph().draw_mermaid())
