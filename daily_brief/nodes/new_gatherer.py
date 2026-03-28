from pydantic import BaseModel, Field
from typing import Literal
from daily_brief.llm.router import model
from daily_brief.llm.state import BriefState

class RawStory(BaseModel):
    story_id: str = Field(description="Id of the story")
    title: str = Field(description="Title of the news story")
    content: str = Field(description="Content of the news story")
    scope: Literal['world', 'national', 'local'] = Field(description="World scope of the news story")

def make_gatherer_node(scope: str):
    async def news_gatherer_node(state: BriefState) -> dict:
        results = []
        return {"articles": results}
    return news_gatherer_node