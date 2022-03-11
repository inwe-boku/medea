# %% imports
from pathlib import Path
import subprocess
import multiprocessing as mp
from collections import OrderedDict
from itertools import product, repeat
from gamstransfer import *


def run_medea(gams_dir, project_dir, medea_gms, project, run_id, compress=True):
    """
    flexible run of power system model medea
    :param gams_dir: string of path to GAMS executable
    :param medea_gms: string of path to GAMS model to solve
    :param project: string of medea-project name
    :param run_id: string of project-scenario (typically one iteration)
    :param project_dir: string of path to GAMS project directory
    :param compress: boolean; set to True to compress output-gdx
    :return:
    """
    if Path(os.getcwd()) != project_dir:
        os.chdir(project_dir)

    # generate identifier of scenario output
    gdx_out = "medea_out{run_id}.gdx".format(run_id=f'_{run_id}' if run_id is not None else '')
    gdx_in = project_dir / f'medea_{run_id}_data.gdx'
    run_str = "{gams_dir}\\gams {medea_gms} {gdx} lo=3 o=nul{prj}{scn}".format(
        gams_dir=gams_dir,
        medea_gms=medea_gms,
        gdx=f'gdx={gdx_out}',
        prj=f' --project={project}' if project is not None else '',
        scn=f' --scenario={run_id}' if run_id is not None else ''
    )
    # call GAMS to solve model / scenario
    subprocess.run(run_str)
    #    f'{gams_dir}\\gams {medea_gms} gdx={gdx_out} lo=3 o=nul --project={project} --scenario={run_id}')
    # compress generated gdx file
    if compress:
        subprocess.run(
            f'gdxcopy -V7C -Replace {gdx_out}'
        )
    # clean up after each run and delete input data (which is also included in output, so no information lost)
    if os.path.isfile(gdx_in):
        os.remove(gdx_in)


def run_medea_campaign(gams_dir, root_dir, project, scenario_id, campaign, compress=True):
    """
    runs / solves a project of power system model medea with strict project directory conventions
    :param campaign:
    :param gams_dir: Complete path to gams.exe
    :param root_dir: Path to
    :param project: string of medea-project name
    :param scenario_id: string of project-scenario (typically one iteration)
    :param compress: boolean; set to True to compress output-gdx
    :return:
    """

    # generate file names
    opt_dir = Path(root_dir) / 'opt'
    gms_model = opt_dir / 'medea_main.gms'
    gdx_out = opt_dir / campaign / f'medea_out_{scenario_id}.gdx'
    input_fname = opt_dir / campaign / f'medea_{scenario_id}_data.gdx'

    # call GAMS to solve model / scenario
    subprocess.run(
        f'{gams_dir}\\gams {gms_model} gdx={gdx_out} lo=3 o=nul --project={project} --scenario={scenario_id}'
    )
    # compress generated gdx file
    if compress:
        subprocess.run(
            f'gdxcopy -V7C -Replace {gdx_out}'
        )
    # clean up after each run and delete input data (which is also included in output, so no information lost)
    if os.path.isfile(input_fname):
        os.remove(input_fname)


# %% parallel processing
def create_scenario_gdx(container, gdx_path, dict_base, dict_campaign):
    """
    Generates gdx input files for each scenario iteration in a separate folder for each campaign.
    :param container: A GAMStransfer Container holding all required MEDEA parameters
    :param gdx_path: a Path-object with the path to the GAMS project directory (project_dir/opt)
    :param dict_base: a nested dictionary that defines baseline values for all parameters to be (potentially) modified.
        Expected structure: dict_base = {'base': {'co2_price': [value], pv_limit: [values]}}
    :param dict_campaign: a nested dictionary with parameter modifications for each campaign
    :return:
    """
    for campaign in dict_campaign.keys():
        # update campaign dictionary
        parms_dict = dict_base.copy()
        parms_dict.update(dict_campaign[campaign])

        od = OrderedDict(sorted(parms_dict.items()))
        cart = list(product(*od.values()))
        moddf = pd.DataFrame(cart, columns=od.keys())

        for par in parms_dict.keys():
            if par not in container.listSymbols():
                _ = Parameter(container, par, [], records=pd.DataFrame(data=[0]))

        # create campaign path if it does not exist
        (gdx_path / campaign).mkdir(parents=True, exist_ok=True)

        for n in range(0, len(cart)):
            for par in parms_dict.keys():
                sym = container.getSymbols(par)
                sym[0].setRecords(pd.DataFrame(data=[moddf.loc[n, par]]))

            identifier = '_'.join(map(str, cart[n]))
            input_fname = gdx_path / campaign / f'medea_{identifier}_data.gdx'
            container.write(str(input_fname))


def run_medea_parallel(number_of_workers, gams_dir, root_dir, project, campaign_dict):
    """
    Run medea models in parallel. Requires pre-prepared gdx-input for each run. create_scenario_gdx can be used for
    this purpose.
    :param gams_dir:
    :param number_of_workers: integer specifying the number of parallel processes started
    :param root_dir: string holding the project's root directory
    :param campaign_dict: dictionary with scenario definitions with format according to medea-conventions
    :return:
    """
    for campaign in campaign_dict.keys():
        od = OrderedDict(sorted(campaign_dict[campaign].items()))
        cart = list(product(*od.values()))
        identifier = ['_'.join(map(str, cart[n])) for n in range(0, len(cart))]

        p = mp.Pool(number_of_workers)
        _ = p.starmap(run_medea_campaign, zip(repeat(gams_dir), repeat(root_dir), repeat(project), identifier,
                                              repeat(campaign)))
