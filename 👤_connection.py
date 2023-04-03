import streamlit as st


def main():
    """
        This is the code used to show the "Connection" page
        The user will connect here and be able to acces to the rest of the application after that
    """
    st.set_page_config(page_title="Connection Page", page_icon="👤")
    st.title("👤Connection")
    if 'username' not in st.session_state:  # User not already connected
        username = st.text_input("Put your username here to connect :")
        if '-' in username:
            st.warning("You can't use '-' in your username")
        else:
            st.session_state.username = username
            st.session_state.last_form_name = None  # To detect if the user create a form with the same name as the previous one
            st.session_state.clicked = False
    else:  # User already connected, but can switch
        username = st.text_input("Put your username here to connect :", st.session_state.username)
        if '-' in username:
            st.warning("You can't use '-' in your username")
        else:
            st.session_state.username = username
            st.session_state.last_form_name = None
    
if __name__ == "__main__":
    main()