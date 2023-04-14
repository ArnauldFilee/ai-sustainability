"""
This file is used to show the Historic page
"""
from typing import Generator

from decouple import config

from ai_sustainability.package_application.application import Application
from ai_sustainability.package_business.models import (
    Answer,
    AnswersList,
    FormAnswers,
    Username,
)
from ai_sustainability.package_user_interface.classes.class_historic import (
    HistoricStreamlit,
)
from ai_sustainability.package_user_interface.utils_streamlit import get_application

ADMIN_USERNAME = "Admin"  # TODO .env


def get_form_list_answers(
    *, app: Application, st_historic: HistoricStreamlit, list_answers: FormAnswers, previous_form_answers: FormAnswers
) -> Generator[AnswersList, None, None]:
    keep_going = True
    i = 0
    change_made = False
    while keep_going:
        next_question = app.get_next_question(list_answers)
        selected_answer = st_historic.ask_question_user(
            next_question, None if change_made else previous_form_answers[len(list_answers)]
        )
        if selected_answer is None:
            break
        keep_going = next_question.type != "end"
        if keep_going:
            yield selected_answer
            # If not already changed and name answer different from previous one and question's label is not Q_Open :
            # The form is modified and we do not fill it automatically with previous answers
            if (
                not change_made
                and list_answers[i][0].text != previous_form_answers[i][0].text
                and next_question.type != "Q_Open"
            ):
                change_made = True
        i += 1


def historic_user(username: Username, st_historic: HistoricStreamlit, app: Application) -> None:
    """
    Function used to show a form with the User view
    """
    list_answered_form = app.get_all_forms_names(username)
    selected_form = st_historic.show_choice_form(list_answered_form)
    if not selected_form:  # if none form selected, don't show the rest
        return

    # get the list with all previous answers contained in the form
    answer_end = Answer(answer_id="end", text="end", help_text="end", modif_crypted=False, list_coef=[])
    previous_form_answers = app.get_list_answers(username, selected_form) + FormAnswers([[answer_end]])
    # TODO change all the "answer", previous_answers, etc names to clarify this all

    keep_going = True
    list_answers: FormAnswers = FormAnswers([])
    i = 0
    change_made = False
    while keep_going:
        next_question = app.get_next_question(list_answers)
        selected_answer = st_historic.ask_question_user(
            next_question, None if change_made else previous_form_answers[len(list_answers)]
        )
        if selected_answer is None:
            return
        keep_going = next_question.type != "end"
        if keep_going:
            list_answers.append(selected_answer)
            # If not already changed and name answer different from previous one and question's label is not Q_Open :
            # The form is modified and we do not fill it automatically with previous answers
            if (
                not change_made
                and list_answers[i][0].text != previous_form_answers[i][0].text
                and next_question.type != "Q_Open"
            ):
                change_made = True
        i += 1

    # If the form is not finish, we wait the user to enter a new answer
    if next_question.type != "end":  # TODO change this condition to a function in Question class
        return

    # We ask the user to give us a name for the form (potentially a new one)
    new_form_name = st_historic.show_input_form_name(selected_form)
    if not new_form_name:
        return

    # If the name is already taken by an other form
    if app.check_form_exist(username, new_form_name) and new_form_name != selected_form:
        if st_historic.check_name_already_taken(username):
            return

    n_best_ai = int(config("NBEST_AI"))
    list_bests_ais = app.calcul_best_ais(n_best_ai, list_answers)
    st_historic.show_best_ai(list_bests_ais)
    if st_historic.show_submission_button():
        app.change_answers(
            list_answers, username, selected_form, new_form_name, list_bests_ais
        )  # TODO change name to save_answer and change the function in DbConnection


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
    selected_form_name = st_historic.show_choice_form(list_answered_form, is_admin=True)
    if not selected_form_name:  # if no form selected, don't show the rest
        return

    # get the list with all previous answers contained in the form
    proposition_end = Answer(answer_id="end", text="end", help_text="end", modif_crypted=False, list_coef=[])
    previous_form_answers = app.get_list_answers(choosen_user, selected_form_name) + FormAnswers([[proposition_end]])
    keep_going = True
    i = 0
    while keep_going:
        list_answers = previous_form_answers[:i]
        next_question = app.get_next_question(list_answers)
        st_historic.show_question_as_admin(next_question, previous_form_answers[i])
        keep_going = next_question.type != "end"
        i += 1
    list_bests_ais = app.get_best_ais(choosen_user, selected_form_name)
    st_historic.show_best_ai(list_bests_ais)


def main() -> None:
    """
    This is the code used to show the previous form completed by an User
    Different usage if User or Admin
    """
    # TODO create a render function
    st_historic = HistoricStreamlit()
    app = get_application()
    username = st_historic.username
    if not username:
        return

    # Connected as an User
    if username != ADMIN_USERNAME:
        historic_user(username, st_historic, app)
    # Connected as an Admin
    else:
        historic_admin(st_historic, app)


if __name__ == "__main__":
    main()
