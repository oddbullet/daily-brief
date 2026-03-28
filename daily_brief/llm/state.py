from langgraph.graph import add_messages
from langchain_core.messages import AnyMessage
from typing_extensions import TypedDict, Annotated


class BriefState(TypedDict):
    location: str
    topic: str

    raw_stories: Annotated[list[AnyMessage], add_messages]
    analyzed_stories: Annotated[list[AnyMessage], add_messages]
    connections: Annotated[list[AnyMessage], add_messages]

    briefing: str
