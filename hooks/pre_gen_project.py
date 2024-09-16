import sys


def validate_project_name():
    project_name = "{{ cookiecutter.project_slug }}"
    if not project_name.isidentifier():
        print(
            f"ERROR: The project name '{project_name}' is not a valid Python identifier.")
        sys.exit(1)


validate_project_name()
