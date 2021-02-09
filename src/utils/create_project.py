import logging
import os
import sys
from shutil import copyfile

from logging_config import setup_logging

dirname = os.path.dirname
sys.path.append(os.path.join(dirname(dirname(dirname(__file__)))))


def create_project(project_name, medea_dir):
    """
    creates project folder and subfolders according to medea-conventions and copies required model and data files.
    Additionally, also fetches some templates to set up scenarios with medea
    :param project_name: name of the project to be initialised
    :param medea_dir: base directory where medea is installed / located
    :return:
    """

    project_dir = os.path.join(medea_dir, 'projects', project_name)
    if os.path.exists(project_dir):
        raise NameError(f'A project called {project_name} already exists.')
    else:
        os.makedirs(project_dir)
        os.makedirs(os.path.join(project_dir, 'doc'))
        os.makedirs(os.path.join(project_dir, 'doc', 'figures'))
        os.makedirs(os.path.join(project_dir, 'opt'))
        os.makedirs(os.path.join(project_dir, 'results'))

        # fetch main gams model, if required
        if not os.path.isfile(os.path.join(medea_dir, 'projects', project_name, 'opt', 'medea_main.gms')):
            copyfile(os.path.join(medea_dir, 'src', 'model', 'medea_main.gms'),
                     os.path.join(medea_dir, 'projects', project_name, 'opt', 'medea_main.gms'))
        # fetch template for custom gams model modifications, if required
        if not os.path.isfile(os.path.join(medea_dir, 'projects', project_name, 'opt', f'medea_{project_name}.gms')):
            copyfile(os.path.join(medea_dir, 'src', 'model', 'medea_custom.gms'),
                     os.path.join(medea_dir, 'projects', project_name, 'opt', f'medea_{project_name}.gms'))
        # fetch main gams data, if required
        if not os.path.isfile(os.path.join(medea_dir, 'projects', project_name, 'opt', 'medea_main_data.gdx')):
            copyfile(os.path.join(medea_dir, 'data', 'gdx', 'medea_main_data.gdx'),
                     os.path.join(medea_dir, 'projects', project_name, 'opt', 'medea_main_data.gdx'))

        # fetch **settings** template, if required
        if not os.path.isfile(os.path.join(medea_dir, 'projects', project_name, 'opt', f'settings_{project_name}.py')):
            with open(os.path.join(medea_dir, 'src', 'templates', 'settings_template.py'), 'r') as f:
                settings_template = f.read()

            settings_project = settings_template.replace('_project_name_', project_name)
            with open(os.path.join(medea_dir, 'projects', project_name, f'settings_{project_name}.py'), 'w') as f:
                f.write(settings_project)

        # read, adjust and write **run** template, if required
        if not os.path.isfile(os.path.join(medea_dir, 'projects', project_name, 'opt', f'run_{project_name}.py')):
            with open(os.path.join(medea_dir, 'src', 'templates', 'run_template.py'), 'r') as f:
                run_template = f.read()

            run_project = run_template.replace('medea.settings_template',
                                               f'projects.{project_name}.settings_{project_name}')
            with open(os.path.join(medea_dir, 'projects', project_name, f'run_{project_name}.py'), 'w') as f:
                f.write(run_project)

        # fetch scenario **results** template, if required
        if not os.path.isfile(os.path.join(medea_dir, 'projects', project_name, 'opt', f'results_{project_name}.py')):
            with open(os.path.join(medea_dir, 'src', 'templates', 'results_template.py'), 'r') as f:
                results_template = f.read()

            results_project = results_template.replace('medea.settings_template',
                                                       f'projects.{project_name}.settings_{project_name}')
            with open(os.path.join(medea_dir, 'projects', project_name, f'results_{project_name}.py'), 'w') as f:
                f.write(results_project)

    logging.info(f'Successfully created files and folders for project {project_name}')


if __name__ == '__main__':
    setup_logging()
    create_project(sys.argv[1], sys.argv[2])
