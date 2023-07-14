# REST-API-RecipeApp

## Description
Recipe API is a robust backend REST API designed specifically for a recipe management application. It offers a comprehensive set of functionalities, including user registration and authentication, recipe and ingredient management, tagging, image uploads, object filtering, search capabilities, and more.

The Django admin interface is also customized to align with the unique requirements of the recipe management application, providing an intuitive and tailored administrative interface. Additionally, a Postgres database was configured to ensure seamless data management, leveraging the scalability and robustness of a relational database structure.

The API was developed using the Django Rest Framework, with a strong focus on Test Driven Development (TDD) approach, and set up to run within Docker containers for ease of management and deployment.

## Requirements
To run the Recipe API locally, you need to have the following software installed on your system:
- Docker Desktop (https://www.docker.com/products/docker-desktop/)

## Installation and Setup
1. Clone the repository from GitHub.
   ```bash
   $ git clone https://github.com/vuxho789/REST-API-RecipeApp.git
   ```

2. Navigate to the working directory.
   ```bash
   $ cd REST-API-RecipeApp
   ```

3. Start the Docker container.
   ```bash
   $ docker-compose up
   ```

4. Open another terminal and run the following command to create a superuser.
   ```bash
   $ docker-compose run --rm app sh -c "python manage.py createsuperuser"
   ```

5. Once the containers are up and running, the Swagger UI of Recipe API can be accessed locally at:

   http://localhost:8000/api/docs

   The admin panel can be access via the login page using the previously created superuser credentials:

   http://localhost:8000/admin

## Contact Me
If you have any questions, please feel free to contact me.
<p align="left">
  <a href="https://www.linkedin.com/in/vutuanho"><img alt="LinkedIn" title="LinkedIn" src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"/></a>
  <a href="mailto:vuho.tech@gmail.com"><img alt="Gmail" title="Gmail" src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white"/></a>
</p>