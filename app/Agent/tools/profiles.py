# tools/profile.py
from langchain.tools import tool
from typing import Optional

# 模拟数据库
user_db = {}

@tool
def get_user_profile(user_id: str) -> dict:
    """查询当前用户的个人资料，包括年龄、身高、体重、伤病信息、器械等。当需要生成计划或给建议时，应先调用此工具获取用户信息。"""
    return user_db.get(user_id, {})

@tool
def update_user_profile(user_id: str, field: str, value: str) -> str:
    """修改用户个人资料的某个字段，如年龄、器械、伤病等。field为字段名，value为新值。"""
    if user_id not in user_db:
        user_db[user_id] = {}
    user_db[user_id][field] = value
    return f"已更新 {field} 为 {value}"