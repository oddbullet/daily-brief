from pydantic import BaseModel, Field
from typing import Literal
from daily_brief.llm.router import model
from daily_brief.llm.state import BriefState

class AnalyzedStory(BaseModel):
    story_id: str = Field(description="Id of the story")
    summary: str = Field(description="Two to three sentence summary of the story")
    sentiment_story: Literal['good', 'neutral', 'bad'] = Field(description="Sentiment of the news story")
    threat_level: Literal['none', 'low', 'medium', 'hight'] = Field(description="Threat level based on how urgent action should be taken")
    relevance_score: int = Field(description="Determines how relevant the story is to the user based on their location")
    categories: list[str] = Field(description="Category or categories that the story falls into")

def story_analyzer_node(state: BriefState):
    pass