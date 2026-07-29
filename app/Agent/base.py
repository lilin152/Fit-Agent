from dotenv import load_dotenv
from langchain.agents import create_agent
import os
from langchain_deepseek import ChatDeepSeek
from IPython.display import Image,display
from io import BytesIO
from PIL import Image
import  matplotlib.pyplot as plt
import sys
from rich import print as rprint
from tools.profiles import get_user_profile, update_user_profile
from tools.plan import generate_weekly_plan
from tools.records import log_training, get_training_record 

load_dotenv(override=True)
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL')

chat_model = ChatDeepSeek(
    model='deepseek-chat',
    api_key= 'sk-d301e0336d4f4f569c6efbc1286c8e25',
    base_url = 'https://api.deepseek.com'
)

tools = [
    get_user_profile,
    update_user_profile,
    generate_weekly_plan,
    log_training,
    get_training_record,
]

agent = create_agent(
    model = chat_model,
    tools = tools,
    system_prompt="你是一个专业的增肌健身助手。当用户询问训练相关问题时，请先通过 get_user_profile 获取他的资料；当用户要求生成计划时调用 generate_weekly_plan；当用户表示完成训练时调用 log_training 记录。请用友好的语气回复。"
)

# response = agent.invoke({"messages": [{"role": "user", "content": "我昨天练完了胸部，卧推和飞鸟都做了"}]})
# print(response["messages"][-1].content)

response = agent.invoke({"messages": [{"role": "user", "content": "帮我安排一周的计划。"}]})
rprint(response)