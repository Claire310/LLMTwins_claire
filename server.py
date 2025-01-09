from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from models import  prompt, weather
import requests
import os
import openai

# Load environment variables from .env file
load_dotenv()
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/health")
async def health():
    return {"result": "Healthy Server!"}

def self_introduction():
    return "我的名字叫做小明，我是一個 AI 聊天機器人，我可以幫助你進行自我介紹。"

self_intro_agent = Agent(
   name="Self-introduction Agent",
   role="自我介紹",
   tools=[self_introduction],
   show_tool_calls=True
)

def analyse_project():
    return "我是專案分析 Agent，我可以幫助你分析專案。"

analysis_project_agent = Agent(
   name="Project analysis Agent",
   role= "專案分析",
   tools=[analyse_project],
   show_tool_calls=True
)

def get_weather_and_suggestions(city: str):
    """
    查詢天氣並依據天氣提供旅遊建議，利用大語言模型生成建議。
    """
    api_key = os.getenv("WEATHER_API_KEY")
    weather_api_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=zh_tw"
    try:
        response = requests.get(weather_api_url)
        weather_data = response.json()

        if response.status_code == 200:
            # 解析天氣資訊
            weather = weather_data['weather'][0]['description']
            temperature = weather_data['main']['temp']
            # 根據天氣情況生成建議，使用語言模型來動態生成
            if "rain" in weather or "storm" in weather or "snow" in weather:
                suggestion = f"由於天氣是 {weather}，氣溫為 {temperature}°C，我建議您參觀室內景點。請探索當地的博物館、藝廊、商場等地方！"
            elif "clear" in weather:
                suggestion = f"天氣晴朗，氣溫為 {temperature}°C，非常適合戶外活動！請考慮去參觀城市公園、登山步道或海灘等地方。"
            elif "cloud" in weather or "overcast" in weather:
                suggestion = f"天氣多雲，氣溫為 {temperature}°C。這樣的天氣非常適合參觀城市的歷史街區或市場，或者在戶外走一走。"
            else:
                suggestion = f"當地天氣是 {weather}，氣溫為 {temperature}°C。根據這個天氣，我建議您可以選擇適合的活動，無論是戶外還是室內！"
            # 用語言模型生成更多具體的景點建議
            suggestion += f"如果您在 {city}，這裡有一些推薦的景點：\n" \
                           f"{generate_suggested_attractions(city, weather)}"

            return suggestion
        else:
            return f"無法查詢 {city} 的天氣，請確認城市名稱是否正確。"

    except Exception as e:
        return f"查詢天氣時發生錯誤：{str(e)}"

def generate_suggested_attractions(city: str, weather: str):
    """
    用大語言模型生成動態的旅遊景點建議。
    """
    prompt = f"請根據以下天氣的好壞和城市名稱，推薦三個戶外或室內的景點：\n" \
             f"城市: {city}\n" \
             f"天氣: {weather}\n" \
             f"使用條列的方式呈現"

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

weather_agent = Agent(
    name="Weather and Travel Suggestion Agent",
    role="查詢天氣與旅遊建議",
    tools=[get_weather_and_suggestions],
    show_tool_calls=True
)

# Create agent team
agent_team = Agent(
    model=OpenAIChat(
        id = "gpt-4o",
        temperature = 1,
        timeout = 30
    ),
   name="Agent Team",
   team=[self_intro_agent, analysis_project_agent, weather_agent],
   add_history_to_messages=True,
   num_history_responses=3,
   show_tool_calls=False,
   tool_call_limit=1
)

@app.post("/prompt")
async def prompt(prompt: prompt):
    response = agent_team.run(f"{prompt.message}", stream=False)
    # 尋找 assistant role 的最後一條訊息
    assistant_content = None
    for message in response.messages:
        if message.role == "assistant" and message.content:
            assistant_content = message.content

    return {"result": True, "message": assistant_content}

@app.post("/weather")
async def weather(weather: weather):
    response = weather_agent.run(weather.city, stream=False)
    return {"result": True, "message": response}