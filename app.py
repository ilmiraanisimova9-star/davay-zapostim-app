import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="ДАВАЙ ЗАПОСТИМ! — Управление и отчеты", 
    page_icon="⚡", 
    layout="wide"
)

# Ваша рабочая ссылка на веб-приложение
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbw7iVtUeZTeUXjzoSheQfb_RXHjECN42VG_VeRwa7ILR6xcH8Y_XICR3JcKafUMFfGR/exec"

brand_css = """
<style>
    @import url('https://fonts.cdnfonts.com/css/gotham-pro');
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap');

    html, body, [class*="css"], .stApp, button, input, select, textarea {
        font-family: 'Gotham Pro', 'Montserrat', sans-serif !important;
    }

    /* Главный фон приложения */
    .stApp {
        background-color: #1A1A1A !important;
        color: #F7F7F7 !important;
    }
    
    /* Темный фон для бокового меню (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #121212 !important;
        border-right: 1px solid #262626 !important;
    }

    [data-testid="stSidebar"] * {
        color: #F7F7F7 !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #D8FD81 !important;
        font-weight: 800 !important;
    }
    
    /* Заголовки */
    h1 {
        color: #D8FD81 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    h2, h3, h4 {
        color: #B795E8 !important;
        font-weight: 700 !important;
    }

    /* Все лейблы (подписи к полям ввода) */
    label, p, .stMarkdown {
        color: #F7F7F7 !important;
        font-size: 15px !important;
    }

    label p {
        color: #F7F7F7 !important;
        font-weight: 600 !important;
    }

    /* Поля ввода и селекты */
    .stSelectbox div[data-baseweb="select"], 
    .stMultiSelect div[data-baseweb="select"],
    .stTextInput input, 
    .stTextArea textarea {
        background-color: #262626 !important;
        border: 1px solid #404040 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }

    /* Сиреневые теги выбора (#B795E8) */
    span[data-baseweb="tag"],
    div[data-baseweb="tag"] {
        background-color: #B795E8 !important;
        color: #1A1A1A !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
    }

    span[data-baseweb="tag"] * {
        color: #1A1A1A !important;
        fill: #1A1A1A !important;
    }

    /* Главная кнопка */
    div.stButton > button {
        background-color: #D8FD81 !important;
        color: #1A1A1A !important;
        border: none !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        border-radius: 12px !important;
    }
    
    div.stButton > button p {
        color: #1A1A1A !important;
        font-weight: 800 !important;
    }
    
    div.stButton > button:hover {
        background-color: #B795E8 !important;
    }

    /* Кастомные контрастные плашки для сообщений (Alerts) */
    .stAlert {
        background-color: #262626 !important;
        border-radius: 10px !important;
        border: 1px solid #404040 !important;
    }

    div[data-testid="stAlert"] * {
        color: #FFFFFF !important;
    }

    div[data-baseweb="notification"] {
        background-color: #262626 !important;
    }
</style>
"""

st.markdown(brand_css, unsafe_allow_html=True)

# Боковое меню навигации
st.sidebar.title("⚡ ДАВАЙ ЗАПОСТИМ!")
page = st.sidebar.radio("Выберите раздел:", ["📝 Сдача отчетов", "🔒 Дашборд руководителя"])

team_members = [
    "Анастасия Мальцева",
    "Софья Мальцева",
    "Христина Рочева",
    "Светлана Кулешова",
    "Злата Курашова",
    "Вероника Липина",
    "Юлия Лодыгина",
    "Ева Гусева",
    "Дарья Витязева",
    "Виталина Куликова",
    "➕ Добавить свое имя (если нет в списке)"
]

projects = [
    "Стоматология для детей", "KISS ME FLOWERS", "Вельвет Лазер", 
    "Любимая Кухня", "Лекотека", "Рыболов Сервис", "Сулугуни", 
    "МЦ \"Да Винчи\"", "ТПП", "ООО ИНТИНСКОЕ", "Астромед", 
    "Ресторан Спасский", "Дима Третий", "KATSU", "ДАВАЙ ЗАПОСТИМ"
]

