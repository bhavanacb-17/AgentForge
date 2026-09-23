import streamlit as st

from api.client import AgentForgeAPI


def show_projects_dashboard(user_id=1):

    st.title("🚀 AgentForge Projects")
    st.write("Manage your software engineering projects.")

    # -------------------------------------------------
    # Search and Filter
    # -------------------------------------------------

    col1, col2 = st.columns([2, 1])

    with col1:
        search_text = st.text_input(
            "🔎 Search Projects",
            placeholder="Search by project name or description...",
            key="project_search"
        )

    with col2:
        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Active",
                "In Progress",
                "Completed",
                "Archived"
            ],
            key="project_status_filter"
        )

    st.divider()

    # -------------------------------------------------
    # Get Projects from Django API
    # -------------------------------------------------

    try:
        all_projects = AgentForgeAPI.get_projects()

    except Exception as error:
        st.error(f"Unable to load projects: {error}")
        return

    # -------------------------------------------------
    # Filter Projects
    # -------------------------------------------------

    projects = all_projects

    if search_text.strip():
        search_value = search_text.strip().lower()

        projects = [
            project
            for project in projects
            if search_value in project.get("name", "").lower()
            or search_value in project.get("description", "").lower()
        ]

    if status_filter != "All":

        status_value = status_filter.lower().replace(" ", "_")

        projects = [
            project
            for project in projects
            if project.get("status", "").lower() == status_value
        ]

    # -------------------------------------------------
    # Create Project Button
    # -------------------------------------------------

    if st.button(
        "➕ Create New Project",
        type="primary",
        key="create_project_button"
    ):
        st.session_state["show_create_project"] = True

    # -------------------------------------------------
    # Create Project Form
    # -------------------------------------------------

    if st.session_state.get("show_create_project", False):

        st.subheader("Create New Project")

        with st.form("create_project_form"):

            name = st.text_input(
                "Project Name",
                placeholder="Example: Student Management System"
            )

            description = st.text_area(
                "Description",
                placeholder="Describe your project..."
            )

            requirements = st.text_area(
                "Requirements",
                placeholder="Enter project requirements..."
            )

            category = st.selectbox(
                "Category",
                [
                    "Web Application",
                    "Mobile Application",
                    "Desktop Application",
                    "API",
                    "AI / Machine Learning",
                    "Other"
                ]
            )

            programming_language = st.selectbox(
                "Programming Language",
                [
                    "Python",
                    "Java",
                    "JavaScript",
                    "TypeScript",
                    "C++",
                    "C#"
                ]
            )

            framework = st.text_input(
                "Framework",
                placeholder="Example: Django / React / Spring Boot"
            )

            database = st.text_input(
                "Database",
                placeholder="Example: MySQL / PostgreSQL"
            )

            additional_instructions = st.text_area(
                "Additional Instructions",
                placeholder="Any additional instructions..."
            )

            submitted = st.form_submit_button(
                "Create Project",
                type="primary"
            )

            if submitted:

                if not name.strip():
                    st.error("Project name is required.")

                elif not description.strip():
                    st.error("Project description is required.")

                else:

                    project_data = {
                        "name": name.strip(),
                        "description": description.strip(),
                        "requirements": requirements.strip(),
                        "category": category,
                        "programming_language": programming_language,
                        "framework": framework.strip(),
                        "database": database.strip(),
                        "additional_instructions": additional_instructions.strip(),
                        "status": "active",
                        "ai_model": "Gemini",
                        "owner": user_id
                    }

                    try:

                        created_project = AgentForgeAPI.create_project(
                            project_data
                        )

                        project_id = created_project["id"]

                        st.success(
                            f"Project created successfully! ID: {project_id}"
                        )

                        st.session_state["show_create_project"] = False

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Unable to create project: {error}"
                        )

    # -------------------------------------------------
    # Display Projects
    # -------------------------------------------------

    st.subheader("Your Projects")

    if not projects:

        st.info(
            "No projects found. Create your first AgentForge project!"
        )

        return

    for project in projects:

        project_id = project["id"]

        with st.container(border=True):

            col1, col2 = st.columns([3, 1])

            with col1:

                st.markdown(
                    f"### 🚀 {project['name']}"
                )

                st.write(
                    project.get("description", "")
                )

                st.caption(
                    f"Category: {project.get('category', 'Not specified')} | "
                    f"Language: {project.get('programming_language', 'Not specified')} | "
                    f"Framework: {project.get('framework') or 'Not specified'}"
                )

                st.caption(
                    f"Status: **{project.get('status', 'Unknown')}** | "
                    f"Created: {project.get('created_at', 'Unknown')}"
                )

            with col2:

                if st.button(
                    "📂 Open",
                    key=f"open_project_{project_id}"
                ):

                    st.session_state["selected_project_id"] = project_id
                    st.session_state["current_page"] = "workspace"

                    st.rerun()

            col1, col2, col3 = st.columns(3)

            # -------------------------------------------------
            # Rename
            # -------------------------------------------------

            with col1:

                if st.button(
                    "✏️ Rename",
                    key=f"rename_project_{project_id}"
                ):

                    st.session_state[
                        f"rename_mode_{project_id}"
                    ] = True

            # -------------------------------------------------
            # Duplicate
            # -------------------------------------------------

            with col2:

                if st.button(
                    "📄 Duplicate",
                    key=f"duplicate_project_{project_id}"
                ):

                    try:

                        original = AgentForgeAPI.get_project(
                            project_id
                        )

                        duplicate_data = {
                            "name": f"{original['name']} Copy",
                            "description": original.get(
                                "description", ""
                            ),
                            "requirements": original.get(
                                "requirements", ""
                            ),
                            "category": original.get(
                                "category", ""
                            ),
                            "programming_language": original.get(
                                "programming_language", ""
                            ),
                            "framework": original.get(
                                "framework", ""
                            ),
                            "database": original.get(
                                "database", ""
                            ),
                            "additional_instructions": original.get(
                                "additional_instructions", ""
                            ),
                            "status": "active",
                            "ai_model": original.get(
                                "ai_model", "Gemini"
                            ),
                            "owner": user_id
                        }

                        new_project = AgentForgeAPI.create_project(
                            duplicate_data
                        )

                        st.success(
                            f"Project duplicated successfully. "
                            f"New ID: {new_project['id']}"
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Unable to duplicate project: {error}"
                        )

            # -------------------------------------------------
            # Delete
            # -------------------------------------------------

            with col3:

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_project_{project_id}"
                ):

                    st.session_state[
                        f"delete_confirm_{project_id}"
                    ] = True

            # -------------------------------------------------
            # Rename Form
            # -------------------------------------------------

            if st.session_state.get(
                f"rename_mode_{project_id}",
                False
            ):

                new_name = st.text_input(
                    "New Project Name",
                    value=project["name"],
                    key=f"new_name_{project_id}"
                )

                if st.button(
                    "Save Name",
                    key=f"save_name_{project_id}"
                ):

                    if not new_name.strip():

                        st.error(
                            "Project name cannot be empty."
                        )

                    else:

                        try:

                            AgentForgeAPI.update_project(
                                project_id,
                                {
                                    "name": new_name.strip()
                                }
                            )

                            st.success(
                                "Project renamed successfully."
                            )

                            st.session_state[
                                f"rename_mode_{project_id}"
                            ] = False

                            st.rerun()

                        except Exception as error:

                            st.error(
                                f"Unable to rename project: {error}"
                            )

            # -------------------------------------------------
            # Delete Confirmation
            # -------------------------------------------------

            if st.session_state.get(
                f"delete_confirm_{project_id}",
                False
            ):

                st.warning(
                    "Are you sure you want to delete this project?"
                )

                confirm_col1, confirm_col2 = st.columns(2)

                with confirm_col1:

                    if st.button(
                        "Yes, Delete",
                        key=f"confirm_delete_{project_id}"
                    ):

                        try:

                            AgentForgeAPI.delete_project(
                                project_id
                            )

                            st.success(
                                "Project deleted successfully."
                            )

                            st.session_state[
                                f"delete_confirm_{project_id}"
                            ] = False

                            st.rerun()

                        except Exception as error:

                            st.error(
                                f"Unable to delete project: {error}"
                            )

                with confirm_col2:

                    if st.button(
                        "Cancel",
                        key=f"cancel_delete_{project_id}"
                    ):

                        st.session_state[
                            f"delete_confirm_{project_id}"
                        ] = False

                        st.rerun()