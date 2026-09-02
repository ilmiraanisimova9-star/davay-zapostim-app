import streamlit as st
import requests
import json
import pandas as pd
import re
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
    .stApp { background-color: #1A1A1A !important; color: #F7F7F7 !important; }
    [data-testid="stSidebar"] { background-color: #121212 !important; border-right: 1px solid #262626 !important; }
    [data-testid="stSidebar"] * { color: #F7F7F7 !important; }
    [data-testid="stSidebar"] h1, h2, h3 { color: #D8FD81 !important; font-weight: 800 !important; }
    h1 { color: #D8FD81 !important; font-weight: 800 !important; letter-spacing: -0.5px; }
    h2, h3, h4 { color: #B795E8 !important; font-weight: 700 !important; }
    label, p, .stMarkdown { color: #F7F7F7 !important; font-size: 15px !important; }
    label p { color: #F7F7F7 !important; font-weight: 600 !important; }
    .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"], .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #262626 !important; border: 1px solid #404040 !important; color: #FFFFFF !important; border-radius: 10px !important;
    }
    span[data-baseweb="tag"], div[data-baseweb="tag"] { background-color: #B795E8 !important; color: #1A1A1A !important; font-weight: 700 !important; border-radius: 6px !important; }
    span[data-baseweb="tag"] * { color: #1A1A1A !important; fill: #1A1A1A !important; }
    div.stButton > button { background-color: #D8FD81 !important; color: #1A1A1A !important; border: none !important; font-weight: 800 !important; font-size: 16px !important; border-radius: 12px !important; }
    div.stButton > button p { color: #1A1A1A !important; font-weight: 800 !important; }
    div.stButton > button:hover { background-color: #B795E8 !important; }
    .stAlert { background-color: #262626 !important; border-radius: 10px !important; border: 1px solid #404040 !important; }
    div[data-testid="stAlert"] * { color: #FFFFFF !important; }
    [data-testid="stMetricValue"] { color: #D8FD81 !important; font-weight: 800 !important; }
</style>
"""
st.markdown(brand_css, unsafe_allow_html=True)

st.sidebar.title("⚡ ДАВАЙ ЗАПОСТИМ!")
page = st.sidebar.radio("Выберите раздел:", ["📝 Сдача отчетов", "🔒 Дашборд руководителя"])

team_members = [
    "Анастасия Мальцева", "Софья Мальцева", "Христина Рочева",
    "Светлана Кулешова", "Злата Курашова", "Вероника Липина",
    "Юлия Лодыгина", "Ева Гусева", "Дарья Витязева",
    "Виталина Куликова", "Софья Супрун", "➕ Добавить свое имя (если нет в списке)"
]

projects = [
    "Стоматология для детей", "KISS ME FLOWERS", "Вельвет Лазер", 
    "Любимая Кухня", "Лекотека", "Рыболов Сервис", "Сулугуни", 
    "МЦ \"Да Винчи\"", "ТПП", "ООО ИНТИНСКОЕ", "Астромед", 
    "Ресторан Спасский", "Дима Третий", "KATSU", "ДАВАЙ ЗАПОСТИМ",
    "Игорь Паламарчук", "ЛОВ ШЫ"
]

roles = [
    "Проектный менеджер", "Контентмейкер", "Видеограф", "Дизайнер", 
    "Монтажер", "Региональная управляющая", "Ведение картографических сервисов",
    "Комьюнити-менеджмент", "Выставление счёта за ОРД"
]

subcontractor_roles = [
    "Контентмейкер", "Дизайнер", "Монтажер", "Видеограф", 
    "Ведение картографических сервисов", "Комьюнити-менеджмент", "Выставление счёта за ОРД"
]

ROLE_BASE_RATES = {
    "Проектный менеджер": 8500, "Контентмейкер": 5000, "Дизайнер": 3000,
    "Монтажер": 5000, "Видеограф": 5000, "Региональная управляющая": 10000,
    "Ведение картографических сервисов": 2500, "Комьюнити-менеджмент": 1500, "Выставление счёта за ОРД": 180
}

def parse_extra_tasks_amount(extra_tasks_str):
    if not extra_tasks_str or not isinstance(extra_tasks_str, str): return 0
    matches = re.findall(r'—\s*(\d+)\s*₽', extra_tasks_str)
    return sum(int(m) for m in matches)

def calculate_project_payment(proj_name, roles_str, details_str, extra_tasks_str=""):
    total = 0
    
    # 1. Поиск точных сумм, вписанных руками через новые поля
    role_matches = re.findall(r'РОЛЬ \[.*?\]: Период - .*?, Сумма - (\d+)\s*₽', details_str)
    if role_matches:
        for match in role_matches:
            total += int(match)
    else:
        # Резервный старый алгоритм для старых отчетов в базе
        roles_list = [r.strip() for r in roles_str.split(",") if r.strip()]
        for role in roles_list:
            if role in ROLE_BASE_RATES:
                total += ROLE_BASE_RATES[role]

    # 2. Мотивация ПМ
    if "KPI: 1 цель" in details_str: total += 500
    elif "KPI: 2 цели" in details_str: total += 1000
    elif "KPI: 3 цели" in details_str: total += 1500

    # 3. Иные задачи
    total += parse_extra_tasks_amount(extra_tasks_str)
    
    return total

# ----------------------------------------------------
# СТРАНИЦА 1: ФОРМА СДАЧИ ОТЧЕТОВ
# ----------------------------------------------------
if page == "📝 Сдача отчетов":
    st.title("⚡ ДАВАЙ ЗАПОСТИМ! — Сдача отчетов")
    st.markdown("Заполните форму отчета за прошедший месяц.")

    col1, col2 = st.columns(2)
    with col1:
        selected_executor = st.selectbox("Имя и фамилия (Исполнитель)", team_members)
        if selected_executor == "➕ Добавить свое имя (если нет в списке)":
            executor = st.text_input("Введите ваше имя и фамилию")
        else:
            executor = selected_executor
    with col2:
        period = st.selectbox("Отчетный период", ["Июль 2026", "Август 2026", "Сентябрь 2026", "Октябрь 2026"])

    st.markdown("---")
    st.subheader("📋 Проекты и выполняемые роли")

    selected_projects = st.multiselect("Выберите проекты, над которыми работали", projects)
    task_data = {}

    if selected_projects:
        for proj in selected_projects:
            st.markdown(f"#### Проект: **{proj}**")
            
            # Контент-пакет (сдельная оплата)
            is_content_package = st.checkbox(f"📦 Контент-пакет / Сдельная оплата [{proj}]", key=f"cp_{proj}")
            total_package = 0
            if is_content_package:
                c_p1, c_p2 = st.columns(2)
                with c_p1: unit_price = st.number_input(f"Цена за 1 единицу ({proj})", min_value=0, value=0, key=f"up_{proj}")
                with c_p2: units_count = st.number_input(f"Количество ({proj})", min_value=0, value=0, key=f"uc_{proj}")
                total_package = unit_price * units_count
                st.info(f"Итого сдельно: **{total_package} ₽**")
            
            proj_roles = st.multiselect(f"Выберите ваши роли в проекте «{proj}»", roles, key=f"roles_{proj}")
            extra_info_list = []
            
            if is_content_package:
                extra_info_list.append(f"КОНТЕНТ-ПАКЕТ: {units_count} шт. по {unit_price} ₽ (Итого: {total_package} ₽)")

            # Детализация своей ставки с учетом периода
            if proj_roles:
                st.markdown("**Уточните период и сумму за ваши роли:**")
                for role in proj_roles:
                    c1, c2 = st.columns(2)
                    with c1:
                        period_val = st.text_input(f"Период ({role})", value="Полный месяц", key=f"per_{role}_{proj}")
                    with c2:
                        def_amt = ROLE_BASE_RATES.get(role, 0)
                        if is_content_package and role == "Проектный менеджер":
                            def_amt = total_package
                        amt_val = st.number_input(f"Сумма к выплате ₽ ({role})", value=int(def_amt), key=f"amt_{role}_{proj}")
                    extra_info_list.append(f"РОЛЬ [{role}]: Период - {period_val}, Сумма - {amt_val} ₽")

            # Блок ПМ: KPI и состав команды
            if "Проектный менеджер" in proj_roles:
                kpi = st.selectbox(f"Достигнуто KPI целей ({proj})", ["0 целей (0₽)", "1 цель (+500₽)", "2 цели (+1000₽)", "3 цели (+1500₽)"], key=f"kpi_{proj}")
                kpi_comment = st.text_input(f"Комментарий к KPI / Оценка ({proj})", key=f"kpicom_{proj}")
                extra_info_list.append(f"KPI: {kpi}. Коммент: {kpi_comment}")

                st.markdown("---")
                st.markdown("👥 **Укажите подрядчиков, работавших на проекте (для сверки):**")
                chosen_sub_roles = st.multiselect(f"Какие роли подрядчиков были на «{proj}»?", subcontractor_roles, key=f"sub_roles_{proj}")
                
                team_declared = []
                for s_role in chosen_sub_roles:
                    sub_list = [m for m in team_members if "➕" not in m] + ["➕ Ввести новое имя"]
                    people = st.multiselect(f"Исполнители на роли «{s_role}» [{proj}]", sub_list, key=f"people_{s_role}_{proj}")
                    
                    role_limit = ROLE_BASE_RATES.get(s_role, 0)
                    current_sum = 0
                    people_details = []
                    
                    for p in people:
                        p_name = p
                        if p == "➕ Ввести новое имя":
                            p_name = st.text_input(f"Введите имя ({s_role} - {proj})", key=f"custom_{s_role}_{proj}")
                            if not p_name: continue
                        
                        colA, colB, colC = st.columns([2, 2, 1])
                        with colA: st.markdown(f"<br>👤 **{p_name}**", unsafe_allow_html=True)
                        with colB: p_period = st.text_input("Период", value="Полный месяц", key=f"pper_{p}_{s_role}_{proj}")
                        with colC: 
                            def_val = role_limit // len(people) if len(people) > 0 else role_limit
                            p_amt = st.number_input("Сумма ₽", value=int(def_val), key=f"pamt_{p}_{s_role}_{proj}")
                            current_sum += p_amt
                        
                        people_details.append(f"{p_name} ({p_period}, {p_amt} ₽)")
                    
                    if current_sum > role_limit and not is_content_package and len(people) > 0:
                        st.error(f"⚠️ Перерасход ФОТ! Сумма по роли «{s_role}» ({current_sum} ₽) превышает базовый лимит ({role_limit} ₽).")
                    
                    if people_details:
                        team_declared.append(f"{s_role}: {', '.join(people_details)}")
                
                if team_declared:
                    extra_info_list.append(f"ЗАЯВЛЕННАЯ КОМАНДА: [{'; '.join(team_declared)}]")

            task_data[proj] = {
                "roles": ", ".join(proj_roles), 
                "extra": "; ".join(extra_info_list)
            }
            st.markdown("---")

    st.subheader("✨ Иные задачи, не учтённые выше")
    has_extra = st.checkbox("Были ли иные задачи за отчетный период?")
    extra_task_desc = ""
    if has_extra:
        task_count = st.number_input("Сколько иных задач вы выполнили?", min_value=1, max_value=10, value=1)
        tasks_list = []
        for i in range(int(task_count)):
            col_ex1, col_ex2 = st.columns([3, 1])
            with col_ex1: task_text = st.text_input(f"Описание задачи №{i+1}", key=f"task_txt_{i}")
            with col_ex2: task_price = st.text_input(f"Стоимость (₽)", key=f"task_prc_{i}")
            if task_text:
                price_str = f" — {task_price}₽" if task_price.strip() else " — цена не указана"
                tasks_list.append(f"• {task_text}{price_str}")
        if tasks_list: extra_task_desc = "; ".join(tasks_list)

    st.markdown(" ")
    if st.button("🚀 Отправить отчет"):
        empty_roles = [p for p, data in task_data.items() if not data["roles"]]
        if not executor or executor.strip() == "": st.error("Укажите ваше имя.")
        elif not selected_projects: st.error("Выберите хотя бы один проект.")
        elif empty_roles: st.error(f"Укажите роли для: {', '.join(empty_roles)}")
        else:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payload = []
            for proj, data in task_data.items():
                payload.append({
                    "Дата и время": now_str, "Исполнитель": executor, "Период": period,
                    "Проект": proj, "Роли": data["roles"], "Детали и KPI": data["extra"],
                    "Разовые задачи": extra_task_desc if proj == selected_projects[0] else ""
                })
            try:
                res = requests.post(WEBHOOK_URL, json=payload)
                if res.status_code == 200:
                    st.success(f"✅ Отчет от **{executor}** зафиксирован!")
                    st.balloons()
                else: st.error(f"Ошибка: статус {res.status_code}")
            except Exception as e: st.error(f"Ошибка соединения: {e}")

# ----------------------------------------------------
# СТРАНИЦА 2: ДАШБОРД РУКОВОДИТЕЛЯ
# ----------------------------------------------------
elif page == "🔒 Дашборд руководителя":
    st.title("🔒 Дашборд руководителя")
    password = st.text_input("Введите пароль:", type="password")
    
    if password == "оплаты подрядчиков!":
        try:
            res = requests.get(WEBHOOK_URL)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                if not df.empty and "Исполнитель" in df.columns:
                    periods = df["Период"].unique().tolist()
                    selected_period = st.selectbox("Отчетный период:", periods)
                    
                    filtered_df = df[df["Период"] == selected_period]
                    executors = filtered_df["Исполнитель"].unique()
                    
                    grand_total = 0
                    pending_extras_count = 0
                    pending_extras_sum = 0
                    executors_payouts = {}
                    
                    for exec_name in executors:
                        user_rows = filtered_df[filtered_df["Исполнитель"] == exec_name]
                        user_sum = 0
                        for idx, row in user_rows.iterrows():
                            extra_str = str(row.get("Разовые задачи", ""))
                            extra_amt = parse_extra_tasks_amount(extra_str)
                            if extra_amt > 0:
                                pending_extras_count += 1
                                pending_extras_sum += extra_amt
                            user_sum += calculate_project_payment(row["Проект"], str(row["Роли"]), str(row["Детали и KPI"]), extra_str)
                        executors_payouts[exec_name] = user_sum
                        grand_total += user_sum
                    
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Всего отчетов", len(filtered_df))
                    col_m2.metric("Команда", f"{len(executors)} чел.")
                    col_m3.metric("Итого ФОТ (с допами)", f"{grand_total:,.0f} ₽".replace(",", " "))
                    
                    if pending_extras_count > 0:
                        st.warning(f"⚡ **Требуют согласования:** {pending_extras_count} иные задачи на **{pending_extras_sum:,.0f} ₽** (заложены в итоговый ФОТ).".replace(",", " "))
                    
                    st.markdown("---")
                    st.subheader("🎯 Статус автосверки (ПМ vs Подрядчики):")
                    
                    pm_rows = filtered_df[filtered_df["Роли"].str.contains("Проектный менеджер", na=False)]
                    if not pm_rows.empty:
                        for idx, pm_row in pm_rows.iterrows():
                            details = str(pm_row["Детали и KPI"])
                            if "ЗАЯВЛЕННАЯ КОМАНДА:" in details:
                                st.info(f"📌 **{pm_row['Проект']}** (ПМ: {pm_row['Исполнитель']}): {details.split('ЗАЯВЛЕННАЯ КОМАНДА:')[1].strip()}")
                    
                    st.markdown("---")
                    st.subheader("💰 Сводный расчет по команде:")
                    for exec_name in executors:
                        user_rows = filtered_df[filtered_df["Исполнитель"] == exec_name]
                        payout = executors_payouts[exec_name]
                        with st.expander(f"👤 **{exec_name}** — проектов: {len(user_rows)} | **К выплате: {payout:,.0f} ₽**".replace(",", " ")):
                            for idx, row in user_rows.iterrows():
                                details = str(row["Детали и KPI"])
                                extra_str = str(row.get("Разовые задачи", ""))
                                p_sum = calculate_project_payment(row["Проект"], str(row["Роли"]), details, extra_str)
                                st.write(f"🔹 **{row['Проект']}** | Роли: *{row['Роли']}* | {details} ➔ **{p_sum:,.0f} ₽**".replace(",", " "))
                                if extra_str and extra_str.strip():
                                    st.warning(f"⚡ **НА СОГЛАСОВАНИИ (Иные задачи):** {extra_str}")
        except Exception as e: st.error(f"Ошибка загрузки: {e}")
    elif password != "": st.error("Неверный пароль.")
