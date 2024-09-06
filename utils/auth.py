import os
import urllib.parse
import streamlit as st

from authlib.integrations.requests_client import OAuth2Session
from google.oauth2 import id_token
from google.auth.transport import requests
from streamlit_js_eval import streamlit_js_eval

from dotenv import load_dotenv
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_AUTHORIZATION_URL = os.getenv("GOOGLE_AUTHORIZATION_URL")
GOOGLE_TOKEN_URL = os.getenv("GOOGLE_TOKEN_URL")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GOOGLE_REVOKE_TOKEN_URL = os.getenv("GOOGLE_REVOKE_TOKEN_URL")

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def login():
    session = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=['openid', 'email', 'profile'],
    )
    authorization_url, state = session.create_authorization_url(GOOGLE_AUTHORIZATION_URL)
    return authorization_url


def fetch_token():
    url_params = st.query_params
    param_string = '&'.join([k+'='+urllib.parse.quote_plus(url_params[k]) for k in url_params])
    authorization_response = REDIRECT_URI + '/?' + param_string
    state = url_params['state']
    
    session = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        state=state,  # Retrieve the stored state
    )

    # Fetch the token using the authorization response
    token = session.fetch_token(GOOGLE_TOKEN_URL, authorization_response=authorization_response)

    return token, state

def get_user_info(token):
    try:
        id_info = id_token.verify_oauth2_token(token['id_token'], requests.Request(), GOOGLE_CLIENT_ID)
        return id_info
    except:
        st.session_state.clear()
        auth()

def revoke_token(token, state):
    session = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        state=state
    )
    session.revoke_token(GOOGLE_TOKEN_URL, token=token['access_token'])
    return

def auth():

    if 'token' not in st.session_state and not(st.query_params.get('code')) and 'code' not in st.session_state:
        authorization_url = login()
        container = st.container(border=True)

        container.html(f"""
            <html>
                <div style="text-align: center;">
                    <img src="https://static.wixstatic.com/media/1e9daa_c5683a65a4104970b975725eb64fc0f7~mv2.png/v1/fill/w_93,h_93,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/logo.png", width=100>
                    <h4>Log in to continue</h4>
                    <hr>
                    <div style="text-align: center;">
                        <a href="{authorization_url}" style="border:1px solid #c3c3c3; color:black; padding:10px 125px; text-align:center; text-decoration:none; display:inline-block;" target="_self">
                            <img src="https://lh3.googleusercontent.com/COxitqgJr1sJnIDe8-jiKhxDx1FrYbtRHKJ9z_hELisAlapwE9LUPh6fcXIfb5vwpbMl4xl9H9TRFPc5NOO8Sb3VSgIBrfRYvW6cUA", width=20/> 
                            <span>Google</span>
                        </a>
                    </div>
                    <hr>
                    <span style="color: #c3c3c3; font-size: small;">5 Grist Mill Road Acton, MA 01720</span>
                </div>
            </html>
        """)
        st.stop()
        
    elif 'token' not in st.session_state and st.query_params.get('code'):
        token, state = fetch_token()
        st.session_state['token'] = token
        st.session_state['state'] = state
        st.session_state['code'] = st.query_params.get('code')
        st.rerun()

    else:
        user_info = get_user_info(st.session_state['token'])

        with st.sidebar.container():
            col1, col2 = st.columns([0.2,0.8])
            with col1:
                st.image(user_info['picture'], width=45)
            with col2:
                st.write(f"{user_info['name']}  \n{user_info['email']}")

            if st.button("👋 Logout", type='secondary'):
                revoke_token(st.session_state['token'], st.session_state['state'])
                st.session_state.clear()
                streamlit_js_eval(js_expressions=f'parent.window.open("{REDIRECT_URI}","_self")')
        return





