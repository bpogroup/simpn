import simpn
from importlib.resources import files 
from os.path import exists

def get_img_asset(asset_name):
    """
    Returns the filepath for the asset within the package directory.
    """
    fspath = files(simpn).joinpath("assets", "img", asset_name)
    if not exists(fspath):
        raise ValueError(f"Unable to find asset :: {fspath}")
    return fspath