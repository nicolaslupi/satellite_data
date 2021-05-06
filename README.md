# satellite_data
Grabs UCS Satellite datasets and combines them in order to have one observation per satellite. For each satellite, additional information such as RAAN is obtained using the Space-Track API. Data is cleaned and some new variables are created. The final result is a dataset containing target orbits for historical launches.

### Instructions
Run the .py files in the following order:
1. merge_ucs_databases.py
2. space_track.py
3. merge_ucs_tle.py
4. raan2mltan.py

The final output is the mltan_database.xlsx