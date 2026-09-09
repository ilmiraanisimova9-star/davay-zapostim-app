import streamlit as st
import requests
import json
import pandas as pd
import re
from datetime import datetime

try:
    from streamlit_local_storage import LocalStorage
    local_storage_available = True
except ImportError:
    local_storage_available = False

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

local_storage = LocalStorage() if local_storage_available else None

st.sidebar.title("⚡ ДАВАЙ ЗАПОСТИМ!")
page = st.sidebar.radio("Выберите раздел:", ["📝 Сдача отчетов (Менеджеры)", "🔒 Дашборд руководителя"])

managers_list = [
    "Анастасия Мальцева", "Софья Мальцева", "Христина Рочева", "➕ Ввести другое имя"
]

default_team_members = [
    "Анастасия Мальцева", "Софья Мальцева", "Христина Рочева",
    "Светлана Кулешова", "Злата Курашова", "Вероника Липина",
    "Юлия Лодыгина", "Ева Гусева", "Дарья Витязева",
    "Виталина Куликова", "Софья Супрун"
]

default_projects = [
    "Стоматология для детей", "KISS ME FLOWERS", "Вельвет Лазер", 
    "Любимая Кухня", "Лекотека", "Рыболов Сервис", "Сулугуни", 
    "МЦ \"Да Винчи\"", "ТПП", "ООО ИНТИНСКОЕ", "Астромед", 
    "Ресторан Спасский", "Дима Третий", "KATSU", "ДАВАЙ ЗАПОСТИМ",
    "Игорь Паламарчук", "ЛОВ ШЫ"
]

if "projects_pool" not in st.session_state:
    st.session_state["projects_pool"] = list(default_projects)

if "selected_projects" not in st.session_state:
    st.session_state["selected_projects"] = []

if "team_pool" not in st.session_state:
    st.session_state["team_pool"] = list(default_team_members)

if "preview_mode" not in st.session_state:
    st.session_state["preview_mode"] = False

if "preview_data" not in st.session_state:
    st.session_state["preview_data"] = None

def clean_person_name(name_str):
    if not name_str:
        return ""
    words = name_str.strip().split()
    return " ".join(w.capitalize() for w in words)

def add_new_project_callback():
    val = st.session_state.get("new_project_text", "").strip()
    if val:
        if val not in st.session_state["projects_pool"]:
            st.session_state["projects_pool"].append(val)
        if val not in st.session_state["selected_projects"]:
            st.session_state["selected_projects"].append(val)
    st.session_state["new_project_text"] = ""

def add_new_teammate_callback():
    raw_val = st.session_state.get("new_sub_team_text", "")
    val = clean_person_name(raw_val)
    if val and val not in st.session_state["team_pool"]:
        st.session_state["team_pool"].append(val)
    st.session_state["new_sub_team_text"] = ""

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

def parse_all_pm_entries(details_str, default_manager_name):
    pm_list = []
    blocks = re.findall(r'РОЛЬ \[Проектный менеджер(?:\s*\(2-й ПМ\))?\]:\s*(?:Исполнитель:\s*([^,;]+),\s*)?Данные\s*-\s*([^,;]+),\s*Сумма\s*-\s*(\d+)\s*₽', details_str)
    
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

    if blocks:
        for idx, b in enumerate(blocks):
            raw_p_name = b[0].strip() if b[0] else ""
            p_name = raw_p_name if raw_p_name else default_manager_name
            p_desc = b[1].strip()
            p_sum = int(b[2])
            
            p_kpi = kpi_bonus if idx == 0 else 0
            p_sav = sav_bonus if idx == 0 else 0
            total = p_sum + p_kpi + p_sav
            
            pm_list.append({
                "name": p_name,
                "base": p_sum,
                "desc": p_desc,
                "goals_bonus": p_kpi,
                "savings_bonus": p_sav,
                "total": total,
                "is_second": (idx > 0)
            })
    else:
        pm_match = re.search(r'РОЛЬ \[Проектный менеджер\]: .*?Сумма - (\d+)\s*₽', details_str)
        base_amt = int(pm_match.group(1)) if pm_match else 8500
        total_pm = base_amt + kpi_bonus + sav_bonus
        pm_list.append({
            "name": default_manager_name,
            "base": base_amt,
            "desc": "Полный месяц",
            "goals_bonus": kpi_bonus,
            "savings_bonus": sav_bonus,
            "total": total_pm,
            "is_second": False
        })
    return pm_list

