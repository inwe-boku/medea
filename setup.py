import setuptools

with open('README.md', 'r', encoding='utf-8') as readme_file:
    readme = readme_file.read()

setuptools.setup(
    name='medea',
    version='0.1.0',
    author='Sebastian Wehrle',
    author_email='sebastian.wehrle@boku.ac.at',
    description='medea - a power system model',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/inwe-energy/medea',
    project_urls={},
    license='MIT',
    packages=['medea'],
    install_requires=['yaml'],
    data_files=[('gms', ['medea/opt/medea_main.gms']),
                ('gms', ['medea/opt/medea_custom.gms'])],
    include_package_data=True,
)
