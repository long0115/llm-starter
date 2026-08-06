"""
Streamlit 前端界面

布局：
    左侧边栏：
        顶部 - 智能体名称
        中间 - 最近对话列表
    右侧区域：
        上部 - 对话消息列表
        底部 - 固定输入框

启动方式：
    streamlit run app.py --server.port 8501
"""

from re import T

import streamlit as st
import requests
from datetime import datetime

# API 配置
API_BASE_URL = "http://localhost:8000"

# 页面配置
st.set_page_config(
    page_title="MultiAgentFlow",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Session State 初始化 ====================

if "sessions" not in st.session_state:
    st.session_state.sessions = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "chat"  # chat / rag / agent
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ==================== API 调用 ====================

def fetch_sessions() -> list:
    """从后端获取最近对话列表"""
    try:
        resp = requests.get(f"{API_BASE_URL}/session/list", params={"limit": 50, "session_type": st.session_state.current_mode}, timeout=20)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

def fetch_session_messages(session_id: str) -> list:
    """获取指定会话的消息历史"""
    try:
        resp = requests.get(f"{API_BASE_URL}/session/{session_id}/messages", params={"limit": 50}, timeout=20)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return []

def create_session(session_type: str, title: str = None) -> dict:
    """创建新会话"""
    try:
        resp = requests.post(f"{API_BASE_URL}/session/create", json={"session_type": session_type, "title": title})
        resp.raise_for_status()
        return resp.json()
    except:
        pass
    return {}

def send_message(question: str) -> dict:
    """根据当前模式发送消息"""

    if st.session_state.current_mode == "chat":
        # 流式响应，逐行读取 SSE
        resp = requests.post(
            f"{API_BASE_URL}/chat/stream",
            json={"message": question, "session_id": st.session_state.session_id},
            stream=True
        )
        resp.raise_for_status()

        full_content = ""
        for line in resp.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                data = line_str[6:]
                if data == "[DONE]":
                    break
                full_content += data

        return {"content": full_content, "session_id": st.session_state.session_id}

    elif st.session_state.current_mode == "rag":
        resp = requests.post(f"{API_BASE_URL}/rag/query", json={"question": question, "use_rerank": False})
        resp.raise_for_status()
        return resp.json()

    elif st.session_state.current_mode == "agent":
        resp = requests.post(f"{API_BASE_URL}/agent/run/flow", json={"question": question, "thread_id": st.session_state.session_id})
        resp.raise_for_status()
        return resp.json()

    return {"error": "未知模式"}

# ==================== 自定义 CSS ====================

st.markdown("""
<style>
    section[data-testid="stSidebar"] .block-container {
        overflow-y: auto;
    }

    .source-tag {
        display: inline-block;
        background-color: #e8f0fe;
        color: #1a73e8;
        border-radius: 4px;
        padding: 3px 10px;
        font-size: 12px;
        margin: 3px 4px 3px 0;
    }

    .st-emotion-cache-10p9htt {
        margin-bottom: 0px;
    }

    .st-emotion-cache-liupih {
        padding-top: 50px;
    }

    p {
        margin-bottom: 0px;
    }

    h1 {
        padding-top: 0px;
    }

</style>
""", unsafe_allow_html=True)

# ==================== 左侧边栏 ====================

def render_sidebar():
    """左侧边栏：智能体名称 + 最近对话"""
    with st.sidebar:
        # 顶部：智能体名称
        st.markdown("<h1>💬 MultiAgentFlow</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#999; font-size:13px; margin-top:-6px; margin-bottom:16px;'>多 Agent 协作工作流框架</p>", unsafe_allow_html=True)

        # 新建对话按钮
        if st.button("新建对话", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.session_id = create_session(session_type=st.session_state.current_mode).get("session_id")

        # 最近对话列表
        st.markdown("<p style='font-size:14px;margin-bottom:15px;'>最近对话</p>", unsafe_allow_html=True)

        st.session_state.sessions = fetch_sessions()
        if st.session_state.sessions:
            for s in st.session_state.sessions:
                title = s.get("title", "未命名会话")
                session_type = s.get("session_type", "chat")
                create_time = s.get("created_at", "")
                current_session_id = s.get("session_id", "")

                is_active = current_session_id == st.session_state.session_id
                display_title = title if len(title) <= 20 else title[:20] + "..."

                # 格式化时间
                dt = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                st.caption(f"{time_str}")

                if st.button(
                    f"{display_title}",
                    key=f"sidebar_{current_session_id}",
                    use_container_width=True,
                    type="secondary" if not is_active else "primary"
                ):
                    st.session_state.session_id = current_session_id
                    st.session_state.current_mode = session_type
                    msgs = fetch_session_messages(current_session_id)
                    st.session_state.messages = [
                        {"role": m["role"], "content": m["content"]} for m in msgs
                    ]
                    st.rerun()

        else:
            st.caption("暂无对话记录")

# ==================== 对话主区域 ====================

def render_message(role: str, content: str, sources: list = None):
    """渲染单条消息，有引用来源时才展示"""
    with st.chat_message(role):
        if role == "assistant":
            st.markdown(content)

            # 有引用来源时才展示
            if sources and len(sources) > 0:
                st.markdown(
                    f"<p style='color:#888; font-size:12px; margin-top:10px; margin-bottom:4px;'>"
                    f"引用来源</p>",
                    unsafe_allow_html=True
                )
                source_tags = ""
                for src in sources:
                    file_name = src.get("file_name", "未知")
                    source_tags += f'<span class="source-tag">{file_name}</span> '
                st.markdown(source_tags, unsafe_allow_html=True)
        else:
            st.markdown(content)


def render_chat_area():
    """右侧：对话区域（消息列表 + 输入框）"""

    mode_labels = {"chat": "Chat 对话", "rag": "RAG 知识库", "agent": "Agent 智能体"}
    mode_descs = {
        "chat": "大模型基础对话",
        "rag": "基于企业知识库回答",
        "agent": "多 Agent 协作处理"
    }

    # 顶部标题栏
    col_title, col_mode = st.columns([8, 1])
    with col_title:
        st.markdown(f"<h3 style='margin-bottom:2px;'>{mode_labels.get(st.session_state.current_mode, '对话')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#999; font-size:13px; margin-top:-10px;margin-bottom: 30px;'>{mode_descs.get(st.session_state.current_mode, '')}</p>", unsafe_allow_html=True)
    with col_mode:
        mode_options = ["chat", "rag", "agent"]
        mode_labels_btn = {"chat": "Chat", "rag": "RAG", "agent": "Agent"}
        idx = mode_options.index(st.session_state.current_mode)
        new_mode = st.selectbox(
            "类型",
            options=mode_options,
            index=idx,
            format_func=lambda x: mode_labels_btn.get(x, x),
            label_visibility="collapsed",
            key="mode_select"
        )
        if new_mode != st.session_state.current_mode:
            st.session_state.current_mode = new_mode
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()
        

    # 消息列表（可滚动区域）
    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"], msg.get("sources"))

    # 输入框
    placeholder = {
        "chat": "输入你的问题，按 Enter 发送",
        "rag": "请输入关于知识库的问题...",
        "agent": "请输入问题，Agent 将自动处理..."
    }

    if prompt := st.chat_input(placeholder.get(st.session_state.current_mode, "请输入..."), key="main_input"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        render_message("user", prompt)

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                result = send_message(prompt)

            if "error" in result:
                st.error(result["error"])
                st.session_state.messages.append({"role": "assistant", "content": f"❌ {result['error']}"})
            else:
                answer = result.get("content", "未获取到回复")
                sources = result.get("sources", [])
                st.markdown(answer)

                if sources and len(sources) > 0:
                    st.markdown(
                        f"<p style='color:#888; font-size:12px; margin-top:10px; margin-bottom:4px;'>"
                        f"📎 已引用 {len(sources)} 个来源</p>",
                        unsafe_allow_html=True
                    )
                    source_tags = ""
                    for src in sources:
                        file_name = src.get("file_name", "未知")
                        source_tags += f'<span class="source-tag">{file_name}</span> '
                    st.markdown(source_tags, unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources if sources else None
                })


# ==================== 主函数 ====================

def main():
    """主函数"""
    render_sidebar()
    render_chat_area()

if __name__ == "__main__":
    main()
