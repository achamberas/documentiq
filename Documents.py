import streamlit as st

from utils.styles import *
from utils.auth import login, fetch_token, get_user_info, auth
from utils.connectors import *
from utils.configs import *
from utils.loaders import *

from dotenv import load_dotenv

# load .env file to environment variables
load_dotenv()

# page_layout(title='Home')
def update_db(key, df):
    if key in st.session_state:

        deleted_rows = st.session_state[key]['deleted_rows']

        if len(deleted_rows)>0:
            deleted_docs = [df['id'][x] for x in deleted_rows]
            deleted_list = "','".join(deleted_docs)

            sql = f'DELETE FROM `rag_test.embeddings` where id in (\'{deleted_list}\')'
            delete_embeddings = bq_conn(sql)

            sql = f'DELETE FROM `rag_test.documents` where id in (\'{deleted_list}\')'
            delete_embeddings = bq_conn(sql)

            st.toast(f'Deleted {deleted_docs} from database.')

def main():
    st.title('Documents')

    # display loaded documents
    sql = """
    SELECT id, name, filetype as type
    FROM `rag_test.documents`
    ORDER BY name
    """

    sources_df = bq_conn(sql)

    filetypes = [
        {'type':'text/plain', 'image':'txt-file.png'},
        {'type':'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image':'word-file.png'},
        {'type':'application/pdf', 'image':'pdf-file.png'},
        {'type':'application/json', 'image':'json-file.png'},
        {'type':'html', 'image':'web.png'},
        {'type':'clipboard', 'image':'clipboard.png'}
    ]

    filetypes_df = pd.DataFrame(filetypes)

    df = sources_df.merge(filetypes_df, on='type')
    df['image_path'] = 'app/static/' + df['image']

    st.write('Previously loaded documents')
    st.data_editor(
        df[['image_path','name']], 
        column_config={
            "image_path": st.column_config.ImageColumn(label="type", width="small")
        },
        key="source_table", 
        num_rows="dynamic", 
        use_container_width=False, 
        hide_index=True, 
        on_change=update_db("source_table", sources_df)
    )

add_styles()
auth()
main()