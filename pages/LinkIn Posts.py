import streamlit as st
import pandas as pd

from utils.agents import *
from utils.tools import *
from utils.styles import *
# from utils.auth import auth

from dotenv import load_dotenv

# load .env file to environment variables
load_dotenv()

linkedin_client_id = os.getenv('LINKEDIN_CLIENT_ID')
linkedin_client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
linkedin_refresh_token = os.getenv('LINKED_IN_REFRESH_TOKEN')

# add_styles()
# auth()

if 'topic' not in st.session_state:
    st.session_state['topic'] = ''
if 'post' not in st.session_state:
    st.session_state['post'] = ''
if 'caption' not in st.session_state:
    st.session_state['caption'] = ''
if 'image_caption' not in st.session_state:
    st.session_state['image_caption'] = ''


l,r = st.columns([4,1])
with l:
    st.title('LinkedIn Posts')
with r:
    st.container(height=10, border=False)
    if st.session_state['post'] != '' and 'img' in st.session_state:
        if st.button('Post', use_container_width=True, type='primary'):
            with st.spinner('Posting to LinkedIn...'):
                post_to_linkedin(st.session_state['post'], st.session_state['img'], linkedin_client_id, linkedin_client_secret, linkedin_refresh_token)
                st.toast('Posted to LinkedIn!')

st.divider()

left_col, right_col = st.columns([1,1])

with left_col:
    topic = st.text_input('Enter a topic', placeholder='Enter a topic', label_visibility="collapsed")
    if topic:
        with st.spinner('Writing...'):

            if st.session_state['topic'] != topic:
                st.session_state['topic'] = topic
                st.session_state['post'] = generate_post(topic)

            # display post in text box for editing
            post = st.text_area('Post', st.session_state['post'], height=610, label_visibility="collapsed", key='post_edit')
            if st.session_state['post'] != st.session_state['post_edit']:
                st.session_state['post'] = st.session_state['post_edit']

with right_col:
    # display buttton to create image if there is post content
    if st.session_state['post'] != '':
        if st.button("Generate Image", use_container_width=True, type='primary'):
            with st.spinner('Creating image...'):
                # create caption
                st.session_state['caption'] = generate_image_caption(st.session_state['post'])

                # create image
                image_prompt = generate_image_prompt(st.session_state['post'])
                st.session_state['orig_img'] = generate_image(image_prompt)
                st.session_state['img'] = st.session_state['orig_img']

        if 'orig_img' in st.session_state:
            # allow exposure adjustment
            if st.slider('Adjust image exposure', 0, 200, 100, step=1, key='exposure'):
                st.session_state['img'] = adjust_image_exposure(st.session_state['orig_img'], st.session_state['exposure'])

            # place pre-created image caption text box
            st.text_input('Image Capation', st.session_state['caption'], key='image_caption')
            # st.session_state['caption'] = st.session_state['image_caption']

            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.checkbox('Add caption'):
                    st.session_state['img'] = text_on_image(st.session_state['img'], st.session_state['image_caption'], st.session_state['margin'], st.session_state['font_size'])
            with col2:
                st.number_input('Margin', 0, 100, 10, key='margin')
            with col3:
                st.number_input('Font Size', 0, 200, 60, key='font_size')

            st.image(st.session_state['img'], use_column_width=True)


