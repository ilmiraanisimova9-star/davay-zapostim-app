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

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbz4-aWJrZ5hS7rjejcPUVnkhtaMnFhsNI50si90q_nathh74qIogvirpXwK_96lKutP/exec"

brand_css = """
<style>
    @import url('https://fonts.cdnfonts.com/css/gotham-pro');
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap');

    html, body, [class*="css"], .stApp, button, input, select, textarea {
        font-family: 'Gotham Pro', 'Montserrat', sans-serif !important;
    }

    .stApp {
        background-color: #1A1A1A !important;
        color: #F7F7F7 !important;
    }
    
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
    
    h1 {
        color: #D8FD81 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    h2, h3, h4 {
        color: #B795E8 !important;
        font-weight: 700 !important;
    }

    label, p, .stMarkdown {
        color: #F7F7F7 !important;
        font-size: 15px !important;
    }

    label p {
        color: #F7F7F7 !important;
        font-weight: 600 !important;
    }

    .stSelectbox div[data-baseweb="select"], 
    .stMultiSelect div[data-baseweb="select"],
    .stTextInput input, 
    .stTextArea textarea {
        background-color: #262626 !important;
        border: 1px solid #404040 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }

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

    .stAlert {
        background-color: #262626 !important;
        border-radius: 10px !important;
        border: 1px solid #404040 !important;
    }

    div[data-testid="stAlert"] * {
        color: #FFFFFF !important;
    }

    [data-testid="stMetricValue"] {
        color: #D8FD81 !important;
        font-weight: 800 !important;
    }
</style>
"""

st.markdown(brand_css, unsafe_allow_html=True)

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
    "Проектный менеджер", 
    "Контентмейкер", 
    "Видеограф", 
    "Дизайнер", 
    "Монтажер", 
    "Региональная управляющая",
    "Ведение картографических сервисов",
    "Выставление счёта за ОРД",
    "Частичная подмена / Дежурство"
]

subcontractor_roles = [
    "Контентмейкер", 
    "Дизайнер", 
    "Монтажер", 
    "Видеограф", 
    "Ведение картографических сервисов",
    "Выставление счёта за ОРД"
]

