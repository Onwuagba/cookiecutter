import os
import re
import subprocess
import sys
import shutil

project_slug = "{{ cookiecutter.project_slug }}"
db_type = "{{ cookiecutter.db_type }}"


def install_requirements():
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def run_command(command):
    """Run a shell command and raise an error if it fails."""
    result = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(
            f"Command failed: {command}\n{result.stderr.decode('utf-8')}")
    return result.stdout.decode('utf-8')


def branch_exists(branch_name):
    """Check if the branch already exists in the remote."""
    remote_branches = run_command('git branch -r')
    return f'origin/{branch_name}' in remote_branches


def initialize_git_and_push():
    repo_link = "{{ cookiecutter.repo_link }}"
    print(f"Setting up repo at {repo_link}...")

    # Initialize Git repository
    run_command('git init')

    # Add all files to Git
    run_command('git add .')

    # Commit initial files
    run_command('git commit -m "Initial commit"')

    # Add the remote repository
    run_command(f'git remote add origin {repo_link}')

    # Check if the 'develop' branch already exists
    if branch_exists('develop'):
        print("The 'develop' branch already exists, skipping branch creation.")
    else:
        # Create the develop branch and push it
        run_command('git checkout -b develop')
        run_command('git push -u origin develop')
        print("The 'develop' branch has been created and pushed.")


def remove_docker_files():
    """Remove Docker-related files if use_docker is set to 'n'."""
    files_to_remove = [
        '.dockerignore',
        'Dockerfile',
        'docker-compose.yml'
    ]

    for file in files_to_remove:
        if os.path.exists(file):
            print(f"Removing {file}...")
            os.remove(file)

    # Remove the docker directory if it exists
    docker_directory = 'docker'
    if os.path.exists(docker_directory) and os.path.isdir(docker_directory):
        print(f"Removing {docker_directory} directory...")
        shutil.rmtree(docker_directory)


def setup_project():
    project_type = "{{ cookiecutter.project_type }}"
    use_celery = "{{ cookiecutter.use_celery }}" == "y"
    use_redis = "{{ cookiecutter.use_redis }}" == "y"
    use_docker = "{{ cookiecutter.use_docker }}" == "y"
    use_sentry = "{{ cookiecutter.use_sentry }}" == "y"
    use_rest_framework = "{{ cookiecutter.use_rest_framework }}" == "y"
    use_graphql = "{{ cookiecutter.use_graphql }}" == "y"
    use_jwt = "{{ cookiecutter.use_jwt }}" == "y"

    # Setup database
    if db_type:
        update_database_config(db_type, project_slug)
        subprocess.check_call(
            [sys.executable, "manage.py", "migrate"])

    # Setup Celery
    if use_celery:
        setup_celery()

    # Setup Docker
    if use_docker:
        setup_docker()
    else:
        print("Docker not selected, removing Docker-related files.")
        remove_docker_files()

    # Setup Sentry
    if use_sentry:
        setup_sentry()

    # Setup REST framework
    if use_rest_framework:
        setup_rest_framework()

    # Setup GraphQL
    if use_graphql:
        setup_graphql()

    # Setup JWT
    if use_jwt:
        setup_jwt()

    # Setup project-specific documentation
    setup_documentation(project_type)

    # Setup pre-commit hooks
    setup_pre_commit()

    # check env file exists
    check_env_file()


def install_database_lib(db_type):
    """Install the relevant database library."""
    if db_type == "PostgreSQL":
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    elif db_type == "SQL Server":
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyodbc"])
    elif db_type == "Oracle":
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "cx_Oracle"])
    elif db_type == "SQLite":
        # SQLite comes pre-installed with Python, no need to install anything.
        pass


def update_database_config(db_type, project_slug):
    """Update the settings.py file with the selected database configuration."""
    settings_file = f"{project_slug}/settings.py"

    # install db dependency
    install_database_lib(db_type)

    with open(settings_file, 'r') as file:
        settings = file.read()

    if db_type == "PostgreSQL":
        database_config = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'your_db_name'),
        'USER': os.environ.get('DB_USER', 'your_db_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_db_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}"""
    elif db_type == "SQL Server":
        database_config = """
DATABASES = {
    'default': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': os.environ.get('DB_NAME', 'your_db_name'),
        'USER': os.environ.get('DB_USER', 'your_db_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_db_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '1433'),
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}"""
    elif db_type == "SQLite":
        database_config = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}"""
    elif db_type == "Oracle":
        database_config = """
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': os.environ.get('DB_NAME', 'your_db_name'),
        'USER': os.environ.get('DB_USER', 'your_db_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_db_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '1521'),
    }
}"""

    # Replace the existing DATABASES setting in settings.py
    # settings = settings.replace("DATABASES = {", database_config)

    settings = re.sub(
        r'DATABASES\s*=\s*\{[^}]*\}', database_config, settings, flags=re.DOTALL)

    with open(settings_file, 'w') as file:
        file.write(settings)


def update_requirements():
    subprocess.check_call(
        [sys.executable, "-m", "pip", "freeze", ">", "requirements.txt"])


def setup_celery():
    celery_file = f"{project_slug}/celery.py"
    with open(celery_file, 'w') as file:
        file.write("""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{{ cookiecutter.project_slug }}.settings')

app = Celery('{{ cookiecutter.project_slug }}')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
        """)

    init_file = f"{project_slug}/__init__.py"
    with open(init_file, 'a') as file:
        file.write("""
from .celery import app as celery_app

