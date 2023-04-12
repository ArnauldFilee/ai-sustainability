"""
This file is used to show the Historic page
"""
from ai_sustainability.package_application.application import Application
from ai_sustainability.package_user_interface.classes.class_historic import (
    HistoricStreamlit,
)
from ai_sustainability.utils.models import AnswersList, User

# General variable, used to begin the main() function
N_BEST_AI = 5


def historic_user(username: User, st_historic: HistoricStreamlit, app: Application) -> None:
    """
    Function used to show a form with the User view
    """
    list_answered_form = app.get_all_forms_names(username)
    selected_form = st_historic.show_choice_form(list_answered_form)
    if not selected_form:  # if none form selected, don't show the rest
        return
    form_name = selected_form.rsplit("-", maxsplit=1)[-1]

    # get the list with all previous answers contained in the form
    previous_answers = app.get_list_answers(selected_form)

    end = False
    list_answers: AnswersList = AnswersList([])
    i = 0
    while not end:
        next_question = app.get_next_question(list_answers)
        selected_answer = st_historic.ask_question_user(next_question, previous_answers[len(list_answers)])
        if selected_answer is None:
            return
        end = next_question.type == "end"
        if not end:
            list_answers.append(selected_answer)
            # If not already changed and name answer different from previous one and question's label is not Q_Open :
            # The form is modified and we do not fill it automatically with previous answers
            if (
                previous_answers[0] is not None
                and list_answers[i] != previous_answers[i]
                and next_question["question_label"] != "Q_Open"
            ):
                previous_answers = [None] * len(previous_answers)
        i += 1
        if i >= len(previous_answers):
            previous_answers.append(None)  # To avoid list index out of range when calling show_question

    # If the form is not finish, we wait the user to enter a new answer
    if next_question["question_label"] != "end":
        return

    # We ask the user to give us a name for the form (potentially a new one)
    new_form_name = st_historic.show_input_form_name(form_name)
    if not new_form_name:
        return

    # If the name is already taken by an other form
    if app.check_form_exist(username, new_form_name) and new_form_name != form_name:
        if st_historic.check_name_already_taken(username):
            return

    list_bests_ais = app.calcul_best_ais(N_BEST_AI, list_answers)
    st_historic.show_best_ai(list_bests_ais)
    if st_historic.show_submission_button():
        app.change_answers(list_answers, username, form_name, new_form_name)


def historic_admin(st_historic: HistoricStreamlit, app: Application) -> None:
    """
    Function used to show a form with the Admin view
    """
    list_username = app.get_all_users()

    # The admin select an user
    choosen_user = st_historic.show_choice_user(list_username)
    if not choosen_user:  # if no user selected, don't show the rest
        return

    # The admin select a form of the choosen user
    list_answered_form = app.get_all_forms_names(choosen_user)
    selected_form = st_historic.show_choice_form(list_answered_form, is_admin=True)
    if not selected_form:  # if no form selected, don't show the rest
        return

    # get the list with all previous answers contained in the form
    previous_answers = app.get_list_answers(selected_form) + [["end"]]
    end = False
    i = 0
    while not end:
        list_answers = previous_answers[:i]
        next_question = app.get_next_question(list_answers)
        st_historic.show_question_as_admin(next_question, previous_answers[i])
        end = next_question["question_label"] == "end"
        i += 1
    list_bests_ais = app.calcul_best_ais(N_BEST_AI, previous_answers[:-1])
    st_historic.show_best_ai(list_bests_ais)


def main() -> None:
    """
    This is the code used to show the previous form completed by an User
    Different usage if User or Admin
    """
    st_historic = HistoricStreamlit()
    app = Application()
    username = st_historic.username
    if not username:
        return

    # Connected as an User
    if username != "Admin":
        historic_user(username, st_historic, app)
    # Connected as an Admin
    else:
        historic_admin(st_historic, app)


if __name__ == "__main__":
    main()
