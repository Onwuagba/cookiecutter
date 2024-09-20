import os
import random
import re
import shutil
import string
import subprocess
import sys

project_slug = "{{ cookiecutter.project_slug }}"
db_type = "{{ cookiecutter.db_type }}"


def install_requirements():
    print("Setting up virtual environment...")
    setup_virtualenv()

    print("Installing requirements...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    print("Installing pre-commit...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pre-commit"])


def run_command(command):
    """Run a shell command and raise an error if it fails."""
    try:
        result = subprocess.run(command, shell=True, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}")
        print(f"Error output: {e.stderr}")
        raise


def branch_exists(branch_name):
    """Check if the branch already exists in the remote."""
    remote_branches = run_command('git branch -r')
    return f'origin/{branch_name}' in remote_branches


def initialize_git_and_push():
    repo_link = "{{ cookiecutter.repo_link }}"
    print(f"Setting up repo at {repo_link}...")

    try:
        run_command('git init')
        run_command('git add .')
        run_command('git commit -m "Initial commit"')
        run_command(f'git remote add origin {repo_link}')

        if branch_exists('develop'):
            print(
                "The 'develop' branch already exists, skipping branch creation.")
        else:
            run_command('git checkout -b develop')
            run_command('git push -u origin develop')
            print("The 'develop' branch has been created and pushed.")
    except Exception as e:
        print(
            f"An error occurred during Git initialization: {str(e)}")
        print("Please check your repository settings and try again.")


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


def set_gitlab_variables():
    """
    Set GitLab CI/CD variables for the project.

    This function asks the user to input their GitLab project ID and personal access
    token. If the user enters 'MANUAL' as the project ID, the function will skip setting
    the variables and return.

    The function sets the following variables:

    - DEPLOYMENT_USER: the username to use for deployment
    - DEPLOYMENT_SERVER: the server to deploy to
    - DEPLOYMENT_PORT: the port to use for deployment

    The function will print a success message for each variable set, or an error message
    if there's an issue setting the variable.

    :return:
    """

    print("\n================\nSetting GitLab CI/CD variables...\n================\n")
    error = False
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "requests"])
    import requests

    # Collect GitLab information
    project_id = input(
        "Enter your GitLab project ID (enter MANUAL if you want to setup manually): ")
    token = input(
        "Enter your GitLab personal access token or type CANCEL to skip: ")

    if not token.strip():
        token = input("Oga, enter your GitLab token naahhh: ")

    if not project_id or project_id.lower() == "manual" or not token or token.lower() == 'cancel':
        print("\n You've chosen to set gitlab manually. \n")
        print('ending gitlab setup...')
        from time import sleep
        sleep(0.05)  # sleep for 50ms
        return

    # Collect variables to set
    variables = {
        "DEPLOYMENT_USER": "{{ cookiecutter.deployment_user }}",
        "DEPLOYMENT_SERVER": "{{ cookiecutter.deployment_server }}",
        "DEPLOYMENT_PORT": "{{ cookiecutter.deployment_port }}",
    }

    url = f"https://gitlab.com/api/v4/projects/{project_id}/variables"
    headers = {"PRIVATE-TOKEN": token}

    for key, value in variables.items():
        data = {
            "key": key,
            "value": value,
            "protected": False,
            "masked": True
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"Successfully set variable: {key}")
        else:
            error = True
            print(
                f"Failed to set variable: {key}."
                f"Status code: {response.status_code}"
            )

    if not error:
        print("\n================\nGitLab CI/CD variables set successfully!\n================\n")