__all__ = ('celery_app',)
        """)

    # Update settings.py with Celery configurations
    settings_file = f"{project_slug}/settings.py"
    with open(settings_file, 'a') as file:
        file.write("""
# Celery configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
        """)

    print("Celery setup complete.")


def setup_docker():
    dockerfile = "Dockerfile"
    if not os.path.exists(dockerfile):
        with open(dockerfile, 'w') as file:
            file.write("""
FROM python:3.9

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE {{ cookiecutter.project_slug }}.settings

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "{{ cookiecutter.project_slug }}.wsgi:application"]
            """)

    docker_compose = "docker-compose.yml"
    if not os.path.exists(docker_compose):
        with open(docker_compose, 'w') as file:
            file.write("""
version: '3'

services:
  web:
    build: .
    command: gunicorn {{ cookiecutter.project_slug }}.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}

volumes:
  postgres_data:
            """)

    dockerignore = ".dockerignore"
    if not os.path.exists(dockerignore):
        with open(dockerignore, 'w') as file:
            file.write("*.pyc\n")
            file.write("*.pyo\n")
            file.write("*.sqlite3\n")
            file.write("*.log\n")
            file.write(".editorconfig\n")
            file.write(".gitattributes\n")
            file.write(".github\n")
            file.write(".gitignore\n")
            file.write(".gitlab-ci.yml\n")
            file.write("*.idea\n")
            file.write(".pre-commit-config.yaml\n")
            file.write(".travis.yml\n")
            file.write("venv\n")
            file.write("*.git\n")
            file.write("*.envs/\n")


def setup_sentry():
    settings_file = f"{project_slug}/settings.py"
    with open(settings_file, 'r') as file:
        settings = file.read()

    settings = settings.replace(
        "MIDDLEWARE = [",
        """MIDDLEWARE = [
    'sentry_sdk.integrations.django.DjangoIntegration',"""
    )

    settings += """
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
    """

    with open(settings_file, 'w') as file:
        file.write(settings)


def setup_rest_framework():
    settings_file = f"{project_slug}/settings.py"
    with open(settings_file, 'r') as file:
        settings = file.read()

    settings = settings.replace(
        "INSTALLED_APPS = [",
        """INSTALLED_APPS = [
    'rest_framework',
    'drf_yasg',"""
    )

    settings += """
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Basic': {
            'type': 'basic'
        },
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}
    """

    with open(settings_file, 'w') as file:
        file.write(settings)


def setup_graphql():
    settings_file = f"{project_slug}/settings.py"
    with open(settings_file, 'r') as file:
        settings = file.read()

    settings = settings.replace(
        "INSTALLED_APPS = [",
        """INSTALLED_APPS = [
    'graphene_django',"""
    )

    settings += """
GRAPHENE = {
    'SCHEMA': '{{ cookiecutter.project_slug }}.schema.schema'
}
    """

    with open(settings_file, 'w') as file:
        file.write(settings)

    schema_file = f"{project_slug}/schema.py"
    with open(schema_file, 'w') as file:
        file.write("""
import graphene

class Query(graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)
        """)


def setup_jwt():
    settings_file = f"{project_slug}/settings.py"
    with open(settings_file, 'r') as file:
        settings = file.read()

    settings = settings.replace(
        "INSTALLED_APPS = [",
        """INSTALLED_APPS = [
    'rest_framework_simplejwt',"""
    )

    settings = settings.replace(
        "'rest_framework.authentication.BasicAuthentication',",
        """'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',"""
    )

    settings += """
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
    """

    with open(settings_file, 'w') as file:
        file.write(settings)


def setup_documentation(project_type: str):
    docs_dir = os.path.join(os.getcwd(), 'docs')
    template_dir = os.path.join(docs_dir, 'templates')

    if project_type.upper() == "VAS":
        src_file = os.path.join(template_dir, 'vas_template.md')
    elif project_type.upper() == "NOTIFICATION":
        src_file = os.path.join(
            template_dir, 'notification_template.md')
    else:  # General
        src_file = os.path.join(template_dir, 'general_template.md')

    dest_file = os.path.join(docs_dir, 'project_docs.md')

    if os.path.exists(src_file):
        shutil.copy(src_file, dest_file)
    else:
        print(
            f"Warning: Documentation template for {project_type} not found.")


def setup_pre_commit():
    pre_commit_config = ".pre-commit-config.yaml"
    if not os.path.exists(pre_commit_config):
        with open(pre_commit_config, 'w') as file:
            file.write("""
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v3.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
-   repo: https://github.com/psf/black
    rev: 21.5b1
    hooks:
    -   id: black
-   repo: https://github.com/PyCQA/flake8
    rev: 3.9.2
    hooks:
    -   id: flake8
-   repo: https://github.com/PyCQA/isort
    rev: 5.8.0
    hooks:
    -   id: isort
-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.812
    hooks:
    -   id: mypy
        args: [--ignore-missing-imports]
            """)

    print("Pre-commit config setup complete.")


def check_env_file():
    env = ".env"
    if not os.path.exists(env):
        print(".env file is missing. Create one using the .env.example")
        exit(1)

    with open(env, 'w') as file:
        if "SECRET_KEY" not in file.read():
            print("SECRET_KEY not found in .env. Please add it.")
            exit(1)

    with open(env, 'w') as file:
        if "ALLOWED_HOSTS" not in file.read():
            print("ALLOWED_HOSTS not found in .env. Please add it.")
            exit(1)

    print("Environment file check complete.")


if __name__ == '__main__':
    install_requirements()
    setup_project()
    initialize_git_and_push()
    update_requirements()
    print("Project setup complete!")
