import os
from shutil import copyfile


def create_project(project_name, medea_dir):
    """
    creates application folder and subfolders according to medea-conventions and copies required model and data files.
    Additionally, also fetches some templates to set up scenarios with medea
    :param project_name: name of the project to be initialised
    :param medea_dir: base directory where medea is installed / located
    :return:
    """

    project_dir = os.path.join(medea_dir, 'applications', project_name)
    if os.path.exists(project_dir):
        raise NameError(f'A project called {project_name} already exists.')
    else:
        os.makedirs(project_dir)
        os.makedirs(os.path.join(project_dir, 'doc'))
        os.makedirs(os.path.join(project_dir, 'doc', 'figures'))
        os.makedirs(os.path.join(project_dir, 'opt'))
        os.makedirs(os.path.join(project_dir, 'results'))

        # fetch main gams model, if required
        if not os.path.isfile(os.path.join(medea_dir, 'applications', project_name, 'opt', 'medea_main.gms')):
            copyfile(os.path.join(medea_dir, 'medea', 'medea_main.gms'),
                     os.path.join(medea_dir, 'applications', project_name, 'opt', 'medea_main.gms'))
        # fetch template for custom gams model modifications, if required
        if not os.path.isfile(os.path.join(medea_dir, 'applications', project_name, 'opt', f'medea_{project_name}.gms')):
            copyfile(os.path.join(medea_dir, 'medea', 'medea_custom.gms'),
                     os.path.join(medea_dir, 'applications', project_name, 'opt', f'medea_{project_name}.gms'))
        # fetch main gams data, if required
        if not os.path.isfile(os.path.join(medea_dir, 'applications', project_name, 'opt', 'medea_main_data.gdx')):
            copyfile(os.path.join(medea_dir, 'medea', 'data', 'input', 'medea_main_data.gdx'),
                     os.path.join(medea_dir, 'applications', project_name, 'opt', 'medea_main_data.gdx'))

        # fetch scenario settings template, if required
        if not os.path.isfile(os.path.join(medea_dir, 'applications', project_name, 'opt', f'settings_{project_name}.py')):
            copyfile(os.path.join(medea_dir, 'medea', 'settings_template.py'),
                     os.path.join(medea_dir, 'applications', project_name, f'settings_{project_name}.py'))

        # fetch scenario run template, if required
        if not os.path.isfile(os.path.join(medea_dir, 'applications', project_name, 'opt', f'run_{project_name}.py')):
            copyfile(os.path.join(medea_dir, 'medea', 'run_template.py'),
                     os.path.join(medea_dir, 'applications', project_name, f'run_{project_name}.py'))

        # fetch scenario results template, if required
        if not os.path.isfile(os.path.join(medea_dir, 'applications', project_name, 'opt', f'results_{project_name}.py')):
            copyfile(os.path.join(medea_dir, 'medea', 'settings_template.py'),
                     os.path.join(medea_dir, 'applications', project_name, f'results_{project_name}.py'))

    print(f'Successfully created files and folders for project {project_name}')
