from langchain.tools import tool
from infra.external.weather_client import search_weather


@tool(return_direct=True)
def get_weather(city: str) -> str:
    """
    查询指定城市的实时天气信息。当用户询问某个城市的天气、温度、是否下雨等问题时调用此工具。
    
    Args:
        city: 城市名称，如"北京"、"上海"
    Returns:
        天气信息字符串
    """

    weather_data = search_weather(city)
    if not weather_data:
        return "未查询到天气信息"

    if weather_data["code"] == "200":
        now = weather_data["now"]
        return (
            f"{city}当前天气：{now['text']}，"
            f"温度{now['temp']}°C，"
            f"体感温度{now['feelsLike']}°C，"
            f"湿度{now['humidity']}%，"
            f"风向{now['windDir']}"
        )
    else:
        return "未查询到天气信息"
    