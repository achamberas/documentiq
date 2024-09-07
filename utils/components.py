import streamlit as st

from utils.styles import *
from utils.auth import login, fetch_token, get_user_info, auth
from utils.connectors import *
from utils.configs import *
from utils.loaders import *

from dotenv import load_dotenv

# load .env file to environment variables
load_dotenv()

def set_form_step(action):
    if action == 'Next':
        st.session_state['current_step'] = st.session_state['current_step'] + 1
    if action == 'Back':
        st.session_state['current_step'] = st.session_state['current_step'] - 1

def doc_load_ui():
    with st.container(height=450, border=False):
        with st.container(height=390):
            if st.session_state['current_step'] == 1:
                st.session_state['doc_loader'] = None

                tab1, tab2, tab3 = st.tabs(["Local", "Web", "Clipboard"])
                with tab1:
                    st.subheader("Load Local Files")
                    with st.container():
                        uploaded_file = st.file_uploader("Choose a file",type=['pdf','json', 'txt', 'docx'])
                with tab2:
                    st.subheader("Load Web Data")
                    with st.container():
                        web_url = st.text_input('Enter a url',key='web_url')
                    if web_url != '':
                        class uploaded_file:
                            name = web_url
                            type = 'html'
                with tab3:
                    st.subheader("Load from Clipboard")
                    with st.container():
                        clipboard = st.text_area('Paste from clipboard',height=220)
                    if clipboard != '':
                        class uploaded_file:
                            name = clipboard[0:15]
                            type = 'clipboard'
                            contents = clipboard

                st.session_state['uploaded_file'] = uploaded_file
        
            if st.session_state['current_step'] == 2:

                if hasattr(st.session_state['doc_loader'], 'summary'):
                    st.write('### Document Summary')
                    st.write( st.session_state['doc_loader'].summary)

                else:

                    uploaded_file = st.session_state['uploaded_file']

                    doc_loader = Loaders(uploaded_file)
                    doc_loader.load_document()

                    if doc_loader.upload_file_type == 'application/json':
                        options = doc_loader.docs_df.columns
                        st.multiselect(label='Select the keys from the JSON file that you\'d like included in the documents.', options=options, key='json_keys')
                        selected_columns = st.session_state['json_keys']
                    else:
                        selected_columns = []

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

                    st.session_state['doc_loader'] = doc_loader

            if st.session_state['current_step'] == 3:

                uploaded_file = st.session_state['uploaded_file']
                doc_loader = st.session_state['doc_loader']

                save_container = st.container(border=False)

                friendly_name = save_container.text_input(label='Name', value=uploaded_file.name)

        form_footer_container = st.empty()
        with form_footer_container.container():
            
            disable_back_button = True if st.session_state['current_step'] == 1 else False
            disable_next_button = False if st.session_state['uploaded_file'] else True
            
            form_footer_cols = st.columns([6,1,1])

            form_footer_cols[1].button('Back',on_click=set_form_step,args=['Back'],disabled=disable_back_button)

            if st.session_state['current_step'] < 3:
                form_footer_cols[2].button('Next',on_click=set_form_step,args=['Next'],disabled=disable_next_button)
            else:
                save_button = form_footer_cols[2].button('Save')
                if save_button:
                    with save_container:
                        with st.spinner('Saving to database...'):
                            doc_loader.load_to_database(friendly_name)
                            st.success("Done!")
                            st.session_state['current_step'] == 1
                            st.session_state['doc_loader'] = None
                            st.rerun()
