import os
from setuptools import setup


os.chdir(os.path.abspath(os.path.dirname(__file__)))


req = [
    'aio-pika',
    'elasticsearch',
    'jinja2',
    'tornado>=5.0',
]
setup(name='datamart_coordinator',
      version='0.0',
      packages=['datamart_coordinator'],
      package_data={'datamart_coordinator': [
          'static/css/*.css', 'static/css/*.css.map',
          'static/js/*.js', 'static/js/*.js.map',
          'templates/*.html',
      ]},
      entry_points={
          'console_scripts': [
              'datamart_coordinator = datamart_coordinator.web:main']},
      install_requires=req,
      description="Coordinator service for DataMart",
      author="Remi Rampin",
      author_email='remi.rampin@nyu.edu',
      maintainer="Remi Rampin",
      maintainer_email='remi.rampin@nyu.edu',
      url='https://gitlab.com/remram44/datamart',
      project_urls={
          'Homepage': 'https://gitlab.com/remram44/datamart',
          'Source': 'https://gitlab.com/remram44/datamart',
          'Tracker': 'https://gitlab.com/remram44/datamart/issues',
      },
      long_description="Coordinator service for DataMart",
      license='BSD-3-Clause',
      keywords=['datamart'],
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Web Environment',
          'Intended Audience :: Science/Research',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: JavaScript',
          'Programming Language :: Python :: 3 :: Only',
          'Topic :: Scientific/Engineering :: Information Analysis'])