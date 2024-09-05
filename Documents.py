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

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Local", "Web", "Clipboard", "API", "Database", "Existing"])

    with tab1:
        st.subheader("Load Local Files")
        with st.container(height=400):
            uploaded_file = st.file_uploader("Choose a file",type=['pdf','json', 'txt', 'docx'])
    with tab2:
        st.subheader("Load Web Data")
        with st.container(height=400):
            web_url = st.text_input('Enter a url',key='web_url')
        if web_url != '':
            class uploaded_file:
               name = web_url
               type = 'html'
    with tab3:
        st.subheader("Load from Clipboard")
        with st.container(height=400):
            clipboard = st.text_area('Paste from clipboard',height=335)
        if clipboard != '':
            class uploaded_file:
               name = clipboard[0:15]
               type = 'clipboard'
               contents = clipboard
    with tab4:
        st.subheader("Load from API")
        with st.container(height=400):
            api_action = st.selectbox('action',key='api_action', options=['GET', 'POST'])
            api_url = st.text_input('host',key='api_url')
            api_header = st.text_input('header',key='api_header')
            api_body = st.text_input('body',key='api_body')
    with tab5:
        st.subheader("Load Database Tables")
        with st.container(height=400):
            db_type = st.selectbox('database',key='db_type', options=['BigQuery', 'Snowflake', 'Postgres', 'MySQL', 'SQL Server'])
            db_host = st.text_input('host',key='db_host')
            db_username = st.text_input('username',key='db_username')
            db_password = st.text_input('password',key='db_password')
    with tab6:
        # display loaded documents
        st.subheader("Loaded Documents")
        sql = """
        SELECT id, name
        FROM `rag_test.documents`
        ORDER BY name
        """

        sources_df = bq_conn(sql)
        with st.container(height=400):
            st.write('Previously loaded documents')
            st.data_editor(sources_df['name'], key="source_table", num_rows="dynamic", use_container_width=True, hide_index=True, height=320, on_change=update_db("source_table", sources_df))

    if uploaded_file is not None or web_url != '' or clipboard != '':

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