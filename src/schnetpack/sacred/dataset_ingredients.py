import os
from sacred import Ingredient
from schnetpack.datasets import ANI1, ISO17, QM9, MD17, MaterialsProject
from schnetpack.data.parsing import ext_xyz_to_db
from schnetpack.data import AtomsData, AtomsDataError
from schnetpack.atomistic import Properties

dataset_ingredient = Ingredient("dataset")


@dataset_ingredient.config
def cfg():
    """configuration for the dataset ingredient"""
    dbpath = None
    dataset = 'CUSTOM'
    property_mapping = {Properties.energy: ISO17.E,
                        Properties.forces: ISO17.F}


@dataset_ingredient.named_config
def custom():
    dbpath = './data/iso17/reference_eq.db'
    fold = 'reference'
    property_mapping = {Properties.energy: ISO17.E,
                        Properties.forces: ISO17.F}


@dataset_ingredient.named_config
def qm9():
    """configuration for the QM9 dataset"""
    dbpath = './data/qm9.db'
    dataset = 'QM9'
    property_mapping = {Properties.energy: QM9.U0,
                        Properties.dipole_moment: QM9.mu,
                        Properties.iso_polarizability: QM9.alpha}


@dataset_ingredient.named_config
def iso17():
    """configuration for the ISO17 dataset"""
    dbpath = './data'
    dataset = 'ISO17'
    fold = 'reference'
    property_mapping = {Properties.energy: ISO17.E,
                        Properties.forces:ISO17.F}


@dataset_ingredient.named_config
def ani1():
    """configuration for the ANI1 dataset"""
    dbpath = './data/ani1.db'
    dataset = 'ANI1'
    num_heavy_atoms = 2
    property_mapping = {Properties.energy: ANI1.energy}


@dataset_ingredient.named_config
def md17():
    """configuration for the MD17 dataset"""
    dbpath = './data'
    dataset = 'MD17'
    molecule = 'aspirin'
    property_mapping = {Properties.energy: MD17.energy,
                        Properties.forces: MD17.forces}


@dataset_ingredient.named_config
def matproj():
    """configuration for the Materials Project dataset"""
    dbpath = './data/matproj.db'
    dataset = 'MATPROJ'
    cutoff = 5.
    api_key = ''
    property_mapping = {Properties.energy_contributions:
                        MaterialsProject.EPerAtom}


@dataset_ingredient.capture
def get_property_map(properties, property_mapping, dbpath):
    """
    Provide property map from model properties to dataset properties.

    Args:
        properties (list): model properties
        property_mapping (dict): dict with all possible mappings
        dbpath (str): path to the local database

    Returns:
        dict: The mapping dictionary with model properties as keys and
        dataset properties as values.

    """
    if type(property_mapping) == str:
        property_mapping =\
            {key: value for key, value in
             [prop.split(':') for prop in property_mapping.split(',')]}
    property_map = {}
    for prop in properties:
        if prop in property_mapping.keys():
            property_map[prop] = property_mapping[prop]
        else:
            raise AtomsDataError('"{}" is not a valid property that is '
                                 'contained in the property_mapping for the '
                                 'database located ad {}.'.format(prop, dbpath))
    return property_map


@dataset_ingredient.capture
def get_ani1(dbpath, num_heavy_atoms, dataset_properties):
    """
    Args:
        dbpath (str): path to the local database
        num_heavy_atoms (int): max number of heavy atoms per molecule
        dataset_properties (list): properties of the dataset

    Returns:
        AtomsData object

    """
    return ANI1(dbpath, num_heavy_atoms=num_heavy_atoms,
                properties=dataset_properties)


@dataset_ingredient.capture
def get_matproj(dbpath, cutoff, api_key, dataset_properties):
    """
    Args:
        dbpath (str): path to the local database
        cutoff (float): cutoff radius
        api_key (str): personal api_key for materialsproject.org
        dataset_properties (list): properties of the dataset

    Returns:
        AtomsData object

    """
    return MaterialsProject(dbpath, cutoff, api_key,
                            properties=dataset_properties)


@dataset_ingredient.capture
def get_iso17(dbpath, fold, dataset_properties):
    """
    Args:
        dbpath (str): path to the local database directory
        fold (str): name of the local iso17 database
        dataset_properties (list): properties of the dataset

    Returns:
        AtomsData object

    """
    return ISO17(dbpath, fold, properties=dataset_properties)


@dataset_ingredient.capture
def get_md17(dbpath, molecule, dataset_properties):
    """
    Args:
        dbpath (str): path to the local database
        molecule (str): name of a molecule that is contained in the MD17 dataset
        dataset_properties (list): properties of the dataset

    Returns:
        AtomsData object

    """
    return MD17(dbpath, molecule=molecule, properties=dataset_properties)


@dataset_ingredient.capture
def get_dataset(_log, dbpath, dataset, dataset_properties=None):
    """
    Get a dataset from the configuration.

    Args:
        dbpath (str): path to the local database
        dataset (str): name of the dataset
        dataset_properties (list): properties of the dataset

    Returns:
        AtomsData object

    """
    dataset = dataset.upper()
    _log.info('Load {} dataset'.format(dataset))
    if dataset == 'QM9':
        return QM9(dbpath, properties=dataset_properties)
    elif dataset == 'ISO17':
        return get_iso17(dataset_properties=dataset_properties)
    elif dataset == 'ANI1':
        return get_ani1(dataset_properties=dataset_properties)
    elif dataset == 'MD17':
        return get_md17(dataset_properties=dataset_properties)
    elif dataset == 'MATPROJ':
        return get_matproj(dataset_properties=dataset_properties)
    elif dataset == 'CUSTOM':
        file, extension = os.path.splitext(dbpath)
        if extension == '.db':
            return AtomsData(dbpath, required_properties=dataset_properties)
        elif extension == '.xyz':
            ext_xyz_to_db(dbpath=file+'.db', xyzpath=dbpath)
            return AtomsData(file+'.db', required_properties=dataset_properties)
        else:
            raise NotImplementedError
    else:
        raise NotImplementedError
