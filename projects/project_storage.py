from pathlib import Path
import shutil


# --------------------------------------------------
# BASE GENERATED PROJECTS DIRECTORY
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

GENERATED_PROJECTS_DIR = BASE_DIR / "generated_projects"


class ProjectStorage:
    """
    Handles physical file and folder storage
    for individual AgentForge projects.
    """

    # --------------------------------------------------
    # CREATE PROJECT FOLDER
    # --------------------------------------------------

    @staticmethod
    def create_project_folder(project_id):
        """
        Create a separate folder for the project.
        """

        project_folder = (
            GENERATED_PROJECTS_DIR / f"project_{project_id}"
        )

        project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        return project_folder

    # --------------------------------------------------
    # GET PROJECT FOLDER
    # --------------------------------------------------

    @staticmethod
    def get_project_folder(project_id):
        """
        Return the folder belonging to a project.
        """

        return (
            GENERATED_PROJECTS_DIR /
            f"project_{project_id}"
        )

    # --------------------------------------------------
    # CREATE FILE
    # --------------------------------------------------

    @staticmethod
    def create_file(project_id, file_path, content=""):
        """
        Create a file inside the project's folder.
        """

        project_folder = ProjectStorage.create_project_folder(
            project_id
        )

        file_path = Path(file_path)

        # Prevent absolute paths
        if file_path.is_absolute():
            raise ValueError(
                "Absolute file paths are not allowed."
            )

        full_path = project_folder / file_path

        # Security check:
        # Make sure file remains inside project folder
        full_path = full_path.resolve()

        if project_folder.resolve() not in full_path.parents:
            raise ValueError(
                "Invalid file path."
            )

        # Create parent folders
        full_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Write file
        full_path.write_text(
            content,
            encoding="utf-8"
        )

        return full_path

    # --------------------------------------------------
    # READ FILE
    # --------------------------------------------------

    @staticmethod
    def read_file(project_id, file_path):
        """
        Read a file belonging to a project.
        """

        project_folder = (
            ProjectStorage.get_project_folder(project_id)
        )

        full_path = (
            project_folder / file_path
        ).resolve()

        if project_folder.resolve() not in full_path.parents:
            raise ValueError(
                "Invalid file path."
            )

        if not full_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not full_path.is_file():
            raise ValueError(
                "The selected path is not a file."
            )

        return full_path.read_text(
            encoding="utf-8"
        )

    # --------------------------------------------------
    # LIST PROJECT FILES
    # --------------------------------------------------

    @staticmethod
    def list_files(project_id):
        """
        Return all files inside a project folder.
        """

        project_folder = (
            ProjectStorage.get_project_folder(project_id)
        )

        if not project_folder.exists():
            return []

        files = []

        for path in project_folder.rglob("*"):

            if path.is_file():

                relative_path = path.relative_to(
                    project_folder
                )

                files.append(
                    str(relative_path)
                )

        return sorted(files)

    # --------------------------------------------------
    # DELETE FILE
    # --------------------------------------------------

    @staticmethod
    def delete_file(project_id, file_path):
        """
        Delete a specific project file.
        """

        project_folder = (
            ProjectStorage.get_project_folder(project_id)
        )

        full_path = (
            project_folder / file_path
        ).resolve()

        if project_folder.resolve() not in full_path.parents:
            raise ValueError(
                "Invalid file path."
            )

        if full_path.exists() and full_path.is_file():
            full_path.unlink()
            return True

        return False

    # --------------------------------------------------
    # DELETE ALL PROJECT FILES
    # --------------------------------------------------

    @staticmethod
    def delete_project_files(project_id):
        """
        Delete the complete physical project folder.
        """

        project_folder = (
            ProjectStorage.get_project_folder(project_id)
        )

        if project_folder.exists():

            shutil.rmtree(
                project_folder
            )

            return True

        return False