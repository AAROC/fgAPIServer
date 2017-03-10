# Tests
This section contains test scripts.
In order to test fgapiserver; the `PYTHON_PATH` environment variable must be set properly and test executed as follows:
```sh
export PYTHONPATH=$PYTHONPATH:..:.
./test_fgapiserver.py
```
Another mandatory configuration is related to the fgapiserver.conf file that must contain default development configuration settings. In particular ensure the matching of the following configuration values in `fgapiserver.conf` fie.
```
fgapisrv_notoken    = True
fgapisrv_notokenusr = test
```

## MySQLdb
Test script makes use of a custom `MySQLdb` class where each SQL statement executed by the `fgapiserverdb.py` file is hardcoded.
The list of supported statements is a python vector of maps called: `queries`.
Each map in the vector has the following structure:

```json
{'query': 'SELECT VERSION()',
 'result': [['5.7.17', ], ]},
```
This class currently does not take in consideration query input values as defined in `sql_data`. Query results are then hardcoded inside the `result` field.

## test_fgapiserver.py
This test script makes use of unittests and its code is splitted in two separated sections. A firt part consists of unit tests on `fgapiserver.py` code; the second part contains functional tests on developed Flask endpoints.
In the functional tests; each returned JSON is compared through its MD5Sum value with the `assertEqual()` method. The MD5Sum value to compare is extracted during the test case development and then hardcoded inside the `assertEqual()` method.

## test_mklogtoken.py
This script executes a simple test on mklogtoken.py code used by the baseline Authentication and Authorization.
It starts to encrypt username/password and timestamp and retrieve back this information with decrypting method.


