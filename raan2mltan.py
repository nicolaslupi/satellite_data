#%%
import numpy as np
import pandas as pd
from jdcal import gcal2jd
import os
import wget
from tqdm import tqdm
current = os.getcwd()

pi = np.pi
pi2 = 2*pi
#%%
filename = current + '/nut80.csv'
if os.path.exists(filename):
    pass
else:
    print('Downloading nut80.csv...')
    wget.download('https://drive.google.com/uc?export=download&id=1lkSPPxPlU1ks-IGu_MR-9A1y29jZsxHo', 'nut80.csv')

data = pd.read_excel('updated_database.xlsx')

#%%
""" Main Functions """
def funarg(t):
  seccon = 206264.8062470964
  rev = 1296000

  arg_1 = ((+0.064 * t + 31.310) * t + 715922.633) * t + 485866.733 + (1325.0 * t) % (1.0) * rev
  arg_1 = arg_1 % rev
  arg_2 = ((-0.012 * t - 0.577) * t + 1292581.224) * t + 1287099.8040 + (99.0 * t) % (1.0) * rev
  arg_2 = arg_2 % rev
  arg_3 = ((+0.011 * t - 13.257) * t + 295263.137) * t + 335778.877 + (1342.0 * t) % (1.0) * rev      
  arg_3 = arg_3 % rev
  arg_4 = ((+0.019 * t - 6.891) * t + 1105601.328) * t + 1072261.307 + (1236.0 * t) % (1.0) * rev
  arg_4 = arg_4 % rev
  arg_5 = ((0.008 * t + 7.455) * t - 482890.539) * t + 450160.280  - (5.0 * t) % (1.0) * rev 
  arg_5 = arg_5 % rev

  arg = [arg_1, arg_2, arg_3, arg_4, arg_5]

  for i in np.arange(len(arg)):
    arg[i] = arg[i] % rev
    if arg[i] < 0.0:
      arg[i] = arg[i] + rev
    arg[i] = arg[i] / seccon

  el     = arg[0]
  elprim = arg[1]
  f      = arg[2]
  d      = arg[3]
  omega  = arg[4]

  return [el, elprim, f, d, omega]

def nod(jdate):
  global inutate, xnod
  
  if 'xnod' not in locals():
    xnod = pd.read_csv('nut80.csv', header=None)
    inutate = 0

  tjcent = (jdate - 2451545.0) / 36525.0
  [l, lp, f, d, om] = funarg(tjcent)

  dpsi = 0
  deps = 0

  for j in np.arange(xnod.shape[0]):
    i = xnod.shape[0] - j - 1
    arg = xnod.iloc[i, 0] * l + xnod.iloc[i, 1] * lp + xnod.iloc[i, 2] * f + xnod.iloc[i, 3] * d + xnod.iloc[i, 4] * om
    dpsi = (xnod.iloc[i, 5] + xnod.iloc[i, 6] * tjcent) * np.sin(arg) + dpsi
    deps = (xnod.iloc[i, 7] + xnod.iloc[i, 8] * tjcent) * np.cos(arg) + deps

  dpsi = dpsi * 1e-4
  deps = deps * 1e-4

  return [dpsi, deps]

