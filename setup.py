from setuptools import setup

setup(
    name='OrgBKP',
    version='0.0.1',
    packages=['orgbkp'],
    url='https://github.com/flribeiro1983/OrgBKP',
    license='MIT',
    author='Fabrício L. Ribeiro',
    author_email='fabricio@fabriciolribeiro.com',
    description='Programa para automação do backup das bases de dados de clientes da Org.',
    install_requires=['boto3',
                      'fdb'],
    package_data={
        '': ['orgbkp_model.ini'],
        }
)
