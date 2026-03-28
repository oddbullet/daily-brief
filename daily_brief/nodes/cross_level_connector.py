from pydantic import BaseModel, Field
from typing import Literal
from daily_brief.llm.router import model
from daily_brief.llm.state import BriefState

class Connection(BaseModel):
    story_ids: list[str]
    chain_description: str
    impact_score: int
    geographic_flow: str

def cross_level_connector_node(state: BriefState):
    pass