def sun2(jdate):
  global suncoef, sdata, rlsun

  if 'suncoef' not in locals():
    sdata=np.array([403406, 0, 4.721964, 1.621043, 195207, -97597, 5.937458, 62830.348067, 119433, -59715,\
                    1.115589, 62830.821524, 112392, -56188, 5.781616, 62829.634302, 3891, -1556, 5.5474, 125660.5691,\
                    2819, -1126, 1.5120, 125660.9845, 1721, -861, 4.1897, 62832.4766, 0, 941, 1.163, 0.813, 660, -264,\
                    5.415, 125659.310, 350, -163, 4.315, 57533.850, 334, 0, 4.553, -33.931, 314, 309, 5.198, 777137.715,\
                    268, -158, 5.989, 78604.191, 242, 0, 2.911, 5.412, 234, -54, 1.423, 39302.098, 158, 0, 0.061, -34.861,\
                    132, -93, 2.317, 115067.698, 129, -20, 3.193, 15774.337, 114, 0, 2.828, 5296.670, 99, -47, 0.52, 58849.27,\
                    93, 0, 4.65, 5296.11, 86, 0, 4.35, -3980.70, 78, -33, 2.75, 52237.69, 72, -32, 4.50, 55076.47, 68, 0, 3.23,\
                    261.08, 64, -10, 1.22, 15773.85, 46, -16, 0.14, 188491.03, 38, 0, 3.44, -7756.55, 37, 0, 4.37, 264.89,\
                    32, -24, 1.14, 117906.27, 29, -13, 2.84, 55075.75, 28, 0, 5.96, -7961.39, 27, -9, 5.09, 188489.81, 27,\
                    0, 1.72, 2132.19, 25, -17, 2.56, 109771.03, 24, -11, 1.92, 54868.56, 21, 0, 0.09, 25443.93, 21, 31, 5.98,\
                    -55731.43, 20, -10, 4.03, 60697.74, 18, 0, 4.27, 2132.79, 17, -12, 0.79, 109771.63, 14, 0, 4.24, -7752.82,\
                    13, -5, 2.01, 188491.91, 13, 0, 2.65, 207.81, 13, 0, 4.98, 29424.63, 12, 0, 0.93, -7.99, 10, 0, 2.21,\
                    46941.14, 10, 0, 3.59, -68.29, 10, 0, 1.50, 21463.25, 10, -9, 2.55, 157208.40])
    suncoef = 0

  sl = sdata[0::4]
  sr = sdata[1::4]
  sa = sdata[2::4]
  sb = sdata[3::4]

  u = (jdate - 2451545) / 3652500

  a1 = 2.18 + u * (-3375.7 + u * 0.36)
  a2 = 3.51 + u * (125666.39 + u * 0.1)
  psi = 0.0000001 * (-834 * np.sin(a1) - 64 * np.sin(a2))
  deps = 0.0000001 * u * (-226938 + u * (-75 + u * (96926 + u * (-2491 - u * 12104))))
  meps = 0.0000001 * (4090928 + 446 * np.cos(a1) + 28 * np.cos(a2))
  eps = meps + deps
  seps = np.sin(eps)
  ceps = np.cos(eps)
  dl = 0
  dr = 0

  for i in np.arange(len(sa)):
    w = sa[i] + sb[i] * u
    dl = dl + sl[i] * np.sin(w)

    if sr[i] != 0:
      dr = dr + sr[i] * np.cos(w)

  dl = (dl * 0.0000001 + 4.9353929 + 62833.196168 * u) % (2.0 * pi)
  dr = 149597870.691 * (dr * 0.0000001 + 1.0001026)
  rlsun = (dl + 0.0000001 * (-993 + 17 * np.cos(3.1 + 62830.14 * u)) + psi) % (2.0 * pi)
  rb = 0

  cl = np.cos(rlsun)
  sl = np.sin(rlsun)
  cb = np.cos(rb)
  sb = np.sin(rb)

  decl = np.arcsin(ceps * sb + seps * cb * sl)
  sra = -seps * sb + ceps * cb * sl
  cra = cb * cl
  rasc = np.arctan2(sra, cra)

  rsun_1 = dr * np.cos(rasc) * np.cos(decl)
  rsun_2 = dr * np.sin(rasc) * np.cos(decl)
  rsun_3 = dr * np.sin(decl)
  rsun = [rsun_1, rsun_2, rsun_3]

  return [rasc, decl, rsun]

def raan2mltan(jdate, raan):
  global eot, rasc_ms
  
  dtr = pi / 180
  rtd = 180 / pi
  atr = dtr / 3600
  [rasc_ts, decl, rsun] = sun2(jdate)

  t = (jdate - 2451545) / 365250
  t2 = t**2
  t3 = t**3
  t4 = t**4
  t5 = t**5

  l0 = dtr * ((280.4664567 + 360007.6982779 * t + 0.03032028 * t2 + t3 / 49931 - t4 / 15299 - t5 / 1988000) % (360))

  [psi, eps] = nod(jdate)

  t = (jdate - 2451545.0) / 36525.0
  t2 = t**2
  t3 = t**3

  obm = atr * (84381.4480 - 46.8150 * t - 0.00059 * t2 + 0.001813 * t3)
  obt = obm + atr * eps
  eot = l0 - dtr * 0.0057183 - rasc_ts + atr * psi * np.cos(obt)
  rasc_ms = (rasc_ts + eot) % pi2
  mltan = rtd * (raan - rasc_ms) / 15.0 + 12.0

  return mltan

#%%
""" Get MLTAN for LEO orbits """
print('\nComputing MLTAN...')
for index, row in tqdm(data.iterrows()):
    if pd.isna(row.epoch) == False:
        if row.orbit_class == 'LEO':
            d, m, y = row.epoch.day, row.epoch.month, row.epoch.year
            julian = sum( gcal2jd(y, m, d) )
            raan = row.RAAN
            raan_rd = np.deg2rad( raan )
            mltan = raan2mltan( julian, raan_rd )
            if mltan < 0:
                mltan += 24
            elif mltan > 24:
                mltan -= 24
            
            data.loc[index, 'mltan'] = mltan

data.to_excel( 'mltan_database.xlsx', index=False )