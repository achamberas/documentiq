import streamlit as st
import pandas as pd
import numpy as np
import os

from langchain_openai.embeddings import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

from utils.connectors import *
from utils.routers import *

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

st.title('Q&A')

sql = """
SELECT id, name
FROM `rag_test.documents`
"""
sources_df = bq_conn(sql)
source_list = list(sources_df['name'])

sources = st.multiselect(
    'source', 
    options= range(len(source_list)),
    format_func=source_list.__getitem__,
)

source_ids = list(sources_df['id'].iloc[sources])
query = st.text_input("Query", placeholder="Enter a question")
words = st.number_input("Words", value=200)
similarity = st.slider("Similarity", value=0.25, min_value=0.1, max_value=1.0, format="%f")

if len(query) > 0:

    route_type = router.invoke({"question": query}).datasource

    with st.spinner('Fetching ' + route_type + '...'):

        if route_type == 'details':
            query = query.replace("'", "\\'")
            embed = OpenAIEmbeddings(model="text-embedding-3-large")
            vector = embed.embed_documents([query])

            sql = f"""
                select d.name, d.filename, e.* 
                from `rag_test.documents` d
                inner join `rag_test.embeddings` e
                    on d.id = e.id
                where d.id in UNNEST({source_ids})
            """

            data = bq_conn(sql)

            # Calculate cosine similarities between the query vector and the dataset
            vectors = np.array(data['vectors'].to_list())
            similarities = pd.DataFrame([s[0] for s in cosine_similarity(vectors, vector)], columns=['similarity'])
            data = pd.concat([data, similarities], axis=1)

            n = 5
            top_n_idx = np.argsort(similarities['similarity'])[-n:]
            references = data[['filename', 'page', 'similarity', 'chunk']].iloc[top_n_idx]
            references = references[references['similarity'].gt(similarity)].sort_values(['similarity'], ascending=False)

            chunks = "\n".join(list(references['chunk']))
            human_prompt = f"Answer this question in less than {words} words:\n\n {query} \n\n by using these blocks of text: \n\n{chunks}"
            system_prompt = "You are a helpful assistant that can answer a human's question by summarizing blocks of text.  You will format answers in markdown format."
        
        else:
            sql = f"""
                select d.filename, d.summary
                from `rag_test.documents` d
                where d.id in UNNEST({source_ids})
            """

            data = bq_conn(sql)
            references = data
            chunks = "\n".join(list(data['summary']))

            human_prompt = f"In less than {words} summarize this text: \n\n{chunks}"
            system_prompt = "You are a helpful assistant that can summarize blocks of text.  You will format answers in markdown format."

        if len(data) > 0:

            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                # api_key="...",  # if you prefer to pass api key in directly instaed of using env vars
                # base_url="...",
                # organization="...",
                # other params...
            )

            messages = [
                ("system", system_prompt),
                ("human", human_prompt)
            ]
            generated_text = llm.invoke(messages).content

            st.write('### Response:')
            st.write(generated_text)
            st.write('### References:')
            st.dataframe(references, use_container_width=True)
        else:
            st.write("### No results.")

    st.toast("Done!")


