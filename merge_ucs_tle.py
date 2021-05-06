#%%
import numpy as np
import pandas as pd
import os, sys
import pickle as pk
import datetime as dt

current = os.getcwd()
SEED = 0

#%%
""" Load TLEs """

class generic_class():
  def __init__(self):
    pass
  def load(self, filename):
    with open(filename, 'rb') as input:
      tmp_dict = pk.load(input)
    self.__dict__.update(tmp_dict)

tles = generic_class()
tles.load('tles.pkl')

#%%
""" Load Merged Databases """
data = pd.read_excel('merged_databases.xlsx')
data['norad'] = data['norad'].map(lambda norad: str(int(norad)))

#%%
""" Combine Both Sources """

for index, sat in data.iterrows():
    norad = sat['norad']
    if norad in list(tles.res.keys()):
      data.loc[index, 'arg_of_perigee'] = float( tles.res[norad]['ARG_OF_PERICENTER'] )
      fecha = dt.datetime.strptime( tles.res[norad]['EPOCH'], '%Y-%m-%d %H:%M:%S' ).date()
      data.loc[index, 'epoch'] = fecha
      if pd.isna( sat['inclination'] ):
        data.loc[index, 'inclination'] = float( tles.res[norad]['INCLINATION'] )

      if sat['orbit_class'] == 'LEO':
        data.loc[index, 'RAAN'] = float( tles.res[norad]['RA_OF_ASC_NODE'] )

data.to_excel( 'updated_database.xlsx', index=False )