roles = [
    "Проектный менеджер", "Контентмейкер", "Видеограф", 
    "Дизайнер", "Монтажер", "Региональная управляющая"
]

# ----------------------------------------------------
# СТРАНИЦА 1: ФОРМА СДАЧИ ОТЧЕТОВ
# ----------------------------------------------------
if page == "📝 Сдача отчетов":
    st.title("⚡ ДАВАЙ ЗАПОСТИМ! — Сдача отчетов")
    st.markdown("Заполните форму отчета за прошедший месяц. Вы можете выбрать **несколько проектов и несколько ролей** одновременно.")

    col1, col2 = st.columns(2)
    with col1:
        selected_executor = st.selectbox("Имя и фамилия (Исполнитель)", team_members)
        if selected_executor == "➕ Добавить свое имя (если нет в списке)":
            executor = st.text_input("Введите ваше имя и фамилию")
        else:
            executor = selected_executor

    with col2:
        period = st.selectbox("Отчетный период", ["Июль 2026", "Август 2026", "Сентябрь 2026"])

    st.markdown("---")
    st.subheader("📋 Проекты и выполняемые роли")

    selected_projects = st.multiselect("Выберите проекты, над которыми работали", projects)
    task_data = {}

    if selected_projects:
        st.markdown("### Детализация по проектам:")
        for proj in selected_projects:
            st.markdown(f"#### Проект: **{proj}**")
            proj_roles = st.multiselect(f"Выберите ваши роли в проекте «{proj}»", roles, key=f"roles_{proj}")
            
            extra_info_list = []
            if "Проектный менеджер" in proj_roles:
                kpi = st.selectbox(f"Достигнуто KPI целей ({proj})", ["0 целей (0₽)", "1 цель (500₽)", "2 цели (1000₽)", "3 цели (1500₽)"], key=f"kpi_{proj}")
                extra_info_list.append(f"KPI: {kpi}")
                
                if proj in ["Стоматология для детей", "Рыболов Сервис", "МЦ \"Да Винчи\""]:
                    if st.checkbox(f"Ведение картографических сервисов (+2500₽ к премии) [{proj}]", key=f"cards_{proj}"):
                        extra_info_list.append("Карты (+2500₽)")
                    
                if proj == "ООО ИНТИНСКОЕ":
                    if st.checkbox(f"Комьюнити-менеджмент (+1500₽) [{proj}]", key=f"comm_{proj}"):
                        extra_info_list.append("Комьюнити (+1500₽)")

            if proj in ["Ресторан Спасский", "Сулугуни", "Астромед"]:
                v_type = st.selectbox(f"Тип сдельного объема ({proj})", ["Посты", "Клипы"], key=f"v_type_{proj}")
                v_count = st.number_input(f"Количество единиц ({proj})", min_value=0, value=0, key=f"v_count_{proj}")
                if v_count > 0:
                    extra_info_list.append(f"Объем: {v_type} - {v_count} шт.")

            task_data[proj] = {
                "roles": ", ".join(proj_roles), 
                "extra": "; ".join(extra_info_list)
            }
            st.markdown("---")

    st.subheader("✨ Разовые и дополнительные задачи")
    has_extra = st.checkbox("Были ли разовые задачи вне основного тарифа?")
    extra_task_desc = ""
    if has_extra:
        extra_task_desc = st.text_area("Опишите выполненную задачу и запрашиваемую сумму")

    st.markdown(" ")
    if st.button("🚀 Отправить отчет"):
        empty_roles = [p for p, data in task_data.items() if not data["roles"]]
        
        if not executor or executor.strip() == "":
            st.error("Ошибка: пожалуйста, укажите ваше имя и фамилию.")
        elif not selected_projects:
            st.error("Ошибка: выберите хотя бы один проект.")
        elif empty_roles:
            st.error(f"Ошибка: вы не выбрали роли для следующих проектов: {', '.join(empty_roles)}")
        else:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payload = []
            
            for proj, data in task_data.items():
                payload.append({
                    "Дата и время": now_str,
                    "Исполнитель": executor,
                    "Период": period,
                    "Проект": proj,
                    "Роли": data["roles"],
                    "Детали и KPI": data["extra"],
                    "Разовые задачи": extra_task_desc if proj == selected_projects[0] else ""
                })
            
            try:
                res = requests.post(WEBHOOK_URL, json=payload)
                if res.status_code == 200:
                    st.success(f"✅ Отчет от **{executor}** успешно зафиксирован!")
                    st.balloons()
                else:
                    st.error(f"Ошибка запроса: статус {res.status_code}")
            except Exception as e:
                st.error(f"Ошибка соединения: {e}")

