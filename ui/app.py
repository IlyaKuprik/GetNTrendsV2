import streamlit as st
import pandas as pd
import requests
import streamlit as st

# Создание вкладок
tab1, tab3 = st.tabs(["База новостей", "Суммаризация (Инсайты)"])

# Контент для первой вкладки
with tab1:
    st.header("База новостей")
    st.write("Последние 100 спаршенных новостей:")

    last_rows = requests.get("http://0.0.0.0:8001/get_last_n_rows?n=100").json() # Ходим в БД 

    news_df = pd.DataFrame(last_rows)
    st.write("**Таблица новостей:**")
    st.dataframe(news_df, use_container_width=True)

actual_data = requests.get("http://0.0.0.0:8002/get_actual_data").json() # Ходим в бек пайплайна

# Контент для третьей вкладки
with tab3:
    st.header("Инсайты (Суммаризация)")
    for item in actual_data["insights"]:
        # Отображение инсайта
        st.subheader("__")
        st.write(item['insight'])

        # Создание разворачивающегося элемента для ощутимых статей
        with st.expander("Новости"):
            for article in item['top_articles']:
                st.write("- " + article)