import pandas as pd
import streamlit as st
import pandas_gbq as pdgbq
import os
import json

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import Docx2txtLoader
# from langchain_google_community import BigQueryLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings

from google.oauth2 import service_account
from google.cloud import bigquery

from utils.connectors import *
from utils.configs import *

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# page_layout(title='Home')

def update_db(key, df):
    if key in st.session_state:

        deleted_rows = st.session_state[key]['deleted_rows']

        if len(deleted_rows)>0:
            deleted_docs = [df['source'][x] for x in deleted_rows]
            deleted_list = "','".join(deleted_docs)

            sql = f'DELETE FROM `rag_test.document_chunks` where source in (\'{deleted_list}\')'
            delete_chunks = bq_conn(sql)

            sql = f'DELETE FROM `rag_test.embeddings` where source in (\'{deleted_list}\')'
            delete_embeddings = bq_conn(sql)

            st.toast(f'Deleted {deleted_docs} from database.')

def main():
    st.title('Documents')

    # display loaded documents

    st.write('Loaded Documents')

    sql = """
    SELECT distinct source
    FROM `rag_test.embeddings`
    """
    
    sources_df = bq_conn(sql)
    st.data_editor(sources_df, key="source_table", num_rows="dynamic", use_container_width=True, hide_index=True, height=400, on_change=update_db("source_table", sources_df))
    # st.button("Update", on_click=update_db("source_table", sources_df))

    # Load new documents
    st.write('Load New Documents')

    uploaded_file = st.file_uploader("Choose a file",type=['pdf','json', 'txt', 'doc', 'docx'])
    if uploaded_file is not None:

        upload_file_name = uploaded_file.name

        upload_file_path = f'docs/tmp_{upload_file_name}'
        upload_file_data = uploaded_file.read()

        with st.form("load_form"):

            if uploaded_file.type == 'text/plain':
                # save file locally
                with open(upload_file_path, 'wb') as uf:
                    uf.write(upload_file_data)

                loader = TextLoader(upload_file_path)
                loader_docs = loader.load()

                docs = []
                for d in loader_docs:
                    docs.append({'page':0, 'page_content':d.page_content})

            elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                # save file locally
                with open(upload_file_path, 'wb') as uf:
                    uf.write(upload_file_data)

                loader = Docx2txtLoader(upload_file_path)
                loader_docs = loader.load()

                docs = []
                for d in loader_docs:
                    docs.append({'page':0, 'page_content':d.page_content})

            elif uploaded_file.type == 'application/pdf':
                # save file locally
                with open(upload_file_path, 'wb') as uf:
                    uf.write(upload_file_data)

                from pypdf import PdfReader
                reader = PdfReader(upload_file_path)
                extract_images = False if len(reader.pages[0].extract_text()) > 0 else True

                loader = PyPDFLoader(upload_file_path, extract_images=extract_images)
                loader_docs = loader.load()

                docs = []
                for d in loader_docs:
                    docs.append({'page':d.metadata['page'], 'page_content':d.page_content})

            elif uploaded_file.type == 'application/json':
                docs = json.loads(uploaded_file.getvalue())
                df = pd.DataFrame(docs)

                st.multiselect(label='Select the keys from the JSON file that you\'d like included in the documents.', options=df.columns, key='json_keys')
                selected_columns = st.session_state['json_keys']
                df = df[selected_columns]
                df['page_content'] = df.apply(lambda x: '\n'.join([selected_columns[i]+': '+x[i] for i in range(0, len(x))]), axis=1)
                df['page'] = df.index
                df['metadata'] = df['page'].apply(lambda x: {'page':x})

                docs = df.to_dict(orient='records')

            submitted = st.form_submit_button("Submit")

            if submitted:
                with st.spinner('Processing document...'):

                    # split text into chunks
                    # split_type = 'text'
                    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    # splits_text = text_splitter.split_documents(docs)
                    # df = pd.DataFrame([[upload_file_name, s.metadata['page'], s.page_content] for s in splits_text], columns=['source', 'page', 'chunk'])

                    split_type = 'semantic'
                    text_splitter = SemanticChunker(
                        OpenAIEmbeddings(), 
                        breakpoint_threshold_type="percentile",
                        breakpoint_threshold_amount=0.1,
                        # number_of_chunks=30
                    )

                    splits_text = []
                    summary = ''

                    for d in docs:
                        page_content = d['page_content']
                        page = d['page']
                        summary = summary + page_content.replace("'", "\\'").replace('"', '\\"')

                        splits = text_splitter.create_documents([page_content])
                        splits_text.extend([{'id': upload_file_name + '-' + str(page), 'source':upload_file_name, 'page':page, 'chunk': d.dict()['page_content']} for d in splits])

                    df = pd.DataFrame(splits_text)
                    df['embedding_type'] = 'details'
                    df['split_type'] = split_type

                    # create embeddings
                    embed = OpenAIEmbeddings(model="text-embedding-3-large")

                    vectors = embed.embed_documents(df['chunk'])
                    df['vectors'] = pd.Series(vectors).to_numpy()
                    # df = df.convert_dtypes()
                    df = df.reset_index()

                    # load to big query
                    GOOGLE_PROJECT = 'gristmill5'
                    credentials = service_account.Credentials.from_service_account_file("creds/gristmill5-e521e2f08f35.json")
                    client = bigquery.Client(GOOGLE_PROJECT, credentials)
                    job_config = bigquery.LoadJobConfig(autodetect=True)
                    job = client.load_table_from_dataframe(df,"gristmill5.rag_test.embeddings",job_config=job_config).result()

                st.toast("Done!")

main()