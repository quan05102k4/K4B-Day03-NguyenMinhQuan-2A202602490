# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Nguyễn Minh Quân
> **Mã Sinh Viên / Mã Học viên:** 2A202602490
> **Chủ đề Lựa chọn:** Đề tài Mở (Open Choice — mục 5, `docs/DANH_SACH_DE_TAI.md`) — **Trợ lý quản lý chi tiêu cá nhân**

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Agent phải suy luận để phân biệt 3 nhóm yêu cầu: hỏi kiến thức chung (mẹo tài chính), tra cứu số liệu đã có, hay ghi nhận một giao dịch mới; với yêu cầu ghép (vừa ghi nhận vừa tra cứu tổng) Agent còn phải quyết định thứ tự ưu tiên hành động nào cần thực hiện trước. |
| **2. Tool Interaction** | 3 / 5 | Hệ thống bắt buộc phải kết nối tới MCP Server (`src/mcp_server.py`) để đọc/ghi "cơ sở dữ liệu" chi tiêu (`MOCK_DATABASE` trong `src/tools.py`) — không thể trả lời chính xác về số dư/lịch sử chi tiêu chỉ bằng kiến thức nội tại của LLM, nên không thể chấm điểm thấp. Tuy nhiên bộ Tool hiện tại chỉ dừng ở mức tối thiểu theo yêu cầu đề bài (đúng 2 tool: 1 tra cứu + 1 hành động), thao tác đơn giản (query/insert trên mock data), chưa có chaining nhiều tool khác nhau hay tích hợp API bên thứ 3 (ngân hàng, ví điện tử...) nên chưa đạt mức 4-5/5. |
| **3. Dynamic Decision** | 4 / 5 | Bước tiếp theo phụ thuộc trực tiếp vào Observation: nếu `expense_query` trả về `NOT_FOUND` thì Agent phải phản hồi lịch sự thay vì bịa số liệu; nếu `add_expense` trả về `SUCCESS` thì Agent tổng hợp `expense_id` và thông điệp xác nhận tương ứng. |
| **4. Long Horizon Goal** | 3 / 5 | Trong phạm vi một phiên hỏi-đáp, Agent cần giữ mục tiêu xuyên suốt là "ghi đúng dữ liệu tài chính, không hallucination"; tuy nhiên do kiến trúc ReAct Loop hiện tại của bài Lab (1 vòng suy luận → 1 Tool Call → tổng hợp) nên chưa xử lý chuỗi hội thoại nhiều lượt dài như một trợ lý tài chính thực thụ theo dõi ngân sách qua nhiều tháng. |
| **TỔNG ĐIỂM AGENTIC FIT** | **14 / 20** | *Tổng điểm 14/20 > 12/20 → Bài toán "Trợ lý quản lý chi tiêu cá nhân" vẫn phù hợp để triển khai dưới dạng Agentic System (ReAct Agent + MCP Server), dù bộ Tool hiện tại còn ở mức tối giản đúng yêu cầu tối thiểu của đề bài.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ✅ Đoạn trích dưới đây được sinh ra khi chạy `python src/app.py --all` kết nối **LLM API thật qua Groq** (`LLM_PROVIDER=groq`, model `openai/gpt-oss-120b`, API tương thích chuẩn OpenAI SDK) — đầy đủ tại `docs/trace_waterfall.json`. Native Tool Calling hoạt động chính xác: Agent tự sinh đúng Tool Call `expense_query` / `add_expense` với tham số trích xuất từ câu hỏi tự nhiên.

Trích đoạn tiêu biểu Tool Call `expense_query` (TC02) từ `docs/trace_waterfall.json`:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu tổng chi tiêu cho danh mục Ăn uống trong tháng 09/2026 của người dùng U001.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "expense_query",
    "arguments": {
      "category": "Ăn uống",
      "month": "09/2026",
      "user_id": "U001"
    },
    "observation": {
      "status": "SUCCESS",
      "user_id": "U001",
      "data": {
        "total_amount": 205000,
        "transaction_count": 2,
        "category_filter": "Ăn uống",
        "month_filter": "09/2026"
      }
    },
    "latency_ms": 1575.91
  },
  {
    "step": 2,
    "action_type": "FINAL_ANSWER",
    "thought": "Tổng hợp kết quả từ MCP Server thành công.",
    "output": "Người dùng U001 đã chi tổng cộng 205,000 VNĐ qua 2 giao dịch (danh mục 'Ăn uống', tháng 09/2026).",
    "latency_ms": 10.0
  }
]
```

Trích đoạn tiêu biểu Tool Call `add_expense` (TC03) từ `docs/trace_waterfall.json`:

```json
{
  "step": 1,
  "query": "Hãy ghi nhận giúp tôi khoản chi 150000 VNĐ cho danh mục Di chuyển của người dùng U001, nội dung là đi taxi về nhà.",
  "action_type": "TOOL_EXECUTION",
  "tool_name": "add_expense",
  "arguments": {
    "amount": 150000,
    "category": "Di chuyển",
    "description": "đi taxi về nhà",
    "user_id": "U001"
  },
  "observation": {
    "status": "SUCCESS",
    "expense_id": "EXP-U001-006",
    "message": "Đã ghi nhận thành công khoản chi 150,000 VNĐ cho danh mục 'Di chuyển' vào ngày 13/09/2026."
  },
  "latency_ms": 1584.25
}
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` (`GROQ_API_KEY`, model `openai/gpt-oss-120b`) và xác nhận Agent chạy mượt mà trên LLM API thật qua Groq (API tương thích chuẩn OpenAI SDK, hỗ trợ Native Tool Calling đầy đủ).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases (chạy trên API thật Groq).
- **Số lượt gọi Tool qua MCP Server chính xác:** 4 lượt (TC02 → `expense_query`, TC03 → `add_expense`, TC04 → `add_expense`, TC05 → `expense_query`; TC01 trả lời trực tiếp không gọi Tool).
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân (`quan05102k4/K4B-Day03-NguyenMinhQuan-2A202602490`, nhánh `main`).

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
