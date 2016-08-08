========
TestCase
========

In CPS, a testcase is defined as a pair of files. The first file is presented to the task type to generate the output,
and is called **input file**. The second file is used by checker to evaluate the score based on the generated output and
is called **output file**.

==========
Input File
==========

Input file of a testcase can either be static or dynamic. 

* Static input files are provided completely by the user. 

* Dynamic input files are generated using a generator, a program written by the user for generating testcases, and
  some arguments provided to it. The generator is specified in TestCase level, so different TestCases can have different
  generators.

Dynamic input files are generated either when a request is made to access them or when asked explicitly by the user.
For example consider the situation where the solution files aren't ready yet, and generation of input takes a long time,
the user can request the inputs to be generated so when solutions are ready, they can be immediately used to generate
outputs or tested in other ways.


===========
Output File
===========

Similar to the input file, output file is either provided by the user(static output file) or is generated using a
solution. The solution is specified in TestCase level, so different TestCases can have different solutions.

Like input file, output file is generated either upon access request, or explicit generation request by user.


====================================
Accessing dynamic input/output files
====================================
When accessing dynamic input/output file in a testcase, it is possible that the requested file hasn't been generated
previously. By default, the generation of the testcase is started automatically and your process will be
blocked until the generation process is completed. Make sure to manually check whether the generation process has been
completed previously. If not, do not access the file to avoid blocking. You may manually request the file to be generated
in the background.


==========================
Dynamic files invalidation
==========================
Dynamic input and outputs are only generated once and are cached until invalidated. The cache is invalidated
either when the corresponding generator(i.e solution for output and generator or its parameters for input) is changed
or upon explicit request of the user.
