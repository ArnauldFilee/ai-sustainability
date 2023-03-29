from gremlin_python import statics
from gremlin_python.driver import client, serializer
import streamlit as st
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
        list_weight = self.run_gremlin_query("g.E('"+edge_id+"').properties('list_coef').value()")[0].split(', ')
        return list_weight
    
    def calcul_weight(self, list_edges):
        return list_edges

    def save_answers(self, answers, username):
        """
        Save answers in db
        Answers = list of list of dict {id: , text:}
        """
        print('DEBUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUG')

        # self.run_gremlin_query("g.addV('user').property('partitionKey', 'Answer').property('id', '"+username+"')")
        for list_answer in answers:
            for dict_answer in list_answer:   
                actual_node = self.run_gremlin_query("g.E('"+str(dict_answer['id'])+"').outV()")[0]
                print('Question:', actual_node['properties']['text'][0]['value'])
                print('Actual node id: ', actual_node['id'])
                next_question_node = self.run_gremlin_query("g.E('"+dict_answer['id']+"').inV()")[0]
                print('Next node id: ', next_question_node['id'])
                new_node_id = 'answer'+actual_node['id']
                next_new_node_id = 'answer'+next_question_node['id']
                new_node_id_exist = self.run_gremlin_query("g.V('"+new_node_id+"').id()")
                next_new_node_id_exist = self.run_gremlin_query("g.V('"+next_new_node_id+"').id()")
                print('new_node_id_exist: ', new_node_id_exist)
                print('next_new_node_id_exist: ', next_new_node_id_exist)
                if not new_node_id_exist:
                    self.run_gremlin_query("g.addV('Answer').property('partitionKey', 'Answer').property('id', '"+new_node_id+"').property('question', '"+actual_node['properties']['text'][0]['value']+"').property('question_id', '"+actual_node['id']+"')")
                    print('If new_node_id created so id: ', self.run_gremlin_query("g.V('"+new_node_id+"').id()"))
                if not next_new_node_id_exist :
                    self.run_gremlin_query("g.addV('Answer').property('partitionKey', 'Answer').property('id', '"+next_new_node_id+"').property('question', '"+actual_node['properties']['text'][0]['value']+"').property('question_id', '"+actual_node['id']+"')")
                    print('If next_new_node_id created so id', self.run_gremlin_query("g.V('"+next_new_node_id+"').id()"))
                self.run_gremlin_query("g.V('"+new_node_id+"').addE('Answer').to(g.V('"+next_new_node_id+"')).property('answer', '"+dict_answer['text']+"').property('proposition_id', '"+dict_answer['id']+"')")
                print('answer added :', dict_answer['text'])
                print('-------------------------------------------------------------------------------------------------------------------------------')