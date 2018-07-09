from setuptools import setup

setup(
    name='OrgBKP',
    version='0.0.1',
    packages=['cldbkp'],
    url='https://github.com/flribeiro/CloudDataBackup',
    license='MIT',
    author='Fabrício L. Ribeiro',
    author_email='fabricio@fabriciolribeiro.com',
    description='Programa para automação do backup de bancos de dados em cloud storages.',
    install_requires=['boto3',
                      'fdb'],
    python_requires='>=3',
    package_data={
        '': ['cldbkp_model.ini'],
        }
)
