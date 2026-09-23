from database.connection import get_connection


def initialize_database():
    """
    Create all database tables required for the AgentForge
    Projects module.
    """

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------
    # 1. USERS TABLE
    # --------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --------------------------------------------------
    # 2. PROJECTS TABLE
    # --------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            requirements TEXT,
            category TEXT,
            programming_language TEXT,
            framework TEXT,
            database TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------
    # 3. PROJECT MESSAGES TABLE
    # --------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (project_id)
                REFERENCES projects(id)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------
    # 4. PROJECT FILES TABLE
    # --------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (project_id)
                REFERENCES projects(id)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------
    # 5. PROJECT HISTORY TABLE
    # --------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (project_id)
                REFERENCES projects(id)
                ON DELETE CASCADE
        )
    """)

    # --------------------------------------------------
    # 6. PROJECT DOCUMENTATION TABLE
    # --------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_documentation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (project_id)
                REFERENCES projects(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()

    print("AgentForge database initialized successfully.")


if __name__ == "__main__":
    initialize_database()