import json
import pandas as pd
import base64
import io

from langchain_openai import ChatOpenAI
from langchain_google_vertexai.vision_models import VertexAIImageGeneratorChat
from PIL import Image

def geothermal_permits(location):

    human_prompt = f"What local and state permits are needed for a residential heat pump system in {location}?"
    system_prompt = "You are a helpful assistant that can answer a human's question about local permitting laws for geothermal heatpump systems."
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    messages = [
        ("system", system_prompt),
        ("human", human_prompt)
    ]
    generated_text = llm.invoke(messages).content

    return generated_text


def geothermal_incentives(location):

    # IRA credits (2023 ammendment) and local, utility (EnergyStar, ConEd), state and federal incentives 
    human_prompt = f"What federal, state and local tax incentives are available with the installation of a heat pump system in {location}?"
    system_prompt = "You are a helpful assistant that can answer a human's question about tax incentives for geothermal heatpump systems."
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    messages = [
        ("system", system_prompt),
        ("human", human_prompt)
    ]
    generated_text = llm.invoke(messages).content

    return generated_text

def decarbonization_penalities(location):

    human_prompt = f"What federal, state and local penalties will be levied for not de-carbonizing a building by a certain date in {location}?"
    system_prompt = "You are a helpful assistant that can answer a human's question about penalities for not de-carbonizing buildings in various locales."
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    messages = [
        ("system", system_prompt),
        ("human", human_prompt)
    ]
    generated_text = llm.invoke(messages).content

    return generated_text

def financial_statement_parse(document):

    system_prompt = "You are an expert accountant that can read and understand income statements containing different types of line items and account codes."
    human_prompt = f"""
        Can you extract all of the line items in the following financial statement?  
        Group the list according to category and sub-category found in the statement for revenue, income, expense and profit.
        Extract the time periods displayed in the columns of the statement.
        Extrct the value for specific sub-cagtegories and time periods
        Return results as a single JSON array with each element containing the category, sub-category, time period and value.
        Do not wrap the json codes in JSON markers. No commentary./n/n 
        {document}?"""
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    messages = [
        ("system", system_prompt),
        ("human", human_prompt)
    ]
    generated_text = llm.invoke(messages).content
    generated_json = json.loads(generated_text)
    """
    line_items = []

    for r in generated_json:
        for key, value in r.items():
            for v in value:
                line_items.append({"category":key, "subcategory":v})

    """
    df = pd.DataFrame(generated_json)
    return df

def analyze_data(question, data):

    system_prompt = "You are a financial data analyst that can look at a table of summarized financial data to determine trends and outliers."
    human_prompt = f"""
        Can you review the dataset below and give a commentary that answers this question: {question}?
        Responses should be less than 50 words.
        DATA: \n
        {data}?"""
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    messages = [
        ("system", system_prompt),
        ("human", human_prompt)
    ]
    generated_text = llm.invoke(messages).content
    return generated_text

def financial_statement_map(categories):

    std_categories = [
        "Revenue",
        "Cost of Goods Sold",
        "Operating Expenses",
        "Income",
        "Profit"
    ]

##########################################
## CREATE SOCIAL MEDIA POSTS AND IMAGES ##
##########################################

def generate_post(topic):
    """Generate a LinkedIn post using OpenAI's API"""

    llm = ChatOpenAI(
        model="gpt-4.5-preview",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    prompt = f"Create an engaging LinkedIn post about: {topic}. Keep it professional and insightful with a hint of personality.  It should be under 200 words.  Include a title with emojis.  Include references and their URLs."
    messages=[{"role": "system", "content": "You are an expert LinkedIn content writer."},
        {"role": "user", "content": prompt}]
 
    generated_text = llm.invoke(messages).content

    return generated_text

def generate_image_prompt(post):
    """Generate a prompt that can be used to create an image"""

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    prompt = f"Create an detailed description for an image that accompanies this LinkedIn post: {post}. No commentary."
    messages=[{"role": "system", "content": "You are a creative expert than can write detailed descriptions for photo reaslitic images that illustrate the theme of LinkedIn posts."},
        {"role": "user", "content": prompt}]
 
    generated_text = llm.invoke(messages).content

    return generated_text

def generate_image(image_prompt):

    # Create Image Gentation model Object
    generator = VertexAIImageGeneratorChat()
    response = generator.invoke(image_prompt)
    generated_image = response.content[0]
    img_base64 = generated_image["image_url"]["url"].split(",")[-1]

    img = Image.open(io.BytesIO(base64.decodebytes(bytes(img_base64, "utf-8"))))

    return img

def generate_image_caption(post):
    """Generate an image captiobn that goes with the post"""

    llm = ChatOpenAI(
        model="gpt-4.5-preview",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    prompt = f"Create a short and compelling caption that summarizes this LinkedIn post: {post}. The caption should be 15-20 words.  No commentary."
    messages=[{"role": "system", "content": "You are a creative writer that creates captions for images that go with LinkedIn posts."},
        {"role": "user", "content": prompt}]
 
    generated_text = llm.invoke(messages).content

    return generated_text