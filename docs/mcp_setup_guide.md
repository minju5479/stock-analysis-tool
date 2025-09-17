# MCP 서버 연결 가이드

## 1. Claude Desktop

### 설정 방법:
1. Claude Desktop을 설치
2. 설정에서 "Model Context Protocol" 활성화
3. `claude_desktop_config.json` 파일을 Claude Desktop 설정 디렉토리에 복사
4. Claude Desktop 재시작

### 사용 예시:
```
Claude, please analyze AAPL stock using the stock analysis tool.
```

## 2. Ollama + MCP

### 설치:
```bash
# Ollama 설치
curl -fsSL https://ollama.ai/install.sh | sh

# MCP 클라이언트 설치
pip install mcp-client
```

### 설정 파일 (`ollama_mcp_config.json`):
```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "python",
      "args": ["stock_analysis_mcp.py"],
      "env": {}
    }
  },
  "ollama": {
    "model": "llama3.2",
    "baseUrl": "http://localhost:11434"
  }
}
```

## 3. OpenAI API + MCP

### 설정 파일 (`openai_mcp_config.json`):
```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "python",
      "args": ["stock_analysis_mcp.py"],
      "env": {}
    }
  },
  "openai": {
    "apiKey": "your-openai-api-key",
    "model": "gpt-4o"
  }
}
```

## 4. LocalAI + MCP

### 설정 파일 (`localai_mcp_config.json`):
```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "python",
      "args": ["stock_analysis_mcp.py"],
      "env": {}
    }
  },
  "localai": {
    "baseUrl": "http://localhost:8080",
    "model": "llama3.2"
  }
}
```

## 5. 커스텀 MCP 클라이언트

### Python 예시:
```python
import asyncio
import json
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

async def main():
    async with stdio_client("python", ["stock_analysis_mcp.py"]) as (read, write):
        async with ClientSession(read, write) as session:
            # 도구 목록 가져오기
            tools = await session.list_tools()
            print("Available tools:", tools)
            
            # 주식 분석 실행
            result = await session.call_tool("analyze_stock", {
                "ticker": "AAPL",
                "period": "1y"
            })
            print("Analysis result:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

## 6. 웹 인터페이스 (Streamlit)

### `web_interface.py`:
```python
import streamlit as st
import asyncio
from stock_analyzer import StockAnalyzer

async def analyze_stock_async(ticker, period):
    analyzer = StockAnalyzer()
    return await analyzer.analyze_stock(ticker, period)

def main():
    st.title("주식 분석 도구")
    
    ticker = st.text_input("주식 티커 입력:", "AAPL")
    period = st.selectbox("분석 기간:", ["1mo", "3mo", "6mo", "1y", "2y"])
    
    if st.button("분석하기"):
        with st.spinner("분석 중..."):
            result = asyncio.run(analyze_stock_async(ticker, period))
            
            if "error" not in result:
                st.success(f"분석 완료: {result['basic_info']['company_name']}")
                st.json(result)
            else:
                st.error(f"오류: {result['error']}")

if __name__ == "__main__":
    main()
```

## 7. FastAPI 웹 서버

### `api_server.py`:
```python
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from stock_analyzer import StockAnalyzer

app = FastAPI()
analyzer = StockAnalyzer()

class StockRequest(BaseModel):
    ticker: str
    period: str = "1y"

@app.post("/analyze")
async def analyze_stock(request: StockRequest):
    result = await analyzer.analyze_stock(request.ticker, request.period)
    return result

@app.get("/price/{ticker}")
async def get_price(ticker: str):
    result = await analyzer.get_stock_price(ticker)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## 8. Discord 봇

### `discord_bot.py`:
```python
import discord
from discord.ext import commands
import asyncio
from stock_analyzer import StockAnalyzer

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
analyzer = StockAnalyzer()

@bot.command()
async def stock(ctx, ticker: str):
    """주식 분석 명령어"""
    async with ctx.typing():
        result = await analyzer.analyze_stock(ticker)
        
        if "error" not in result:
            basic = result['basic_info']
            embed = discord.Embed(
                title=f"{basic['company_name']} ({ticker})",
                description=f"현재가: ${basic['current_price']} ({basic['price_change_percentage']}%)"
            )
            embed.add_field(name="섹터", value=basic['sector'], inline=True)
            embed.add_field(name="P/E 비율", value=basic['pe_ratio'], inline=True)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"오류: {result['error']}")

bot.run('YOUR_DISCORD_TOKEN')
```

## 실행 방법

### 1. 가상환경 활성화:
```bash
source venv/bin/activate
```

### 2. 필요한 패키지 설치:
```bash
pip install streamlit fastapi uvicorn discord.py
```

### 3. 원하는 인터페이스 실행:

**웹 인터페이스:**
```bash
streamlit run web_interface.py
```

**API 서버:**
```bash
python api_server.py
```

**Discord 봇:**
```bash
python discord_bot.py
```

## 주의사항

1. **API 키 관리**: OpenAI API 키 등은 환경변수로 관리
2. **에러 처리**: 네트워크 오류, API 제한 등에 대한 처리 필요
3. **캐싱**: 동일한 요청에 대한 캐싱 구현 권장
4. **보안**: 웹 인터페이스의 경우 적절한 인증/인가 구현 필요 