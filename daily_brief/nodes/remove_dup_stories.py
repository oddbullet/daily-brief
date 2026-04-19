from daily_brief.llm.state import BriefState
from daily_brief.nodes.new_gatherer import RawStory

_SCOPE_PRIORITY = {"world": 0, "national": 1, "local": 2}

async def remove_duplicate_story_node(state: BriefState):
    raw_stories = state['raw_stories']

    seen: dict[str, RawStory] = {}
    for story in raw_stories:
        url = story["url"]
        if url not in seen or _SCOPE_PRIORITY[story["scope"]] < _SCOPE_PRIORITY[seen[url]["scope"]]:
            seen[url] = story

    return {"deduped_stories": list(seen.values())}


if __name__ == "__main__":
    import asyncio

    stories = [
        {"story_id": "world_0",    "title": "Story A", "content": "...", "url": "https://example.com/a", "scope": "world"},
        {"story_id": "national_0", "title": "Story A", "content": "...", "url": "https://example.com/a", "scope": "national"},
        {"story_id": "national_1", "title": "Story B", "content": "...", "url": "https://example.com/b", "scope": "national"},
        {"story_id": "local_0",    "title": "Story B", "content": "...", "url": "https://example.com/b", "scope": "local"},
        {"story_id": "local_1",    "title": "Story C", "content": "...", "url": "https://example.com/c", "scope": "local"},
    ]

    state: BriefState = {
        "provider": "",
        "location": "",
        "topic": "",
        "tavily_cache": False,
        "situation": "",
        "world_directive": "",
        "national_directive": "",
        "local_directive": "",
        "raw_stories": stories,
        "deduped_stories": [],
        "analyzed_stories": [],
        "connections": [],
        "briefing": "",
    }

    result = asyncio.run(remove_duplicate_story_node(state))
    for s in result["raw_stories"]:
        print(f"  [{s['scope']}] {s['story_id']} — {s['url']}")