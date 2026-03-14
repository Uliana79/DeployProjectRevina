import streamlit as st
import requests
import pandas as pd

API_BASE_URL = "http://localhost:8004"

st.title("Таблица с данными электроэнергии")

if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'records_data' not in st.session_state:
    st.session_state.records_data = None


def load_records(page_num):
    try:
        response = requests.get(
            f"{API_BASE_URL}/records",
            params={"page": page_num}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return None


if st.button("Загрузить данные", type="primary"):
    with st.spinner(f'Загрузка данных ...'):
        data = load_records(st.session_state.current_page)
        if data:
            st.session_state.records_data = data


if st.session_state.records_data:
    with st.spinner(f'Загрузка страницы ...'):
        data = st.session_state.records_data
        
        col1, col2= st.columns([1,4])
        with col1:
            st.metric("Всего записей", data.get("total", 0))
        with col2:
            st.metric("Cтраница", f"{data.get('page', 1)} из {data.get('total_pages', 1)}")
        
        if data.get("records"):
            df = pd.DataFrame(data["records"])
            
            st.dataframe(
                df,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "timestep": "Время",
                    "consumption_eur": "Потребление в Европейской части России",
                    "consumption_sib": "Потребление в Азиатской части России", 
                    "price_eur": "Цены в Европейской части России",
                    "price_sib": "Цены в Азиатской части России"
                }
            )
            
            col1, col2, col3, col4 = st.columns([1,1,2,0.4], vertical_alignment="bottom")
            with col1:
                if st.button("Предыдущая", type="primary", disabled=st.session_state.current_page <= 1):
                    st.session_state.current_page -= 1
                    new_data = load_records(st.session_state.current_page)
                    if new_data:
                        st.session_state.records_data = new_data
                    st.rerun()
            
            with col2:
                option = st.selectbox("Перейти на страницу", range(1, data.get('total_pages', 1)+1), index=st.session_state.current_page-1)
                if option!= st.session_state.current_page:
                    st.session_state.current_page = option
                    new_data = load_records(st.session_state.current_page)
                    if new_data:
                        st.session_state.records_data = new_data
                    st.rerun()
                    
            with col4:
                if st.button("Следующая",type="primary", disabled=st.session_state.current_page >= data.get('total_pages', 1)):
                    st.session_state.current_page += 1
                    new_data = load_records(st.session_state.current_page)
                    if new_data:
                        st.session_state.records_data = new_data
                    st.rerun()
        