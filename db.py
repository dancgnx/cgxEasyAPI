# object database
import re

sdk = None
def init(sdk_in):
    """ initilize the module
    :param sdk_in: authenticated cloudgenix API object
    :type sdk_in: cloudgenix.API()
    """
    global sdk 
    sdk = sdk_in

# init db sturcture
db={}
# sites
db['id2site'] = {}
db['name2site'] = {}
db['name2element'] = {}

def init_db(db_name):
    """ initilize sites translation db
    """
    if db_name in ['id2site', 'name2site']:
        for site in sdk.get.sites().cgx_content['items']:
            db['id2site'][site['id']] = site
            db['name2site'][site['name']] = site
    elif db_name in ['name2element']:
        for element in sdk.get.elements().cgx_content['items']:
            db['name2element'][element['name']] = element

def fetch(db_name, db_key):
    """ extract object by key
    :param db_name: The database name
    :type db_name: str
    :param db_key: The key to search for
    :type db_key: str
    :returns: object
    :rtype: dictionary
    """
    # if tranlatio db is empty, build it
    if not db[db_name]:
        init_db(db_name)
    return db[db_name].get(db_key, None)
def get_re(db_name, db_re):
    """ get a list of object by re on the key
    :param db_name: Cloudgenix sites object id
    :type db_name: str
    :param db_re: regular expression to search
    :type db_re: str - re format
    :returns: mathcing objects
    :rtype: list of dictionary
    """ 
    if not db[db_name]:
        init_db(db_name)

    return [
        value for key, value in db[db_name].items() 
        if key and re.search(db_re, key)
    ]
    