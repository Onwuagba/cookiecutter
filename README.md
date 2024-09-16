# Cookiecutter Usage Guide

This guide will walk you through the process of using this custom cookiecutter template to create a new Django project.

## Prerequisites

1. Python 3.6 or higher
2. pip
3. cookiecutter

If you don't have cookiecutter installed, you can install it using pip:

```
pip install cookiecutter
```

## Using the Cookiecutter

1. Run the cookiecutter command:

```
cookiecutter https://github.com/Onwuagba/cookiecutter.git
```

2. You will be prompted to enter values for the following variables:

   - `project_name`: The name of your project
   - `project_slug`: A slugified version of your project name (auto-generated, but you can modify)
   - `app_name`: The name of the main Django app
   - `project_type`: Choose from VAS, notification, or general
   - `editor`: Your preferred code editor (vscode, pycharm, or sublime)
   - `db_type`: Choose from postgresql, SQL Server, or sqlite
   - `db_version`: The version of the database you're using
   - `use_celery`: Whether to include Celery configuration (y/n)
   - `use_docker`: Whether to include Docker configuration (y/n)
   - `use_whitenoise`: Whether to include Whitenoise for serving static files (y/n)
   - `use_swagger`: Whether to include Swagger for API documentation (y/n)
   - `python_version`: The version of Python you're using

3. After answering all the prompts, cookiecutter will create a new directory with your project name, containing all the necessary files and directories.

4. Navigate into your new project directory:

```
cd your-project-name
```

5. Create a new virtual environment:

```
python -m venv venv
```

6. Activate the virtual environment:

   - On Windows: `venv\Scripts\activate`
   - On macOS and Linux: `source venv/bin/activate`

7. Install the required dependencies:

```
pip install -r requirements.txt
```

8. Copy the `.env.example` file to `.env` and fill in the required values.

9. Run migrations:

```
python manage.py migrate
```

10. Create a superuser:

```
python manage.py createsuperuser
```

11. Start the development server:

```
python manage.py runserver
```

Your new Django project is now set up and ready for development!

## Additional Notes

- If you chose to use Docker, you can build and run your project using:
  ```
  docker-compose up --build -d
  ```

- To run tests, use:
  ```
  python manage.py test
  ```

- The API documentation (if Swagger is enabled) can be accessed at `/docs/`. Remember that authentication is required to view the documentation.

- Make sure to follow the commit message guidelines specified in the README.md file.

- Review the `.gitlab-ci.yml` file for the CI/CD pipeline configuration and adjust as needed for your specific deployment requirements.

Happy coding!
