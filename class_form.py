import math
import heapq
import numpy as np
import streamlit as st
from gremlin_python import statics
from gremlin_python.driver import client, serializer

statics.load_statics(globals())

@st.cache_resource
def connect(endpoint, database_name, container_name, primary_key):
        return client.Client(
            'wss://' + endpoint + ':443/', 'g',
            username="/dbs/" + database_name + "/colls/" + container_name,
            password=primary_key,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )

class Form:
    
    def __init__(self, endpoint, database_name, container_name, primary_key):
        self.gremlin_client = connect(endpoint, database_name, container_name, primary_key)
    
    def run_gremlin_query(self, query):
        """
        Run a gremlin query
        
        Parameters :
            - query : the gremlin query to run (string) (Exemple : "g.V()")
        """
        run = self.gremlin_client.submit(query).all()
        result = run.result()
        return result

    def close(self):
        """
        Close the connection to the database, must be called at the end of the program
        """
        self.gremlin_client.close()
    
    def add_question(self, node_id, modif_crypted):
        """
        Add question from db to form
        """
        q_type = self.run_gremlin_query("g.V('"+node_id+"').label()")
        if q_type[0] == "Q_Open":
            next_node_id, answer, modif_crypted = self.add_open_question(node_id, modif_crypted)
        elif q_type[0] == "Q_QCM":
            next_node_id, answer, modif_crypted = self.add_qcm_question(node_id, modif_crypted)
        elif q_type[0] == "Q_QRM":
            next_node_id, answer, modif_crypted = self.add_qrm_question(node_id, modif_crypted)
        elif q_type[0] == "Q_QCM_Bool":
            next_node_id, answer, modif_crypted = self.add_qcm_bool_question(node_id, modif_crypted)
        elif q_type[0] == "end":
            next_node_id = "end"
            answer = None
        else:
            print("Error: unknown question type")
        return next_node_id, answer, modif_crypted
    
    def add_open_question(self, node_id, modif_crypted):
        """
        Add open question from db to form
        """
        question = self.get_text_question(node_id)
        next_node_id = self.run_gremlin_query("g.V('"+node_id+"').outE().inV().id()")[0]
        answer = st.text_area(label=question, height=100,label_visibility="visible")
        if not answer:
            answer = None
            next_node_id = None
        answer = [{
            "text": answer,
            "id": self.run_gremlin_query("g.V('"+node_id+"').outE().id()")[0],
        }]
        return next_node_id, answer, modif_crypted
    
    def add_qcm_question(self, node_id, modif_crypted):
        """
        Add qcm question from db to form
        """
        question = self.get_text_question(node_id)
        options = ['<Select an option>']
        propositions, props_ids = self.get_propositions_of_question(node_id, modif_crypted)
        for option in propositions:
            options.append(option)
        answer = st.selectbox(label=question, options=options, index=0)
        if answer == '<Select an option>':
            answer = None
            next_node_id = None
        else:
            index = propositions.index(answer)
            next_node_id = self.run_gremlin_query("g.E('"+props_ids[index]+"').inV().id()")[0]
            text = self.run_gremlin_query("g.E('"+props_ids[index]+"').properties('text')")[0]
            answer = [{"id": props_ids[index], 'text': text['value']}]
        return next_node_id, answer, modif_crypted

    def add_qrm_question(self, node_id, modif_crypted):
        """
        Add qrm question from db to form
        """
        question = self.get_text_question(node_id)
        options = []
        propositions, props_ids = self.get_propositions_of_question(node_id, modif_crypted)
        for option in propositions:
            options.append(option)
        answers = st.multiselect(label=question, options=options, default=None)
        answers_returned = []
        if answers == []:
            answers = None
            next_node_id = None
        else:
            next_node_id = self.run_gremlin_query("g.V('"+node_id+"').outE().inV().id()")[0]
            for answer in answers:
                index = propositions.index(answer)
                text = self.run_gremlin_query("g.E('"+props_ids[index]+"').properties('text')")[0]
                answers_returned.append({'id': props_ids[index], 'text': text['value']})
        return next_node_id, answers_returned, modif_crypted
    
    def add_qcm_bool_question(self, node_id, modif_crypted):
        """
        Add qcm bool question from db to form
        """
        question = self.get_text_question(node_id)
        options = ['<Select an option>']
        propositions, props_ids = self.get_propositions_of_question(node_id, modif_crypted)
        for option in propositions:
            options.append(option)
        answer = st.selectbox(label=question, options=options, index=0)
        if answer == '<Select an option>':
            answer = None
            next_node_id = None
        else:
            index = propositions.index(answer)
            next_node_id = self.run_gremlin_query("g.E('"+props_ids[index]+"').inV().id()")[0]
            text = self.run_gremlin_query("g.E('"+props_ids[index]+"').properties('text')")[0]
            modif_crypted = answer == 'Yes'
            answer = [{"id": props_ids[index], 'text': text['value']}]
        return next_node_id, answer, modif_crypted
    
    def get_text_question(self, node_id):
        """
        Get text of a question
        """
        question = self.run_gremlin_query("g.V('"+node_id+"').properties('text').value()")[0]
        return question

    def get_propositions_of_question(self, node_id, modif_crypted):
        """
        Get propositions of a question
        """
        propositions = []
        props_ids = []
        if modif_crypted:
            for edges in self.run_gremlin_query("g.V('"+node_id+"').outE().id()"):
                if self.run_gremlin_query("g.E('"+edges+"').properties('modif_crypted').value()")[0] == 'false':
                    props_ids.append(edges)
                    propositions.append(self.run_gremlin_query("g.E('"+edges+"').properties('text').value()")[0])
        else:
            propositions = self.run_gremlin_query("g.V('"+node_id+"').outE().properties('text').value()")
            props_ids = self.run_gremlin_query("g.V('"+node_id+"').outE().id()")
        
        return propositions, props_ids
    
    def get_weight(self, edge_id):
        """
            Get the list_coef from the edge with edge_id id
        """
        list_weight = self.run_gremlin_query("g.E('"+edge_id+"').properties('list_coef').value()")[0].split(", ")
        for i in range(len(list_weight)):
            list_weight[i] = float(list_weight[i])
        return list_weight
    
    def calcul_best_AIs(self, nbAI, answers):
        """
            Return the nbAI best AIs from a list of answers
        """
        list_AI = self.run_gremlin_query("g.V('1').properties('list_AI')")[0]['value'].split(",")
        coef_AI = [1] * len(list_AI)
        for i in range(len(answers)):
            for j in range(len(answers[i])):
                list_coef = self.get_weight(answers[i][j]["id"])
                coef_AI = np.multiply(coef_AI, list_coef)
        # We put all NaN value to -1
        for i in range(len(coef_AI)):
            if coef_AI[i] != coef_AI[i]:  # if a NaN value is encounter, we put it to -1
                coef_AI[i] = -1
        best = list(heapq.nlargest(nbAI, np.array(coef_AI)))
        # We put the nbAI best AI in list_bests_AIs
        list_bests_AIs = []
        for i in range(nbAI):
            if best[i] > 0:
                index = list(coef_AI).index(best[i])
                list_bests_AIs.append(list_AI[index])
        self.show_best_AI(list_bests_AIs)
        return list_bests_AIs
    
    def show_best_AI(self, list_bests_AIs):
        """
            Method used to show the n best AI obtained after the user has completed the Form
            The number of AI choosen is based on the nbAI wanted by the user and the maximum of available AI for the use of the user
            (If there is only 3 AI possible, but the user asked for 5, only 3 will be shown)
        """
        if len(list_bests_AIs) > 0:
            st.subheader("There is "+str(len(list_bests_AIs))+" IA corresponding to your specifications, here they are in order of the most efficient to the least:", anchor=None)
            for i in range(len(list_bests_AIs)):
                st.caption(str(i+1)+") "+list_bests_AIs[i])
        else:
            st.subheader("There is no AI corresponding to your request, please make other choices in the form", anchor=None)
        return None

    def save_answers(self, answers, username):
        """
        Save answers in db
        """
        self.run_gremlin_query("g.addV('user').property('partitionKey', 'Answer').property('id', '"+username+"')")
        previous_node_id = username
        for answer in answers:
            if type(answer) == dict:
                vertex = self.run_gremlin_query("g.E('"+answer['id']+"').outV()")[0]
                next_node_id = 'answer'+vertex['id']
                self.run_gremlin_query("g.addV('Answer').property('partitionKey', 'Answer').property('id', '"+next_node_id+"').property('question', '"+vertex['properties']['text'][0]['value']+"').property('question_id', '"+vertex['id']+"')")
                self.run_gremlin_query("g.V('"+previous_node_id+"').addE('answer').to(g.V('"+next_node_id+"')).property('answer', '"+answer['text']+"').property('proposition_id', '"+answer['id']+"')")
            elif type(answer) == list:
                i = 0
                for ans in answer:
                    vertex = self.run_gremlin_query("g.E('"+ans+"').outV()")[0]
                    next_node_id = 'answer'+vertex['id']
                    if i == 0:
                        self.run_gremlin_query("g.addV('Answer').property('partitionKey', 'Answer').property('id', '"+next_node_id+"').property('question', '"+vertex['properties']['text'][0]['value']+"').property('question_id', '"+vertex['id']+"')")
                    self.run_gremlin_query("g.V('"+previous_node_id+"').addE('answer').to(g.V('"+next_node_id+"')).property('proposition_id', '"+ans+"').property('answer', '"+self.run_gremlin_query("g.E('"+ans+"').properties('text').value()")[0]+"')")
                    i += 1
                    
            else:
                vertex = self.run_gremlin_query("g.E('"+answer+"').outV()")[0]
                next_node_id = 'answer'+vertex['id']
                self.run_gremlin_query("g.addV('Answer').property('partitionKey', 'Answer').property('id', '"+next_node_id+"').property('question', '"+vertex['properties']['text'][0]['value']+"').property('question_id', '"+vertex['id']+"')")
                self.run_gremlin_query("g.V('"+previous_node_id+"').addE('answer').to(g.V('"+next_node_id+"')).property('proposition_id', '"+answer+"').property('answer', '"+self.run_gremlin_query("g.E('"+answer+"').properties('text').value()")[0]+"')")

            previous_node_id = next_node_id
