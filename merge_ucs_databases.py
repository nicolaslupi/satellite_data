#%%
import os
import numpy as np
import pandas as pd
import datetime as dt
import re
from tqdm import tqdm
import wget
from zipfile import ZipFile
current = os.getcwd()
PATH = os.path.join(current, 'databases')

#%%
if os.path.exists(PATH):
  pass
else:
  if os.path.exists(current + '/databases.zip') == False:
    print('Downloading databases.zip...')
    wget.download('https://drive.google.com/uc?export=download&id=1Kwhw3tAWjlAXjkU50cEsic-HE_KiWu8c', 'databases.zip')
  print('Unzipping to /databases')
  with ZipFile('databases.zip', 'r') as zipObj:
    zipObj.extractall('databases')

#%%
""" Main Functions """
def correct_inclination(incl):
  if isinstance( incl, str ):
    if re.search('°', incl) is None:
      """ Esta OK """
      return incl
    else:
      return re.sub('°', repl='', string=incl)
  else:
    return incl

def decimals(string):
  if isinstance(string, str):
    return re.sub(',', '.', string)
  else:
    return string

def str2long(string):
  if re.search('\d', string) is None:
    """ Doesn't Contain Longitude """
    return np.nan
  else:
    """ Contains Longitude Data """
    longitude = re.split(pattern=' (?=\d)', string=string)[1]
    longitude = re.split(pattern='° ', string=longitude)
    if len(longitude) > 1:
      if longitude[1] == 'E':
        return float( longitude[0] )
      elif longitude[1] == 'W':
        return - float( longitude[0] )
      elif longitude[1] == '':
        return float( longitude[0] )
      else:
        return np.nan
    
    else:
      longitude = re.split('°', longitude[0])[0]
      longitude = float( longitude )
      if longitude == 0:
        return longitude
      else:
        return np.nan

def simplify_users(string):
  if re.search( pattern = 'mil', string = string.lower() ) is not None:
    return 'Military'
  if re.search( pattern = 'gov', string = string.lower() ) is not None:
    return 'Government'
  if re.search( pattern = 'com', string = string.lower() ) is not None:
    return 'Commercial'
  if re.search( pattern = 'civ', string = string.lower() ) is not None:
    return 'Civil'
  return string

def process_database(database):
  database.drop( database[pd.isna(database['NORAD Number'])].index, inplace=True ) # Remove Nans
  database.drop( database[pd.isna(database['COSPAR Number'])].index, inplace=True ) # Remove Nans
  database['NORAD Number'] = database['NORAD Number'].apply(lambda norad: str(int(norad))) # NORAD to str
  database['COSPAR Number'] = database['COSPAR Number'].apply(lambda cospar: cospar.replace(' ', '')) # Remove spaces
  database['COSPAR_NORAD'] = database['COSPAR Number'] + '-' + database['NORAD Number'] # Combine COSPAR & NORAD
  if 'Longitude of position in GEO' in database.columns:
    database.rename(columns = {'Longitude of position in GEO': 'Longitude of GEO (degrees)'}, inplace=True)

  if 'Class of Orbit' in database.columns: # New Version of Database
    database['Longitude of GEO (degrees)'] = database['Longitude of GEO (degrees)'].apply( decimals )

  else:
    """ Si no tiene Class of Orbit """
    database.drop( database[pd.isna( database['Type of Orbit'] )].index, inplace=True ) # Remove Nans
    database.loc[ database['Type of Orbit'].str.contains('LEO'), 'Class of Orbit' ] = 'LEO'
    database.loc[ database['Type of Orbit'].str.contains('GEO'), 'Class of Orbit' ] = 'GEO'
    database.loc[ database['Type of Orbit'].str.contains('MEO'), 'Class of Orbit' ] = 'MEO'
    database.loc[ database['Type of Orbit'].str.contains('Elliptical'), 'Class of Orbit' ] = 'Elliptical'

    database['Longitude of GEO (degrees)'] = database[ database['Class of Orbit'] == 'GEO' ][ 'Type of Orbit' ].apply( str2long )

  return database

#%%
""" Load Databases """
def load_databases(path):
  databases = []
  database_names = os.listdir(path)
  database_names.sort()
  for database in database_names:
    new_database = pd.read_excel('databases/' + database)
    new_database = process_database( new_database )
    databases.append( new_database )
    print('Read ' + database)
  databases = np.array( databases, dtype=object )
  reverse_databases = np.flip( databases )

  COSPAR_NORAD = [ database['COSPAR_NORAD'].dropna() for database in databases ]
  unique_cospar_norad = np.unique( np.concatenate( np.array(COSPAR_NORAD, dtype=object) ) )
  tracked = unique_cospar_norad

  for i in tqdm( np.arange(reverse_databases.shape[0]) ):
    tmp_db = reverse_databases[i][ reverse_databases[i]['COSPAR_NORAD'].isin( tracked ) ].reset_index(drop=True)
    tmp_db = tmp_db[['COSPAR Number', 'NORAD Number', 'COSPAR_NORAD', 'Class of Orbit', 'Type of Orbit',\
                    'Launch Mass (kg.)', 'Dry Mass (kg.)', 'Users', 'Date of Launch', 'Longitude of GEO (degrees)', \
                    'Perigee (km)', 'Apogee (km)', 'Inclination (degrees)', 'Operator/Owner', 'Country of Operator/Owner']]

    tmp_db.columns = ['cospar','norad', 'cospar_norad', 'orbit_class', 'orbit_type', 'launch_mass', 'dry_mass', 'users', \
                      'date', 'GEO_long_degrees', 'perigee', 'apogee', 'inclination', 'operator', 'country']
    reverse_databases[i] = tmp_db
    present = np.isin( tracked, tmp_db['cospar_norad'] )
    tracked = tracked[ ~present ]
  
  return reverse_databases

#%%
""" Merge Databases """
def merge_databases( databases ):
  data = pd.concat(databases, ignore_index=True)
  data['year'] = data['date'].map(lambda fecha: fecha.year)

  data['dry_mass'] = pd.to_numeric(data['dry_mass'], errors='coerce')
  data['launch_mass'] = pd.to_numeric(data['launch_mass'], errors='coerce')
  data['inclination'] = pd.to_numeric(data['inclination'].apply( correct_inclination ), errors='coerce')
  data['users'] = data.users.apply( simplify_users )
  data['GEO_long_degrees'] = pd.to_numeric(data['GEO_long_degrees'])
  greater_than_180 = data['GEO_long_degrees'] > 180
  if any(greater_than_180):
    data.loc[ greater_than_180, 'GEO_long_degrees' ] -= 360

  data.loc[ (~pd.isna( data.orbit_type )) & (data.orbit_type.str.contains( 'Sun' )), 'orbit_type' ] = 'Sun-Synchronous'
  data.loc[ data.orbit_type == 'LEO/P', 'orbit_type' ] = 'Polar'
  data.loc[ data.orbit_type == 'LEO/I', 'orbit_type' ] = 'Non-Polar Inclined'
  data.loc[ data.orbit_type == 'LEO/E', 'orbit_type' ] = 'Equatorial'
  data.loc[ data.orbit_type == 'LEO', 'orbit_type' ] = np.nan
  data.loc[ data.orbit_type == 'Circular', 'orbit_type' ] = 'Intermediate'
  data.loc[ data.orbit_type == 'Retrograde', 'orbit_type' ] = np.nan

  return data

data = merge_databases( load_databases( PATH ) )
data.to_excel( 'merged_databases.xlsx', index=False )