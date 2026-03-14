import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.express as px

API_BASE_URL = "https://deploy-backend-revina.onrender.com"

tab1, tab2 = st.tabs(["Добавить запись", "Удалить запись"])

with tab1:
    st.header("Добавление новой записи")
    
    with st.form("my_form"):
        date = st.date_input("Дата", datetime.now())
        time = st.time_input("Время", datetime.now().time().replace(minute=0, second=0, microsecond=0))
        timestep = f"{date} {time.strftime('%H:%M')}"            
        consumption_eur = st.number_input("Потребление в Европейской части России", value=100000.0, step=1000.0, format="%.6f")
        consumption_sib = st.number_input("Потребление в Азиатской части России", value=100000.0, step=1000.0, format="%.6f")
        price_eur = st.number_input("Цена в Европейской части России", value=50.0, step=0.5, format="%.2f")
        price_sib = st.number_input("Цена в Азиатской части России", value=45.0, step=0.5, format="%.2f")
        
        submitted = st.form_submit_button("Сохранить", type="primary")
    
    if submitted:
        if consumption_eur<0 or consumption_sib<0 or price_eur<0 or price_sib<0:
            st.error("Значения не могут быть отрицательными!")
        else:
            data = {
                "timestep": timestep,
                "consumption_eur": consumption_eur,
                "consumption_sib": consumption_sib,
                "price_eur": price_eur,
                "price_sib": price_sib
            }
            
            try:
                response = requests.post(f"{API_BASE_URL}/records", json=data)
                if response.status_code == 201:
                    st.success("Запись успешно добавлена!")
                    st.json(response.json())
                else:
                    st.error(f"Ошибка: {response.json().get('detail', 'Неизвестная ошибка')}")
            except Exception as e:
                st.error(f"Ошибка: {e}")


with tab2:
    st.header("Удаление записи")
    
    with st.form("delete_form"):
        record_id = st.number_input("ID записи для удаления", min_value=1, step=1)
        submitted = st.form_submit_button("Удалить", type="primary")
    
    if submitted:
        try:
            response = requests.delete(f"{API_BASE_URL}/records/{record_id}")
            if response.status_code == 200:
                st.success(f"{response.json().get('detail')}")
            else:
                st.error(f"{response.json().get('detail')}")
        except Exception as e:
            st.error(f"Ошибка: {e}")
            
            

st.markdown("---")
st.subheader("Визуализация данных")

def load_all_records():
    try:
        response = requests.get(f"{API_BASE_URL}/records/all")
        if response.status_code == 200:
            return response.json()          
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return None
    
with st.spinner(f'Идет визуализация ...'):
    records = load_all_records()

    if records:
        df = pd.DataFrame(records)
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['timestep'])
            df = df.sort_values('datetime')        
            col1, col2 = st.columns(2)
            with col1:
                fig_cons = px.line(df, x='datetime', y=['consumption_eur', 'consumption_sib'],
                                title=f"Потребление электроэнергии", 
                                labels={'value': 'МВт·ч', 'datetime': 'Дата', 'variable': 'Регион'})
                new_names = {'consumption_eur': 'Европейская часть', 'consumption_sib': 'Азиатская часть'}
                st.plotly_chart(fig_cons, use_container_width=True)
            
            with col2:
                fig_price = px.histogram(df, x=['price_eur', 'price_sib'], title=f"Распределение цен", nbins=30,
                                        barmode='overlay',
                                        opacity=0.7)
                fig_price.update_layout(legend_title_text='Регион', xaxis_title="Цена", yaxis_title="Количество записей")
                new_names = {'price_eur': 'Европейская часть', 'price_sib': 'Азиатская часть'}
                st.plotly_chart(fig_price, use_container_width=True)
    else:
        st.info("Нет данных для отображения графиков")