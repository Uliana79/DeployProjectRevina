
import streamlit as st

API_BASE_URL = "https://deploy-backend-revina.onrender.com" 

st.set_page_config(layout="wide")

pages = {
    "p1":[st.Page("page1.py")],
    "p2":[st.Page("page2.py")]

}

pg = st.navigation([st.Page("page1.py", title="Таблица с данными"),st.Page("page2.py", title="Взаимодействия с данными")])
pg.run()
