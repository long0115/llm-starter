"""
Streamlit 前端界面

功能：
    - 多 Agent 切换（Simple/Flow/Supervisor）
    - 对话历史管理
    - Markdown 渲染
    - Token 使用统计

启动方式：
    streamlit run app.py --server.port 8501
"""

import streamlit as st
import requests
import json
from datetime import datetime

# 页面配置
st.set_page_config(
    page_title="MultiAgentFlow 演示系统",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 配置
API_BASE_URL = "http://localhost:8000"

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_agent" not in st.session_state:
    st.session_state.current_agent = "simple"

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def send_message(question: str, agent_type: str) -> dict:
    """
    发送消息到后端 API

    Args:
        question: 用户问题
        agent_type: Agent 类型 (simple/flow/supervisor)

    Returns:
        API 响应字典
    """
    # 根据 Agent 类型选择接口
    if agent_type == "supervisor":
        url = f"{API_BASE_URL}/agent/run/supervisor"
    elif agent_type == "flow":
        url = f"{API_BASE_URL}/agent/run/flow"
    else:
        url = f"{API_BASE_URL}/agent/run/simple"

    payload = {
        "question": question,
        "thread_id": st.session_state.thread_id
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "无法连接到后端服务，请确保 API 服务已启动"}
    except requests.exceptions.Timeout:
        return {"error": "请求超时，请稍后重试"}
    except Exception as e:
        return {"error": f"请求失败: {str(e)}"}


def render_message(role: str, content: str):
    """
    渲染单条消息

    Args:
        role: 消息角色 (user/assistant)
        content: 消息内容
    """
    with st.chat_message(role):
        if role == "assistant":
            # 助手消息支持 Markdown 渲染
            st.markdown(content)
        else:
            # 用户消息直接显示
            st.write(content)


def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title("🤖 AI 演示系统")
        st.markdown("---")

        # Agent 类型选择
        st.subheader("Agent 类型")
        agent_type = st.radio(
            "选择 Agent 模式",
            ["simple", "flow", "supervisor"],
            format_func=lambda x: {
                "simple": "Simple Agent（简单工具调用）",
                "flow": "Flow Agent（流程编排）",
                "supervisor": "Supervisor（多 Agent 协作）"
            }.get(x, x),
            key="agent_selector"
        )

        # 更新当前 Agent
        if agent_type != st.session_state.current_agent:
            st.session_state.current_agent = agent_type
            st.rerun()

        st.markdown("---")

        # 会话管理
        st.subheader("会话管理")
        st.write(f"当前会话 ID: `{st.session_state.thread_id}`")

        if st.button("️ 清空对话", use_container_width=True):
            st.session_state.messages = []
            st.session_state.thread_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            st.rerun()

        st.markdown("---")

        # 系统信息
        st.subheader("系统信息")
        st.write("后端 API: `http://localhost:8000`")

        # 健康检查
        try:
            health = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if health.status_code == 200:
                st.success("✅ 后端服务正常")
            else:
                st.error("❌ 后端服务异常")
        except:
            st.error("❌ 无法连接后端服务")


def render_chat_interface():
    """渲染聊天界面"""
    # 显示历史消息
    for message in st.session_state.messages:
        render_message(message["role"], message["content"])

    # 聊天输入框
    if prompt := st.chat_input("请输入你的问题..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        render_message("user", prompt)

        # 显示加载状态
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                # 调用后端 API
                response = send_message(prompt, st.session_state.current_agent)

                # 处理响应
                if "error" in response:
                    error_msg = response["error"]
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ {error_msg}"})
                else:
                    # 成功响应
                    answer = response.get("content", "未获取到回复")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})


def render_agent_info():
    """渲染 Agent 说明信息"""
    st.markdown("---")

    agent_descriptions = {
        "simple": """
        **Simple Agent** - 简单工具调用模式

        - 直接调用 LLM + 工具
        - 支持工具：计算器、天气查询、时间查询
        - 适合：简单的工具调用场景
        """,
        "flow": """
        **Flow Agent** - 流程编排模式

        - 意图识别 → 路由 → 专业处理
        - 支持：普通对话、RAG 知识库、工具调用
        - 适合：需要多步骤处理的复杂场景
        """,
        "supervisor": """
        **Supervisor Agent** - 多 Agent 协作模式

        - 协调者分析意图 → 路由到专家 Agent → 汇总结果
        - 专家 Agent：RAG 知识库、工具调用、普通对话
        - 适合：需要多个专业 Agent 协作的复杂任务
        """
    }

    with st.expander("📖 当前 Agent 说明"):
        st.markdown(agent_descriptions.get(st.session_state.current_agent, ""))


def main():
    """主函数"""
    # 渲染侧边栏
    render_sidebar()

    # 主标题
    st.title("💬 AI Agent 对话系统")
    st.caption(f"当前模式: **{st.session_state.current_agent.upper()}**")

    # 渲染聊天界面
    render_chat_interface()

    # 渲染 Agent 说明
    render_agent_info()


if __name__ == "__main__":
    main()
