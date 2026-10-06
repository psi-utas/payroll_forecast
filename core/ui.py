import streamlit as st


def _clear(prefix: str):
    for k in [k for k in st.session_state if k.startswith(prefix)]:
        del st.session_state[k]


def clear_all_button(prefix: str):
    """Top-right 'Clear All': removes every widget value and result whose key starts with `prefix`."""
    _, c = st.columns([6, 1])
    c.button("Clear All", key=f"{prefix}clear_btn", on_click=_clear, args=(prefix,), width="stretch")
