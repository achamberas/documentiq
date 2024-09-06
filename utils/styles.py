import streamlit as st

def add_styles():
    st.markdown(
        """
        <style>
            button[kind="custom"] {
                background: none!important;
                border: none;
                padding: 0!important;
                color: black !important;
                text-decoration: none;
                cursor: pointer;
                border: none !important;
            }
            button[kind="custom"]:hover {
                text-decoration: none;
                color: black !important;
            }
            button[kind="custom"]:focus {
                outline: none !important;
                box-shadow: none !important;
                color: black !important;
            }

            .st-emotion-cache-1v0mbdj {
                width: 45px;
                height: 45px;
                border-radius: 50%;
                overflow: hidden;
                box-shadow: 0 0 5px rgba(0, 0, 0, 0.3);
            }
            
            .st-emotion-cache-1v0mbdj img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }

            .st-emotion-cache-1tgh22k {
                position: absolute; 
                bottom: 0; 
                height: 110px; 
                margin-bottom: 15px
            }

            .st-emotion-cache-1sbzbzn {
                padding-top: 35px;
            }

        </style>
        """,
        unsafe_allow_html=True,
    )