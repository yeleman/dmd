# dmd
DRC Malaria Dashboard


## Linux dependencies

`apt-get install build-essential libssl-dev libffi-dev python-dev p7zip-full`

## Setup

* PIP requirements
* Fixtures
* Partners:
 * dhisbot
 * validationbot
* Import DHIS data

```
# m h  dom mon dow   command

# DHIS import 3 times per month, with 3 months update
0 8 10,20,1 * * ~/envs/dmd/bin/python ~/dmd/manage.py import-dhis-data -p `date +"%Y-%m"` -i -u
0 2 10,20,1 * * ~/envs/dmd/bin/python ~/dmd/manage.py export_all_records

# cold-fusion cache
0 22 * * * ~/envs/dmd/bin/python ~/dmd/manage.py update_cached_data

# Database dump
0 3 * * * ~/envs/dmd/bin/python ~/dmd/manage.py dump_db
0 5 * * * ~/envs/dmd/bin/python ~/dmd/manage.py rotate_dumps
```
