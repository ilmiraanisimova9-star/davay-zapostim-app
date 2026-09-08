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
    
    /* Контрастные и видимые подсказки (placeholders) */
    ::placeholder {
        color: #A6A6A6 !important;
        opacity: 1 !important;
    }
    ::-webkit-input-placeholder {
        color: #A6A6A6 !important;
        opacity: 1 !important;
    }
    :-ms-input-placeholder {
        color: #A6A6A6 !important;
        opacity: 1 !important;
    }

    .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"], .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #262626 !important; border: 1px solid #4D4D4D !important; color: #FFFFFF !important; border-radius: 10px !important;
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
page = st.sidebar.radio("Выберите раздел:", ["📝 Сдача отчетов (Менеджеры)", "🔒 Дашборд руководителя"])

managers_list = [
    "Анастасия Мальцева", "Софья Мальцева", "Христина Рочева", "➕ Ввести другое имя"
]

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

def parse_pm_payment(details_str):
    pm_match = re.search(r'РОЛЬ \[Проектный менеджер\]: .*?Сумма - (\d+)\s*₽', details_str)
    if pm_match:
        amt = int(pm_match.group(1))
    else:
        amt = 8500
    if "KPI: 1 цель" in details_str: amt += 500
    elif "KPI: 2 цели" in details_str: amt += 1000
    elif "KPI: 3 цели" in details_str: amt += 1500
    return amt

def parse_subcontractors_from_details(details_str):
    sub_data = []
    team_match = re.search(r'ЗАЯВЛЕННАЯ КОМАНДА:\s*\[(.*?)\]', details_str)
    if not team_match:
        return sub_data
    
    content = team_match.group(1)
    role_blocks = content.split("; ")
    for block in role_blocks:
        if ":" not in block: continue
        role_part, people_part = block.split(":", 1)
        role = role_part.strip()
        items = people_part.split("), ")
        for item in items:
            item = item.strip().rstrip(")")
            m = re.match(r'^(.*?)\s*\((.*?),\s*(\d+)\s*₽', item)
            if m:
                p_name = m.group(1).strip()
                p_desc = m.group(2).strip()
                p_sum = int(m.group(3))
                sub_data.append({"name": p_name, "role": role, "desc": p_desc, "sum": p_sum})
    return sub_data

