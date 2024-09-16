# {{cookiecutter.project_name}}

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in the required values
6. Run migrations: `python manage.py migrate`
7. Create a superuser: `python manage.py createsuperuser`
8. Run the development server: `python manage.py runserver`

## Docker Setup

If using Docker:

1. Build the image: `docker-compose build`
2. Run the containers: `docker-compose up -d`

## Testing

Run tests with: `python manage.py test`

## Documentation

Access the API documentation at `/docs/` (requires authentication).

## Commit Messages

Please follow the conventional commits specification for commit messages:
https://www.conventionalcommits.org/

## CI/CD

This project uses GitLab CI/CD. See `.gitlab-ci.yml` for the pipeline configuration.