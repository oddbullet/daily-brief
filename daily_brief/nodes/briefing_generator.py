from pydantic import BaseModel, Field
from daily_brief.llm.router import model
from daily_brief.llm.state import BriefState

class Briefing(BaseModel):
    content: str

def briefing_generator_node(state: BriefState):
    pass