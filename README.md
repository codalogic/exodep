# exodep

Exodep falls in the class of Dependency Management tools - just.  Most
Dependency Management tools, such as Ruby gem, Python Pip and Node.js npm
are designed to help programs run.  Exodep is intended to help manage
dependencies when building programs in languages such as C++, C# and Java.

Exodep's focus is on downloading dependencies. Unlike other Dependency
Management tools, it doesn't offer special help on how downloaded files
are compiled, or resolve conflicts between different versions of an
external library being used in the same project.

Most other Dependency Management tools operate in a one-click style fashion.
With Exodep it is expected that you may have to edit exodep configuration
files as part of your project setup in order to get the files you want in
the right place for your particular project.

As such Exodep might be more accurately described as a Dependecy
Downloader, or Dependency Refresher.

# Getting Started

Firstly, you'll need Python 3 on your system.

Once you've got Python installed, the simplest way to install `exodep` is to
simply copy `exodep.py` to your repo, most likely placing it in its
top-level directory.  You can then configure `exodep` using `exodep`
configuration files as described below.

## Windows Installer

If you are on Windows, you can download and install the [`exodep`
Windows MSI installer](https://raw.githubusercontent.com/codalogic/exodep/master/installers/windows/Release/exodep.msi).

This doesn't install Python 3, but it does add registry settings to create a
context menu entry in Windows Explorer to run `exodep.py` in the current folder.

On the downside, it may not always be the most up-to-date
version.  One option is to install `exodep` into a location other than the
default `C:\Program Files\...` folder, such as `C:\Programs\Exodep`.  This
then doesn't require Administrator permissions to write to it, and `exodep.py`
can be used to update itself with the latest version simply by double clicking
on it in Windows Explorer, or by using the right-click context menu.

# Principles of Operation

Exodep downloads files from a Github, Gitlab or Bitbucket-like central code repository
over HTTP.  It can also copy from files that are on a central file server
that is mounted into your directory structure.  For convenience it's assumed that
the former scenario is in effect.

The basic command for downloading a file is the `get` command.  So that this
command can be compact, exodep has a `uritemplate` that says how to convert the
file named in the `get` command into a URL that can be used to download the
desired file.  As part of this, exodep allows the user to specify variables.
These can be used to expand the `uritemplate` and specify where the downloaded
files should be copied to.  The `default` command allows setting default values
for variables that can be overridden.

More than one exodep configuration file can be used in a project.  This is
supported using the `include` command.

# Configuration

The operation of `exodep.py` is configured using configuration files.  The
configuration file to use can be specified on the command line.

If no configuration file is specified, the default usage scenario, `exodep.py`
will interpret the contents of the file named `mydeps.exodep`.

If `mydeps.exodep` is not present it will look for a file called
`exodep-imports/mydeps.exodep`.

If that is also not present it will look for `exodep` files in the
`exodep-imports/` directory and its sub-directories by globbing `*.exodep`.
Before globbing the contents of a directory, it will test whether a file
called `__init.exodep` is present.  If the init file is found, the context it
creates will be used while processing `exodep` files found in the directory
and its sub-directories.  This allows simple customisation of the
behaviour of imported `exodep` files without having to edit them.

Note that, during globbing, files with names beginning with `__` and `^` are
skipped.  (Exodep file names beginning with `__` are reserved to have special
meaning to `exodep`, and files beginning with `^` are designated as
user-specified, non-globbed files.)

After all `exodep` files in a directory and its sub-directories have been
processed, if present, the directory's `__end.exodep` file will be processed.

Finally, if a file named `__pause.exodep` is present, a pause until the user
presses the return key will be performed.

# Configuration file format

Exodep configuration files are line oriented.  Each command must be on its
own line.  The various commands are documented below.

## Comments

Comments begin with a `#`.  Blank lines and lines consisting only of comments
are ignored.

Comments can appear on their own line or at the end of a command line but are
not permitted on lines that set variables.

Example:

    # This is a comment
    hosting gitlab    # This is a comment
    $var   # This is NOT a comment (will be assigned to the variable)

## include

A dependency may be dependent on other files specified in other exodep
configuarion files.  These dependencies can be specified using the `include`
command.  The same exodep configuration file can be `include`d in multiple
configuration files.  Its contents are only processed the first time it is
`include`d.

Example:

    include other-library.exodep

## uritemplate

The URI template is used to map the files mentioned in the `get` commands
into a URL that can be used to download a file.

When you want to download files from Github or BitBucket, rather than using
the `uritemplate` command, it is recommended that the `hosting` command is
used.

By default the URI template is configured for Github and looks like:

    https://raw.githubusercontent.com/${owner}/${project}/${strand}/${path}${file}

As part of downloading a file the variables such as `$owner` and `$project` are
substituted into the template to form a valid URL.  See the sections below for
further details on the 'magical' `$strand`, `$path` and `$file` variables.

Example:

    uritemplate https://raw.githubusercontent.com/myacct/myproj/master/${file}

## hosting

The `hosting` command provides an easier and less error prone way of setting
a URI template for common hosting providers.  Currently Github, Bitbucket and
Gitlab are supported.  In effect, the default is `github`.

`hosting local` indicates that the files on the local system or accessible
via regular file names on the local system.

Examples:

    hosting bitbucket
    hosting github
    hosting gitlab
    hosting local

## authority

Specifies where the 'original', authorative exodep file of the downloaded exodep
file being processed is located.  The remote, authorative version is downloaded
and if it differs from the local version an error message is displayed.

Example:

    $owner codalogic
    $project exodep
    $strand apple
    versions

    authority exodep-exports/exodep.exodep

## uses

Specifies the name of an exodep file that this exodep file depends on.

exodep will look for all the exodep files it can find and if it doesn't find
the one named in the `uses` command it will report an error.

For example, the following will report an error if `other.exodep` is not
found in the `exodep-imports` sub-directory tree:

    uses http://github.com/example/path/exodep-exports/other.exodep

## variables

Variables can be set to values that can be substituted into the URI template
and the destination file specification of the get command.  Variables are
set using the form:

    $variable_name  variable_value

The `variable_value` may contain spaces.  The `variable_name` can not.
`variable_value` can be absent, in which case the variable is set to the
empty string.

Certain variables, such as `$owner` and `$project` have standardised meanings
by convention.

Other variables like `$strand` and `$path` have special 'magical' behaviour.
See the section 'versions' command below for more on the `$strand` variable.

The `$file` variable is automatically set by the `get` command and should
not be set manual in a configuration.

When performing variable expansion, the sequence `${variable_name}` is
replaced by the value of the variable `$variable_name`.

Before invoking a `get` (or `versions`) command using the default URI
templates the variables `$owner`, `$project` and `$strand` must be set.
The `$path` variable is automatically set to the empty string at start-up.

Examples:

    $owner codalogic
    $project exodep
    $strand apple

When the `$project` variable is set, the variable `$lcproject` is also
automatically set with all characters set to lower case.

Variables with names starting with two underscores (`__`) are reserved for use
by `exodep` internally, and shouldn't be set by the user.

## default

The `default` command allows a configuration called by another script to
specify default values.  The format is:

    default $variable_name  variable_value

In this case, if the `$variable_name` variable already as a value it is not
overwritten.  This allows, for example, a configuration to specify a default
location for header files, which can be overridden by a configuration file
that includes it.

For example, part of a configuration for a library, called my-lib.exodep,
might include:

    default $h_files include/my-lib/
    get my-lib.h ${h_files}

A configuration file that includes the above project can enforce it's
value for `$h_files` by doing:

    $h_files include/
    include my-lib.exodep

As a result of this, the `get` command would be expanded to:

    get my-lib.h include/

## showvars

The `showvars` command shows the currently set variables in alphabetical
order.  If a variable references other variables, both the un-expanded
and expanded forms are shown.  It is intended to aid debugging.

For example, given:

    $pet dog
    $animal ${pet}

Would yield:

    $animal: ${pet} -> dog
    $pet: dog

## versions

The `versions` command downloads a file called `versions.exodep` from the
top-level directory of the remote server's master branch.  If this command is
invoked and is successful the value stored in the `$strand` variable
is looked up in this file and converted to a suitable Git branch name
before doing URI template expansion.

The active lines in the `versions.exodep` file consist of a Git branch
name (or similar VCS concept) followed by a list of space separated
strand names that can be mapped to it.

The file may also include comments and blank lines for clarity.

For example, with a `versions.exodep` file containing:

    # These are my mappings

    master banana
    defunct1 apple alpha

if the `$strand` variable is set to `apple`, the look-up operation would
yield `defunct1` and this value would be used in place of the `${strand}`
field when forming the URL for file downloading.  The resulting URL might
look like:

    https://raw.githubusercontent.com/codalogic/exodep/defunct1/exodep.py

This mechanims allows for separation of a version name and the repository
branch on which it is stored.

Example:

    versions

## autovars

`autovars` conveniently sets up a number of variables, based on the value of
the `$project` variable.  The following commands are effectively run, where
`<project-safe-name>` is the value of `$project` with any hyphen (`-`) characters
converted to underscores (`_`):

    versions    # Only executed if $strand != 'master'

    default $ext_home
    default $ext_test_home      test/

    # These arethe top level of the various include/src directories etc.
    default $inc_dst       ${ext_home}include/
    default $src_dst       ${ext_home}src/
    default $code_dst      ${ext_home}
    default $test_inc_dst  ${ext_test_home}include/
    default $test_src_dst  ${ext_test_home}src/
    default $test_code_dst ${ext_test_home}
    default $build_dst     ${ext_home}build/
    default $lib_dst       ${ext_home}lib/
    default $bin_dst       ${ext_home}bin/
    default $scripts_dst   ${ext_home}scripts/

    # These allow the format of project specified files to be changed. e.g. whether it should be "include/myproj/myfile.h" or just "include/myfile.h"
    default $proj_inc_dst        ${inc_dst}${project}/
    default $proj_src_dst        ${src_dst}${project}/
    default $proj_code_dst       ${code_dst}${project}/
    default $proj_test_inc_dst   ${test_inc_dst}${project}/
    default $proj_test_src_dst   ${test_src_dst}${project}/
    default $proj_test_code_dst  ${test_code_dst}${project}/
    default $proj_build_dst      ${build_dst}${project}/
    default $proj_lib_dst        ${lib_dst}${project}/
    default $proj_bin_dst        ${bin_dst}${project}/
    default $proj_scripts_dst    ${scripts_dst}${project}/

    default $<project-safe-name>_inc_dst        ${proj_inc_dst}
    default $<project-safe-name>_src_dst        ${proj_src_dst}
    default $<project-safe-name>_code_dst       ${proj_code_dst}
    default $<project-safe-name>_test_inc_dst   ${proj_test_inc_dst}
    default $<project-safe-name>_test_src_dst   ${proj_test_src_dst}
    default $<project-safe-name>_test_code_dst  ${proj_test_code_dst}
    default $<project-safe-name>_build_dst      ${proj_build_dst}
    default $<project-safe-name>_lib_dst        ${proj_lib_dst}
    default $<project-safe-name>_bin_dst        ${proj_bin_dst}
    default $<project-safe-name>_scripts_dst    ${proj_scripts_dst}

If the `$project` variable contains upper case letters, the following variables
are also set:

    default $<lcproject-safe-name>_inc_dst        ${inc_dst}${lcproject}/
    default $<lcproject-safe-name>_src_dst        ${src_dst}${lcproject}/
    default $<lcproject-safe-name>_code_dst       ${code_dst}${lcproject}/
    default $<lcproject-safe-name>_test_inc_dst   ${test_inc_dst}${lcproject}/
    default $<lcproject-safe-name>_test_src_dst   ${test_src_dst}${lcproject}/
    default $<lcproject-safe-name>_test_code_dst  ${test_code_dst}${lcproject}/
    default $<lcproject-safe-name>_build_dst      ${build_dst}${lcproject}/
    default $<lcproject-safe-name>_lib_dst        ${lib_dst}${lcproject}/
    default $<lcproject-safe-name>_bin_dst        ${bin_dst}${lcproject}/
    default $<lcproject-safe-name>_scripts_dst    ${scripts_dst}${lcproject}/

For example, if you have the following in `__init.exodep`:

    $ext_home external/
    $build_dst build/
    $lib_dst  lib/

And the following in `my-proj.exodep`:

    $project  my-proj
    autovars

This would result in the following variables being setup:

    $ext_home external/

    $inc_dst      external/include/
    $src_dst      external/src/
    $code_dst     external/
    $build_dst    build/
    $lib_dst      lib/
    $bin_dst      external/bin/
    $scripts_dst  external/scripts/

    $my_proj_inc_dst      external/include/my-proj/
    $my_proj_src_dst      external/src/my-proj/
    $my_proj_code_dst     external/my-proj/
    $my_proj_build_dst    build/my-proj/
    $my_proj_lib_dst      lib/my-proj/
    $my_proj_bin_dst      external/bin/my-proj/
    $my_proj_scripts_dst  external/scripts/my-proj/

Variables of the form `???_inc_???` and `???_src_???` are intended to be used
with languages that separate code into include files and source files, such as
C++.  Variables of the form `???_code_???` are intended to be used with
languages that don't use include files, such as Java and C#.  Languages such
as Python and Ruby might be associated with the `???_code_???` variables, if
the project is a Python / Ruby project.  If the project incorporates
Python / Ruby as a project support function, for example to run tests or
generate code, then the Python / Ruby might be associated with the
`???_scripts_???` variable.

To prevent files being put in project specific sub-directories, set variables such as:

    $proj_inc_dst        ${inc_dst}

To ensure project specific sub-directories use only lower case names, use
variables such as:

    $proj_inc_dst        ${inc_dst}${lcproject}/

See also the `lcvars` command.

## lcvars

When run prior to the `autovars` command, typically in the `__init.exodep` file,
this invokes the following commands:

    default $proj_inc_dst        ${inc_dst}${lcproject}/
    default $proj_src_dst        ${src_dst}${lcproject}/
    default $proj_code_dst       ${code_dst}${lcproject}/
    default $proj_test_inc_dst   ${test_inc_dst}${lcproject}/
    default $proj_test_src_dst   ${test_src_dst}${lcproject}/
    default $proj_test_code_dst  ${test_code_dst}${lcproject}/
    default $proj_build_dst      ${build_dst}${lcproject}/
    default $proj_lib_dst        ${lib_dst}${lcproject}/
    default $proj_bin_dst        ${bin_dst}${lcproject}/
    default $proj_scripts_dst    ${scripts_dst}${lcproject}/

This will cause the generated project specific sub-directories to have
lower case names.

## get and bget

The `get` command downloads a text file and the `bget` command downloads
a binary file.  Other than that they have the same functionality.

The commands have the format:

    get   <src-file-name>  <destination>
    bget  <src-file-name>  <destination>

If `destination` resolves to an existing directory, or the name ends in a
`/` then the file identified by <src-file-name> is conditionally
downloaded to that directory.  Otherwise `<destination>` is considered to
be the name of the file to be downloaded to.

The download process initially downloads the file to a temporary location.
It is then compared with any possibly previously downloaded file, and only
moved to the target destination if the files are different.

`<src-file-name>` can be a locally defined URI template.  This is only
recommended for 'quick and dirty' setups.

When `<src-file-name>` is not a URI template, then `src-file-name` is
used as the value of the `${file}` field in URI template expansion.

A single argument form of `get` and `bget` are also supported.  The behaviour
depends on whether the `dest` command has been previously specified.

If the `dest` command has not been previously specified, the following:

    get <src-file-name>

is effectively treated as:

    get <src-file-name>  ${path}<src-file-name>

(As `$path` is included as part of the default URI template expansion,
this has the effect of the two files having the same name.)

If the `dest` command has been specified, the following:

    dest output/
    get <src-file-name>

is effectively treated as:

    get <src-file-name> output/

The `dest` command can be reset by doing:

    dest

`copy` is a legacy alias of `get` and `bcopy` is an alias of `bget`.

## dest

See `get and bget` command for how the `dest` command works.

## subst

The `subst` command substitutes exodep variables contained in a named file.
For example, it can be used to customise a downloaded makefile.

The format of the command is:

    subst <src-file-name> <dst-file-name>

`<dst-file-name>` may be absent, in which case the command is effectively
`subst <src-file-name> <src-file-name>`.

The src file is processed line by line.  Each instance of strings of the
form `${exodep:<var-name>}` is replaced by the `$<var-name>` exodep variable.

For example, given exodep variables of the form:

    $h_path   include/
    $cpp_path src/

and an input file containing the line:

    g++ -I ${exodep:h_path} ${exodep:cpp_path}file1.cpp

the output file would contain:

    g++ -I include/ src/file1.cpp

## cp, mv

`cp` and `mv` allow copying and moving files on the host file system.

They have the form:

    cp <src> <dst>
    mv <src> <dst>

Exodep variables are expanded in the `src` and `dst` names.

To avoid needlessly changing file timestamps, the `cp` command
will only copy a file if the destination doesn't exist or the source and
destination are different.

Example:

    cp results.log ${log_path}final-results.log

## rm

`rm` allows removing a file from the host file system.

The form is:

    rm <file>

Exodep variables are expanded in the `file` name.

Example:

    rm ${tmp}build.log

## mkdir, rmdir

`mkdir` and `rmdir` allow making and removing directories / folders on
the host file system.

They have the form:

    mkdir <dir>
    rmdir <dir>

Exodep variables are expanded in the `dir` name.

`mkdir` will not complain if the directory is already present.

`rmdir` does not require the directory to be empty to remove it.

Example:

    mkdir ${logs}
    rmdir ${tmp}

## touch

`touch` makes sure that a file of the specified name exists.  Note that it
will not create an parent directories in the named file path if they are
not already present.  The format is:

    touch <file>

For example:

    rm alerts-made.txt
    onalerts touch alerts-made.txt

## exec

Causes a shell command to be executed.  It's probably a good idea to use
this command with the `windows`, `linux` or `osx` conditional commands.

Exodep variables in the command are expanded before the command is executed.

Example:

    linux exec make

## on

The `on` command allows conditional execution of exodep commands based on the
value of variables. It has the form:

    on $<var_name> <command>

If the variable $<var_name> is present and is not the empty string, is not
`0` and is not, ignoring case, equal to `false` then the exodep command is
run.

Example:

    on $want_so exec make libso

## ondir, onfile

The `ondir` and `onfile` commands allow conditional execution of exodep
commands based on whether a named directory or named file exists
(respectively).

They have the form:

    ondir <directory name> <command>
    onfile <file name> <command>

Example:

    ondir htdocs default $php_dst htdocs/
    ondir httpdocs default $php_dst httpdocs/
    default $php_dst ./

and:

    onfile send-report.py exec send-report.py

## onlastchanged

The `onlastchanged` command allows conditional execution of exodep commands based
on whether the last downloaded file has been changed.

It has the form:

    onlastchanged <command>

Example:

    get makefile
    onlastchanged make

See also `onchanged` and `onanychanged`.

## onchanged

The `onchanged` command allows conditional execution of exodep commands based
on whether any files have been created or modied by the current outer or
`include`d config script.

It has the form:

    onchanged <command>

See also `onanychanged`.

Example:

    onchanged exec build

## onanychanged

`onanychanged` is similar to `onchanged`.  The difference is that the
sub-command associated with this command will executed if a file has been
created or modified as any point during the running of the `exodep.py`
script, irrespective of whether it was in the out configuration file or
an `include`d configuration file.

Example:

    onanychanged exec commit

## onalerts

`onalerts` executes the associated command if any alert messages have been
processed.  The format is:

    onalerts <command>

For example:

    onalerts exec send-alerts-report.py

## windows, linux, osx

`windows`, `linux` and `osx` are command pre-fixes that allow conditional
executation of a command based on the platform the configuration is running
on.  For example, if you only wanted to download a makefile when on Linux,
you could do:

    linux get makefile ./

## not

The `not` command inverts the conditions looked for in the conditional
commands.  So, for example, `onfile` by itself executes its associated
command if the named file is present, whereas `not onfile` would look for
the absence of a file.

For example:

    not onanychanged echo There were no changes

## echo

Prints the message associated with the command to the screen.  Variable
expansion is performed prior to printing the message.  The format is:

    echo <message>


For example:

    onanychanged echo There were changes

## alert

Prints out an alert message.  Each alert message is displayed as the command
is processed, and is also stored.  The `showalerts` command (perhaps invoked in
`exodep-imports/__end.exodep`) will print out all the accumulated alerts. This
feature is intended to make the alerts more visible.

For example:

    get makefile
    onlastchanged alert makefile changed

    ...
    showalerts
    windows pause

## showalerts

See the `alert` command for more information.

## alertstofile

`alertstofile` sends any recorded alerts to the file named in the command. The
command format is:

    alertstofile <file>

If the named file already exists it will be renamed to `<file>.old` before the
new alerts are written to the file.

If there are no alerts to be written, the named file will effectively be
deleted.  Hence scripts using `exodep` can use the presence or absence of the
named file to determine if alerts were generated.

For example:

    alertstofile alerts.exodep

## pause

The `pause` command will wait for user to press the `Return` key before
continuing.  This can give the user the chance to see any errors, particularly
if running the script by double-clicking it on Windows.  For example, the
following could be placed in the `exodep-imports/__end.exodep`:

    windows onanychanged pause

The `pause` command can optionally specify a message to be displayed prior
to pausing.  For example:

    onchanged pause Project foo has changed

## stop

The `stop` command terminates processing.  If the command has an associated
message, this will be printed out.  If the the file
`exodep-imports/__onstop.exodep` exists, this will be processed in the current
context before execution terminates.

Example:

    get LICENSE
    onlastchanged stop Oh dear! License changed! We might need to think about this

# Example

This is an example configuration for including the `dsl-pa` project at
[https://github.com/codalogic/dsl-pa](https://github.com/codalogic/dsl-pa)
into another project.

    $owner   codalogic
    $project dsl-pa
    $strand  angst

    autovars

    $path include/dsl-pa/
    get dsl-pa.h          ${dsl_pa_inc_dst}
    get dsl-pa-dsl-pa.h   ${dsl_pa_inc_dst}
    get dsl-pa-alphabet.h ${dsl_pa_inc_dst}
    get dsl-pa-reader.h   ${dsl_pa_inc_dst}

    $path src/dsl-pa/
    get dsl-pa-dsl-pa.cpp   ${dsl_pa_src_dst}
    get dsl-pa-alphabet.cpp ${dsl_pa_src_dst}
    get dsl-pa-reader.cpp   ${dsl_pa_src_dst}

The automatic setting of `$dsl_pa_inc_dst` and `$dsl_pa_src_dst` as default
values via `autovars` allows the configuration to be easily created,
while also offering the option to modify its default behaviour.

# Command-line Flags

`--pause` or `-p` will cause `exodep` to pause and wait for user input once
the update has been done.

# Best Current Practices

It's a bit early to talk about Best Practices at this stage.  However, the
intent is to document here strategies that work well with Exodep.

Projects will typically want to both import files using `exodep` and export
them.  To support this it is suggested that a project include two
sub-directories called `exodep-imports` and `exodep-exports` for imports
and exports respectively.

If `exodep` config files are both imported and exported
they can be placed and editted in the `exodep-imports` sub-directory and an
`exodep` configuration file (e.g. `_copy-exports.exodep`) can be used to
copy them to the `exodep-exports` sub-directory.

Some projects, such as utility libraries may have multiple parts that can be
separately exported.  It's suggested that the `exodep` files for such projects
be named according to the format `project-name.sub-feature.exodep`, e.g.
`myutils.string-ops.exodep`.

If you change the contents of an `exodep` configuration file included into
your project, modify its name by prefixing it with your project name.  For
example, if you edit the `importedlib.exodep` file from the `importedlib`
project, and place it in your `myproj` project, call it
`myproj.importedlib.exodep`.

`exodep` configuration file names associated with downloads should not begin
with `_` or `^` characters.

`exodep` configuration files with names beginning with `__` (2 underscores,
for example `__init.exodep`) are reserved to have
special meaning to the `exodep` processor.  `exodep` configuration file names
beginning with `_` (1 underscore, e.g. `_copy-exports.exodep`), should be used
for user-specified local processing, not directly related to downloading files.
`exodep` file names beginning with `^` are also designated for user-specified,
local processing.  The difference is that files with names beginning with a
single `_` are processed during the globbing process, and files with names
beginning with `^` are not processed during the globbing phase.  As a result,
processing of files with names beginning with `^` must be explicitly invoked
in another `exodep` configuration file, such as `exodep-imports/__init.exodep`
or `exodep-imports/__end.exodep`.

To make it easier to download dependent code, and facilitate sharing of code
without clashing of names, it is suggested that
the headers and source are separated into separate directory trees, called
`./include/` and `./src/` respectively.  Within each of these directories, a
directory with the name of the project is placed.  (e.g. leading to
`./include/myproject/` and `./src/myproject/`.)  Files for the projects are
then placed in their respective directories, leading to file names like:
`./include/myproject/myfile.h` and `./src/myproject/myfile.cpp`.  (Parts
of the project that are not intended to be downloaded via `exodep` can be
structured according to developer preference.)

It's suggested that a version controlled project is self-contained such that it
contains all of it external dependencies as part of the repo, rather than
having to run exodep to load them as part of setting up a project.  This makes
it easier to use the repo, makes sure that multiple distributed
snapshots are consistent between developers and permits investigating older
repo versions.

# Bugs and Issues

You can see and submit issues here: [https://github.com/codalogic/exodep/issues](https://github.com/codalogic/exodep/issues)

Larger bugs / issues include:

- The `get` command does not allow specifying file names that contain spaces

# Testing

Open a shell and cd to the `test` directory.  Then run `exodep-unittest.py`.

# License

    The MIT License (MIT)

    Copyright (c) 2016-17 Codalogic Ltd

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
