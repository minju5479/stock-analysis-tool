#!/usr/bin/env python3
"""
MCP 서버 테스트 스크립트
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

class MCPTester:
    def __init__(self):
        self.process = None
    
    async def start_server(self):
        """MCP 서버를 시작합니다."""
        try:
            self.process = await asyncio.create_subprocess_exec(
                sys.executable, "stock_analysis_mcp.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            print("MCP 서버가 시작되었습니다.")
        except Exception as e:
            print(f"서버 시작 실패: {e}")
            return False
        return True
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """MCP 서버에 요청을 보냅니다."""
        if not self.process:
            return {"error": "서버가 시작되지 않았습니다"}
        
        try:
            # MCP 요청 형식으로 변환
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": request["name"],
                    "arguments": request["arguments"]
                }
            }
            
            # 요청 전송
            request_str = json.dumps(mcp_request) + "\n"
            self.process.stdin.write(request_str.encode())
            await self.process.stdin.drain()
            
            # 응답 읽기
            response_line = await self.process.stdout.readline()
            response = json.loads(response_line.decode().strip())
            
            return response.get("result", {})
            
        except Exception as e:
            return {"error": f"요청 처리 실패: {e}"}
    
    async def test_tools(self):
        """모든 도구를 테스트합니다."""
        test_cases = [
            {
                "name": "get_stock_price",
                "arguments": {"ticker": "AAPL"}
            },
            {
                "name": "analyze_stock",
                "arguments": {"ticker": "MSFT", "period": "6mo"}
            },
            {
                "name": "get_technical_indicators",
                "arguments": {"ticker": "GOOGL", "period": "1y"}
            },
            {
                "name": "get_financial_info",
                "arguments": {"ticker": "TSLA"}
            }
        ]
        
        print("=== MCP 서버 테스트 시작 ===\n")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"테스트 {i}: {test_case['name']}")
            print(f"티커: {test_case['arguments']['ticker']}")
            
            result = await self.send_request(test_case)
            
            if "error" in result:
                print(f"❌ 오류: {result['error']}")
            else:
                print("✅ 성공")
                # 결과의 일부만 출력
                if "content" in result and result["content"]:
                    content = result["content"][0].get("text", "")
                    try:
                        parsed_content = json.loads(content)
                        if "ticker" in parsed_content:
                            print(f"   티커: {parsed_content['ticker']}")
                        if "basic_info" in parsed_content:
                            basic = parsed_content["basic_info"]
                            # 티커에 따라 통화 기호 결정
                            currency_symbol = "￦" if ticker.endswith('.KS') else "$"
                            print(f"   현재가: {currency_symbol}{basic.get('current_price', 'N/A')}")
                            print(f"   변화율: {basic.get('price_change_percentage', 'N/A')}%")
                    except:
                        print(f"   응답: {content[:200]}...")
            
            print()
    
    async def cleanup(self):
        """서버를 종료합니다."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("MCP 서버가 종료되었습니다.")

async def main():
    """메인 테스트 함수"""
    tester = MCPTester()
    
    try:
        # 서버 시작
        if await tester.start_server():
            # 잠시 대기 (서버 초기화 시간)
            await asyncio.sleep(2)
            
            # 도구 테스트
            await tester.test_tools()
        else:
            print("서버 시작에 실패했습니다.")
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 