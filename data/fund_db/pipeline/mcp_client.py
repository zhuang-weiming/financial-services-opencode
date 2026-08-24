"""
Morningstar MCP Client for Fund Data Loading
Supports JSON-RPC 2.0 protocol over HTTP.
"""
import requests
import json
import time
from typing import List, Dict, Optional, Generator


try:
    from config import MCP_URL as BASE_URL, TOKEN_FILE
except ImportError:            # 允许独立使用本文件
    BASE_URL = "https://mcp.morningstar.com/mcp"
    TOKEN_FILE = "/tmp/morningstar_token.json"


class MorningstarMCPClient:
    """Client for Morningstar MCP server using JSON-RPC 2.0
    
    认证说明 (M9): Bearer token 有效期 24h, 存放路径见 config.TOKEN_FILE。
    过期时重跑 OAuth 流程获取新 token 写回该文件即可, 客户端会自动加载。"""
    
    BASE_URL = BASE_URL
    TOKEN_FILE = TOKEN_FILE
    
    # Key datapoints
    DATAPOINTS = {
        'fund_size': 'OF009',
        'fund_size_daily': 'OF99A',
        'inception_date': 'OS00F',
        'sharpe_1y': 'RR010',
        'sharpe_3y': 'RR011',
        'return_1m': 'PM004',
        'return_ytd': 'PM00A',
        'return_1y': 'PM00C',
        'category': 'OF003',
        'star_rating': 'RR01Y',
        'medalist_rating': 'MMR01',
        'sustainability_rating': 'ESG48',
        'style_box': 'HS05A',
        'fund_domicile': 'LS017',
        'currency': 'LS05M',
        'is_index': 'OF00C',
        'is_ucits': 'OF016',
        'is_retail': 'MF01F',
        'is_leveraged': 'MF01D',
        'expense_ratio': 'ZZ006',
        'std_dev_1y': 'RR014',
    }
    
    def __init__(self):
        self.session_id = None
        self.token = self._load_token()
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'Authorization': f'Bearer {self.token}',
        }
        self._initialize()
    
    def _load_token(self):
        with open(self.TOKEN_FILE) as f:
            return json.load(f)['access_token']
    
    def _initialize(self):
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "fund-loader", "version": "1.0.0"}
            }
        }
        resp = requests.post(self.BASE_URL, json=body, headers=self.headers, timeout=30)
        self.session_id = resp.headers.get('mcp-session-id', '')
        if self.session_id:
            self.headers['mcp-session-id'] = self.session_id
    
    def _call_tool(self, tool_name: str, arguments: dict, max_retries: int = 3) -> Optional[dict]:
        """Call an MCP tool and parse the SSE response"""
        for attempt in range(max_retries):
            body = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000) % 100000,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            try:
                resp = requests.post(self.BASE_URL, json=body, headers=self.headers, timeout=120)
                if resp.status_code != 200:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return None
                
                text = resp.text
                if 'data:' in text:
                    for line in text.strip().split('\n'):
                        if line.startswith('data:'):
                            data_str = line[5:].strip()
                            data = json.loads(data_str)
                            result = data.get('result', {})
                            if result.get('isError'):
                                error_msg = result.get('content', [{}])[0].get('text', '')
                                print(f"  Tool error: {error_msg[:200]}")
                                return None
                            # Return the inner 'result' field from structuredContent if present
                            structured = result.get('structuredContent', {})
                            inner_result = structured.get('result', structured)
                            return inner_result
                time.sleep(0.5)
            except Exception as e:
                print(f"  Exception: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        return None
    
    def id_lookup(self, identifiers: List[str] = None, datapoints: List[str] = None) -> Optional[dict]:
        args = {}
        if identifiers:
            args['investment_identifiers'] = identifiers
        if datapoints:
            args['datapoints'] = datapoints
        return self._call_tool('morningstar-id-lookup-tool', args)
    
    def get_data(self, investment_ids: List[str], datapoint_ids: List[str],
                 start_date: str = '', end_date: str = '') -> Optional[dict]:
        args = {
            'investment_ids': investment_ids,
            'datapoint_ids': datapoint_ids,
        }
        if start_date:
            args['start_date'] = start_date
        if end_date:
            args['end_date'] = end_date
        return self._call_tool('morningstar-data-tool', args)
    
    def get_holdings(self, investment_ids: List[str], num_holdings: int = 10) -> Optional[dict]:
        return self._call_tool('morningstar-fund-holdings-tool', {
            'investment_ids': investment_ids,
            'num_holdings': num_holdings,
        })
    
    def screen(self, universe: str, criteria: List[dict], page_size: int = 100,
               pagination_token: str = '', action: str = '') -> Optional[dict]:
        args = {
            'universe': universe,
            'screener_criteria': criteria,
            'page_size': min(page_size, 200),
        }
        if pagination_token:
            args['pagination_token'] = pagination_token
            args['pagination_action'] = action
        return self._call_tool('morningstar-screener-tool', args)
    
    def screen_paginated(self, universe: str, criteria: List[dict], 
                         max_pages: int = 50, page_size: int = 100) -> Generator[dict, None, None]:
        """Generator that yields all results from a screener query with pagination"""
        token = ''
        for page in range(max_pages):
            action = 'next' if page > 0 else ''
            result = self.screen(universe, criteria, page_size=page_size, 
                               pagination_token=token, action=action)
            if not result:
                break
            
            results = result.get('results', [])
            yield result
            
            token = result.get('pagination_token_next', '')
            if not token:
                break


if __name__ == "__main__":
    # Quick test
    client = MorningstarMCPClient()
    print("Client initialized")
    
    # Test screener
    result = client.screen('FE', [
        {"datapoint_id": "RR01Y", "operator": ">", "value": "3"}
    ], page_size=3)
    
    if result:
        print(f"Total results: {result.get('total_result_count', 'N/A')}")
        for r in result.get('results', []):
            print(f"  {r.get('morningstar_id')}: {r.get('name')}")