def parse_savings_data(details_str):
    saved_agency = 0
    pm_bonus = 0
    desc_list = []
    
    sav_match = re.search(r'ОПТИМИЗАЦИЯ:\s*(.*?)\s*\(Экономия:\s*(\d+)\s*₽\);\s*БОНУС ПМ:\s*(\d+)\s*₽', details_str)
    if sav_match:
        desc_list.append(f"💡 Оптимизация: {sav_match.group(1)} (Сэкономлено: {sav_match.group(2)} ₽ ➔ Бонус ПМ: {sav_match.group(3)} ₽)")
        saved_agency = int(sav_match.group(2))
        pm_bonus += int(sav_match.group(3))
    else:
        old_sav_match = re.search(r'ОПТИМИЗАЦИЯ:\s*(.*?);\s*БОНУС ПМ:\s*(\d+)\s*₽', details_str)
        if old_sav_match:
            desc_list.append(f"💡 Оптимизация: {old_sav_match.group(1)} (Бонус ПМ: {old_sav_match.group(2)} ₽)")
            pm_bonus += int(old_sav_match.group(2))
            
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

    # ЭКРАН 2: ПРЕДПРОСМОТР И ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ
    if st.session_state["preview_mode"] and st.session_state["preview_data"]:
        p_data = st.session_state["preview_data"]
        
        st.info("🔍 **Шаг проверки:** Пожалуйста, внимательно сверьте итоговую таблицу перед окончательной отправкой в систему.")
        st.markdown(f"### Сводная ведомость отчета: **{p_data['manager']}** ({p_data['period']})")
        
        st.dataframe(pd.DataFrame(p_data["summary_rows"]), use_container_width=True, hide_index=True)
        
        c_tot1, c_tot2 = st.columns(2)
        with c_tot1:
            st.markdown(f"#### Итого к выплате вам: <span style='color: #D8FD81;'>{p_data['total_pm']:,.0f} ₽</span>".replace(",", " "), unsafe_allow_html=True)
        with c_tot2:
            st.markdown(f"#### Итого выплаты команде/со-менеджерам: <span style='color: #B795E8;'>{p_data['total_subs']:,.0f} ₽</span>".replace(",", " "), unsafe_allow_html=True)
            
        st.markdown("---")
        
        c_act1, c_act2 = st.columns([1, 2])
        with c_act1:
            if st.button("✏️ Вернуться и исправить"):
                st.session_state["preview_mode"] = False
                st.rerun()
        with c_act2:
            if st.button("🚀 Всё верно, отправить отчет в базу!"):
                try:
                    res = requests.post(WEBHOOK_URL, json=p_data["payload"])
                    if res.status_code == 200:
                        st.success(f"✅ Отчет успешно зафиксирован в системе!")
                        st.balloons()
                        if local_storage:
                            local_storage.deleteItem("agency_report_draft")
                        st.session_state["preview_mode"] = False
                        st.session_state["preview_data"] = None
                    else:
                        st.error(f"Ошибка сохранения: статус {res.status_code}")
                except Exception as e:
                    st.error(f"Ошибка соединения: {e}")

    # ЭКРАН 1: ФОРМА ВВОДА ДАННЫХ
    else:
        st.markdown("Заполните финансовый отчет по вашим проектам и задействованным подрядчикам.")

        saved_draft = None
        if local_storage:
            try:
                saved_draft = local_storage.getItem("agency_report_draft")
                if isinstance(saved_draft, str) and saved_draft.strip().startswith("{"):
                    saved_draft = json.loads(saved_draft)
            except Exception:
                saved_draft = None

        c_draft1, c_draft2 = st.columns([1, 1])
        with c_draft1:
            if saved_draft and isinstance(saved_draft, dict):
                if st.button("📥 Восстановить черновик из памяти"):
                    for k, v in saved_draft.items():
                        if k in ["projects_pool", "team_pool", "selected_projects"]:
                            st.session_state[k] = v
                        else:
                            st.session_state[k] = v
                    st.success("Черновик успешно восстановлен!")
                    st.rerun()
        with c_draft2:
            if saved_draft:
                if st.button("🗑 Очистить сохраненный черновик"):
                    local_storage.deleteItem("agency_report_draft")
                    st.info("Черновик удален.")
                    st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            m_index = None
            if "f_manager" in st.session_state and st.session_state["f_manager"] in managers_list:
                m_index = managers_list.index(st.session_state["f_manager"])
            selected_manager = st.selectbox("Менеджер проекта", managers_list, index=m_index, placeholder="Выберите имя...", key="f_manager")
            if selected_manager == "➕ Ввести другое имя":
                manager_name_raw = st.text_input(
                    "Введите имя и фамилию менеджера (как в паспорте)", 
                    placeholder="Например: Анна Смирнова",
                    help="Важно: пишите строго сначала ИМЯ, затем ФАМИЛИЮ, как в паспорте.",
                    key="f_manager_custom"
                )
                manager_name = clean_person_name(manager_name_raw)
            else:
                manager_name = selected_manager
        with col2:
            p_periods = ["Июль 2026", "Август 2026", "Сентябрь 2026", "Октябрь 2026"]
            p_index = None
            if "f_period" in st.session_state and st.session_state["f_period"] in p_periods:
                p_index = p_periods.index(st.session_state["f_period"])
            period = st.selectbox("Отчетный период", p_periods, index=p_index, placeholder="Выберите период...", key="f_period")

        st.markdown("---")
        st.subheader("📋 Проекты под управлением")

        with st.expander("➕ Добавить новый проект (без ограничений по количеству)"):
            c_new1, c_new2 = st.columns([3, 1])
            with c_new1:
                st.text_input(
                    "Название проекта / сообщества (дословно)", 
                    placeholder="Например: KATSU | Доставка Сыктывкар",
                    help="Укажите точное название сообщества в соцсетях с сохранением регистра.",
                    key="new_project_text"
                )
            with c_new2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("➕ Добавить проект", on_click=add_new_project_callback)

        chosen_projects = st.multiselect(
            "Выберите проекты, которые вы вели в этом месяце", 
            st.session_state["projects_pool"], 
            default=st.session_state["selected_projects"],
            placeholder="Выберите проекты из списка..."
        )
        st.session_state["selected_projects"] = chosen_projects

        with st.expander("👤 Добавить нового исполнителя/подрядчика в общий список команды"):
            c_sub1, c_sub2 = st.columns([3, 1])
            with c_sub1:
                st.text_input(
                    "Имя и Фамилия подрядчика (как в паспорте)",
                    placeholder="Например: Алина Соколова",
                    help="Пишите строго: сначала Имя, затем Фамилия (как в паспорте). Подрядчик добавится в выпадающий список для всех ролей.",
                    key="new_sub_team_text"
                )
            with c_sub2:
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("➕ Добавить в команду", on_click=add_new_teammate_callback)

        task_data = {}
        validation_errors = []
        client_summary_collector = []
        total_pm_payout_calc = 0
        total_subs_payout_calc = 0

        available_team = list(st.session_state["team_pool"]) + ["➕ Ввести разово новое имя"]

        if chosen_projects:
            for proj in chosen_projects:
                st.markdown(f"### Проект: **{proj}**")
                
                is_content_package = st.checkbox("📦 Контент-пакет / Сдельная оплата", key=f"cp_{proj}")
                extra_info_list = []
                
                st.markdown("**Ваша ставка за проект (Проектный менеджер):**")
                c1, c2 = st.columns(2)
                with c1:
                    pm_period = st.text_input(
                        "Период / объем (если не полный месяц)", 
                        placeholder="Например: 01.07–15.07, 50% или 5 постов", 
                        key=f"pm_per_{proj}"
                    )
                with c2:
                    def_pm_amt = None if is_content_package else 8500
                    pm_amt = st.number_input(
                        "Сумма к выплате ПМ (₽)", 
                        min_value=0,
                        value=def_pm_amt, 
                        placeholder="0",
                        help="Для комплексных проектов базовая ставка не может превышать 8 500 ₽" if not is_content_package else None,
                        key=f"pm_amt_{proj}"
                    )
                
                safe_pm_per = pm_period.strip() if pm_period and pm_period.strip() else "Полный месяц"
                raw_pm_amt = st.session_state.get(f"pm_amt_{proj}", pm_amt)
                safe_pm_amt = raw_pm_amt if raw_pm_amt is not None else 0

                extra_info_list.append(f"РОЛЬ [Проектный менеджер]: Данные - {safe_pm_per}, Сумма - {safe_pm_amt} ₽")

                # РАЗДЕЛЕНИЕ СТАВКИ МЕНЕДЖЕРА
                has_second_pm = st.checkbox("➕ Разделить менеджерскую ставку (второй ПМ / подмена / менеджер на съемке)", key=f"has_pm2_{proj}")
                safe_pm2_amt = 0
                pm2_name = None
                safe_pm2_per = ""

                if has_second_pm:
                    st.markdown("##### Второй менеджер проекта:")
                    col_pm2_a, col_pm2_b, col_pm2_c = st.columns([2, 2, 1])
                    with col_pm2_a:
                        chosen_pm2 = st.selectbox(
                            "Выберите второго менеджера", 
                            available_team, 
                            index=None, 
                            placeholder="Выберите специалиста...", 
                            key=f"pm2_sel_{proj}"
                        )
                        pm2_name = chosen_pm2
                        if chosen_pm2 == "➕ Ввести разово новое имя":
                            pm2_custom = st.text_input(
                                "Имя и Фамилия второго менеджера", 
                                placeholder="Например: Анастасия Мальцева", 
                                key=f"pm2_custom_{proj}"
                            )
                            pm2_name = clean_person_name(pm2_custom)
                    with col_pm2_b:
                        pm2_period = st.text_input(
                            "Период / роль второго ПМ", 
                            placeholder="Например: менеджер на съемке, 50% месяца", 
                            key=f"pm2_per_{proj}"
                        )
                        safe_pm2_per = pm2_period.strip() if pm2_period and pm2_period.strip() else "Со-менеджер"
                    with col_pm2_c:
                        pm2_amt = st.number_input(
                            "Сумма второму ПМ (₽)", 
                            min_value=0, 
                            value=None, 
                            placeholder="0", 
                            key=f"pm2_amt_{proj}"
                        )
                        raw_pm2_amt = st.session_state.get(f"pm2_amt_{proj}", pm2_amt)
                        safe_pm2_amt = raw_pm2_amt if raw_pm2_amt is not None else 0

                    if pm2_name:
                        extra_info_list.append(f"РОЛЬ [Проектный менеджер (2-й ПМ)]: Исполнитель: {pm2_name}, Данные - {safe_pm2_per}, Сумма - {safe_pm2_amt} ₽")
                        total_subs_payout_calc += safe_pm2_amt
                        client_summary_collector.append({
                            "Проект / Задача": proj,
                            "Кому выплата (ФИО)": pm2_name,
                            "Роль": "Проектный менеджер (со-менеджер)",
                            "Детали / Объем": safe_pm2_per,
                            "Сумма": f"{safe_pm2_amt:,.0f} ₽".replace(",", " ")
                        })

                combined_pm_base = safe_pm_amt + safe_pm2_amt
                if not is_content_package and combined_pm_base > 8500:
                    err_msg = f"Проект «{proj}»: суммарная ставка проектных менеджеров ({combined_pm_base} ₽) не может превышать 8 500 ₽."
                    st.error(f"⚠️ {err_msg}")
                    validation_errors.append(err_msg)

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
                            value=None, 
                            step=500, 
                            placeholder="0",
                            help="Максимальное вознаграждение за цели проекта — 1 500 ₽",
                            key=f"goals_bonus_{proj}"
                        )
                    
                    safe_goals_desc = goals_desc.strip() if goals_desc and goals_desc.strip() else "Без описания"
                    raw_goals_bonus = st.session_state.get(f"goals_bonus_{proj}", goals_bonus)
                    safe_goals_bonus = raw_goals_bonus if raw_goals_bonus is not None else 0

                    if safe_goals_bonus > 1500:
                        err_goals = f"Проект «{proj}»: вознаграждение за цели ({safe_goals_bonus} ₽) не может превышать 1 500 ₽."
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
                        available_team, 
                        index=None, 
                        placeholder="Выберите исполнителя...", 
                        key=f"p1_sel_{s_role}_{proj}"
                    )
                    
                    p1_name = chosen_p1
                    if chosen_p1 == "➕ Ввести разово новое имя":
                        p1_custom = st.text_input(
                            f"Введите имя и фамилию ({s_role})", 
                            placeholder="Например: Иван Иванов (строго: Имя Фамилия)", 
                            help="Пишите строго: сначала Имя, затем Фамилия (как в паспорте).",
                            key=f"custom_p1_{s_role}_{proj}"
                        )
                        p1_name = clean_person_name(p1_custom)
                    
                    has_second = st.checkbox(f"➕ Добавить второго исполнителя на роль «{s_role}» (подмена/разделение)", key=f"has_p2_{s_role}_{proj}")
                    p2_name = None
                    if has_second:
                        chosen_p2 = st.selectbox(
                            f"Второй исполнитель на роль «{s_role}»", 
                            available_team, 
                            index=None, 
                            placeholder="Выберите второго исполнителя...", 
                            key=f"p2_sel_{s_role}_{proj}"
                        )
                        p2_name = chosen_p2
                        if chosen_p2 == "➕ Ввести разово новое имя":
                            p2_custom = st.text_input(
                                f"Введите имя и фамилию второго ({s_role})", 
                                placeholder="Например: Мария Петрова (строго: Имя Фамилия)", 
                                help="Пишите строго: сначала Имя, затем Фамилия (как в паспорте).",
                                key=f"custom_p2_{s_role}_{proj}"
                            )
                            p2_name = clean_person_name(p2_custom)

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
                            raw_p_amt = st.session_state.get(f"pamt_{p}_{p_idx}_{s_role}_{proj}", p_amt)
                            safe_amt = raw_p_amt if raw_p_amt is not None else 0
                            current_sum += safe_amt
                        
                        safe_p_period = p_period.strip() if p_period and p_period.strip() else "Полный месяц"
                        people_details.append(f"{p} ({safe_p_period}, {safe_amt} ₽)")
                        
                        client_summary_collector.append({
                            "Проект / Задача": proj,
                            "Кому выплата (ФИО)": p,
                            "Роль": s_role,
                            "Детали / Объем": safe_p_period,
                            "Сумма": f"{safe_amt:,.0f} ₽".replace(",", " ")
                        })
                        total_subs_payout_calc += safe_amt
                    
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
                        value=None, 
                        step=250, 
                        placeholder="0",
                        help=f"Максимум 50% от реальной экономии по подрядчикам: {max_allowed_bonus} ₽",
                        key=f"sav_bonus_{proj}"
                    )
                
                raw_savings_bonus = st.session_state.get(f"sav_bonus_{proj}", savings_bonus)
                safe_savings_bonus = raw_savings_bonus if raw_savings_bonus is not None else 0

                if safe_savings_bonus > 0 and real_savings == 0:
                    err_sav = f"Проект «{proj}»: нельзя начислить бонус за экономию, так как по подрядчикам выставлены максимальные ставки (экономия 0 ₽)."
                    st.error(f"⚠️ {err_sav}")
                    validation_errors.append(err_sav)
                elif safe_savings_bonus > max_allowed_bonus:
                    err_sav = f"Проект «{proj}»: бонус менеджера ({safe_savings_bonus} ₽) превышает 50% от фактической экономии ({max_allowed_bonus} ₽)."
                    st.error(f"⚠️ {err_sav}")
                    validation_errors.append(err_sav)

                if safe_savings_bonus > 0:
                    safe_sav_desc = savings_desc.strip() if savings_desc and savings_desc.strip() else "Причина не указана"
                    extra_info_list.append(f"ОПТИМИЗАЦИЯ: {safe_sav_desc} (Экономия: {real_savings} ₽); БОНУС ПМ: {safe_savings_bonus} ₽")

                pm_project_total = safe_pm_amt + safe_goals_bonus + safe_savings_bonus
                total_pm_payout_calc += pm_project_total
                
                pm_details_str = f"База: {safe_pm_amt} ₽"
                if safe_goals_bonus > 0:
                    pm_details_str += f" + Цели: {safe_goals_bonus} ₽"
                if safe_savings_bonus > 0:
                    pm_details_str += f" + Бонус экономии: {safe_savings_bonus} ₽"

                client_summary_collector.append({
                    "Проект / Задача": proj,
                    "Кому выплата (ФИО)": manager_name if manager_name else "ПМ",
                    "Роль": "Проектный менеджер (ведущий)",
                    "Детали / Объем": pm_details_str,
                    "Сумма": f"{pm_project_total:,.0f} ₽".replace(",", " ")
                })

                task_data[proj] = {
                    "roles": "Проектный менеджер", 
                    "extra": "; ".join(extra_info_list)
                }
                st.markdown("---")

        st.subheader("✨ Иные задачи, не учтённые выше")
        has_extra = st.checkbox("Были ли иные задачи за отчетный период?", key="has_extra_tasks_toggle")
        extra_task_desc = ""
        extra_tasks_sum = 0
        if has_extra:
            task_count = st.number_input("Сколько иных задач вы согласовали?", min_value=1, max_value=10, value=1, key="extra_task_count")
            tasks_list = []
            for i in range(int(task_count)):
                col_ex1, col_ex2 = st.columns([3, 1])
                with col_ex1: task_text = st.text_input(f"Описание задачи №{i+1}", placeholder="Например: разработка брендбука", key=f"task_txt_{i}")
                with col_ex2: task_price = st.text_input(f"Вознаграждение (₽)", placeholder="100", key=f"task_prc_{i}")
                if task_text:
                    num_p = int(re.sub(r'\D', '', task_price)) if re.sub(r'\D', '', task_price) else 0
                    extra_tasks_sum += num_p
                    price_str = f" — {task_price}₽" if task_price and task_price.strip() else " — цена не указана"
                    tasks_list.append(f"• {task_text}{price_str}")
                    
                    client_summary_collector.append({
                        "Проект / Задача": "⚡ Иные задачи",
                        "Кому выплата (ФИО)": manager_name if manager_name else "ПМ",
                        "Роль": "Разовое поручение",
                        "Детали / Объем": task_text,
                        "Сумма": f"{num_p:,.0f} ₽".replace(",", " ")
                    })
            if tasks_list: extra_task_desc = "; ".join(tasks_list)
            total_pm_payout_calc += extra_tasks_sum

        st.markdown(" ")

        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn2:
            if st.button("💾 Сохранить черновик"):
                if local_storage:
                    draft_to_save = {}
                    for k, v in st.session_state.items():
                        if k.startswith(("f_", "cp_", "pm_", "has_pm2_", "pm2_", "goals_", "sub_roles_", "p1_", "p2_", "has_p2_", "custom_p", "pper_", "pamt_", "sav_", "task_", "extra_", "has_extra_")):
                            draft_to_save[k] = v
                    draft_to_save["projects_pool"] = st.session_state.get("projects_pool", default_projects)
                    draft_to_save["selected_projects"] = st.session_state.get("selected_projects", [])
                    draft_to_save["team_pool"] = st.session_state.get("team_pool", default_team_members)
                    
                    local_storage.setItem("agency_report_draft", json.dumps(draft_to_save))
                    st.success("💾 Черновик сохранен в браузере! Данные не пропадут.")
                else:
                    st.warning("Библиотека LocalStorage не установлена.")

        with col_btn1:
            if validation_errors:
                st.warning("⛔ **Проверка заблокирована!** Исправьте ошибки перед отправкой:")
                for e in validation_errors:
                    st.markdown(f"• {e}")
                st.button("👁 Предпросмотр и проверка отчета", disabled=True)
            else:
                if st.button("👁 Предпросмотр и проверка отчета"):
                    if not manager_name or manager_name.strip() == "": 
                        st.error("Пожалуйста, выберите имя менеджера.")
                    elif not period: 
                        st.error("Пожалуйста, выберите отчетный период.")
                    elif not chosen_projects: 
                        st.error("Выберите хотя бы один проект.")
                    else:
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        payload = []
                        for idx, (proj, data) in enumerate(task_data.items()):
                            payload.append({
                                "Дата и время": now_str, "Исполнитель": manager_name, "Период": period,
                                "Проект": proj, "Роли": data["roles"], "Детали и KPI": data["extra"],
                                "Разовые задачи": extra_task_desc if idx == 0 else ""
                            })
                        
                        st.session_state["preview_data"] = {
                            "manager": manager_name,
                            "period": period,
                            "summary_rows": client_summary_collector,
                            "total_pm": total_pm_payout_calc,
                            "total_subs": total_subs_payout_calc,
                            "payload": payload
                        }
                        st.session_state["preview_mode"] = True
                        st.rerun()

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
                    
                    project_rows = []
                    project_details_map = {}
                    contractor_payouts = {}
                    extra_tasks_records = []
                    seen_extras = set()
                    
                    grand_total_projects = 0
                    grand_total_extras = 0
                    grand_total_saved = 0
                    
                    for idx, row in filtered_df.iterrows():
                        p_name = row["Проект"]
                        p_manager = row["Исполнитель"]
                        p_details = str(row["Детали и KPI"])
                        p_extra = str(row.get("Разовые задачи", ""))
                        
                        all_pms = parse_all_pm_entries(p_details, p_manager)
                        lead_pm = all_pms[0]
                        second_pms = all_pms[1:] if len(all_pms) > 1 else []
                        
                        subs = parse_subcontractors_from_details(p_details)
                        sav_info = parse_savings_data(p_details)
                        
                        subs_sum = sum(s["sum"] for s in subs)
                        second_pm_sum = sum(sp["sum"] if "sum" in sp else sp["base"] for sp in second_pms)
                        all_pms_total = sum(p["total"] for p in all_pms)
                        
                        project_clean_total = all_pms_total + subs_sum
                        grand_total_projects += project_clean_total
                        grand_total_saved += sav_info["saved_agency"]
                        
                        for p_person in all_pms:
                            name_pm = p_person["name"]
                            if name_pm not in contractor_payouts:
                                contractor_payouts[name_pm] = {"projects": [], "extras": 0, "extra_items": []}
                            
                            p_desc_list = [f"База: {p_person['base']} ₽"]
                            if p_person['goals_bonus'] > 0:
                                p_desc_list.append(f"Цели: +{p_person['goals_bonus']} ₽")
                            if p_person['savings_bonus'] > 0:
                                p_desc_list.append(f"Бонус за экономию: +{p_person['savings_bonus']} ₽")
                                
                            role_label = "Проектный менеджер" if not p_person["is_second"] else "Проектный менеджер (со-менеджер)"
                            contractor_payouts[name_pm]["projects"].append({
                                "project": p_name,
                                "role": role_label,
                                "desc": ", ".join(p_desc_list),
                                "sum": p_person["total"]
                            })
                        
                        for s in subs:
                            c_name = s["name"]
                            if c_name not in contractor_payouts:
                                contractor_payouts[c_name] = {"projects": [], "extras": 0, "extra_items": []}
                            contractor_payouts[c_name]["projects"].append({
                                "project": p_name,
                                "role": s["role"],
                                "desc": s["desc"],
                                "sum": s["sum"]
                            })
                        
                        extra_sum = parse_extra_tasks_amount(p_extra)
                        if extra_sum > 0:
                            clean_task_name = re.sub(r'\s*—\s*\d+\s*₽?', '', p_extra).strip()
                            clean_task_name = clean_task_name.lstrip("•").strip()
                            
                            extra_key = (p_manager, clean_task_name, extra_sum)
                            if extra_key not in seen_extras:
                                seen_extras.add(extra_key)
                                grand_total_extras += extra_sum
                                contractor_payouts[p_manager]["extras"] += extra_sum
                                contractor_payouts[p_manager]["extra_items"].append({
                                    "desc": clean_task_name,
                                    "sum": extra_sum
                                })
                                extra_tasks_records.append({
                                    "Менеджер": p_manager,
                                    "Задача": clean_task_name,
                                    "Сумма": f"{extra_sum:,.0f} ₽".replace(",", " ")
                                })
                        
                        project_rows.append({
                            "Проект": p_name,
                            "Ведущий ПМ": p_manager,
                            "ПМ: База (все)": f"{sum(p['base'] for p in all_pms):,.0f} ₽",
                            "ПМ: Цели": f"{lead_pm['goals_bonus']:,.0f} ₽" if lead_pm['goals_bonus'] > 0 else "—",
                            "ПМ: Бонус за экономию": f"{lead_pm['savings_bonus']:,.0f} ₽" if lead_pm['savings_bonus'] > 0 else "—",
                            "Выплаты подрядчикам": f"{subs_sum:,.0f} ₽",
                            "Итого расход на проект": f"{project_clean_total:,.0f} ₽",
                            "Сэкономлено агентству": f"{sav_info['saved_agency']:,.0f} ₽" if sav_info['saved_agency'] > 0 else "0 ₽",
                            "raw_total": project_clean_total
                        })
                        
                        project_details_map[p_name] = {
                            "manager": p_manager,
                            "all_pms": all_pms,
                            "subs": subs,
                            "sav_info": sav_info,
                            "project_clean_total": project_clean_total
                        }

                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    col_m1.metric("Проектов в отчете", len(filtered_df))
                    col_m2.metric("Специалистов к выплате", f"{len(contractor_payouts)} чел.")
                    col_m3.metric("Бюджет проектов (факт)", f"{grand_total_projects:,.0f} ₽".replace(",", " "))
                    col_m4.metric("Сэкономлено агентству", f"{grand_total_saved:,.0f} ₽".replace(",", " "))
                    
                    st.markdown("---")
                    
                    st.subheader("📊 1. Бюджеты проектов (чистая экономика)")
                    st.markdown("Сводная смета строго по проектным расходам клиента без примеси разовых агентских поручений.")
                    
                    df_proj = pd.DataFrame(project_rows).drop(columns=["raw_total"])
                    st.dataframe(df_proj, use_container_width=True, hide_index=True)
                    
                    with st.expander("🔍 Карточка детального просмотра проекта (состав команды и обоснования)"):
                        selected_detail_proj = st.selectbox("Выберите проект для изучения:", list(project_details_map.keys()))
                        if selected_detail_proj:
                            p_info = project_details_map[selected_detail_proj]
                            cd1, cd2 = st.columns(2)
                            with cd1:
                                st.markdown(f"**Ответственные менеджеры:**")
                                for pm_i in p_info["all_pms"]:
                                    tag = " (ведущий)" if not pm_i["is_second"] else " (со-менеджер / выезд)"
                                    st.markdown(f"• **{pm_i['name']}{tag}:** ставка {pm_i['base']} ₽ ({pm_i['desc']})")
                                    if pm_i['goals_bonus'] > 0:
                                        st.markdown(f"  └ Доплата за цели: +{pm_i['goals_bonus']} ₽")
                                    if pm_i['savings_bonus'] > 0:
                                        st.markdown(f"  └ Бонус за экономию: +{pm_i['savings_bonus']} ₽")
                                st.markdown(f"**Обоснования бонусов и целей:**\n\n{p_info['sav_info']['justification']}")
                            with cd2:
                                st.markdown("**Команда подрядчиков на проекте:**")
                                if p_info["subs"]:
                                    for s in p_info["subs"]:
                                        st.markdown(f"• **{s['role']}:** {s['name']} — {s['sum']} ₽ ({s['desc']})")
                                    
                                    unique_roles = set(s['role'] for s in p_info['subs'])
                                    planned_subs = sum(ROLE_BASE_RATES.get(r, 0) for r in unique_roles)
                                    actual_subs = sum(s['sum'] for s in p_info['subs'])
                                    
                                    st.markdown("---")
                                    st.markdown(f"**Заложено по смете ролей подрядчиков:** **{planned_subs:,.0f} ₽**".replace(",", " "))
                                    
                                    if actual_subs > planned_subs:
                                        over_amt = actual_subs - planned_subs
                                        st.markdown(
                                            f"**Фактически за месяц:** <span style='color: #FF4B4B; font-weight: 800; font-size: 16px;'>{actual_subs:,.0f} ₽ ⚠️ (Превышение лимита на {over_amt:,.0f} ₽)</span>".replace(",", " "), 
                                            unsafe_allow_html=True
                                        )
                                    else:
                                        saved_amt = planned_subs - actual_subs
                                        status_label = f" (экономия {saved_amt:,.0f} ₽)" if saved_amt > 0 else " (в рамках сметы)"
                                        st.markdown(
                                            f"**Фактически за месяц:** <span style='color: #D8FD81; font-weight: 800; font-size: 16px;'>{actual_subs:,.0f} ₽</span> <span style='color: #A6A6A6;'>{status_label}</span>".replace(",", " "), 
                                            unsafe_allow_html=True
                                        )
                                else:
                                    st.markdown("— Подрядчики не привлекались")

                    if extra_tasks_records:
                        st.markdown("---")
                        st.subheader("✨ Разовые поручения / Иные задачи")
                        st.markdown("Задачи, не входящие в стандартные сметы проектов (личные поручения, внутренние задачи агентства).")
                        st.dataframe(pd.DataFrame(extra_tasks_records), use_container_width=True, hide_index=True)

                    st.markdown("---")
                    st.subheader("💰 2. Таблица к выплате на человека")
                    st.markdown("Итоговая сумма к перечислению каждому специалисту с детализацией по проектам и разовым задачам.")
                    
                    summary_contractors = []
                    for c_name, data in contractor_payouts.items():
                        proj_total = sum(t["sum"] for t in data["projects"])
                        final_total = proj_total + data["extras"]
                        
                        lines = [f"{t['project']} ({t['role']}: {t['sum']} ₽)" for t in data["projects"]]
                        if data["extras"] > 0:
                            lines.append(f"Иные задачи: {data['extras']} ₽")
                            
                        summary_contractors.append({
                            "Специалист": c_name,
                            "Итого к выплате": f"{final_total:,.0f} ₽".replace(",", " "),
                            "Проектов": len(data["projects"]),
                            "Детализация выплат": " | ".join(lines),
                            "raw_total": final_total,
                            "raw_data": data
                        })
                    
                    df_contractors = pd.DataFrame(summary_contractors).sort_values(by="raw_total", ascending=False)
                    st.dataframe(df_contractors.drop(columns=["raw_total", "raw_data"]), use_container_width=True, hide_index=True)

                    with st.expander("💳 Расчетный лист по специалисту перед переводом", expanded=True):
                        c_names_list = [row["Специалист"] for row in summary_contractors]
                        chosen_c = st.selectbox("Выберите специалиста для проверки:", c_names_list)
                        if chosen_c:
                            c_record = next(item for item in summary_contractors if item["Специалист"] == chosen_c)
                            c_data = c_record["raw_data"]
                            
                            st.markdown(f"### Итого к выплате **{chosen_c}**: <span style='color: #D8FD81;'>{c_record['Итого к выплате']}</span>", unsafe_allow_html=True)
                            
                            sheet_rows = []
                            for p_entry in c_data["projects"]:
                                sheet_rows.append({
                                    "Проект / Источник": p_entry["project"],
                                    "Роль": p_entry["role"],
                                    "Примечание / Детали": p_entry["desc"],
                                    "Сумма к выплате": f"{p_entry['sum']:,.0f} ₽".replace(",", " ")
                                })
                            
                            if c_data["extra_items"]:
                                for ex_item in c_data["extra_items"]:
                                    sheet_rows.append({
                                        "Проект / Источник": "⚡ Разовые поручения",
                                        "Роль": "Иные задачи",
                                        "Примечание / Детали": ex_item["desc"],
                                        "Сумма к выплате": f"{ex_item['sum']:,.0f} ₽".replace(",", " ")
                                    })
                            
                            df_sheet = pd.DataFrame(sheet_rows)
                            st.dataframe(df_sheet, use_container_width=True, hide_index=True)

        except Exception as e: st.error(f"Ошибка загрузки: {e}")
    elif password != "": st.error("Неверный пароль.")
