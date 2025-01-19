from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from models import  prompt
from utils.format import format_html
from utils.module_handler import load_agents_from_directory
import os

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



loaded_agent_teams = {}

@app.post("/prompt")
async def handle_prompt(prompt: prompt):
    try:
        role = prompt.role

        if role not in loaded_agent_teams:
            role_dir = f"agents/{role}"
            if not os.path.exists(role_dir):
                raise HTTPException(status_code = 404, detail = f"找不到角色{role}的目錄")

            agent = load_agents_from_directory(role_dir)
            if not agent:
                raise HTTPException(status_code = 404, detail = f"在{role}目錄中找不到可用的agent")

            loaded_agent_teams[role] = agent

        agent_team = loaded_agent_teams[role]
        response = agent_team.run(
            f"""
            {prompt.message}
            重要指示:
            1.立即執行實際的分析或查詢操作
            2.返回包含具體數據的完整結果
            3.使用HTML格式，並將回答包含在<div>標籤中
            4.確保使用中文回答
            5.不要只是描述任務 - 必須執行實際操作
            """,
            stream = False
        )

        # 處理回應
        assistant_content = None
        for message in response.messages:
            if message.role == "assistant" and message.content:
                assistant_content = message.content
                break
        
        if assistant_content is None:
            raise HTTPException(status_code = 500, detail = f"無法獲取助理回應")

        formatted_content = format_html(assistant_content.strip())
        return {"result": True, "message": assistant_content}

    except Exception as e:
        return{
            "result": False,
            "message":f"<div>處理過程發生錯誤:{e}</div>"
        }