# ----------------------------------------------------
# СТРАНИЦА 1: ФОРМА ДЛЯ ПРОЕКТНОГО МЕНЕДЖЕРА
# ----------------------------------------------------
if page == "📝 Сдача отчетов (Менеджеры)":
    st.title("⚡ ДАВАЙ ЗАПОСТИМ! — Сдача отчета менеджера")
    st.markdown("Заполните финансовый отчет по вашим проектам и задействованным подрядчикам.")

    col1, col2 = st.columns(2)
    with col1:
        selected_manager = st.selectbox("Менеджер проекта", managers_list, index=None, placeholder="Выберите имя...")
        if selected_manager == "➕ Ввести другое имя":
            manager_name = st.text_input("Введите имя менеджера")
        else:
            manager_name = selected_manager
    with col2:
        period = st.selectbox("Отчетный период", ["Июль 2026", "Август 2026", "Сентябрь 2026", "Октябрь 2026"], index=None, placeholder="Выберите период...")

    st.markdown("---")
    st.subheader("📋 Проекты под управлением")

    selected_projects = st.multiselect("Выберите проекты, которые вы вели в этом месяце", projects, placeholder="Выберите проекты из списка...")
    task_data = {}

    if selected_projects:
        for proj in selected_projects:
            st.markdown(f"### Проект: **{proj}**")
            
            is_content_package = st.checkbox("📦 Контент-пакет / Сдельная оплата", key=f"cp_{proj}")
            extra_info_list = []
            
            # Данные по ставке менеджера
            st.markdown("**Ваша ставка за проект (Проектный менеджер):**")
            c1, c2 = st.columns(2)
            with c1:
                pm_period = st.text_input(
                    "Период / объем (если не полный месяц)", 
                    value="", 
                    placeholder="Например: 01.07–15.07 или 50%", 
                    key=f"pm_per_{proj}"
                )
            with c2:
                def_pm_amt = 0 if is_content_package else 8500
                pm_amt = st.number_input("Сумма к выплате ПМ (₽)", value=int(def_pm_amt), key=f"pm_amt_{proj}")
            
            safe_pm_per = pm_period.strip() if pm_period.strip() else "Полный месяц"
            extra_info_list.append(f"РОЛЬ [Проектный менеджер]: Данные - {safe_pm_per}, Сумма - {pm_amt} ₽")

            if not is_content_package:
                kpi = st.selectbox("Достигнуто KPI целей", ["0 целей (0₽)", "1 цель (+500₽)", "2 цели (+1000₽)", "3 цели (+1500₽)"], key=f"kpi_{proj}")
                kpi_comment = st.text_input("Комментарий к KPI / Оценка", placeholder="Например: цели выполнены досрочно", key=f"kpicom_{proj}")
                extra_info_list.append(f"KPI: {kpi}. Коммент: {kpi_comment}")

            # Подрядчики проекта
            st.markdown("---")
            st.markdown("👥 **Укажите подрядчиков проекта и суммы к выплате:**")
            chosen_sub_roles = st.multiselect("Какие роли подрядчиков были на проекте?", subcontractor_roles, placeholder="Выберите роли из списка...", key=f"sub_roles_{proj}")
            
            team_declared = []
            for s_role in chosen_sub_roles:
                sub_list = [m for m in team_members if "➕" not in m] + ["➕ Ввести новое имя"]
                people = st.multiselect(f"Исполнители на роли «{s_role}»", sub_list, placeholder="Выберите исполнителей...", key=f"people_{s_role}_{proj}")
                
                role_limit = ROLE_BASE_RATES.get(s_role, 0)
                current_sum = 0
                people_details = []
                
                for p in people:
                    p_name = p
                    if p == "➕ Ввести новое имя":
                        p_name = st.text_input(f"Введите имя ({s_role})", key=f"custom_{s_role}_{proj}")
                        if not p_name: continue
                    
                    colA, colB, colC = st.columns([2, 2, 1])
                    with colA: st.markdown(f"<br>👤 **{p_name}**", unsafe_allow_html=True)
                    with colB: 
                        p_period = st.text_input(
                            "Период / объем", 
                            value="", 
                            placeholder="Например: 01.07–15.07 или 5 клипов", 
                            key=f"pper_{p}_{s_role}_{proj}"
                        )
                    with colC: 
                        def_val = role_limit // len(people) if len(people) > 0 and not is_content_package else 0
                        p_amt = st.number_input("Сумма ₽", value=int(def_val), key=f"pamt_{p}_{s_role}_{proj}")
                        current_sum += p_amt
                    
                    safe_p_period = p_period.strip() if p_period.strip() else "Полный месяц"
                    people_details.append(f"{p_name} ({safe_p_period}, {p_amt} ₽)")
                
                if current_sum > role_limit and not is_content_package and len(people) > 0:
                    st.error(f"⚠️ Перерасход ФОТ! Сумма по роли «{s_role}» ({current_sum} ₽) превышает базовый лимит ({role_limit} ₽).")
                
                if people_details:
                    team_declared.append(f"{s_role}: {', '.join(people_details)}")
            
            if team_declared:
                extra_info_list.append(f"ЗАЯВЛЕННАЯ КОМАНДА: [{'; '.join(team_declared)}]")

            task_data[proj] = {
                "roles": "Проектный менеджер", 
                "extra": "; ".join(extra_info_list)
            }
            st.markdown("---")

    st.subheader("✨ Иные задачи, не учтённые выше")
    has_extra = st.checkbox("Были ли иные задачи за отчетный период?")
    extra_task_desc = ""
    if has_extra:
        task_count = st.number_input("Сколько иных задач вы согласовали?", min_value=1, max_value=10, value=1)
        tasks_list = []
        for i in range(int(task_count)):
            col_ex1, col_ex2 = st.columns([3, 1])
            with col_ex1: task_text = st.text_input(f"Описание задачи №{i+1}", placeholder="Например: разработка брендбука", key=f"task_txt_{i}")
            with col_ex2: task_price = st.text_input(f"Стоимость (₽)", placeholder="3000", key=f"task_prc_{i}")
            if task_text:
                price_str = f" — {task_price}₽" if task_price.strip() else " — цена не указана"
                tasks_list.append(f"• {task_text}{price_str}")
        if tasks_list: extra_task_desc = "; ".join(tasks_list)

    st.markdown(" ")
    if st.button("🚀 Отправить отчет"):
        if not manager_name or manager_name.strip() == "": 
            st.error("Пожалуйста, выберите имя менеджера.")
        elif not period: 
            st.error("Пожалуйста, выберите отчетный период.")
        elif not selected_projects: 
            st.error("Выберите хотя бы один проект.")
        else:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            payload = []
            for proj, data in task_data.items():
                payload.append({
                    "Дата и время": now_str, "Исполнитель": manager_name, "Период": period,
                    "Проект": proj, "Роли": data["roles"], "Детали и KPI": data["extra"],
                    "Разовые задачи": extra_task_desc if proj == selected_projects[0] else ""
                })
            try:
                res = requests.post(WEBHOOK_URL, json=payload)
                if res.status_code == 200:
                    st.success(f"✅ Отчет менеджера **{manager_name}** успешно зафиксирован!")
                    st.balloons()
                else: st.error(f"Ошибка: статус {res.status_code}")
            except Exception as e: st.error(f"Ошибка соединения: {e}")

