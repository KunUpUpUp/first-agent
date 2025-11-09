import os
from datetime import datetime

from dotenv import load_dotenv
import requests
import json
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
from langchain_community.chat_models import ChatTongyi
from langchain.agents import create_agent

# 加载环境变量， 如果相同变量名称， 则覆盖
load_dotenv(override=True)

# 内置搜索工具
search_tool = TavilySearchResults(max_results=5, topic="general")


class WeatherQuery(BaseModel):
    loc: str = Field(description="城市名称")

@tool(args_schema=WeatherQuery)
def get_weather(loc):
    """
    查询即时天气函数
    :param loc: 必要参数，字符串类型，用于表示查询天气的具体城市名称，\
    注意，中国的城市需要用对应城市的英文名称代替，例如如果需要查询杭州市天气，则loc参数需要输入"Hangzhou"
    :return OpenWeather API查询即时天气的结果，具体URL请求地址为:https://api.openweathermap.org/data/2.5/weather\
    返回结果对象类型为解析之后的JSON格式对象，并用字符串形式进行表示，其中包含了全部重要的天气信息
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": loc,
        "APPID": os.getenv('OPENWEATHER_API_KEY'),
        "units": "metric",
        "lang": "zh_cn"
    }

    response = requests.get(url, params=params)

    data = response.json()
    return json.dumps(data)

@tool
def write_file(content: str) -> str:
    """
    将指定内容写入本地文件
    :param content: 必要参数，字符串类型，用于表示需要写入文档的具体内容
    :return 写入结果提示信息
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"/data/pythonProjects/Chatbot/output/output_{timestamp}.md"

        # 确保目录存在
        output_dir = "/data/pythonProjects/Chatbot/output"
        os.makedirs(output_dir, exist_ok=True)  # 关键改进：自动创建目录

        # 写入文件
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        abs_path = os.path.abspath(filename)
        return f"已成功写入本地文件：{abs_path}"

    except Exception as e:
        return f"文件写入失败：{str(e)}"

# 内置工具列表
tools = [search_tool, get_weather, write_file]

# 创建模型
model = ChatTongyi(model="qwen-flash")

prompt = """
你是一名乐于助人的智能助手，擅长根据用户的问题选择合适的工具来查询信息并回答。

当用户的问题涉及**天气信息**时，你应该优先调用`get_weather`工具来查询用户指定城市的天气信息，并总结查询结果。

当用户的问题涉及**新闻、事件、实时动态**时，你应该优先调用`search_tool`工具来检索最新的相关信息，并总结查询结果。

如果问题既包含天气又包含新闻、事件、实时动态，你应该先调用`search_tool`工具查询天气，再使用`search_tool查询新闻、事件、实时动态`，最后将结果合并后返回给用户。

当用户提及**写入文件**类操作时，你应该调用`write_file`工具来将用户提问的内容总结并写入本地文件，写入格式为markdown。

所有回答应使用**中文**进行回答，并且使用**中文**进行总结，条理清晰，符合事实。
"""

# 创建agent
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=prompt
)