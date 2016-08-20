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

You'll need Python 3 on your system.  Once you've got that installed,
simply copy `exodep.py` to your repo, most likely placing it in its
top-level directory.  You can then configure `exodep` using `exodep`
configuration files as described below.

# Principles of Operation

Exodep downloads files from a Github or Bitbucket like central code repository
over HTTP.  It can also copy from files that are on a central file server
that is mounted into your directory structure.  For convenience we assume that
the former scenario is in effect.

The basic command for downloading a file is the `copy` command.  So that this
command can be compact, exodep has a `uritemplate` that says how to convert the
file named in the `copy` command into a URL that can be used to download the
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

If that is also not present it will look for a file called
`exodep-imports/__init.exodep`.  If the init file is found it will process it
and then interpret all the `exodep` config files it finds by globbing
`exodep-imports/*.exodep` using the context created by processing
`exodep-imports/__init.exodep`.  This allows simple customisation of the
behaviour of imported `exodep` files without having to edit them.

If `exodep-imports/__init.exodep` is not
found then it will interpret all the config files it finds by globbing
`exodep-imports/*.exodep`.

# Configuration file format

Exodep configuration files are line oriented.  Each command must be on its
own line.  The various commands are documented below.

## Comments

Comments begin with a `#`.  Blank lines and lines consistig only of comments
are ignored.

Example:

    # A comment

## include

A dependency may be dependent on other files specified in other exodep
configuarion files.  These dependencies can be specified using the `include`
command.  The same exodep configuration file can be `include`d in multiple
configuration files.  Its contents are only processed the first time it is
`include`d.

Example:

    include other-library.exodep

## uritemplate

The URI template is used to map the files mentioned in the `copy` commands
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
a URI template for common hosting providers.  Currently Github and Bitbucket
are supported.  In effect, the default is `github`.

Examples:

    hosting bitbucket
    hosting github

## variables

Variables can be set to values that can be substituted into the URI template
and the destination file specification of the copy command.  Variables are
set using the form:

    $variable_name  variable_value

The `variable_value` may contain spaces.  The `variable_name` can not.

Certain variables, such as `$owner` and `$project` have standardised meanings
by convention.

Other variables like `$strand` and `$path` have special 'magical' behaviour.
See the section 'versions' command below for more on the `$strand` variable.

The `$file` variable is automatically set by the `copy` command and should
not be set manual in a configuration.

When performing variable expansion, the sequence `${variable_name}` is
replaced by the value of the variable `$variable_name`.

Before invoking a `copy` (or `versions`) command using the default URI
templates the variables `$owner`, `$project` and `$strand` must be set.
The `$path` variable is automatically set to the empty string at start-up.

Examples:

    $owner codalogic
    $project exodep
    $strand apple

### default

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
    copy my-lib.h ${h_files}

A configuration file that includes the above project can enforce it's
value for `$h_files` by doing:

    $h_files include/
    include my-lib.exodep

As a result of this, the `copy` command would be expanded to:

    copy my-lib.h include/

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

## copy and bcopy

The `copy` command downloads a text file and the `bcopy` command downloads
a binary file.  Other than that they have the same functionality.

The commands have the format:

    copy  <src-file-name>  <destination>
    bcopy  <src-file-name>  <destination>

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

A single argument form of `copy` and `bcopy` are also supported.  In this
case, the following:

    copy <src-file-name>

is effectively treated as:

    copy <src-file-name>  ${path}<src-file-name>

(As `$path` is included as part of the default URI template expansion,
this has the effect of the two files having the same name.)

`get` is an alias of `copy` and `bget` is an alias of `bcopy`.

## subst

The `subst` command substitutes exodep variables into a named file.

The format of the command is:

    subst <src-file-name> <dst-file-name>

`<dst-file-name>` may be absent, in which case the command is effectively
`subst <src-file-name> <src-file-name>`.

The src file is processed line by line.  Each instance of strings of the
form `${exodep:<var-name>}` is replaced by the `$<var-name>` exodep variable.

