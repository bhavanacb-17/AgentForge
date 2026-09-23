import requests


class AgentForgeAPI:
    BASE_URL = "http://127.0.0.1:8000/api"

    @classmethod
    def get_projects(cls):
        response = requests.get(
            f"{cls.BASE_URL}/projects/",
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def create_project(cls, project_data):
        response = requests.post(
            f"{cls.BASE_URL}/projects/",
            json=project_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_project(cls, project_id):
        response = requests.get(
            f"{cls.BASE_URL}/projects/{project_id}/",
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def update_project(cls, project_id, project_data):
        response = requests.patch(
            f"{cls.BASE_URL}/projects/{project_id}/",
            json=project_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def delete_project(cls, project_id):
        response = requests.delete(
            f"{cls.BASE_URL}/projects/{project_id}/",
            timeout=10
        )
        response.raise_for_status()
        return True