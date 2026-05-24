import os
import time

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Enterprise Document RAG", page_icon="📚", layout="wide")
st.title("📚 Enterprise Document Intelligence")

try:
    doc_res = requests.get(f"{API_BASE_URL}/documents/")
    all_docs = doc_res.json() if doc_res.status_code == 200 else []
    health = requests.get("http://localhost:8000/health").json()
    st.sidebar.success(f"Backend Status: Online (v{health.get('version', 'unknown')})")
except requests.exceptions.ConnectionError:
    st.error("Backend Status: Offline. Please start the FastAPI server.")
    st.stop()

has_completed_docs = any(doc["status"] == "completed" for doc in all_docs)
is_processing = any(
    doc["status"] in ["pending", "parsing", "chunking", "indexing"] for doc in all_docs
)

tab_chat, tab_docs = st.tabs(["💬 Ask Assistant", "📄 Document Management"])

with tab_chat:
    st.subheader("Query your knowledge base")

    if not has_completed_docs:
        st.info(
            "👋 Welcome! Please upload and wait for at least one "
            "document to finish processing in the 'Document "
            "Management' tab before asking questions."
        )
    else:
        query = st.text_input("Ask a question about your documents:")
        col1, col2 = st.columns([1, 5])
        with col1:
            top_k = st.number_input(
                "Sources to retrieve", min_value=1, max_value=20, value=5
            )
            threshold = st.number_input(
                "Strictness (Score >)",
                min_value=-5.0,
                max_value=5.0,
                value=0.0,
                step=0.5,
            )

        if st.button("Submit Query", type="primary"):
            if not query:
                st.warning("Please enter a question.")
            else:
                with st.spinner("Searching and synthesizing..."):
                    payload = {
                        "query": query,
                        "top_k_retrieve": 20,
                        "top_k_return": top_k,
                        "score_threshold": threshold,
                    }
                    res = requests.post(f"{API_BASE_URL}/qa/ask", json=payload)

                    if res.status_code == 200:
                        data = res.json()
                        st.markdown("### Answer")
                        st.info(data["answer"])

                        citations = data.get("citations", [])
                        if citations:
                            st.markdown(
                                f"**Citations ({len(citations)} highly "
                                "relevant chunks used):**"
                            )
                            for i, cite in enumerate(citations):
                                with st.expander(
                                    f"Source {i + 1} | "
                                    f"Doc ID: {cite['document_id'][:8]}... | "
                                    f"Relevance: {cite['rerank_score']:.2f}"
                                ):
                                    st.write(cite["text_content"])
                                    st.json(cite["metadata_json"])
                        else:
                            st.warning(
                                "No citations met the strictness "
                                "threshold. Answer was bypassed."
                            )
                    else:
                        st.error(f"Error: {res.text}")

with tab_docs:
    st.subheader("Upload New Document")
    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, TXT, or Markdown", type=["pdf", "docx", "txt", "md"]
    )

    if st.button("Upload & Process", type="secondary"):
        if uploaded_file is not None:
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type,
                )
            }
            res = requests.post(f"{API_BASE_URL}/documents/", files=files)
            if res.status_code == 201:
                st.success("File uploaded! Processing started.")
                time.sleep(1)
                st.rerun()
            elif res.status_code == 409:
                st.warning("This document has already been uploaded.")
        else:
            st.warning("Please select a file first.")

    st.divider()
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.subheader("Document Repository")
    with col_b:
        auto_refresh = st.toggle("Auto-refresh status", value=is_processing)

    if all_docs:
        df = pd.DataFrame(all_docs)[["id", "filename", "status", "created_at"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
        if auto_refresh and is_processing:
            time.sleep(3)
            st.rerun()
    else:
        st.info("No documents found. Upload one to get started.")
