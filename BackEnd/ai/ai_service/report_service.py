from ai.ai_service.ai_core.memory import get_chat_history
from ai.ai_service.ai_core.chain import summary_chain, analysis_chain


async def write_daily_report(child_id: str):

    history_obj = get_chat_history(child_id)
    messages = await history_obj.aget_messages()
    summary_list = await summary_chain.ainvoke({"history": messages})
    analysis_report = await analysis_chain.ainvoke({"history": messages})

    return {"summary": summary_list, "analysis": analysis_report}
