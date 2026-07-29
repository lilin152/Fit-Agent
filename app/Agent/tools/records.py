# tools/record.py
from langchain.tools import tool

training_records = {}  # user_id -> list of records

@tool
def log_training(user_id: str, date: str, exercises_completed: list) -> str:
    """
    记录用户某一天的训练完成情况。
    exercises_completed 是一个列表，包含已完成动作的名称。
    未列出的动作自动标记为未完成。
    """
    if user_id not in training_records:
        training_records[user_id] = []
    # 读取当天计划，标记完成/未完成
    # ... 逻辑
    training_records[user_id].append({
        "date": date,
        "completed": exercises_completed,
        "status": "saved"
    })
    return f"已记录 {date} 的训练完成情况。"

@tool
def get_training_record(user_id: str, week_start: str = None) -> dict:
    """查看用户某周的训练记录，week_start格式为YYYY-MM-DD。"""
    # 按周聚合返回
    return {"records": training_records.get(user_id, [])}