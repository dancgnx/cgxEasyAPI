# object database

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
    """ extract site object by id
    :param site_id: Cloudgenix sites object id
    :type site_id: str
    :returns: Cloudgenix site object
    :rtype: dictionary
    """
    # if tranlatio db is empty, build it
    if not db[db_name]:
        init_db(db_name)
    return db[db_name].get(db_key, None)
    