def calculate_project_payment(proj_name, roles_str, details_str):
    total = 0
    roles_list = [r.strip() for r in roles_str.split(",") if r.strip()]
    
    is_40k_project = proj_name in ["KATSU", "Лекотека", "KISS ME FLOWERS", "Вельвет Лазер"]
    
    for role in roles_list:
        if role == "Проектный менеджер":
            total += 8000
        elif role == "Контентмейкер":
            total += 6000 if is_40k_project else 5000
        elif role == "Дизайнер":
            total += 4000
        elif role == "Монтажер":
            total += 4000
        elif role == "Видеограф":
            total += 5000
        elif role == "Региональная управляющая":
            total += 10000
        elif role == "Ведение картографических сервисов":
            total += 2500
        elif role == "Выставление счёта за ОРД":
            total += 180

    if "KPI: 1 цель" in details_str:
        total += 500
    elif "KPI: 2 цели" in details_str:
        total += 1000
    elif "KPI: 3 цели" in details_str:
        total += 1500

    if "Комьюнити (+1500₽)" in details_str:
        total += 1500

    return total

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
            
            # Блок подмены
            is_replacement = st.checkbox(f"Была частичная подмена / работал(а) неполный месяц [{proj}]", key=f"repl_check_{proj}")
            if is_replacement:
                repl_comment = st.text_input(f"Укажите даты, кого подменяли и суть задач ({proj})", key=f"repl_txt_{proj}")
                if repl_comment:
                    extra_info_list.append(f"ПОДМЕНА: {repl_comment}")

            # Расширенный блок для Проектных менеджеров: гибкий выбор подрядчиков
            if "Проектный менеджер" in proj_roles:
                st.markdown("👥 **Укажите подрядчиков, работавших на проекте (для сверки):**")
                chosen_sub_roles = st.multiselect(f"Какие роли подрядчиков были на проекте «{proj}»?", subcontractor_roles, key=f"sub_roles_{proj}")
                
                team_declared = []
                for s_role in chosen_sub_roles:
                    people = st.multiselect(f"Исполнители на роли «{s_role}» [{proj}]", [m for m in team_members if "➕" not in m], key=f"people_{s_role}_{proj}")
                    if people:
                        team_declared.append(f"{s_role}: {', '.join(people)}")
                
                if team_declared:
                    extra_info_list.append(f"ЗАЯВЛЕННАЯ КОМАНДА: [{'; '.join(team_declared)}]")

                kpi = st.selectbox(f"Достигнуто KPI целей ({proj})", ["0 целей (0₽)", "1 цель (500₽)", "2 цели (1000₽)", "3 цели (1500₽)"], key=f"kpi_{proj}")
                extra_info_list.append(f"KPI: {kpi}")
                
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
    
    password = st.text_input("Введите пароль для доступа к финансовому отчету:", type="password")
    
    if password == "1234":
        st.success("Доступ разрешен!")
        st.markdown("---")
        
        try:
            res = requests.get(WEBHOOK_URL)
            if res.status_code == 200:
                raw_data = res.json()
                df = pd.DataFrame(raw_data)
                
                if not df.empty and "Исполнитель" in df.columns:
                    periods = df["Период"].unique().tolist()
                    selected_period = st.selectbox("Выберите отчетный период:", periods)
                    
                    filtered_df = df[df["Период"] == selected_period]
                    executors = filtered_df["Исполнитель"].unique()
                    
                    grand_total = 0
                    executors_payouts = {}
                    
                    for exec_name in executors:
                        user_rows = filtered_df[filtered_df["Исполнитель"] == exec_name]
                        user_sum = 0
                        for idx, row in user_rows.iterrows():
                            user_sum += calculate_project_payment(row["Проект"], str(row["Роли"]), str(row["Детали и KPI"]))
                        executors_payouts[exec_name] = user_sum
                        grand_total += user_sum
                    
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Всего отчетов", len(filtered_df))
                    col_m2.metric("Команда", f"{len(executors)} чел.")
                    col_m3.metric("Итого к выплате (базово)", f"{grand_total:,.0f} ₽".replace(",", " "))
                    
                    st.markdown("---")
                    st.subheader("🎯 Статус автосверки (ПМ vs Подрядчики):")
                    
                    pm_rows = filtered_df[filtered_df["Роли"].str.contains("Проектный менеджер", na=False)]
                    if not pm_rows.empty:
                        for idx, pm_row in pm_rows.iterrows():
                            details = str(pm_row["Детали и KPI"])
                            if "ЗАЯВЛЕННАЯ КОМАНДА:" in details:
                                st.info(f"📌 **{pm_row['Проект']}** (ПМ: {pm_row['Исполнитель']}): {details.split('ЗАЯВЛЕННАЯ КОМАНДА:')[1].strip()}")
                    else:
                        st.caption("В этом периоде проектные менеджеры пока не указывали составы команд.")
                    
                    st.markdown("---")
                    st.subheader("💰 Сводный расчет по каждому члену команды:")
                    
                    for exec_name in executors:
                        user_rows = filtered_df[filtered_df["Исполнитель"] == exec_name]
                        payout = executors_payouts[exec_name]
                        
                        with st.expander(f"👤 **{exec_name}** — проектов: {len(user_rows)} | **Базовый расчет: {payout:,.0f} ₽**".replace(",", " ")):
                            st.markdown("**Детализация расчета:**")
                            for idx, row in user_rows.iterrows():
                                details = str(row["Детали и KPI"])
                                p_sum = calculate_project_payment(row["Проект"], str(row["Роли"]), details)
                                
                                if "ПОДМЕНА:" in details:
                                    st.warning(f"⚠️ **{row['Проект']}** | Роли: *{row['Роли']}* | {details}")
                                else:
                                    st.write(f"🔹 **{row['Проект']}** | Роли: *{row['Роли']}* | {details} ➔ **{p_sum:,.0f} ₽**".replace(",", " "))
                                
                                if row.get("Разовые задачи") and str(row["Разовые задачи"]).strip():
                                    st.info(f"💡 Разовые задачи (требуют согласования): {row['Разовые задачи']}")
                else:
                    st.info("В таблице пока нет записей.")
            else:
                st.error("Не удалось получить данные с сервера.")
        except Exception as e:
            st.error(f"Ошибка загрузки: {e}")
            
    elif password != "":
        st.error("Неверный пароль. Доступ ограничен.")
