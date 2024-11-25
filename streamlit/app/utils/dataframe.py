"""Module for utility functions related to dataframes.

The dataframe_with_selections function is a workaround of the standard
streamlit st_dataframe to keep the selection tickbox visible.
"""
import streamlit as st
import numpy as np


# (https://github.com/streamlit/streamlit/issues/688)
def dataframe_with_selections(df, column_config={}):
    """Display a dataframe with a selection tickbox always visible."""
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)
    column_config["Select"] = st.column_config.CheckboxColumn(required=True)
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config=column_config,
        disabled=df.columns,
    )
    selected_indices = list(np.where(edited_df.Select)[0])
    selected_rows = df[edited_df.Select]
    return {"selected_rows_indices": selected_indices,
            "selected_rows": selected_rows}