# ----------------------------------------------------
# СТРАНИЦА 2: ДАШБОРД РУКОВОДИТЕЛЯ
# ----------------------------------------------------
elif page == "🔒 Дашборд руководителя":
    st.title("🔒 Дашборд руководителя")
    password = st.text_input("Введите пароль:", type="password")
    
    if password == "оплата подрядчиков2026!":
        try:
            res = requests.get(WEBHOOK_URL)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                if not df.empty and "Исполнитель" in df.columns:
                    periods = df["Период"].unique().tolist()
                    selected_period = st.selectbox("Отчетный период:", periods)
                    
                    filtered_df = df[df["Период"] == selected_period]
                    
                    project_fots = []
                    contractor_payouts = {}
                    grand_total_fot = 0
                    
                    for idx, row in filtered_df.iterrows():
                        p_name = row["Проект"]
                        p_manager = row["Исполнитель"]
                        p_details = str(row["Детали и KPI"])
                        p_extra = str(row.get("Разовые задачи", ""))
                        
                        pm_sum = parse_pm_payment(p_details)
                        extra_sum = parse_extra_tasks_amount(p_extra)
                        subs = parse_subcontractors_from_details(p_details)
                        
                        subs_sum = sum(s["sum"] for s in subs)
                        project_total = pm_sum + subs_sum + extra_sum
                        grand_total_fot += project_total
                        
                        if p_manager not in contractor_payouts:
                            contractor_payouts[p_manager] = []
                        contractor_payouts[p_manager].append({
                            "project": p_name,
                            "role": "Проектный менеджер",
                            "desc": "Управление проектом",
                            "sum": pm_sum + extra_sum
                        })
                        
                        for s in subs:
                            c_name = s["name"]
                            if c_name not in contractor_payouts:
                                contractor_payouts[c_name] = []
                            contractor_payouts[c_name].append({
                                "project": p_name,
                                "role": s["role"],
                                "desc": s["desc"],
                                "sum": s["sum"]
                            })
                        
                        subs_summary_list = [f"{s['role']}: {s['name']} ({s['sum']} ₽)" for s in subs]
                        project_fots.append({
                            "Проект": p_name,
                            "Менеджер": p_manager,
                            "ФОТ ПМ": f"{pm_sum:,.0f} ₽",
                            "Команда подрядчиков": ", ".join(subs_summary_list) if subs_summary_list else "Без подрядчиков",
                            "ФОТ Подрядчиков": f"{subs_sum:,.0f} ₽",
                            "Иные задачи": f"{extra_sum:,.0f} ₽" if extra_sum > 0 else "—",
                            "Итого ФОТ проекта": f"{project_total:,.0f} ₽",
                            "raw_total": project_total
                        })
                    
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Проектов в отчете", len(filtered_df))
                    col_m2.metric("Человек к выплате", f"{len(contractor_payouts)} чел.")
                    col_m3.metric("Итоговый ФОТ агентства", f"{grand_total_fot:,.0f} ₽".replace(",", " "))
                    
                    st.markdown("---")
                    
                    # ТАБЛИЦА 1: ФОТ ПРОЕКТОВ
                    st.subheader("📊 1. Таблица по ФОТу проектов")
                    st.markdown("Сводный бюджет по каждому проекту: сколько начислено менеджеру и распределено на подрядчиков.")
                    
                    df_proj = pd.DataFrame(project_fots).drop(columns=["raw_total"])
                    st.dataframe(df_proj, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    
                    # ТАБЛИЦА 2: ВЫПЛАТЫ ПОДРЯДЧИКАМ
                    st.subheader("💰 2. Таблица с общей суммой к выплате на человека")
                    st.markdown("Итоговая сумма к переводу каждому специалисту, сложенная со всех проектов.")
                    
                    summary_contractors = []
                    for c_name, tasks in contractor_payouts.items():
                        c_total = sum(t["sum"] for t in tasks)
                        details_list = [f"{t['project']} ({t['role']} — {t['desc']}: {t['sum']} ₽)" for t in tasks]
                        summary_contractors.append({
                            "Специалист": c_name,
                            "Итого к выплате": f"{c_total:,.0f} ₽".replace(",", " "),
                            "Количество проектов": len(tasks),
                            "Детализация": "; ".join(details_list),
                            "raw_total": c_total
                        })
                    
                    df_contractors = pd.DataFrame(summary_contractors).sort_values(by="raw_total", ascending=False).drop(columns=["raw_total"])
                    st.dataframe(df_contractors, use_container_width=True, hide_index=True)

        except Exception as e: st.error(f"Ошибка загрузки: {e}")
    elif password != "": st.error("Неверный пароль.")
