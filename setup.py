from setuptools import setup

setup(
    name='flask-scheema',
    version='0.0.1',
    packages=['flask_scheema', 'flask_scheema.api', 'flask_scheema.scheema', 'flask_scheema.services',
              'flask_scheema.specification'],
    url='https://github.com/arched-dev/flask-scheema',
    license='MIT',
    author='arched.dev (Lewis Morris)',
    author_email='hello@arched.dev',
    description='Rapidly prototype Flask/SQLAlchemy APIs and automatically generate documentation with this advanced tool. Designed for agility, it allows for swift creation of high-quality API prototypes. With customizable configuration options, it can be seamlessly extended for production use, ensuring scalability and adaptability for real-world applications.'
)
