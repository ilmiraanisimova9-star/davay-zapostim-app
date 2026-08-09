import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="ДАВАЙ ЗАПОСТИМ! — Сдача отчетов", page_icon="📊", layout="centered")

st.title("📊 ДАВАЙ ЗАПОСТИМ! — Сдача отчетов за месяц")
st.markdown("Пожалуйста, заполните форму отчета. Вы можете выбрать **несколько проектов и ролей** одновременно.")

executors = [
    "Христина Рочева", 
    "Анастасия Мальцева", 
    "Маша", 
    "Софья Мальцева", 
    "Светлана Кулешова", 
    "Злата", 
    "Юля"
]

projects = [
    "Стоматология для детей",
    "KISS ME FLOWERS",
    "Вельвет Лазер",
    "Любимая Кухня",
    "Лекотека",
    "Рыболов Сервис",
    "Сулугуни",
    "МЦ \"Да Винчи\"",
    "ТПП",
    "ООО ИНТИНСКОЕ",
    "Астромед",
    "Ресторан Спасский",
    "Дима Третий",
    "KATSU",
    "ДАВАЙ ЗАПОСТИМ"
]

roles = [
    "Проектный менеджер",
    "Контентмейкер",
    "Видеограф",
    "Дизайнер",
    "Монтажер",
    "Региональная управляющая"
]

with st.form("report_form"):
    col1, col2 = st.columns(2)
    with col1:
        executor = st.selectbox("Ваше ФИО (Исполнитель)", executors)
    with col2:
        period = st.selectbox("Отчетный период", ["Июль 2026", "Август 2026", "Сентябрь 2026"])
    
    st.markdown("---")
    st.subheader("📋 Проекты и выполняемые роли")
    
    selected_projects = st.multiselect("Выберите проекты", projects)
    
    task_data = {}
    if selected_projects:
        st.markdown("### Детали по выбранным проектам:")
        for proj in selected_projects:
            st.markdown(f"**Проект: {proj}**")
            proj_roles = st.multiselect(f"Роли в проекте \"{proj}\"", roles, key=f"roles_{proj}")
            
            extra_info = {}
            if "Проектный менеджер" in proj_roles:
                extra_info["kpi_goals"] = st.selectbox(f"Достигнуто KPI целей ({proj})", ["0 целей (0₽)", "1 цель (500₽)", "2 цели (1000₽)", "3 цели (1500₽)"], key=f"kpi_{proj}")
                if proj in ["Стоматология для детей", "Рыболов Сервис", "МЦ \"Да Винчи\""]:
                    extra_info["cards"] = st.checkbox(f"Ведение картографических сервисов (+2500₽ к премии) [{proj}]", key=f"cards_{proj}")
                if proj == "ООО ИНТИНСКОЕ":
                    extra_info["community"] = st.checkbox(f"Комьюнити-менеджмент (+1500₽) [{proj}]", key=f"comm_{proj}")
            
            if proj in ["Ресторан Спасский", "Сулугуни", "Астромед"]:
                extra_info["volume_type"] = st.selectbox(f"Тип сдельного объема ({proj})", ["Посты", "Клипы"], key=f"v_type_{proj}")
                extra_info["volume_count"] = st.number_input(f"Количество единиц ({proj})", min_value=0, value=0, key=f"v_count_{proj}")

            task_data[proj] = {
                "roles": proj_roles,
                "extra": extra_info
            }
            st.markdown("---")

    st.subheader("✨ Разовые и дополнительные задачи")
    has_extra = st.checkbox("Были ли разовые задачи вне основного тарифа?")
    extra_task_desc = ""
    if has_extra:
        extra_task_desc = st.text_area("Опишите задачу и запрашиваемую сумму")

    submitted = st.form_submit_button("🚀 Отправить отчет")

    if submitted:
        if not executor or not selected_projects:
            st.error("Пожалуйста, выберите ваше ФИО и хотя бы один проект.")
        else:
            st.success("Отчет успешно сформирован и передан в систему!")
            st.json({
                "executor": executor,
                "period": period,
                "tasks": task_data,
                "extra_task": extra_task_desc,
                "timestamp": str(datetime.now())
            })
