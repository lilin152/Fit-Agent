# tools/plan.py
from langchain.tools import tool
from datetime import date, timedelta

@tool
def generate_weekly_plan(user_id: str, start_date: str = None) -> dict:
    """
    根据用户资料生成一周的训练计划。
    如果用户没有指定起始日期，默认从下一个周一开始。
    计划内容基于用户的训练天数、器械、伤病等信息自动生成。
    返回结构化的计划字典。
    """
    # 这里会先调用 get_user_profile 获取用户数据
    # 根据用户训练天数、伤病排除动作等生成计划
    # 返回计划数据（例如列表），后续可以格式化为表格展示
    profile = get_user_profile.invoke({"user_id": user_id})
    # ... 生成逻辑
    return {
        "week": "2026-07-28 至 2026-08-03",
        "days": [
            {
                "date": "2026-07-28",
                "muscle": "胸部",
                "exercises": [
                    {"name": "杠铃卧推", "sets": 3, "reps": 10, "rest": 90, "weight": "80% 极限"}
                ]
            }
        ]
    }