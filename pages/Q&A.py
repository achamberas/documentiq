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
SELECT distinct source
FROM `rag_test.embeddings`
"""
sources_df = bq_conn(sql)
source_list = list(sources_df['source'])

source = st.multiselect('source', options=source_list)
query = st.text_input("Query", placeholder="Enter a question")
words = st.number_input("Words", value=200)
similarity = st.slider("Similarity", value=0.25, min_value=0.1, max_value=1.0, format="%f")

if len(query) > 0:

    route_type = router.invoke({"question": query}).datasource
    route_type = 'details'

    with st.spinner('Fetching ' + route_type + '...'):

        query = query.replace("'", "\\'")
        embed = OpenAIEmbeddings(model="text-embedding-3-large")
        vector = embed.embed_documents([query])

        sql = f"""
            select * 
            from `rag_test.embeddings` 
            where source in UNNEST({source})
            and embedding_type = '{route_type}'
        """

        data = bq_conn(sql)

        # Calculate cosine similarities between the query vector and the dataset
        vectors = np.array(data['vectors'].to_list())
        similarities = pd.DataFrame([s[0] for s in cosine_similarity(vectors, vector)], columns=['similarity'])
        data = pd.concat([data, similarities], axis=1)

        n = 5
        top_n_idx = np.argsort(similarities['similarity'])[-n:]
        references = data[['source', 'page', 'similarity', 'chunk']].iloc[top_n_idx]
        references = references[references['similarity'].gt(similarity)].sort_values(['similarity'], ascending=False)

        if len(data) > 0:

            chunks = "\n".join(list(references['chunk']))
            human_prompt = f"Answer this question in less than {words} words:\n\n {query} \n\n by using these blocks of text: \n\n{chunks}"
            system_prompt = "You are a helpful assistant that can answer a human's question by summarizing blocks of text.  You will format answers in markdown format."

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