# ----------------------------------------------------
# СТРАНИЦА 2: ДАШБОРД РУКОВОДИТЕЛЯ
# ----------------------------------------------------
elif page == "🔒 Дашборд руководителя":
    st.title("🔒 Дашборд руководителя")
    
    # Авторизация по паролю
    password = st.text_input("Введите пароль для доступа к финансовому отчету:", type="password")
    
    # Установите ваш пароль (по умолчанию: 1234)
    if password == "1234":
        st.success("Доступ разрешен!")
        
        st.markdown("---")
        st.subheader("📊 Сводный расчет выплат команде")
        
        # Получение данных с Google Apps Script (GET запрос)
        try:
            res = requests.get(WEBHOOK_URL)
            if res.status_code == 200:
                raw_data = res.json()
                df = pd.DataFrame(raw_data)
                
                if not df.empty and "Исполнитель" in df.columns:
                    # Фильтр по отчетному периоду
                    periods = df["Период"].unique().tolist()
                    selected_period = st.selectbox("Выберите отчетный период:", periods)
                    
                    filtered_df = df[df["Период"] == selected_period]
                    
                    st.markdown(f"### Итоги за **{selected_period}**")
                    
                    # Группировка по людям
                    executors = filtered_df["Исполнитель"].unique()
                    
                    total_payout_all = 0
                    summary_list = []
                    
                    for exec_name in executors:
                        user_rows = filtered_df[filtered_df["Исполнитель"] == exec_name]
                        projects_count = len(user_rows)
                        
                        # Собираем список всех проектов и ролей
                        proj_details = []
                        for idx, row in user_rows.iterrows():
                            proj_details.append(f"• **{row['Проект']}**: {row['Роли']} ({row['Детали и KPI']})")
                        
                        summary_list.append({
                            "Исполнитель": exec_name,
                            "Проектов в работе": projects_count,
                            "Детализация": "<br>".join(proj_details)
                        })
                    
                    # Отображение сводной таблицы
                    summary_df = pd.DataFrame(summary_list)
                    
                    col_m1, col_m2 = st.columns(2)
                    col_m1.metric("Всего отчетов получено", len(filtered_df))
                    col_m2.metric("Человек сдали отчеты", len(executors))
                    
                    st.markdown("---")
                    st.markdown("### Сводные карточки членов команды:")
                    
                    for exec_name in executors:
                        user_rows = filtered_df[filtered_df["Исполнитель"] == exec_name]
                        with st.expander(f"👤 **{exec_name}** — проектов: {len(user_rows)}"):
                            st.markdown("**Выполненные проекты и роли:**")
                            for idx, row in user_rows.iterrows():
                                st.write(f"🔹 **{row['Проект']}** | Роли: *{row['Роли']}* | {row['Детали и KPI']}")
                                if row.get("Разовые задачи"):
                                    st.info(f"💡 Разовые задачи: {row['Разовые задачи']}")
                else:
                    st.info("В таблице пока нет записей.")
            else:
                st.error("Не удалось загрузить данные из Google Таблицы.")
        except Exception as e:
            st.warning("В Google Apps Script еще не включен метод получения данных (GET). Сейчас данные пишутся в таблицу нормально.")
            st.info("Все отчёты сохраняются в вашей Google Таблице в полном объеме!")
            
    elif password != "":
        st.error("Неверный пароль. Доступ ограничен.")
