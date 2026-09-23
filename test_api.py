from api.client import AgentForgeAPI


projects = AgentForgeAPI.get_projects()

print("Projects:", projects)