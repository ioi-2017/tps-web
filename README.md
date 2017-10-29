Task Preparation System (TPS) - Web Interface
=============================================

The Task Preparation System (TPS) is used to prepare tasks (problems) in programming contests. It has been developed and first used in the IOI 2017 in Tehran, Iran.

TPS consists of a web interface and a command line interface called tps-cli. This is the git repository of the web interface. You may find git repository of tps-cli here.

tps-web visualization of problems prepared using tps-cli. It also provides additional tools including:
* Discussion forums for each problem
* Secure file transfer
* Executing the solution on the judging system (used for exact timing)
* Provide export packages

Cloning the repository
----------------------
TPS includes `isolate` as a submodule. For cloning use:
```bash
git clone --recursive
```
If you have already cloned TPS use:
```bash
git submodule update --init
```

Documentation
-------------
You may find the documentation under the docs directory.

(Note: The documentation is currently incomplete)

License
-------

This software is distributed under the MIT license (see LICENSE.txt),
and uses third party libraries that are distributed under their own terms
(see LICENSE-3RD-PARTY.txt).

Copyright
---------
Copyright (c) 2017, IOI 2017 Host Technical Committee
