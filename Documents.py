import streamlit as st

from utils.auth import login, fetch_token, get_user_info, auth
from utils.connectors import *
from utils.configs import *
from utils.loaders import *

from dotenv import load_dotenv

# load .env file to environment variables
load_dotenv()

# page_layout(title='Home')

def update_db(key, df):
    if key in st.session_state:

        deleted_rows = st.session_state[key]['deleted_rows']

        if len(deleted_rows)>0:
            deleted_docs = [df['id'][x] for x in deleted_rows]
            deleted_list = "','".join(deleted_docs)

            sql = f'DELETE FROM `rag_test.embeddings` where id in (\'{deleted_list}\')'
            delete_embeddings = bq_conn(sql)

            sql = f'DELETE FROM `rag_test.documents` where id in (\'{deleted_list}\')'
            delete_embeddings = bq_conn(sql)

            st.toast(f'Deleted {deleted_docs} from database.')

def main():
    st.title('Documents')

    # display loaded documents

    st.write('Loaded Documents')

    sql = """
    SELECT id, name
    FROM `rag_test.documents`
    """

    sources_df = bq_conn(sql)
    st.data_editor(sources_df['name'], key="source_table", num_rows="dynamic", use_container_width=True, hide_index=True, height=400, on_change=update_db("source_table", sources_df))

    # Load new documents
    st.write('Load New Documents')

    uploaded_file = st.file_uploader("Choose a file",type=['pdf','json', 'txt', 'docx'])
    if uploaded_file is not None:

        with st.form("load_form"):

            friendly_name = st.text_input(label='Name', value=uploaded_file.name)

            doc_loader = Loaders(uploaded_file, friendly_name)
            doc_loader.load_document()

            if doc_loader.upload_file_type == 'application/json':
                options = doc_loader.docs_df.columns
                st.multiselect(label='Select the keys from the JSON file that you\'d like included in the documents.', options=options, key='json_keys')
                selected_columns = st.session_state['json_keys']
            else:
                selected_columns = []

            submitted = st.form_submit_button("Submit")

            if submitted:
                with st.spinner('Loading document...'):
                    doc_loader.process_document(selected_columns)
                with st.spinner('Splitting document...'):
                    split_type = 'semantic'
                    doc_loader.split_document(split_type)

                with st.spinner('Creating embeddings...'):
                    doc_loader.create_embeddings()

                with st.spinner('Summarizing document...'):
                    doc_loader.summarize_document()
                    st.write('### Document Summary')
                    st.write(doc_loader.summary)

                with st.spinner('Loading to database...'):
                    doc_loader.load_to_database()

                st.success("Done!")

auth()
main()