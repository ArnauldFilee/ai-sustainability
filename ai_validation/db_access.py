"""
This file contains the class DbConnection, used to connect to the database and to run the queries
"""

from decouple import config
from gremlin_python import statics
from gremlin_python.driver import client, serializer

from ai_sustainability.package_business.models import Query, Username

FIRST_NODE_ID = "1"
END_TYPE = config("END_TYPE")
statics.load_statics(globals())


def connect(endpoint: str, database_name: str, container_name: str, primary_key: str) -> client.Client:
    return client.Client(
        "wss://" + endpoint + ":443/",
        "g",
        username="/dbs/" + database_name + "/colls/" + container_name,
        password=primary_key,
        message_serializer=serializer.GraphSONSerializersV2d0(),
    )


class DbAccess:
    """
    Class to manage the database Gremlin CosmosDB
    """

    def __init__(self) -> None:
        self.gremlin_client: client.Client = connect(
            endpoint="questions-db.gremlin.cosmos.azure.com",
            database_name="graphdb",
            container_name=config("DATABASENAME"),
            primary_key=config("PRIMARYKEY"),
        )

    def close(self) -> None:
        """
        Close the connection to the database
        """
        self.gremlin_client.close()

    def run_gremlin_query(self, query: Query) -> list:
        """
        Run a gremlin query

        Parameters :
            - query : the gremlin query to run (Exemple : Query("g.V()"))

        Return :
            - list of all result that correspond to the query
        """
        run = self.gremlin_client.submit(query).all()
        return run.result()

    def get_all_users(self) -> list[Username]:
        """
        Return all Username in the database
        """
        return self.run_gremlin_query(Query("g.V().hasLabel('user').id()"))

    def get_all_metrics(self, username: Username, form_name: str) -> list[str]:
        """
        Return all the needed metrics to evaluate a list of ai based on a completed form
        """
        list_metrics: list[str] = []
        node_id = f"{username}-answer{FIRST_NODE_ID}-{form_name}"
        query = Query(f"g.V('{node_id}')")
        node = self.run_gremlin_query(query)[0]
        while node["label"] != "end":
            query_edge = Query(f"g.V('{node['id']}').outE()")
            out_edge = self.run_gremlin_query(query_edge)[0]
            if "metric" in out_edge["properties"]:
                list_metrics += out_edge["properties"]["metric"].split(",")
            query = Query(f"g.V('{node['id']}').out()")
            node = self.run_gremlin_query(query)[0]
        return list_metrics
