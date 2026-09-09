with st.expander("➕ Добавить новый проект (без ограничений по количеству)"):
        c_new1, c_new2 = st.columns([3, 1])
        with c_new1:
            new_proj_input = st.text_input(
                "Название проекта / сообщества (дословно)", 
                placeholder="Например: KATSU | Доставка Сыктывкар",
                help="Укажите точное название сообщества в соцсетях с сохранением регистра.",
                key="new_project_text"
            )
        with c_new2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Добавить проект"):
                clean_name = new_proj_input.strip()
                if clean_name:
                    if clean_name not in st.session_state["projects_pool"]:
                        st.session_state["projects_pool"].append(clean_name)
                    if clean_name not in st.session_state["selected_projects"]:
                        st.session_state["selected_projects"].append(clean_name)
                    st.rerun()

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
            new_sub_input = st.text_input(
                "Имя и Фамилия подрядчика (как в паспорте)",
                placeholder="Например: Алина Соколова",
                help="Пишите строго: сначала Имя, затем Фамилия (как в паспорте). Подрядчик добавится в выпадающий список для всех ролей.",
                key="new_sub_team_text"
            )
        with c_sub2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Добавить в команду"):
                clean_sub = clean_person_name(new_sub_input)
                if clean_sub and clean_sub not in st.session_state["team_pool"]:
                    st.session_state["team_pool"].append(clean_sub)
                    st.rerun()
