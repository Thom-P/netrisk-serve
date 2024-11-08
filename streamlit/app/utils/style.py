import streamlit as st


def apply_style_tweaks():
    # Adjust margins (reduce top one)
    st.markdown("""
    <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 3rem;
                padding-left: 5rem;
                padding-right: 5rem;
            }
    </style>
    """, unsafe_allow_html=True)

    # Hacky patch to remove +/- buttons on number inputs causing instabilities on
    # repetitive clicks (https://github.com/streamlit/streamlit/issues/894)
    st.markdown("""
    <style>
        button.step-up {display: none;}
        button.step-down {display: none;}
        div[data-baseweb] {border-radius: 4px;}
    </style>""", unsafe_allow_html=True)

    # Change fontsize of expander and tabs widgets
    # Nb: the ids might change with new streamlit releases
    st.markdown("""
    <style>
        div[data-testid="stExpander"] details summary p{font-size: 1rem;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] button
        [data-testid="stMarkdownContainer"] p {
            font-size: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    return
