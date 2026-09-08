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
    
    ::placeholder { color: #A6A6A6 !important; opacity: 1 !important; }
    ::-webkit-input-placeholder { color: #A6A6A6 !important; opacity: 1 !important; }
    :-ms-input-placeholder { color: #A6A6A6 !important; opacity: 1 !important; }

    .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"], .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #262626 !important; border: 1px solid #4D4D4D !important; color: #FFFFFF !important; border-radius: 10px !important;
    }
    span[data-baseweb="tag"], div[data-baseweb="tag"] { background-color: #B795E8 !important; color: #1A1A1A !important; font-weight: 700 !important; border-radius: 6px !important; }
    span[data-baseweb="tag"] * { color: #1A1A1A !important; fill: #1A1A1A !important; }
    div.stButton > button { background-color: #D8FD81 !important; color: #1A1A1A !important; border: none !important; font-weight: 800 !important; font-size: 16px !important; border-radius: 12px !important; }
    div.stButton > button p { color: #1A1A1A !important; font-weight: 800 !important; }
    div.stButton > button:hover { background-color: #B795E8 !important; }
    div.stButton > button:disabled { background-color: #404040 !important; color: #888888 !important; cursor: not-allowed !important; }
    div.stButton > button:disabled p { color: #888888 !important; }
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
    "Виталина Куликова", "Софья Супрун", "➕ Ввести новое имя"
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

def parse_pm_payment_breakdown(details_str):
    pm_match = re.search(r'РОЛЬ \[Проектный менеджер\]: .*?Сумма - (\d+)\s*₽', details_str)
    base_amt = int(pm_match.group(1)) if pm_match else 8500
    
    kpi_bonus = 0
    kpi_bonus_match = re.search(r'(?:ВОЗНАГРАЖДЕНИЕ ЗА ЦЕЛИ|ПРЕМИЯ ЗА ЦЕЛИ):\s*(\d+)\s*₽', details_str)
    if kpi_bonus_match:
        kpi_bonus = int(kpi_bonus_match.group(1))
    else:
        if "KPI: 1 цель" in details_str: kpi_bonus = 500
        elif "KPI: 2 цели" in details_str: kpi_bonus = 1000
        elif "KPI: 3 цели" in details_str: kpi_bonus = 1500
        
    sav_bonus = 0
    sav_bonus_match = re.search(r'БОНУС ПМ:\s*(\d+)\s*₽', details_str)
    if sav_bonus_match:
        sav_bonus = int(sav_bonus_match.group(1))
        
    total_pm = base_amt + kpi_bonus + sav_bonus
    return {
        "base": base_amt,
        "goals_bonus": kpi_bonus,
        "savings_bonus": sav_bonus,
        "total": total_pm
    }

def parse_savings_data(details_str):
    saved_agency = 0
    pm_bonus = 0
    desc_list = []
    
    sav_match = re.search(r'ОПТИМИЗАЦИЯ:\s*(.*?)\s*\(Экономия:\s*(\d+)\s*₽\);\s*БОНУС ПМ:\s*(\d+)\s*₽', details_str)
    if sav_match:
        desc_list.append(f"💡 Оптимизация: {sav_match.group(1)} (Сэкономлено: {sav_match.group(2)} ₽ ➔ Бонус ПМ: {sav_match.group(3)} ₽)")
        saved_agency = int(sav_match.group(2))
        pm_bonus = int(sav_match.group(3))
    else:
        old_sav_match = re.search(r'ОПТИМИЗАЦИЯ:\s*(.*?);\s*БОНУС ПМ:\s*(\d+)\s*₽', details_str)
        if old_sav_match:
            desc_list.append(f"💡 Оптимизация: {old_sav_match.group(1)} (Бонус ПМ: {old_sav_match.group(2)} ₽)")
            pm_bonus = int(old_sav_match.group(2))
            
    goals_match = re.search(r'ЦЕЛИ:\s*(.*?);\s*(?:ВОЗНАГРАЖДЕНИЕ ЗА ЦЕЛИ|ПРЕМИЯ ЗА ЦЕЛИ):\s*(\d+)\s*₽', details_str)
    if goals_match:
        if int(goals_match.group(2)) > 0:
            desc_list.append(f"🎯 Вклад в цели: {goals_match.group(1)} (+{goals_match.group(2)} ₽)")
            
    return {
        "saved_agency": saved_agency,
        "pm_bonus": pm_bonus,
        "justification": "; \n".join(desc_list) if desc_list else "—"
    }

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
    validation_errors = []

    if selected_projects:
        for proj in selected_projects:
            st.markdown(f"### Проект: **{proj}**")
            
            is_content_package = st.checkbox("📦 Контент-пакет / Сдельная оплата", key=f"cp_{proj}")
            extra_info_list = []
            
            st.markdown("**Ваша ставка за проект (Проектный менеджер):**")
            c1, c2 = st.columns(2)
            with c1:
                pm_period = st.text_input(
                    "Период / объем (если не полный месяц)", 
                    value="", 
                    placeholder="Например: 01.07–15.07, 50% или 5 постов", 
                    key=f"pm_per_{proj}"
                )
            with c2:
                def_pm_amt = None if is_content_package else 8500
                pm_amt = st.number_input(
                    "Сумма к выплате ПМ (₽)", 
                    min_value=0,
                    max_value=1000000 if is_content_package else 8500,
                    value=def_pm_amt, 
                    placeholder="0",
                    help="Для комплексных проектов базовая ставка не может превышать 8 500 ₽" if not is_content_package else None,
                    key=f"pm_amt_{proj}"
                )
            
            safe_pm_per = pm_period.strip() if pm_period.strip() else "Полный месяц"
            safe_pm_amt = pm_amt if pm_amt is not None else 0

            if not is_content_package and safe_pm_amt > 8500:
                err_msg = f"Проект «{proj}»: базовая ставка ПМ не может превышать 8 500 ₽."
                st.error(f"⚠️ {err_msg}")
                validation_errors.append(err_msg)

            extra_info_list.append(f"РОЛЬ [Проектный менеджер]: Данные - {safe_pm_per}, Сумма - {safe_pm_amt} ₽")

            safe_goals_bonus = 0
            if not is_content_package:
                st.markdown("**🎯 Выполнение целей проекта:**")
                kpi_col1, kpi_col2 = st.columns([3, 2])
                with kpi_col1:
                    goals_desc = st.text_input(
                        "Какие цели были выполнены?", 
                        placeholder="Например: перевыполнили охваты на 25%, привлекли 40 заявок", 
                        key=f"goals_desc_{proj}"
                    )
                with kpi_col2:
                    goals_bonus = st.number_input(
                        "Оцени свой вклад в цели (до 1 500 ₽)", 
                        min_value=0, 
                        max_value=1500,
                        value=None, 
                        step=500, 
                        placeholder="0",
                        help="Максимальное вознаграждение за цели проекта — 1 500 ₽",
                        key=f"goals_bonus_{proj}"
                    )
                
                safe_goals_desc = goals_desc.strip() if goals_desc.strip() else "Без описания"
                safe_goals_bonus = goals_bonus if goals_bonus is not None else 0

                if safe_goals_bonus > 1500:
                    err_goals = f"Проект «{proj}»: вознаграждение за цели не может превышать 1 500 ₽."
                    st.error(f"⚠️ {err_goals}")
                    validation_errors.append(err_goals)

                extra_info_list.append(f"ЦЕЛИ: {safe_goals_desc}; ВОЗНАГРАЖДЕНИЕ ЗА ЦЕЛИ: {safe_goals_bonus} ₽")

            st.markdown("---")
            st.markdown("👥 **Укажите подрядчиков проекта и суммы к выплате:**")
            chosen_sub_roles = st.multiselect("Какие роли подрядчиков были на проекте?", subcontractor_roles, placeholder="Выберите роли из списка...", key=f"sub_roles_{proj}")
            
            team_declared = []
            total_subs_limit = 0
            total_subs_actual = 0

            for s_role in chosen_sub_roles:
                st.markdown(f"#### Роль: **{s_role}**")
                
                chosen_p1 = st.selectbox(
                    f"Исполнитель на роль «{s_role}»", 
                    team_members, 
                    index=None, 
                    placeholder="Выберите исполнителя...", 
                    key=f"p1_sel_{s_role}_{proj}"
                )
                
                p1_name = chosen_p1
                if chosen_p1 == "➕ Ввести новое имя":
                    p1_name = st.text_input(f"Введите имя ({s_role})", key=f"custom_p1_{s_role}_{proj}")
                
                has_second = st.checkbox(f"➕ Добавить второго исполнителя на роль «{s_role}» (подмена/разделение)", key=f"has_p2_{s_role}_{proj}")
                p2_name = None
                if has_second:
                    chosen_p2 = st.selectbox(
                        f"Второй исполнитель на роль «{s_role}»", 
                        team_members, 
                        index=None, 
                        placeholder="Выберите второго исполнителя...", 
                        key=f"p2_sel_{s_role}_{proj}"
                    )
                    p2_name = chosen_p2
                    if chosen_p2 == "➕ Ввести новое имя":
                        p2_name = st.text_input(f"Введите имя второго ({s_role})", key=f"custom_p2_{s_role}_{proj}")

                role_limit = ROLE_BASE_RATES.get(s_role, 0)
                active_people = [p for p in [p1_name, p2_name] if p]
                if active_people:
                    total_subs_limit += role_limit
                
                current_sum = 0
                people_details = []
                
                for p_idx, p in enumerate(active_people):
                    colA, colB, colC = st.columns([2, 2, 1])
                    with colA: st.markdown(f"<br>👤 **{p}**", unsafe_allow_html=True)
                    with colB: 
                        p_period = st.text_input(
                            "Период / объем", 
                            value="", 
                            placeholder="Например: 01.07–15.07, 50% или 5 постов", 
                            key=f"pper_{p}_{p_idx}_{s_role}_{proj}"
                        )
                    with colC: 
                        def_val = role_limit // len(active_people) if len(active_people) > 0 and not is_content_package else None
                        p_amt = st.number_input(
                            "Сумма ₽", 
                            min_value=0,
                            value=int(def_val) if def_val is not None else None, 
                            placeholder="0",
                            key=f"pamt_{p}_{p_idx}_{s_role}_{proj}"
                        )
                        safe_amt = p_amt if p_amt is not None else 0
                        current_sum += safe_amt
                    
                    safe_p_period = p_period.strip() if p_period.strip() else "Полный месяц"
                    safe_amt = p_amt if p_amt is not None else 0
                    people_details.append(f"{p} ({safe_p_period}, {safe_amt} ₽)")
                
                total_subs_actual += current_sum

                if current_sum > role_limit and not is_content_package and len(active_people) > 0:
                    err_sub = f"Проект «{proj}», роль «{s_role}»: сумма ({current_sum} ₽) превышает базовый лимит ({role_limit} ₽)."
                    st.error(f"⚠️ Превышение лимита бюджета! {err_sub}")
                    validation_errors.append(err_sub)
                
                if people_details:
                    team_declared.append(f"{s_role}: {', '.join(people_details)}")
            
            if team_declared:
                extra_info_list.append(f"ЗАЯВЛЕННАЯ КОМАНДА: [{'; '.join(team_declared)}]")

            real_savings = max(0, total_subs_limit - total_subs_actual) if not is_content_package else 0
            max_allowed_bonus = real_savings // 2

            st.markdown("---")
            st.markdown("**💡 Оптимизация бюджета подрядчиков:**")
            sav_col1, sav_col2, sav_col3 = st.columns([3, 2, 2])
            with sav_col1:
                savings_desc = st.text_input(
                    "За счет чего удалось сэкономить бюджет?", 
                    placeholder="Например: договорилась на пакетную скидку", 
                    key=f"sav_desc_{proj}"
                )
            with sav_col2:
                st.markdown(f"<p style='margin-bottom: 2px; font-size: 14px;'>Сэкономлено агентству (факт):</p><h3 style='margin: 0; color: #D8FD81;'>{real_savings:,.0f} ₽</h3>".replace(",", " "), unsafe_allow_html=True)
            with sav_col3:
                savings_bonus = st.number_input(
                    "Бонус менеджера (до 50%, ₽)", 
                    min_value=0, 
                    max_value=int(max_allowed_bonus) if max_allowed_bonus > 0 else 0,
                    value=None, 
                    step=250, 
                    placeholder="0",
                    help=f"Максимум 50% от реальной экономии по подрядчикам: {max_allowed_bonus} ₽",
                    key=f"sav_bonus_{proj}"
                )
            
            safe_savings_bonus = savings_bonus if savings_bonus is not None else 0

            if safe_savings_bonus > 0 and real_savings == 0:
                err_sav = f"Проект «{proj}»: нельзя начислить бонус за экономию, так как по подрядчикам выставлены максимальные ставки (экономия 0 ₽)."
                st.error(f"⚠️ {err_sav}")
                validation_errors.append(err_sav)
            elif safe_savings_bonus > max_allowed_bonus:
                err_sav = f"Проект «{proj}»: бонус менеджера ({safe_savings_bonus} ₽) превышает 50% от фактической экономии ({max_allowed_bonus} ₽)."
                st.error(f"⚠️ {err_sav}")
                validation_errors.append(err_sav)

            if safe_savings_bonus > 0:
                safe_sav_desc = savings_desc.strip() if savings_desc.strip() else "Причина не указана"
                extra_info_list.append(f"ОПТИМИЗАЦИЯ: {safe_sav_desc} (Экономия: {real_savings} ₽); БОНУС ПМ: {safe_savings_bonus} ₽")

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
            with col_ex2: task_price = st.text_input(f"Вознаграждение (₽)", placeholder="100", key=f"task_prc_{i}")
            if task_text:
                price_str = f" — {task_price}₽" if task_price.strip() else " — цена не указана"
                tasks_list.append(f"• {task_text}{price_str}")
        if tasks_list: extra_task_desc = "; ".join(tasks_list)

    st.markdown(" ")
    if validation_errors:
        st.warning("⛔ **Отправка заблокирована!** Исправьте следующие ошибки перед сдачей отчета:")
        for e in validation_errors:
            st.markdown(f"• {e}")
        st.button("🚀 Отправить отчет", disabled=True)
    else:
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
    
    if password == "оплата подрядчиков26!":
        try:
            res = requests.get(WEBHOOK_URL)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                if not df.empty and "Исполнитель" in df.columns:
                    periods = df["Период"].dropna().unique().tolist()
                    
                    ordered_default = ["Октябрь 2026", "Сентябрь 2026", "Август 2026", "Июль 2026"]
                    sorted_periods = [p for p in ordered_default if p in periods] + [p for p in periods if p not in ordered_default]
                    
                    selected_period = st.selectbox("Отчетный период:", sorted_periods if sorted_periods else periods)
                    
                    filtered_df = df[df["Период"] == selected_period]
                    
                    project_budgets = []
                    contractor_payouts = {}
                    grand_total_budget = 0
                    grand_total_saved = 0
                    
                    for idx, row in filtered_df.iterrows():
                        p_name = row["Проект"]
                        p_manager = row["Исполнитель"]
                        p_details = str(row["Детали и KPI"])
                        p_extra = str(row.get("Разовые задачи", ""))
                        
                        pm_info = parse_pm_payment_breakdown(p_details)
                        extra_sum = parse_extra_tasks_amount(p_extra)
                        subs = parse_subcontractors_from_details(p_details)
                        sav_info = parse_savings_data(p_details)
                        
                        grand_total_saved += sav_info["saved_agency"]
                        subs_sum = sum(s["sum"] for s in subs)
                        project_total = pm_info["total"] + subs_sum + extra_sum
                        grand_total_budget += project_total
                        
                        if p_manager not in contractor_payouts:
                            contractor_payouts[p_manager] = []
                        contractor_payouts[p_manager].append({
                            "project": p_name,
                            "role": "Проектный менеджер",
                            "desc": f"База {pm_info['base']} ₽ + Цели {pm_info['goals_bonus']} ₽ + Бонус {pm_info['savings_bonus']} ₽",
                            "sum": pm_info["total"] + extra_sum
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
                        project_budgets.append({
                            "Проект": p_name,
                            "Менеджер": p_manager,
                            "База ПМ": f"{pm_info['base']:,.0f} ₽",
                            "Цели (ПМ)": f"{pm_info['goals_bonus']:,.0f} ₽" if pm_info['goals_bonus'] > 0 else "—",
                            "Бонус за экономию": f"{pm_info['savings_bonus']:,.0f} ₽" if pm_info['savings_bonus'] > 0 else "—",
                            "Итого ПМ": f"{(pm_info['total'] + extra_sum):,.0f} ₽",
                            "Сэкономлено агентству": f"{sav_info['saved_agency']:,.0f} ₽" if sav_info['saved_agency'] > 0 else "0 ₽",
                            "Команда подрядчиков": ", ".join(subs_summary_list) if subs_summary_list else "Без подрядчиков",
                            "Выплаты подрядчикам": f"{subs_sum:,.0f} ₽",
                            "Иные задачи": f"{extra_sum:,.0f} ₽" if extra_sum > 0 else "—",
                            "Итого бюджет проекта": f"{project_total:,.0f} ₽",
                            "Обоснование": sav_info["justification"],
                            "raw_total": project_total
                        })
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    col_m1.metric("Проектов в отчете", len(filtered_df))
                    col_m2.metric("Специалистов к выплате", f"{len(contractor_payouts)} чел.")
                    col_m3.metric("Фактический бюджет выплат", f"{grand_total_budget:,.0f} ₽".replace(",", " "))
                    col_m4.metric("Сэкономлено агентству", f"{grand_total_saved:,.0f} ₽".replace(",", " "))
                    
                    st.markdown("---")
                    
                    st.subheader("📊 1. Таблица по бюджетам проектов")
                    st.markdown("Сводная смета по каждому проекту с прозрачной детализацией ставки, целей и бонусов ПМ.")
                    
                    df_proj = pd.DataFrame(project_budgets).drop(columns=["raw_total"])
                    st.dataframe(df_proj, use_container_width=True, hide_index=True)
                    
                    st.markdown("---")
                    
                    st.subheader("💰 2. Таблица с общей суммой к выплате на человека")
                    st.markdown("Итоговая сумма к переводу каждому специалисту, сложенная со всех проектов.")
                    
                    summary_contractors = []
                    for c_name, tasks in contractor_payouts.items():
                        c_total = sum(t["sum"] for t in tasks)
                        details_list = [f"{t['project']} ({t['role']}: {t['sum']} ₽)" for t in tasks]
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
