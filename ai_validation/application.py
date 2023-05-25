"""File used for all application layer of the result part of the application"""


from typing import Optional, Tuple

from ai_validation.business import Business
from ai_validation.db_access import DbAccess
from ai_validation.mlflow_access import MlflowConnector


class Application:
    """Application layer"""

    def __init__(self) -> None:
        self.database = DbAccess()
        self.mlflow_connector = MlflowConnector()
        self.business = Business()

    def get_all_user(self) -> list[str]:
        return self.database.get_all_users()

    def get_metrics(self, username: str, form_name: str, replace_accuracy: bool = True) -> list[str]:
        # Use replace_accuracy if an "Accuracy" metric is log in the mlflow experience
        raw_metrics = self.database.get_all_metrics(username, form_name)
        return self.business.replace_accuracy(raw_metrics) if replace_accuracy else raw_metrics

    def get_experiment_from_user(self, selected_user: Optional[str]) -> Optional[Tuple[list[str], list[str]]]:
        return self.mlflow_connector.get_experiment(selected_user)

    def get_ai_from_experiment(self, selected_experiment_id: str, used_metric: list[str]) -> Optional[list]:
        """
        Function used to get all ai raked and there hyper parameters
        Return : Tuple(list:list[(ai_name:str, coef:float, param:str)], used_metric:list)
        """
        selected_experiment_name = self.mlflow_connector.get_experiment_name(selected_experiment_id)
        selected_experiment = selected_experiment_name.split("-")
        if len(selected_experiment) <= 2:
            return None
        run_page = self.mlflow_connector.get_run_page(selected_experiment_id)
        return self.business.rank_ais(run_page, used_metric)
