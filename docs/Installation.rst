This documentation is incomplete.

============
Requirements
============
TPS is in python 3. We encourage you to use a virtualenv.

You may use the following commands to install all the requirements in Ubuntu:

.. sourcecode:: bash

  sudo apt-get install python-dev libpq-dev postgresql cgroup-lite python-pip
  pip install -r requirements.txt

=========================
Configuring TPS
=========================
TPS code is located under directory tps.

The main configuration files are located inside tps/tps.

You should create local_settings.py in that directory to override some of default configurations such as database/judge information.

You may find a sample of contents of this file in local_settings.sample.py.

Another file called local_settings.sample.dev.py contains sample configurations for developers.


=========================
Installing sandbox
=========================
TPS uses isolate for sandboxing and enforcing limits on time and memory.

A copy of isolate is located in the root of this project in directory isolate.

You may use make isolate in that directory in order to compile isolate. You don't need to install isolate.

=========================
Initializing database
=========================
After configuring database, run the following command (if you are using a virtual environment make sure it's activated):

.. sourcecode:: bash

  ./manage.py migrate

It assumes you are in tps directory.

=========================
Running
=========================
You may run TPS like any other django apps using manage.py.

However we recommend using a proxy web server such as nginx and using a wsgi web server such as gunicorn.

TPS also requires celery to be run for executing background tasks. The celery should have workers on both the default queue (celery) and the invoke queue.

For example you may use the following command:

.. sourcecode:: bash

  celery -A cps multi start 16 -c:1-6 2 -c:7-16 3 -l DEBUG -Q:1-6 invoke -Q:7-16 celery
