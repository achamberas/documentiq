import os
import streamlit as st

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI


class RouteQuery(BaseModel):
    datasource: Literal["summary", "details"] = Field(
        ...,
        description="Given a user question choose whether to summarize a document or answer specific questions about details in the document",
    )

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

structured_llm = llm.with_structured_output(RouteQuery)

system = """
You are an expert at routing a user question to the appropriate query engine.
Based on the context of the question, route it to a summary query engine or detail engine.
"""
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

router = prompt | structured_llm