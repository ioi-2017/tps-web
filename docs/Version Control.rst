====================
Why version control?
====================
In any collaborative system, a version control system must be present which will take care of simultaneous changes
applied by contributors. It's also important to introduce a system for keeping changes' history as well as providing
the feature of reverting to a previous version in case of mistakes by collaborators.

===========================
CPS' version control system
===========================
The main challenge faced in introducing a version control system is the method of data storage.
Different approaches for storing data were considered for handling version control in CPS which are shortly explained
and then compared to each other below. It is necessary to be acquainted with CPS database entities to fully understand
the text below.

1. JSON as database: Consider a database system where tables and rows are
represented by directories and JSON files, respectively. Thus, a problem would simply be a collection of JSON files
which can be viewed as a separate git repository, every edit session being a clone of this repository.

2. DMS-Git: In this approach, a normal Database Management System such as PostgreSQL
 would be used to store entities data. All required communications with the database is done through DMS. Additionally,
 similar to the first approach, data is also stored as JSON files, and a git repository is created for each problem.
 Starting an edit session, results in duplicating current problem's data in the DMS,
 as well as making a clone of the problem's repository. However, JSON files are only updated when a change in the history,
 should be recorded(e.g. a commit for an edit session or a request of merge to master problem repository).
 In these cases, DMS data is first dumped over current JSON files. Then, the operation is handled using git.

3. DMS-only: This is the most straight-forward approach. Using a normal DMS and handling VCS-related operations
manually(e.g. Cloning every data when starting a new edit session, merging data as long as the same field was not
edited in both sessions and reporting a conflict otherwise).

================             ==============================             ==============================
    Approach                            Upsides                                    Downsides
================             ==============================             ==============================
JSON as database             * Using git for handling VCS-              * No currently available
                               operations.                                backends for Django.
                             * Fast problem cloning(for                 * No professional DMS feature
                               new edit sessions)                         (e.g. triggers) is present
DMS-Git                      * Using git for handling VCS-              * Data is stored in two ways.
                               operations.                              * Complicated operations
                             * Professional DMS features
                               available
DMS-only                     * Simple                                   * No sophisticated git
                             * Easy to handle                             operations.
================             ==============================             ==============================


It was concluded that there is no need for sophisticated merge operations like git,
as it is completely acceptable to produce a conflict error if the same field was edited in both sessions(i.e. there is no
need to try and resolve merge conflicts occurred in the same field). Thus, although it requires implementation of VCS
operations, the third approach was chosen, due to its simplicity.
