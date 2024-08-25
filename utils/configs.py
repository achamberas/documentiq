import streamlit as st

def page_layout(title='Home'):

    url_params = st.query_params()

    sidebar="expanded"

    if 'sidebar' in url_params:
        sidebar = url_params['sidebar'][0]

    st.set_page_config(
        initial_sidebar_state=sidebar,
        page_title="Four37 - " + title,
        page_icon="🌎",
    )

    margins_css = """
        <style>
            .main > div {
                padding-top: 0rem;
                padding-bottom: 0rem;
                padding-left: 0rem;
                padding-right: 0rem;
            }
        </style>
    """

    #st.markdown(margins_css, unsafe_allow_html=True)

    return