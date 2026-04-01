import operator
from typing_extensions import TypedDict, Annotated

class BriefState(TypedDict):
    provider: str
    location: str
    topic: str
    tavily_cache: bool

    situation: str
    world_directive: str
    national_directive: str
    local_directive: str

    raw_stories: Annotated[list, operator.add]
    analyzed_stories: Annotated[list, operator.add]
    connections: Annotated[list, operator.add]

    briefing: str
