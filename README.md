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
0 8 10,20,1 * * cd ~/dmd && ~/envs/dmd/bin/python ./manage.py import-dhis -p `date +"%Y-%m"` -i -u

# Database dump
0 3 * * * cd ~/dmd && ~/envs/dmd/bin/python ./manage.py dump_db
0 5 * * * cd ~/dmd && ~/envs/dmd/bin/python ./manage.py rotate_dumps
```
