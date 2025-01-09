# LLMTwins
https://docs.phidata.com/agents/introduction

## Environment

#### Environment Variables:
- OPENAI_API_KEY: OpenAI API Key

## Installation
```bash=
python3.10 -m venv env
source env/bin/active
pip3 install -r requirements.txt
```

## Run
```bash=
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

#新增功能
新增搜尋城市天氣及旅遊推薦功能，使用者輸入城市後，AI搜尋回覆天氣狀況並藉此推薦三個旅遊景點
