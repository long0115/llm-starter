import requests
from infra.settings import settings
from infra.utils.log_util import logger


def search_weather(city: str) -> dict:
    """
    查询指定城市的实时天气信息。当用户询问某个城市的天气、温度、是否下雨等问题时调用此工具。
    
    Args:
        city: 城市名称，如"北京"、"上海"
    Returns:
        天气信息字典
    """
    
    if not settings.WEATHER_API_KEY:
        logger.error("天气API密钥未配置，请在环境变量中设置 WEATHER_API_KEY")
        return None
    try:
        # 获取天气信息
        location_id = _search_location_id(city)
        response = requests.get(
            f"{settings.WEATHER_API_HOST}/v7/weather/now", 
            params={
                "location": location_id,
                "lang": "zh"
            }, 
            headers={
                "X-QW-Api-Key": settings.WEATHER_API_KEY
            }
        )
        
        # 解析 JSON 响应
        data = response.json()
        logger.info(f"天气查询结果: {data}")
        return data
    except Exception as e:
        logger.error(f"获取天气异常: {str(e)}")
        return None
    

def _search_location_id(city_name):
    """城市名 → LocationID"""
    response = requests.get(
        f"{settings.WEATHER_API_HOST}/geo/v2/city/lookup", 
        params={
            "location": city_name,
            "lang": "zh"
        }, 
        headers={
            "X-QW-Api-Key": settings.WEATHER_API_KEY
        }
    )
    data = response.json()
    if data["code"] == "200" and data["location"]:
        return data["location"][0]["id"]
    raise ValueError(f"找不到城市: {city_name}")