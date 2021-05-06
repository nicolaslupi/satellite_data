#%%
import os
import wget
import requests
import json
import configparser
from time import sleep
from datetime import datetime

import numpy as np
import pandas as pd
import pickle as pk
from tqdm import tqdm
current = os.getcwd()

filename = current + '/SLTrack.ini'
print('Retrieving Space-Track login data...')
if os.path.exists(filename):
  os.remove(filename)
wget.download('https://drive.google.com/uc?export=download&id=1ja_1sgA4GXEoTTE8ypKe3pSqeJfw-kVb', 'SLTrack.ini')

#%%
""" Load what I've done so far """

class generic_class():
  def __init__(self):
    pass
  def load(self, filename):
    with open(filename, 'rb') as input:
      tmp_dict = pk.load(input)
    self.__dict__.update(tmp_dict)

tles = generic_class()

filename = current + '/tles.pkl'
if os.path.exists(filename):
  print('\nUsing existing data')
else:
  print('\nRetrieving tles.pkl...')
  wget.download('https://drive.google.com/uc?export=download&id=1TIUzCP2QGM6R-UXcugNmFz4cFIOKG9Xn', 'tles.pkl')

tles.load('tles.pkl')
res = tles.res
failed = tles.failed
processed = list(res.keys()) + failed  

#%%
""" Open Merged Databases from UCS """
SEED = 0

data = pd.read_excel('merged_databases.xlsx')
data['norad'] = data['norad'].apply( str )
if 'processed' not in locals():
  to_be_processed = data.norad
else:
  to_be_processed = data.norad[[norad not in processed for norad in data.norad]]

""" Store Results """
class tles():
  def __init__(self):
    pass
  def store(self, failed, res):
    self.failed = failed
    self.res = res
  def write(self, filename):
    with open(filename, 'wb') as output:
      pk.dump(self.__dict__, output, pk.HIGHEST_PROTOCOL)

save_results = tles()

#%%
""" Space-track.org Main Settings """

class MyError(Exception):
    def __init___(self,args):
        Exception.__init__(self,"my exception was raised with arguments {0}".format(args))
        self.args = args

uriBase                 = "https://www.space-track.org"
requestLogin            = "/ajaxauth/login"
requestCmdAction        = "/basicspacedata/query" 
requestSat_1            = "/class/tle/NORAD_CAT_ID/"
requestSat_2            = "/orderby/EPOCH asc/limit/1/emptyresult/show/"

config = configparser.ConfigParser()
config.read("./SLTrack.ini")
configUsr = config.get("configuration","username")
configPwd = config.get("configuration","password")
siteCred = {'identity': configUsr, 'password': configPwd}

#%%
""" API Queries """
i = 0

with requests.Session() as session:
  resp = session.post(uriBase + requestLogin, data = siteCred)
  if resp.status_code != 200:
      raise MyError(resp, "POST fail on login")
  print(resp.status_code)

  for norad in tqdm(np.unique(to_be_processed)):
    resp = session.get(uriBase + requestCmdAction + requestSat_1 + norad + requestSat_2 )
    if resp.status_code != 200:
      print(resp)
      print(norad)
      failed.append(norad)
    else:
      content = json.loads(resp.text)
      if len(content) > 0:
        res[norad] = json.loads( resp.text )[0]
      else:
        failed.append(norad)
        print(norad + 'empty')

    sleep(12)
    save_results.store(failed, res)
    save_results.write('tles.pkl')
    i += 1
        
n_processed = len(failed) + len(list(res.keys()))
print('Processed so far', n_processed)
filename = current + '/SLTrack.ini'
os.remove(filename)