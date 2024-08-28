import uuid
import pandas as pd
import json
import os

from pypdf import PdfReader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import Docx2txtLoader

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain

from utils.connectors import bq_load_from_df

# os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

class Loaders:
    def __init__(self, uploaded_file, friendly_name):

        self.upload_file = uploaded_file
        self.upload_file_name = uploaded_file.name
        self.friendly_name = friendly_name
        self.upload_file_type = uploaded_file.type
        self.upload_file_path = f'docs/tmp_{self.upload_file_name}'
        self.upload_file_data = uploaded_file.read()
        self.upload_file_id = str(uuid.uuid4())

        
    def load_document(self):
        if self.upload_file_type == 'text/plain':
            # save file locally
            with open(self.upload_file_path, 'wb') as uf:
                uf.write(self.upload_file_data)

            loader = TextLoader(self.upload_file_path)
            self.loader_docs = loader.load()

        elif self.upload_file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            # save file locally
            with open(self.upload_file_path, 'wb') as uf:
                uf.write(self.upload_file_data)

            loader = Docx2txtLoader(self.upload_file_path)
            self.loader_docs = loader.load()

        elif self.upload_file_type == 'application/pdf':
            # save file locally
            with open(self.upload_file_path, 'wb') as uf:
                uf.write(self.upload_file_data)

            reader = PdfReader(self.upload_file_path)
            extract_images = False if len(reader.pages[0].extract_text()) > 0 else True

            loader_message = "Loading document with OCR..." if extract_images else "Loading document..."
            loader = PyPDFLoader(self.upload_file_path, extract_images=extract_images)
            self.loader_docs = loader.load()

        elif self.upload_file_type == 'application/json':
            docs = json.loads(self.upload_file.getvalue())
            self.docs_df = pd.DataFrame(docs)

    def process_document(self, selected_columns=[]):

        if self.upload_file_type == 'application/json':

            json_df = self.docs_df[selected_columns]
            json_df['page_content'] = json_df.apply(lambda x: '\n'.join([selected_columns[i]+': '+x[i] for i in range(0, len(x))]), axis=1)
            json_df['page'] = json_df.index
            json_df['metadata'] = json_df['page'].apply(lambda x: {'page':x})

            self.docs = json_df.to_dict(orient='records')

        else:
            if len(self.loader_docs) == 1:
                self.loader_docs[0].metadata['page'] = 0

            self.docs = []
            for d in self.loader_docs:
                self.docs.append({'page':d.metadata['page'], 'page_content':d.page_content})

    def split_document(self, split_type):

        if split_type == 'semantic':
            text_splitter = SemanticChunker(
                OpenAIEmbeddings(), 
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=0.1,
                # number_of_chunks=30
            )

        else:
            # split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=200
            )

        splits_text = []

        for d in self.docs:
            page_content = d['page_content']
            page = d['page']

            splits = text_splitter.create_documents([page_content])
            splits_text.extend([{'id': self.upload_file_id, 'source':self.upload_file_name, 'page':page, 'embedding_type':'details', 'split_type':split_type, 'chunk': d.dict()['page_content']} for d in splits])

        self.df = pd.DataFrame(splits_text)

    def create_embeddings(self):

        # create embeddings
        embed = OpenAIEmbeddings(model="text-embedding-3-large")

        vectors = embed.embed_documents(self.df['chunk'])
        self.df['vectors'] = pd.Series(vectors).to_numpy()
        self.df = self.df.reset_index()

    def summarize_document(self):
        # summarize document using map-reduce
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Map
        map_template = """The following is a set of documents
        {docs}
        Based on this list of docs, please identify the main themes in 300 or fewer words
        Helpful Answer:"""
        map_prompt = PromptTemplate.from_template(map_template)
        map_chain = LLMChain(llm=llm, prompt=map_prompt)
        self.summary = map_chain.run(self.docs)

    def load_to_database(self):

        # load embeddings to big query
        bq_load_from_df(self.df, "gristmill5.rag_test.embeddings")

        # load document contents and summary to big query
        docs_df = pd.DataFrame([[self.upload_file_id, self.friendly_name, self.upload_file_name, self.upload_file_type, self.upload_file_data, self.summary]], columns=['id', 'name', 'filename', 'filetype', 'contents', 'summary'])
        bq_load_from_df(docs_df, "gristmill5.rag_test.documents")

        # delete loaded document
        if os.path.exists(self.upload_file_path):
            os.remove(self.upload_file_path)

