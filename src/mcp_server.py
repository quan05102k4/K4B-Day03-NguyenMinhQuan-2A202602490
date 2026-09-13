"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.

Chủ đề: TRỢ LÝ QUẢN LÝ CHI TIÊU CÁ NHÂN (Personal Expense Manager Assistant)
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPExpenseServer:
    """
    Giả lập MCP Server tuân thủ chuẩn giao thức Model Context Protocol
    """
    def __init__(self, server_name: str = "expense-tracker-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực thi request gọi Tool theo chuẩn MCP JSON-RPC
        1. Gọi dispatch_tool_call(tool_name, arguments) để lấy chuỗi JSON kết quả từ Tool Router.
        2. Chuyển đổi chuỗi JSON kết quả thành Python Dictionary.
        3. Đóng gói phản hồi theo chuẩn giao thức MCP JSON-RPC 2.0.
        """
        result_str = dispatch_tool_call(tool_name, arguments)
        content = json.loads(result_str)
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (expense-tracker-mcp-server)")
    print("==========================================================")

    server = MCPExpenseServer()
    tools = server.list_tools()
    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố: {len(tools)}")

    test_result = server.call_tool("expense_query", {"user_id": "U001"})
    if not test_result:
        print("⏳ Hàm call_tool() đang trả về rỗng. Kiểm tra lại 'src/mcp_server.py'!")
    else:
        print(f"✅ Test dispatch tool 'expense_query' thành công:")
        print(f"   Phản hồi JSON-RPC: {json.dumps(test_result, ensure_ascii=False)}")
