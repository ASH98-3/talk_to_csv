import os
import requests
import pandas as pd
import streamlit as st

BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="TalkToCSV",
    page_icon="🗂️",
    layout="centered"
)

st.title("🗂️ TalkToCSV")
st.caption("Upload a CSV or Excel file and ask questions in plain English.")

# --- Session state init ---
if "session_id"    not in st.session_state: st.session_state.session_id    = None
if "messages"      not in st.session_state: st.session_state.messages      = []
if "first_answer"  not in st.session_state: st.session_state.first_answer  = True
if "columns"       not in st.session_state: st.session_state.columns       = []
if "rows"          not in st.session_state: st.session_state.rows          = 0

# --- Upload ---
uploaded = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx", "xls"],
    help="Supports CSV and Excel files"
)

if uploaded and st.session_state.session_id is None:
    with st.spinner("Uploading and processing your dataset..."):
        resp = requests.post(
            f"{BACKEND}/upload",
            files={"file": (uploaded.name, uploaded.getvalue())},
        )

    if resp.ok:
        data = resp.json()
        st.session_state.session_id   = data["session_id"]
        st.session_state.columns      = data["columns"]
        st.session_state.rows         = data["rows"]
        st.session_state.messages     = []
        st.session_state.first_answer = True
    else:
        st.error(f"Upload failed: {resp.text}")

# --- Dataset info ---
if st.session_state.session_id:
    col1, col2 = st.columns(2)
    col1.metric("Rows", f"{st.session_state.rows:,}")
    col2.metric("Columns", len(st.session_state.columns))

    with st.expander("View columns"):
        st.write(", ".join(st.session_state.columns))

    st.divider()

    # --- Chat history ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.write(msg["content"])
            else:
                # show reasoning only on first answer
                if msg.get("show_reasoning") and msg.get("reasoning"):
                    st.info(f"🤔 {msg['reasoning']}")

                st.write(msg["content"])

                if msg.get("table"):
                    st.dataframe(
                        pd.DataFrame(msg["table"]),
                        use_container_width=True
                    )

                if msg.get("sql"):
                    with st.expander("🔍 See SQL query"):
                        st.code(msg["sql"], language="sql")

                if msg.get("pandas_code"):
                    with st.expander("🔍 See pandas expression"):
                        st.code(msg["pandas_code"], language="python")

    # --- Chat input ---
    question = st.chat_input("Ask something about your data...")

    if question:
        # show user message
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        # call backend
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                resp = requests.post(
                    f"{BACKEND}/ask",
                    json={
                        "session_id": st.session_state.session_id,
                        "question":   question,
                    },
                )

            if resp.ok:
                data          = resp.json()
                show_reasoning = st.session_state.first_answer

                # show reasoning on first answer only
                if show_reasoning and data.get("reasoning"):
                    st.info(f"🤔 {data['reasoning']}")

                st.write(data["answer"])

                if data.get("table"):
                    st.dataframe(
                        pd.DataFrame(data["table"]),
                        use_container_width=True
                    )

                if data.get("sql"):
                    with st.expander("🔍 See SQL query"):
                        st.code(data["sql"], language="sql")

                if data.get("pandas_code"):
                    with st.expander("🔍 See pandas expression"):
                        st.code(data["pandas_code"], language="python")

                # store in history
                st.session_state.messages.append({
                    "role":          "assistant",
                    "content":       data["answer"],
                    "table":         data.get("table"),
                    "sql":           data.get("sql"),
                    "pandas_code":   data.get("pandas_code"),
                    "reasoning":     data.get("reasoning"),
                    "show_reasoning": show_reasoning,
                })

                st.session_state.first_answer = False

            else:
                st.error(f"Error: {resp.text}")

else:
    st.info("👆 Upload a dataset above to get started.")