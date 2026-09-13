"""
🖥️ GIAO DIỆN TRỰC QUAN (STREAMLIT) CHO TRỢ LÝ QUẢN LÝ CHI TIÊU CÁ NHÂN
Tái sử dụng toàn bộ logic ReAct Agent + MCP Server đã xây dựng trong src/app.py, src/mcp_server.py, src/providers.py.

Chạy bằng lệnh:
    streamlit run src/ui_app.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from app import run_react_agent, save_waterfall_trace
from mcp_server import MCPExpenseServer
from providers import get_llm_provider
from tools import MOCK_DATABASE

load_dotenv()

st.set_page_config(page_title="Trợ lý Quản lý Chi tiêu Cá nhân", page_icon="💰", layout="wide")


@st.cache_resource
def load_backend():
    """Khởi tạo LLM Provider và MCP Server 1 lần duy nhất cho cả phiên làm việc"""
    provider = get_llm_provider()
    mcp_server = MCPExpenseServer()
    return provider, mcp_server


provider, mcp_server = load_backend()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "all_traces" not in st.session_state:
    st.session_state.all_traces = []

# ==============================================================================
# SIDEBAR: THÔNG TIN HỆ THỐNG & SỔ CHI TIÊU HIỆN TẠI
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Trạng thái Hệ thống")
    st.markdown(f"**🔌 LLM Provider:** `{provider.__class__.__name__}`")
    st.markdown(f"**🤖 Model:** `{getattr(provider, 'model_name', 'N/A')}`")
    st.markdown(f"**🌐 MCP Server:** `{mcp_server.server_name}` (v{mcp_server.version})")

    tools_list = mcp_server.list_tools()
    with st.expander(f"🛠️ Tools công bố qua MCP ({len(tools_list)})"):
        for t in tools_list:
            st.markdown(f"- **`{t['name']}`**: {t['description']}")

    st.divider()
    st.header("📒 Sổ Chi Tiêu (Mock Database)")
    user_ids = list(MOCK_DATABASE.keys()) or ["U001"]
    selected_user = st.selectbox("Chọn người dùng", user_ids)

    records = MOCK_DATABASE.get(selected_user, [])
    if records:
        df = pd.DataFrame(records)
        total = df["amount"].sum()
        st.metric("Tổng chi tiêu đã ghi nhận", f"{total:,.0f} VNĐ")
        st.bar_chart(df.groupby("category")["amount"].sum())
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dữ liệu chi tiêu cho người dùng này.")

    st.divider()
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.all_traces = []
        st.rerun()

# ==============================================================================
# MAIN: GIAO DIỆN CHAT VỚI REACT AGENT
# ==============================================================================
st.title("💰 Trợ lý Quản lý Chi tiêu Cá nhân")
st.caption("ReAct Agent + MCP Server — Bài Lab 3 (Day 03): Chatbot vs ReAct Agent")

st.markdown("**💡 Câu hỏi gợi ý:**")
example_cols = st.columns(3)
examples = [
    "Cho tôi vài mẹo để tiết kiệm chi tiêu hàng tháng?",
    "Hãy tra cứu tổng chi tiêu danh mục Ăn uống của U001 trong tháng 09/2026",
    "Ghi nhận giúp tôi khoản chi 150000 VNĐ cho danh mục Di chuyển của U001",
]
example_clicked = None
for col, example in zip(example_cols, examples):
    if col.button(example, use_container_width=True):
        example_clicked = example

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("trace"):
            with st.expander("🔍 Xem chi tiết ReAct Trace (Thought → Action → Observation)"):
                for event in msg["trace"]:
                    if event["action_type"] == "TOOL_EXECUTION":
                        st.markdown(f"🧠 **Thought:** {msg.get('thought', '')}")
                        st.markdown(f"🛠️ **Action:** `{event['tool_name']}({event['arguments']})`")
                        st.json(event["observation"])
                        st.caption(f"⏱️ Latency: {event['latency_ms']} ms")
                    elif event["action_type"] == "FINAL_ANSWER":
                        st.caption(f"⏱️ Tổng hợp Final Answer — Latency: {event['latency_ms']} ms")

user_input = example_clicked or st.chat_input("Nhập câu hỏi về chi tiêu của bạn...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Đang suy luận (ReAct Loop)..."):
            trace_logs = run_react_agent(user_input, provider, mcp_server)
            st.session_state.all_traces.extend(trace_logs)
            save_waterfall_trace(st.session_state.all_traces)

            final_event = next((e for e in reversed(trace_logs) if e["action_type"] == "FINAL_ANSWER"), None)
            final_answer = final_event["output"] if final_event else "Không thể tạo phản hồi."
            thought = next((e.get("thought", "") for e in trace_logs if e["action_type"] == "TOOL_EXECUTION"), "")

        st.markdown(final_answer)
        with st.expander("🔍 Xem chi tiết ReAct Trace (Thought → Action → Observation)"):
            for event in trace_logs:
                if event["action_type"] == "TOOL_EXECUTION":
                    st.markdown(f"🧠 **Thought:** {thought}")
                    st.markdown(f"🛠️ **Action:** `{event['tool_name']}({event['arguments']})`")
                    st.json(event["observation"])
                    st.caption(f"⏱️ Latency: {event['latency_ms']} ms")
                elif event["action_type"] == "FINAL_ANSWER":
                    st.caption(f"⏱️ Tổng hợp Final Answer — Latency: {event['latency_ms']} ms")

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": final_answer,
        "trace": trace_logs,
        "thought": thought
    })
    st.rerun()
