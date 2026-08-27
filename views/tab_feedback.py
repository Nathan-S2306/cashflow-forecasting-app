import pandas as pd
import streamlit as st
from core.db import add_feedback, load_feedback


def render_feedback_tab():
    st.header("💬 Feedback & Ideas Log")
    st.caption("Log bugs, feature ideas, or layout improvements directly into SQLite.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Submit New Entry")
        f_cat = st.selectbox("Category", ["Feature Request", "Bug Report", "UX / UI Idea", "General"], key="fb_cat")
        f_text = st.text_area("Details", placeholder="Describe your suggestion or issue...", key="fb_text")

        if st.button("Submit Feedback", key="fb_submit"):
            if f_text.strip():
                add_feedback(f_cat, f_text.strip())
                st.success("Thank you! Feedback saved.")
                st.rerun()
            else:
                st.warning("Please enter feedback text before submitting.")

    with col2:
        st.subheader("Logged Feedback Backlog")
        items = load_feedback()
        if items:
            df_fb = pd.DataFrame(items, columns=["ID", "Category", "Feedback", "Submitted At"])
            st.dataframe(df_fb[["Category", "Feedback", "Submitted At"]], use_container_width=True, hide_index=True)
        else:
            st.info("No feedback logged yet.")