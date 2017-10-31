Task Preparation System (TPS) - Web Interface
=============================================

The Task Preparation System (TPS) is used to prepare tasks (problems) in programming contests. 
It has been developed and first used in the [IOI 2017](http://ioi2017.org/) in Tehran, Iran.

TPS consists of a web interface and a command-line interface, called TPS-Web and TPS-CLI, respectively.
The web interface is provided here. You may find the command-line interface at
https://github.com/ioi-2017/tps-cli.

The TPS-CLI provides a set of scripts for preparing the tasks, while
The TPS-Web provides a web interface to visualize the tasks,
and prepare them for final release.

Features
--------
* Visualize task components and structure
* Execute the solutions on real judging environments (e.g. CMS) for exact timing
* Generate verification report
* Export final packages in custom formats 
* Discussion forums for each problem
* Secure file transfer


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
