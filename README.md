# 🗣️ CivicVoice-Backend

An interactive complaint and suggestion portal built with Django to enhance transparency and responsiveness in local government services. Citizens can submit issues, track their progress, and receive updates. Admins and staff manage submissions through an intuitive dashboard.


## 🚀 Features

- 🧾 Submit complaints and suggestions
- 🔐 User authentication (citizens, staff, admins)
- 🔄 Real-time complaint status tracking
- 📬 Notification system (email or in-app)
- 📊 Admin dashboard for efficient issue resolution


### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy civicvoice_backend

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest


### Celery

This app comes with Celery.

To run a celery worker:

```bash
cd civicvoice_backend
celery -A config.celery_app worker -l info
```

Please note: For Celery's import magic to work, it is important _where_ the celery commands are run. If you are in the same folder with _manage.py_, you should be right.

To run [periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html), you'll need to start the celery beat scheduler service. You can start it as a standalone process:

```bash
cd civicvoice_backend
celery -A config.celery_app beat
```

or you can embed the beat service inside a worker with the `-B` option (not recommended for production use):

```bash
cd civicvoice_backend
celery -A config.celery_app worker -B -l info
```

### Email Server

In development, it is often nice to be able to see emails that are being sent from your application. For that reason local SMTP server [MailHog](https://github.com/mailhog/MailHog) with a web interface is available as docker container.

With MailHog running, to view messages that are sent by your application, open your browser and go to `http://127.0.0.1:8025`

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=dxh_py> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

# Docker 

To build and run the application using Docker, use the following commands:

```bash
docker compose -f local.yml build
docker compose -f local.yml up 
docker compose -f local.yml run --rm django /bin/bash

```