For example, given exodep variables of the form:

    $h_path   include/
    $cpp_path src/

and an input file of the form:

    g++ -I ${exodep:h_path} ${exodep:src}file1.cpp

the output file would be:

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

## exec

Causes a shell command to be executed.  It's probably a good idea to use
this command with the `windows`, `linux` or `osx` conditional commands.

Exodep variables in the command are expanded before the command is executed.

Example:

    linux exec make

## on

The `on` command allows conditional execution of exodep ommands. It has
the form:

    on $<var_name> <command>

If the variable $<var_name> is present and is not the empty string then the
exodep command is run.

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

## windows, linux, osx

`windows`, `linux` and `osx` are command pre-fixes that allow conditional
executation of a command based on the platform the configuration is running
on.  For example, if you only wanted to download a makefile when on Linux,
you could do:

    linux copy makefile ./

# Example

This is an example configuration for including the `dsl-pa` project at
[https://github.com/codalogic/dsl-pa](https://github.com/codalogic/dsl-pa)
into another project.

    default $h_dst   include/dsl-pa/
    default $cpp_dst src/dsl-pa/

    default $dsl_pa_h_dst   ${h_dst}
    default $dsl_pa_cpp_dst ${cpp_dst}

    $owner   codalogic
    $project dsl-pa
    $strand  angst

    hosting github
    versions    # Invoking 'versions' must happen after setting $owner/$project variables

    $path include/dsl-pa/
    copy dsl-pa.h          ${h_dst}
    copy dsl-pa-dsl-pa.h   ${h_dst}
    copy dsl-pa-alphabet.h ${h_dst}
    copy dsl-pa-reader.h   ${h_dst}

    $path src/
    copy dsl-pa-dsl-pa.cpp   ${cpp_dst}
    copy dsl-pa-alphabet.cpp ${cpp_dst}
    copy dsl-pa-reader.cpp   ${cpp_dst}

Setting `$dsl_pa_h_dst` and `$h_dst`, and `$dsl_pa_cpp_dst` and `$cpp_dst`
as default values allows for the configuration to be used stand-alone, while
also offering a configuration that includes it the option to modify its
behaviour.

# Best Current Practices

It's a bit early to talk about Best Practices at this stage.  However, the
intent is to document here strategies that work well with Exodep.

Projects will typically want to both import files using `exodep` and export
them.  To support this it is suggested that a project include two
sub-directories called `exodep-imports` and `exodep-exports` for imports
and exports respectively.

If `exodep` config files are both imported and exported
they can be placed and editted in the `exodep-imports` sub-directory and an
`exodep` configuration file (e.g. `__copy-exports.exodep`) can be used to
copy them to the `exodep-exports` sub-directory.

If a project exports multiple `exodep` configuration files, it maybe
appropriate to put all those files within a sub-directory of the
`exodep-imports` sub-directory in the importing project.

Some projects, such as utility libraries may have multiple parts that can be
separately exported.  It's suggested that the `exodep` files for such projects
be named according to the format `project-name.sub-feature.exodep`, e.g.
`myutils.string-ops.exodep`.

If when including an `exodep` configuration file into your project, modify the
name by prefixing it with your project name.  For example, if you edit the
`mylib.exodep` file from the `mylib` project, and place it in your `myproj`
project, call it `myproj.mylib.exodep`.

It's suggested that a version controlled project is self-contained such that it
contains all of it external dependencies as part of the repo, rather than
having to run exodep to load them as part of setting up a project.  This makes
it easier to use the repo, makes sure that multiple distributed
snapshots are consistent between developers and permits investigating older
repo versions.

# Bugs and Issues

You can see and submit issues here: [https://github.com/codalogic/exodep/issues](https://github.com/codalogic/exodep/issues)

Larger bugs / issues include:

- The `copy` command does not allow specifying file names that contain spaces

# Testing

Open a shell and cd to the `test` directory.  Then run `exodep-unittest.py`.

# License

    The MIT License (MIT)

    Copyright (c) 2016 Codalogic Ltd

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
