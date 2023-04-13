"""
Class for statistic page
Streamlit class
"""
import plotly.graph_objects as go
import streamlit as st

from ai_sustainability.package_user_interface.utils_streamlit import (
    check_user_connection,
)
from ai_sustainability.utils.models import SelectedEdge


class StatisticStreamlit:
    """
    Class used to show all the streamlit UI for the Form page

    Methods :
        - __init__ : initialise the UI and check if the user is connected
        - check_if_admin : chek if the user is an admin, show some messages in both cases
        - display_statistic_edges : show stats based on the edges
        - display_statistic_ais : show stats based on the AIs
    """

    def __init__(self) -> None:
        st.set_page_config(page_title="Statistic Page", page_icon="📊")
        st.title("📊Statistic")
        self.username = check_user_connection()
        st.session_state.clicked = False

    def check_if_admin(self, username: str) -> bool:
        if username != "Admin":
            st.write("You are not an Admin")
            st.write("You can't access to this page")
            return False
        st.write("Welcome Admin")
        st.write("You can now see the statistic of the form")
        return True

    def display_statistic_edges(self, edge_selected: list[SelectedEdge]) -> None:
        """
        Display bar graph of edges selected

        Parameters:
            - edge_selected (dict): dictionnary with proposition_id as key and number of time it was selected as value
        """
        print(edge_selected)
        with st.spinner("Loading..."):
            print(
                "##########################################\n##########################################\n##########################################\n##########################################\n"
            )
            # sort the dict on keys
            edge_selected.sort(key=lambda x: x.edge)
            hover_text = []  # text with the in and out node
            text = []  # Text of the selected answer
            count_edges = []  # Number of times each edge was selected
            for edge in edge_selected:
                print(edge)
                node_in = edge.edge.split("-")[0]
                node_out = edge.edge.split("-")[1]
                hover_text.append(f"Q {node_in} to Q {node_out}")
                text.append(edge.text)
                count_edges.append(edge.nb_selected)
            list_edge_name = list({k.edge for k in edge_selected}).sort()
            print(list_edge_name)
            fig = go.Figure(data=[go.Bar(x=list(list_edge_name), y=list(count_edges), hovertext=text, text=hover_text)])
            fig.update_layout(
                title="Number of times each edge was selected",
                xaxis_title="Edges/Propositions id",
                yaxis_title="Number of times selected",
                yaxis=dict(dtick=1),
            )
            st.plotly_chart(fig)

    def display_statistic_ais(self) -> None:
        pass
