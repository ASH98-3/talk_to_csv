import os
import requests
import pandas as pd
import plotly.express as px
import streamlit as st

BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="TalkToCSV",
    page_icon="🗂️",
    layout="wide"
)

# --- Session state init ---
for key, default in {
    "session_id":   None,
    "messages":     [],
    "first_answer": True,
    "columns":      [],
    "rows":         0,
    "preview":      None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# --- Chart renderer — defined first so it's available everywhere ---
def render_chart(chart_type, table, chart_x, chart_y):
    if not table:
        return
    df = pd.DataFrame(table)
    
    # auto-detect columns if chart_x/chart_y don't match actual columns
    cols = df.columns.tolist()
    if chart_x not in df.columns and len(cols) >= 2:
        chart_x = cols[0]  # first column is always category
        chart_y = cols[1]  # second column is always value
    
    try:
        if chart_type == "bar":
            fig = px.bar(df, x=chart_x, y=chart_y, title=f"{chart_y} by {chart_x}")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "pie":
            fig = px.pie(df, names=chart_x, values=chart_y, title=f"{chart_y} by {chart_x}")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "line":
            fig = px.line(df, x=chart_x, y=chart_y, title=f"{chart_y} over {chart_x}")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "histogram":
            fig = px.histogram(df, x=chart_x, title=f"Distribution of {chart_x}")
            st.plotly_chart(fig, use_container_width=True)
        elif chart_type == "scatter":
            fig = px.scatter(df, x=chart_x, y=chart_y, title=f"{chart_x} vs {chart_y}")
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass

# --- Sidebar ---
with st.sidebar:
    st.title("🗂️ TalkToCSV")
    st.caption("Ask questions about your data in plain English.")
    st.divider()

    uploaded = st.file_uploader(
        "Upload dataset",
        type=["csv", "xlsx", "xls"],
        help="Supports CSV and Excel files"
    )

    if uploaded and st.session_state.session_id is None:
        with st.spinner("Processing..."):
            resp = requests.post(
                f"{BACKEND}/upload",
                files={"file": (uploaded.name, uploaded.getvalue())},
            )
        if resp.ok:
            data = resp.json()
            st.session_state.session_id   = data["session_id"]
            st.session_state.columns      = data["columns"]
            st.session_state.rows         = data["rows"]
            st.session_state.preview      = data["preview"]
            st.session_state.messages     = []
            st.session_state.first_answer = True
            st.success("Dataset loaded!")
        else:
            st.error(f"Upload failed: {resp.text}")

    if st.session_state.session_id:
        st.divider()
        st.metric("Rows",    f"{st.session_state.rows:,}")
        st.metric("Columns", len(st.session_state.columns))

        with st.expander("📋 Columns"):
            for col in st.session_state.columns:
                st.text(f"• {col}")

        st.divider()

        if st.button("🔄 Upload new file", use_container_width=True):
            st.session_state.session_id   = None
            st.session_state.messages     = []
            st.session_state.first_answer = True
            st.session_state.columns      = []
            st.session_state.rows         = 0
            st.session_state.preview      = None
            st.rerun()

        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.messages     = []
            st.session_state.first_answer = True
            st.rerun()

    st.divider()
    st.caption("Built with FastAPI · LangGraph · Groq · ChromaDB")


# --- Main area ---
if not st.session_state.session_id:
    st.title("Welcome to TalkToCSV 👋")
    st.write("Upload a CSV or Excel file in the sidebar to get started.")
    st.info(
        "💡 You can ask questions like:\n"
        "- What is the average salary by job title?\n"
        "- Which country has the most job postings?\n"
        "- Show me missing values in the dataset\n"
        "- What are the top skills for Data Engineers?"
    )

else:
    if st.session_state.preview:
        with st.expander("📊 Data preview (first 5 rows)"):
            st.dataframe(pd.DataFrame(st.session_state.preview), use_container_width=True)

    st.divider()

    # --- Chat history ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.write(msg["content"])
            else:
                if msg.get("show_reasoning") and msg.get("reasoning"):
                    st.caption(f"🤔 {msg['reasoning']}")

                st.write(msg["content"])

                if msg.get("chart_type") and msg.get("table"):
                    render_chart(
                        msg["chart_type"],
                        msg["table"],
                        msg.get("chart_x"),
                        msg.get("chart_y"),
                    )

                if msg.get("table"):
                    st.dataframe(pd.DataFrame(msg["table"]), use_container_width=True)

                if msg.get("sql"):
                    with st.expander("🔍 SQL query"):
                        st.code(msg["sql"], language="sql")

                if msg.get("pandas_code"):
                    with st.expander("🔍 Pandas expression"):
                        st.code(msg["pandas_code"], language="python")

    # --- Chat input ---
    question = st.chat_input("Ask something about your data...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Analysing your question..."):
                resp = requests.post(
                    f"{BACKEND}/ask",
                    json={
                        "session_id": st.session_state.session_id,
                        "question":   question,
                    },
                )

            if resp.ok:
                data           = resp.json()
                show_reasoning = st.session_state.first_answer

                if show_reasoning and data.get("reasoning"):
                    st.caption(f"🤔 {data['reasoning']}")

                st.write(data["answer"])

                if data.get("chart_type") and data.get("table"):
                    render_chart(
                        data["chart_type"],
                        data["table"],
                        data.get("chart_x"),
                        data.get("chart_y"),
                    )

                if data.get("table"):
                    st.dataframe(
                        pd.DataFrame(data["table"]),
                        use_container_width=True
                    )

                if data.get("sql"):
                    with st.expander("🔍 SQL query"):
                        st.code(data["sql"], language="sql")

                if data.get("pandas_code"):
                    with st.expander("🔍 Pandas expression"):
                        st.code(data["pandas_code"], language="python")

                st.session_state.messages.append({
                    "role":           "assistant",
                    "content":        data["answer"],
                    "table":          data.get("table"),
                    "sql":            data.get("sql"),
                    "pandas_code":    data.get("pandas_code"),
                    "reasoning":      data.get("reasoning"),
                    "chart_type":     data.get("chart_type"),
                    "chart_x":        data.get("chart_x"),
                    "chart_y":        data.get("chart_y"),
                    "show_reasoning": show_reasoning,
                })

                st.session_state.first_answer = False

            else:
                st.error(f"Error: {resp.text}")