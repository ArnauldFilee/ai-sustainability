import streamlit as st
from class_form import Form
from decouple import config
def main():
    st.title("Feedback")
    username = st.text_input("Enter your username here")
    if username:
        form = Form(
            endpoint = "questions-db.gremlin.cosmos.azure.com",
            database_name = "graphdb",
            container_name = 'Form',
            primary_key= config('PRIMARYKEY'),
        )
        username_exists = form.run_gremlin_query("g.V('"+username+"')")
        if username_exists:
            st.write("Welcome back "+username)
            st.write("You can now give us your feedback")
            text = st.text_area("Your feedback: ")
            if text:
                form.save_feedback(text, username)
                st.write("Your feedback has been saved")
                st.write("Thank you for your this !")
        else:
            st.write("You have to fill the form first")
            st.write("Please fill the form first and come back to give us your feedback")
            st.write("Thank you")

if __name__ == "__main__":
      main()