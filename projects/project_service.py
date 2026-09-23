from database.connection import get_connection


class ProjectService:
    """
    Handles all project-related database operations.
    """

    # --------------------------------------------------
    # CREATE PROJECT
    # --------------------------------------------------

    @staticmethod
    def create_project(
        user_id,
        name,
        description="",
        requirements="",
        category="Other",
        programming_language="Python",
        framework="",
        database="",
        status="Active"
    ):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO projects (
                user_id,
                name,
                description,
                requirements,
                category,
                programming_language,
                framework,
                database,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            name,
            description,
            requirements,
            category,
            programming_language,
            framework,
            database,
            status
        ))

        project_id = cursor.lastrowid

        # Record project creation
        cursor.execute("""
            INSERT INTO project_history (
                project_id,
                activity_type,
                description
            )
            VALUES (?, ?, ?)
        """, (
            project_id,
            "PROJECT_CREATED",
            f"Project '{name}' was created."
        ))

        connection.commit()
        connection.close()

        return project_id

    # --------------------------------------------------
    # GET ALL PROJECTS FOR A USER
    # --------------------------------------------------

    @staticmethod
    def get_projects(user_id):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                user_id,
                name,
                description,
                requirements,
                category,
                programming_language,
                framework,
                database,
                status,
                created_at,
                updated_at
            FROM projects
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))

        projects = cursor.fetchall()

        connection.close()

        return projects

    # --------------------------------------------------
    # GET SINGLE PROJECT
    # --------------------------------------------------

    @staticmethod
    def get_project(project_id, user_id):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                user_id,
                name,
                description,
                requirements,
                category,
                programming_language,
                framework,
                database,
                status,
                created_at,
                updated_at
            FROM projects
            WHERE id = ?
            AND user_id = ?
        """, (project_id, user_id))

        project = cursor.fetchone()

        connection.close()

        return project

    # --------------------------------------------------
    # UPDATE PROJECT
    # --------------------------------------------------

    @staticmethod
    def update_project(
        project_id,
        user_id,
        name,
        description,
        requirements,
        category,
        programming_language,
        framework,
        database,
        status
    ):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE projects
            SET
                name = ?,
                description = ?,
                requirements = ?,
                category = ?,
                programming_language = ?,
                framework = ?,
                database = ?,
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            AND user_id = ?
        """, (
            name,
            description,
            requirements,
            category,
            programming_language,
            framework,
            database,
            status,
            project_id,
            user_id
        ))

        # Record history
        cursor.execute("""
            INSERT INTO project_history (
                project_id,
                activity_type,
                description
            )
            VALUES (?, ?, ?)
        """, (
            project_id,
            "PROJECT_UPDATED",
            f"Project '{name}' was updated."
        ))

        connection.commit()
        connection.close()

    # --------------------------------------------------
    # RENAME PROJECT
    # --------------------------------------------------

    @staticmethod
    def rename_project(project_id, user_id, new_name):
        connection = get_connection()
        cursor = connection.cursor()

        # Get old name
        cursor.execute("""
            SELECT name
            FROM projects
            WHERE id = ?
            AND user_id = ?
        """, (project_id, user_id))

        project = cursor.fetchone()

        if not project:
            connection.close()
            return False

        old_name = project[0]

        cursor.execute("""
            UPDATE projects
            SET
                name = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            AND user_id = ?
        """, (
            new_name,
            project_id,
            user_id
        ))

        cursor.execute("""
            INSERT INTO project_history (
                project_id,
                activity_type,
                description
            )
            VALUES (?, ?, ?)
        """, (
            project_id,
            "PROJECT_RENAMED",
            f"Project renamed from '{old_name}' to '{new_name}'."
        ))

        connection.commit()
        connection.close()

        return True

    # --------------------------------------------------
    # DELETE PROJECT
    # --------------------------------------------------

    @staticmethod
    def delete_project(project_id, user_id):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT name
            FROM projects
            WHERE id = ?
            AND user_id = ?
        """, (project_id, user_id))

        project = cursor.fetchone()

        if not project:
            connection.close()
            return False

        project_name = project[0]

        cursor.execute("""
            DELETE FROM projects
            WHERE id = ?
            AND user_id = ?
        """, (
            project_id,
            user_id
        ))

        connection.commit()
        connection.close()

        return True

    # --------------------------------------------------
    # DUPLICATE PROJECT
    # --------------------------------------------------

    @staticmethod
    def duplicate_project(project_id, user_id):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                name,
                description,
                requirements,
                category,
                programming_language,
                framework,
                database,
                status
            FROM projects
            WHERE id = ?
            AND user_id = ?
        """, (
            project_id,
            user_id
        ))

        project = cursor.fetchone()

        if not project:
            connection.close()
            return None

        (
            name,
            description,
            requirements,
            category,
            programming_language,
            framework,
            database,
            status
        ) = project

        new_name = f"{name} (Copy)"

        cursor.execute("""
            INSERT INTO projects (
                user_id,
                name,
                description,
                requirements,
                category,
                programming_language,
                framework,
                database,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            new_name,
            description,
            requirements,
            category,
            programming_language,
            framework,
            database,
            status
        ))

        new_project_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO project_history (
                project_id,
                activity_type,
                description
            )
            VALUES (?, ?, ?)
        """, (
            new_project_id,
            "PROJECT_DUPLICATED",
            f"Project duplicated from project ID {project_id}."
        ))

        connection.commit()
        connection.close()

        return new_project_id

    # --------------------------------------------------
    # SEARCH PROJECTS
    # --------------------------------------------------

    @staticmethod
    def search_projects(user_id, search_text=""):
        connection = get_connection()
        cursor = connection.cursor()

        search_pattern = f"%{search_text}%"

        cursor.execute("""
            SELECT
                id,
                user_id,
                name,
                description,
                requirements,
                category,
                programming_language,
                framework,
                database,
                status,
                created_at,
                updated_at
            FROM projects
            WHERE user_id = ?
            AND (
                name LIKE ?
                OR description LIKE ?
            )
            ORDER BY updated_at DESC
        """, (
            user_id,
            search_pattern,
            search_pattern
        ))

        projects = cursor.fetchall()

        connection.close()

        return projects

    # --------------------------------------------------
    # FILTER PROJECTS BY STATUS
    # --------------------------------------------------

    @staticmethod
    def get_projects_by_status(user_id, status):
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                user_id,
                name,
                description,
                requirements,
                category,
                programming_language,
                framework,
                database,
                status,
                created_at,
                updated_at
            FROM projects
            WHERE user_id = ?
            AND status = ?
            ORDER BY updated_at DESC
        """, (
            user_id,
            status
        ))

        projects = cursor.fetchall()

        connection.close()

        return projects