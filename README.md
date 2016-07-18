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
top-level directory.  You can then create a `mydeps.exodep` file, as
described below, that tells exodep what to do.

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
configuration file to use can be specified on the command line.  If no
configuration file is specified, the default usage scenario, `exodep.py` will
interpret the contents of the file named `mydeps.exodep`.

Exodep configuration files are line oriented.  Each command must be on its
own line.  The various commands are documented below.

## Comments

Comments begin with a `#`.  Blank lines and lines consistig only of comments
are ignored.

Example:

    # A comment

## include

## uritemplate

## hosting

## variables

### Magical Variables

### Strands and Versions

## copy and bcopy

# Best Practices

It's a bit early to talk about Best Practices at this stage.  However, the
intent is to document here strategies that work well with Exodep.

# Bugs and Issues

You can see and submit issues here: [https://github.com/codalogic/exodep/issues](https://github.com/codalogic/exodep/issues)

Larger bugs / issues include:

- The `copy` command does not allow specifying file names that contain spaces

# Testing
Open a shell and cd to the `test` directory.  Then run `exodep-unittest.py`.