def setup_project():
    project_type = "{{ cookiecutter.project_type }}"
    use_celery = "{{ cookiecutter.use_celery }}" == "y"
    use_redis = "{{ cookiecutter.use_redis }}" == "y"
    use_whitenoise = "{{ cookiecutter.use_whitenoise }}" == "y"
    use_docker = "{{ cookiecutter.use_docker }}" == "y"
    use_rest_framework = "{{ cookiecutter.use_rest_framework }}" == "y"
    use_graphql = "{{ cookiecutter.use_graphql }}" == "y"
    use_jwt = "{{ cookiecutter.use_jwt }}" == "y"

    # Setup database
    if db_type:
        update_database_config(db_type, project_slug)
        # subprocess.check_call(
        #     [sys.executable, "manage.py", "migrate"])

    # Setup Celery
    if use_celery:
        setup_celery()

    # Setup Docker
    if use_docker:
        setup_docker()
    else:
        print("Docker not selected, removing Docker-related files.")
        remove_docker_files()

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

    # add whitenoise if set
    if use_whitenoise:
        add_whitenoise_middleware()

    # replace_app_name()

    # setup gitlab project variables
    set_gitlab_variables()


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
    settings = re.sub(
        r'DATABASES\s*=\s*\{[^}]*\}',
        database_config.strip(),  # Remove leading/trailing whitespace
        settings,
        flags=re.DOTALL
    )

    with open(settings_file, 'w') as file:
        file.write(settings)


def update_requirements():
    """
    Update the requirements.txt file with the current package versions
    and install pre-commit hooks.

    This function is idempotent and safe to run multiple times.
    """

    # Capture the output of `pip freeze` and write to `requirements.txt`
    with open("requirements.txt", "w") as f:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "freeze"], stdout=f)

    # Install pre-commit hooks
    subprocess.check_call(
        ["pre-commit", "install", "--install-hooks"])

    print("Requirements updated and pre-commit hooks installed.")


