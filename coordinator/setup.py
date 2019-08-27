import os
from setuptools import setup


os.chdir(os.path.abspath(os.path.dirname(__file__)))


req = [
    'aio-pika',
    'datamart_core',
    'elasticsearch~=7.0',
    'prometheus_client',
    'PyYaml',
    'jinja2',
    'tornado>=5.0',
]
setup(name='datamart-coordinator-service',
      version='0.0',
      packages=['coordinator'],
      package_data={'coordinator': [
          'static/css/*.css', 'static/css/*.css.map',
          'static/js/*.js', 'static/js/*.js.map',
          'templates/*.html',
          'elasticsearch.yml',
      ]},
      entry_points={
          'console_scripts': [
              'coordinator = coordinator.web:main']},
      install_requires=req,
      description="Coordinator service for DataMart",
      author="Remi Rampin",
      author_email='remi.rampin@nyu.edu',
      maintainer="Remi Rampin",
      maintainer_email='remi.rampin@nyu.edu',
      url='https://gitlab.com/ViDA-NYU/datamart/datamart',
      project_urls={
          'Homepage': 'https://gitlab.com/ViDA-NYU/datamart/datamart',
          'Source': 'https://gitlab.com/ViDA-NYU/datamart/datamart',
          'Tracker': 'https://gitlab.com/ViDA-NYU/datamart/datamart/issues',
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
