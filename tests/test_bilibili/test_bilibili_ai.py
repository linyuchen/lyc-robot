import asyncio

from src.common.bilibili.api import get_ai_summary

async def test_get_ai_summary():
    cid = "33381680778"
    av_id = ""
    bv_id = "BV1zRsozuEsG"

    summary = await get_ai_summary(cid, av_id, bv_id)
    print(summary)
    assert summary is not None
    assert isinstance(summary, str)
    assert len(summary) > 0

asyncio.run(test_get_ai_summary())