def setup_celery():
    print("Installing celery...")

    # Install specific versions of Celery and Kombu
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install",
            "celery==5.2.3", "kombu==5.3.0b3"]
    )

    print("Setting up celery...")
    celery_file = f"{project_slug}/celery.py"
    with open(celery_file, 'w') as file:
        file.write("""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      '{{ cookiecutter.project_slug }}.settings')

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
    with open(settings_file, 'r+') as file:
        content = file.read()
        if "CELERY_BROKER_URL" not in content:
            file.seek(0, 2)  # Move to the end of the file
            file.write("""
# Celery configuration
CELERY_BROKER_URL = os.environ.get(
    'CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get(
    'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
            """)

    print("Celery setup complete.")


def setup_docker():
    """
    Set up Dockerfile and docker-compose.yml for the project.

    Installs gunicorn, copies the requirements.txt file to the Docker image, and
    runs the collectstatic management command to collect static files. Uses the
    Docker Compose file to define a service for the web application and a service
    for the database.

    The Docker Compose file defines a service for the web application and a
    service for the database. The web application service uses the Dockerfile to
    build the image, sets the environment variables from the .env file, and maps
    port 8000 on the host to port 8000 in the container.

    The .dockerignore file is used to ignore files and directories that should not
    be included in the Docker image. The files and directories listed in the
    .dockerignore file are ignored by Docker when building the image.
    """

    print("\n=====Setting up docker...\n=======")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "gunicorn"])

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

CMD ["gunicorn", "--bind", "0.0.0.0:8000",
    "{{ cookiecutter.project_slug }}.wsgi:application"]
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
    print("Installing drf...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "djangorestframework"])

    print("setting up django-filter...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "django-filter"])

    print("Setting up rest-framework...")
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
    print("Installing django-graphene...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "graphene-django"])

    print("Setting up django-graphene...")
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
    print("Installing djangorestframework-simplejwt...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "djangorestframework-simplejwt"])

    print("Setting up jwt...")
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
    """
    Setup project-specific documentation.

    Copies a documentation template from the templates folder to docs/index.md.
    The template is chosen based on the project type, and the templates folder is
    deleted afterward.

    Args:
        project_type: The type of the project (VAS, NOTIFICATION, or General).

    Returns:
        None
    """
    docs_dir = os.path.join(os.getcwd(), 'docs')
    template_dir = os.path.join(docs_dir, 'templates')

    if project_type.upper() == "VAS":
        src_file = os.path.join(template_dir, 'vas_template.md')
    elif project_type.upper() == "NOTIFICATION":
        src_file = os.path.join(
            template_dir, 'notification_template.md')
    else:  # General
        src_file = os.path.join(template_dir, 'general_template.md')

    dest_file = os.path.join(docs_dir, 'index.md')

    if os.path.exists(src_file):
        # Copy the selected template to the docs directory
        shutil.copy(src_file, dest_file)
        print(
            f"Documentation template for {project_type} has been set up.")

        # Remove the templates folder after copying the file
        shutil.rmtree(template_dir, ignore_errors=True)
    else:
        print(
            f"Warning: Documentation template for {project_type} not found.")


def setup_pre_commit():
    pre_commit_config = ".pre-commit-config.yaml"
    if not os.path.exists(pre_commit_config):
        print("Warning: precommit file not found")
        with open(pre_commit_config, 'w') as file:
            file.write("""
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: check-ast
    -   id: check-json
    -   id: check-case-conflict
    -   id: check-merge-conflict

-   repo: https://github.com/psf/black
    rev: 21.6b0
    hooks:
    -   id: black

-   repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
    -   id: flake8

-   repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
    -   id: isort

-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
    -   id: mypy
        args: [--strict]

-   repo: local
    hooks:
      - id: check-commit-message
        name: Commit message check
        entry: |
          bash -c "COMMIT_MSG=$(cat $1); 
                   if ! echo \"$COMMIT_MSG\" | grep -E '^(feat|fix|update|docs|chore|refactor|test|style): '; 
                   then echo 'Invalid commit message. Use format: (feat|fix|update|docs|chore|refactor|test|style): Message'; 
                   exit 1; 
                   fi"
        language: system

exclude: '\.venv'
            """)

    print("Pre-commit config setup complete.")


def generate_secret_key():
    """Generate a Django secret key."""
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.SystemRandom().choice(chars) for _ in range(50))


def update_db_url(db_type):
    """Generate the DATABASE_URL based on the selected db_type."""
    if db_type == "PostgreSQL":
        return "postgres://user:password@localhost:5432/dbname"
    elif db_type == "SQL Server":
        return "mssql://user:password@localhost:1433/dbname"
    elif db_type == "SQLite":
        return "sqlite:///db.sqlite3"
    elif db_type == "Oracle":
        return "oracle://user:password@localhost:1521/dbname"
    else:
        return ""


def check_env_file():
    """
    Check if the .env file exists. If not, create one from .env.example.

    Replace placeholders in the .env file with actual values:

    - SECRET_KEY: a randomly generated secret key
    - DATABASE_URL: based on the selected db_type
    - CELERY_BROKER_URL: if Celery is enabled, set to redis://localhost:6379/0

    Verify that the .env file contains the required variables:

    - SECRET_KEY
    - ALLOWED_HOSTS

    Exit with an error message if any of the above checks fail.
    """
    env_file = ".env"
    env_example = ".env.example"

    try:
        if not os.path.exists(env_file):
            print(
                f"{env_file} is missing. Creating one from {env_example}...")

            if not os.path.exists(env_example):
                raise FileNotFoundError(
                    f"{env_example} not found. Cannot create {env_file}.")

            shutil.copy(env_example, env_file)

            with open(env_file, 'r') as file:
                env_content = file.read()

            secret_key = generate_secret_key()
            env_content = env_content.replace(
                "your-secret-key-here", secret_key)

            db_type = "{{ cookiecutter.db_type }}"
            db_url = update_db_url(db_type)
            env_content = env_content.replace(
                "postgres://user:password@localhost:5432/dbname", db_url)

            use_celery = "{{ cookiecutter.use_celery }}"
            if use_celery == "y":
                broker_url = "CELERY_BROKER_URL=redis://localhost:6379/0"
                if "CELERY_BROKER_URL" not in env_content:
                    env_content += f"\n{broker_url}"

            with open(env_file, 'w') as file:
                file.write(env_content)

            print(".env file created and updated.")
        else:
            print(".env file already exists. Verifying its content...")

        with open(env_file, 'r') as file:
            env_content = file.read()

        if "SECRET_KEY" not in env_content:
            raise ValueError(
                "SECRET_KEY not found in .env. Please add it.")

        if "ALLOWED_HOSTS" not in env_content:
            raise ValueError(
                "ALLOWED_HOSTS not found in .env. Please add it.")

        print("Environment file check complete.")

    except (IOError, OSError) as e:
        print(
            f"An error occurred while working with the .env file: {str(e)}")
        sys.exit(1)
    except ValueError as e:
        print(str(e))
        sys.exit(1)


def add_whitenoise_middleware():
    settings_file = "{{ cookiecutter.project_slug }}/settings.py"

    # Read the settings file
    with open(settings_file, 'r') as file:
        content = file.read()

    # Insert WhiteNoise middleware after SecurityMiddleware
    security_middleware = "'django.middleware.security.SecurityMiddleware',"
    whitenoise_middleware = "'whitenoise.middleware.WhiteNoiseMiddleware',"

    if whitenoise_middleware not in content:
        # Insert WhiteNoise middleware in the correct position
        content = content.replace(
            security_middleware,
            f"{security_middleware}\n    {whitenoise_middleware}"
        )

    # Add STATIC_ROOT setting if not present
    if "STATIC_ROOT" not in content:
        static_root = "\nSTATIC_ROOT = BASE_DIR / 'staticfiles'\n"
        content += static_root

    # Write the updated content to the settings file
    with open(settings_file, 'w') as file:
        file.write(content)

    print("Whitenoise middleware and STATIC_ROOT added to settings.py.")

    # Create the templates folder if it does not exist
    templates_dir = os.path.join(
        "{{ cookiecutter.project_slug }}", "templates")
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        print(f"Created templates directory at: {templates_dir}")

    # Update the TEMPLATES setting
    update_templates_dir_in_settings()


def update_templates_dir_in_settings():
    settings_file = "{{ cookiecutter.project_slug }}/settings.py"

    with open(settings_file, 'r') as file:
        content = file.read()

    # Check if 'DIRS' is in TEMPLATES settings and update the template directory
    if "'DIRS':" in content:
        content = content.replace(
            "'DIRS': [],",
            f"'DIRS': [BASE_DIR / 'templates'],"
        )

    # Write the updated settings back to the file
    with open(settings_file, 'w') as file:
        file.write(content)

    print("TEMPLATES DIR updated in settings.py.")


def replace_app_name():
    app_name = "{{ cookiecutter.app_name }}"
    files_to_update = [
        "manage.py",
        "{{ cookiecutter.project_slug }}/settings.py",
        "{{ cookiecutter.project_slug }}/urls.py",
        f"{{ cookiecutter.project_slug }}/{app_name}/apps.py"
    ]

    for file_path in files_to_update:
        print(f"- updating {file_path}...")
        with open(file_path, 'r') as file:
            content = file.read()

        content = content.replace(
            "{{ cookiecutter.app_name }}", app_name)

        with open(file_path, 'w') as file:
            file.write(content)
        print(f"- {file_path} updated successfully")


def setup_virtualenv():
    try:
        if not os.path.exists('venv'):
            subprocess.check_call(
                [sys.executable, "-m", "venv", "venv"])

        if os.name == 'nt':  # Windows
            activate_script = os.path.join(
                'venv', 'Scripts', 'activate.bat')
        else:
            activate_script = os.path.join('venv', 'bin', 'activate')

        if os.name == 'nt':
            subprocess.call(activate_script, shell=True)
        else:
            subprocess.call(f"source {activate_script}", shell=True)

        print("Virtual environment created and activated.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {str(e)}")
        sys.exit(1)
    except OSError as e:
        print(f"Error activating virtual environment: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    print("Project setup started...")
    install_requirements()
    setup_project()
    initialize_git_and_push()
    update_requirements()
    print("Project setup complete!")
