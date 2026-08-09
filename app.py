import streamlit as st
from datetime import datetime

st.set_page_config(page_title="ДАВАЙ ЗАПОСТИМ! — Сдача отчетов", page_icon="📊", layout="centered")

st.title("📊 ДАВАЙ ЗАПОСТИМ! — Сдача отчетов за месяц")
st.markdown("Заполните форму отчета за прошедший месяц. Вы можете выбрать **несколько проектов и несколько ролей** одновременно.")

# Список исполнителей
executors = [
    "Христина Рочева", 
    "Анастасия Мальцева", 
    "Маша", 
    "Софья Мальцева", 
    "Светлана Кулешова", 
    "Злата", 
    "Юля"
]

# Проекты
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

# Роли
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
    
    selected_projects = st.multiselect("Выберите проекты, над которыми работали", projects)
    
    task_data = {}
    total_calculated = 0
    
    if selected_projects:
        st.markdown("### Детализация по проектам:")
        for proj in selected_projects:
            st.markdown(f"#### Проект: **{proj}**")
            proj_roles = st.multiselect(f"Выберите ваши роли в проекте «{proj}»", roles, key=f"roles_{proj}")
            
            extra_info = {}
            if "Проектный менеджер" in proj_roles:
                kpi = st.selectbox(f"Достигнуто KPI целей ({proj})", ["0 целей (0₽)", "1 цель (500₽)", "2 цели (1000₽)", "3 цели (1500₽)"], key=f"kpi_{proj}")
                extra_info["kpi"] = kpi
                
                if proj in ["Стоматология для детей", "Рыболов Сервис", "МЦ \"Да Винчи\""]:
                    cards = st.checkbox(f"Ведение картографических сервисов (+2500₽ к премии) [{proj}]", key=f"cards_{proj}")
                    extra_info["cards"] = cards
                    
                if proj == "ООО ИНТИНСКОЕ":
                    community = st.checkbox(f"Комьюнити-менеджмент (+1500₽) [{proj}]", key=f"comm_{proj}")
                    extra_info["community"] = community

            if proj in ["Ресторан Спасский", "Сулугуни", "Астромед"]:
                v_type = st.selectbox(f"Тип сдельного объема ({proj})", ["Посты", "Клипы"], key=f"v_type_{proj}")
                v_count = st.number_input(f"Количество единиц ({proj})", min_value=0, value=0, key=f"v_count_{proj}")
                extra_info["v_type"] = v_type
                extra_info["v_count"] = v_count

            task_data[proj] = {"roles": proj_roles, "extra": extra_info}
            st.markdown("---")

    st.subheader("✨ Разовые и дополнительные задачи")
    has_extra = st.checkbox("Были ли разовые задачи вне основного тарифа?")
    extra_task_desc = ""
    if has_extra:
        extra_task_desc = st.text_area("Опишите выполненную задачу и запрашиваемую сумму")

    submitted = st.form_submit_button("🚀 Отправить отчет")

    if submitted:
        # Проверка заполнения
        empty_roles = [p for p, data in task_data.items() if not data["roles"]]
        
        if not executor or not selected_projects:
            st.error("Ошибка: выберите ваше ФИО и хотя бы один проект.")
        elif empty_roles:
            st.error(f"Ошибка: вы не выбрали роли для следующих проектов: {', '.join(empty_roles)}")
        else:
            st.success("✅ Отчет успешно сформирован и передан на утверждение!")
            st.balloons()
            st.info("Ваши данные приняты. Расчет выплат будет доступен в сводном ведомости.")
