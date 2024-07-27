"""
Module pour rassembler le code à utiliser dans l'explo de la BDNB
"""
from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path("../data/open_data_millesime_2022-10-d_dep92_csv/csv")

BAT_KEY = "batiment_groupe_id"

ENSEIGNEMENT_DICT = {
    "rabelais_mat": "920490000C0167_a7d6a1e1aa7fcb7 ",
    "boileau":"uf920490024401_19e9d8bf322bb27",
    "haut-mesnil_mat": "uf920490024389_7f3ccc2799de586",
    #"briand_mat": ? pas trouvé sur GoRenove "92049_0045_00087",
    #"buffalo_mat": ? pas trouvé sur GoRenove "92049_9650_00041",
    "berthelot_mat": "uf920490024399_23723cf7aac094c",
    "arnoux_mat": "920490000A0148_d4dfcc07a128b02",
    #"jeanne_darc_mat": ? pas trouvé dans la base adresse...
    "yaguel_yaacov_mat":"uf920490021183_26c68224c38b9e7",
    "pardess_hannah_mat": "920490000O0110_9f18a4514600a8f",
    "queneau_elt": "920490000G0010_54e125a97b6b096",
    "renaudel": "uf920490024390_d3b7f519ee82f90",
    "rabelais": "920490000C0167_a7d6a1e1aa7fcb7",
    "jeanne_darc": "920490000B0262_4c9e065498b4d43",
    "jean_monnet": "920490000X0080_ac0c3301627df2e",
    "genevoix": "920490000R0051_8f30b00a36f6490",
    # "doisneaux": ? pas trouvé sur GoRenove
    "faculte_dentaire": "uf920490009851_79d8cb03b57154f",
}

AUTRES_DICT = {
    # ci-dessous, que des bâtiments tertiaires ordinaires !
    #"croix-rouge": "920490000F0056_c3088e25da3ba15",
    # "asn": "92049_5160_00015",
    "maison_assoc": "920490000Q0053_24bae3c1076ade2"
}


def get_bat_gp_df():
    """
    Get the 'batiment_groupe' data
    """
    return pd.read_csv(DATA_DIR / "batiment_groupe.csv", index_col=BAT_KEY)


def get_bat_montrouge():
    """
    Get 'batiment_groupe' for Montrouge
    """
    bat_gp_df = get_bat_gp_df()
    
    return bat_gp_df[bat_gp_df["code_commune_insee"] == 92049][['s_geom_groupe', 'contient_fictive_geom_groupe']]


def get_bat_gp_ffo():
    """
    Get data from 'ffo' data source
    """
    return pd.read_csv(DATA_DIR / "batiment_groupe_ffo_bat.csv", index_col=BAT_KEY)


def get_bat_gp_ign():
    """
    Get data from IGN
    """
    return pd.read_csv(DATA_DIR / "batiment_groupe_bdtopo_bat.csv", index_col=BAT_KEY)


def get_full_bat_montrouge():
    """
    Compile 'full' batiment data from multiple data sources
    """
    bat_montrouge = get_bat_montrouge()
    bat_gp_ffo = get_bat_gp_ffo()
    bat_gp_ign = get_bat_gp_ign()
    
    merge_1 = bat_montrouge.merge(bat_gp_ffo[["annee_construction", "usage_niveau_1_txt"]], how='left', right_index=True, left_index=True)
    
    return merge_1.merge(bat_gp_ign[["l_nature", "l_usage_1"]], how='left', right_index=True, left_index=True)


def select_comm_bat(full_bat_montrouge):
    """
    Select relevant 'bâtiments tertiaires' from provided data 
    
    NB: relies on preliminary investigation for the commune at hand, namely Montrouge. See code below for specific conditions used.
    """
    cond_mask = (full_bat_montrouge["usage_niveau_1_txt"]=="Tertiaire & Autres") | (
        (full_bat_montrouge["usage_niveau_1_txt"].isnull()) & (full_bat_montrouge["l_usage_1"].str.contains("Commercial et services", na=False))
    )
    
    exclusion_usage_nature_mask = (full_bat_montrouge["l_nature"].str.contains("Tour, donjon", na=False)) | (
        full_bat_montrouge["l_usage_1"].str.contains("Sportif", na=False)) | (
        full_bat_montrouge["l_usage_1"].str.contains("Religieux", na=False))
    
    exclusion_enseignement = full_bat_montrouge.index.isin(list(ENSEIGNEMENT_DICT.values()))
    
    exclusion_autre = full_bat_montrouge.index.isin(list(AUTRES_DICT.values()))
    
    return full_bat_montrouge[cond_mask & ~exclusion_usage_nature_mask & ~exclusion_enseignement & ~exclusion_autre]


def get_adresse_df():
    return pd.read_csv(DATA_DIR / "batiment_groupe_adresse.csv", index_col=BAT_KEY)
    
    
def get_bat_cstr_df():
    """
    Get data for 'batiment_construction', *i.e.* a single building within a group.
    
    NB: there can be multiple 'batiment_construction's for a single 'batiment_groupe'
    """
    return pd.read_csv(DATA_DIR / "batiment_construction.csv")


def select_bat_cstr(comm_bat_df, bat_cstr_df):
    """
    Select suitable 'batiment_construction' based on provided 'batiment_groupe' data
    """
    select_idx = comm_bat_df.index
    
    return bat_cstr_df[bat_cstr_df[BAT_KEY].isin(select_idx)].copy()


def get_bat_cstr(bat_key):
    """
    Retrieve 'batiment_construction' from a 'batiment_groupe' id
    """
    bat_cstr_df = get_bat_cstr_df()
    
    return bat_cstr_df[bat_cstr_df[BAT_KEY]==bat_key]


def estimate_levels(bat_cstr_df):
    """
    Estimate the number of levels of 'batiment_construction' from the 'hauteur' variable.
    
    Create column 'levels_estim'
    
    NB:
    * "hauteur" is given in m
    * floor_height is specified in m
    """
    floor_height = 2.5
    
    bat_cstr_df["levels_estim"] = (bat_cstr_df["hauteur"]/floor_height).apply(np.floor)
    
    return bat_cstr_df


def estimate_s_total_cstr(bat_cstr_df):
    """
    From a dataframe with 'levels_estim', evaluate total surface of 'batiment_construction'
    """
    bat_cstr_df["s_total_cstr_estim"] = bat_cstr_df["levels_estim"] * bat_cstr_df["s_geom_cstr"]
    
    return bat_cstr_df
