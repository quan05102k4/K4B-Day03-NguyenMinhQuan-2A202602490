"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.

Chủ đề: TRỢ LÝ QUẢN LÝ CHI TIÊU CÁ NHÂN (Personal Expense Manager Assistant)
Đề tài Mở (Open Choice - mục 5, docs/DANH_SACH_DE_TAI.md)
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1 (LOOKUP): Tra cứu chi tiêu đã ghi nhận của người dùng
    {
        "name": "expense_query",
        "description": "Tra cứu các khoản chi tiêu đã ghi nhận của người dùng, có thể lọc theo danh mục và/hoặc theo tháng để biết tổng số tiền đã chi.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Mã người dùng cần tra cứu (ví dụ: 'U001')"
                },
                "category": {
                    "type": "string",
                    "description": "Danh mục chi tiêu cần lọc (ví dụ: 'Ăn uống', 'Di chuyển', 'Giải trí'). Bỏ trống nếu muốn tra cứu tất cả danh mục."
                },
                "month": {
                    "type": "string",
                    "description": "Tháng cần lọc theo định dạng 'MM/YYYY' (ví dụ: '09/2026'). Bỏ trống nếu muốn tra cứu tất cả các tháng."
                }
            },
            "required": ["user_id"]
        }
    },

    # Tool 2 (ACTION): Ghi nhận một khoản chi tiêu mới
    {
        "name": "add_expense",
        "description": "Ghi nhận (thêm mới) một khoản chi tiêu vào sổ chi tiêu cá nhân của người dùng.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Mã người dùng thực hiện khoản chi (ví dụ: 'U001')"
                },
                "category": {
                    "type": "string",
                    "description": "Danh mục của khoản chi tiêu (ví dụ: 'Ăn uống', 'Di chuyển', 'Giải trí', 'Hóa đơn')"
                },
                "amount": {
                    "type": "number",
                    "description": "Số tiền đã chi tiêu, tính bằng VNĐ (ví dụ: 150000)"
                },
                "description": {
                    "type": "string",
                    "description": "Ghi chú/mô tả ngắn cho khoản chi (ví dụ: 'Ăn trưa với đồng nghiệp')"
                },
                "date_str": {
                    "type": "string",
                    "description": "Ngày phát sinh chi tiêu theo định dạng 'DD/MM/YYYY'. Nếu không cung cấp, hệ thống sẽ lấy ngày hiện tại."
                }
            },
            "required": ["user_id", "category", "amount"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "U001": [
        {"category": "Ăn uống", "amount": 85000, "date": "02/09/2026", "description": "Ăn trưa văn phòng"},
        {"category": "Ăn uống", "amount": 120000, "date": "05/09/2026", "description": "Đi ăn tối với bạn"},
        {"category": "Di chuyển", "amount": 60000, "date": "03/09/2026", "description": "Đi Grab đến công ty"},
        {"category": "Giải trí", "amount": 250000, "date": "07/09/2026", "description": "Xem phim cuối tuần"},
        {"category": "Hóa đơn", "amount": 500000, "date": "01/09/2026", "description": "Tiền điện tháng 9"},
    ],
    "U002": [
        {"category": "Ăn uống", "amount": 95000, "date": "04/09/2026", "description": "Đi chợ mua đồ ăn"},
    ],
}


def _normalize_month(date_str: str) -> str:
    """Trích xuất phần MM/YYYY từ chuỗi ngày DD/MM/YYYY"""
    parts = date_str.strip().split("/")
    if len(parts) == 3:
        return f"{parts[1]}/{parts[2]}"
    return date_str


def execute_expense_query(user_id: str, category: Optional[str] = None, month: Optional[str] = None) -> str:
    """Thực thi tra cứu chi tiêu theo user_id, có thể lọc theo danh mục và/hoặc tháng"""
    user_key = user_id.strip().upper()
    records = MOCK_DATABASE.get(user_key)

    if not records:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu chi tiêu nào cho người dùng '{user_id}'"
        }, ensure_ascii=False)

    filtered = records
    if category:
        filtered = [r for r in filtered if r["category"].strip().lower() == category.strip().lower()]
    if month:
        filtered = [r for r in filtered if _normalize_month(r["date"]) == month.strip()]

    if not filtered:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy khoản chi tiêu nào khớp với bộ lọc (danh mục='{category}', tháng='{month}') cho người dùng '{user_id}'"
        }, ensure_ascii=False)

    total_amount = sum(r["amount"] for r in filtered)
    return json.dumps({
        "status": "SUCCESS",
        "user_id": user_id,
        "data": {
            "total_amount": total_amount,
            "transaction_count": len(filtered),
            "category_filter": category,
            "month_filter": month,
            "records": filtered
        }
    }, ensure_ascii=False)


def execute_add_expense(user_id: str, category: str, amount: float, description: str = "", date_str: str = None) -> str:
    """Thực thi ghi nhận một khoản chi tiêu mới"""
    user_key = user_id.strip().upper()
    final_date = date_str.strip() if date_str else datetime.now().strftime("%d/%m/%Y")

    new_record = {
        "category": category,
        "amount": amount,
        "date": final_date,
        "description": description or ""
    }

    MOCK_DATABASE.setdefault(user_key, []).append(new_record)
    expense_id = f"EXP-{user_key}-{len(MOCK_DATABASE[user_key]):03d}"

    return json.dumps({
        "status": "SUCCESS",
        "expense_id": expense_id,
        "user_id": user_id,
        "data": new_record,
        "message": f"Đã ghi nhận thành công khoản chi {amount:,.0f} VNĐ cho danh mục '{category}' vào ngày {final_date}."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "expense_query": execute_expense_query,
    "add_expense": execute_add_expense
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)


if __name__ == "__main__":
    print(f"✅ [TOOLS CHECK]: Đã đăng ký thành công {len(TOOLS_SCHEMA)} Native Tools trong TOOLS_SCHEMA!")

    test_result = json.loads(dispatch_tool_call("expense_query", {"user_id": "U001"}))
    print(f"🔎 Kết quả gọi thử expense_query: Status {test_result.get('status')} (Người dùng U001)")
