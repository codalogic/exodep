#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2016 Codalogic Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Exodep is a simple dependency downloader. See the following for more details:
#
#     https://github.com/codalogic/exodep

import argparse
import sys
import re
import io
import os
import urllib.request
import tempfile
import shutil
import filecmp
import glob

host_templates = {
        'github': 'https://raw.githubusercontent.com/${owner}/${project}/${strand}/${path}${file}',
        'gitlab': 'https://gitlab.com/${owner}/${project}/raw/${strand}/${path}${file}',
        'bitbucket': 'https://bitbucket.org/${owner}/${project}/raw/${strand}/${path}${file}' }

onstop_exodep = 'exodep-imports/__onstop.exodep'

default_vars = { 'strand': 'master', 'path': '' }

exodep_file_set = {}

class StopException( Exception ):
    pass

def main():
    args = process_command_line_args()
    collect_exodep_file_set()
    run( args )

def process_command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument( "recipe", nargs="?", default=None, help="An exodep file to be processed" )
    parser.add_argument( "-p", "--pause", help="pause after execution", action="store_true" )
    return parser.parse_args()

def collect_exodep_file_set( dir = 'exodep-imports' ):
    for file in glob.glob( dir + '/*.exodep' ):
        exodep_file_set[os.path.basename(file)] = 1
    for subdir in glob.glob( dir + '/*' ):
        subdir = subdir.replace( '\\', '/' )
        if os.path.isdir( subdir ):
            collect_exodep_file_set( subdir )

def run( args ):
    try:
        if args.recipe:
            ProcessDeps( args.recipe )
        elif os.path.isfile( 'mydeps.exodep' ):
            ProcessDeps( 'mydeps.exodep' )
        elif os.path.isfile( 'exodep-imports/mydeps.exodep' ):
            ProcessDeps( 'exodep-imports/mydeps.exodep' )
        else:
            process_globbed_exodep_imports( 'exodep-imports', default_vars )

        if args.pause:
            pause()

    except StopException:
        pass

def process_globbed_exodep_imports( dir, vars ):
    init_exodep = dir + '/__init.exodep'
    end_exodep = dir + '/__end.exodep'
    pause_exodep = dir + '/__pause.exodep'
    if os.path.isfile( init_exodep ):
        pd = ProcessDeps( init_exodep, vars )
        vars = pd.get_vars()
    for file in glob.glob( dir + '/*.exodep' ):
        file = file.replace( '\\', '/' )
        if not is_ignored_glob( file ):
            ProcessDeps( file, vars )
    for subdir in glob.glob( dir + '/*' ):
        subdir = subdir.replace( '\\', '/' )
        if os.path.isdir( subdir ):
            process_globbed_exodep_imports( subdir, vars )
    if os.path.isfile( end_exodep ):
        ProcessDeps( end_exodep, vars )
    if os.path.isfile( pause_exodep ):
        pause()

def is_ignored_glob( file ):
    return file.find( '/__' ) >= 0 or file.find( '/^' ) >= 0;

class ProcessDeps:
    are_any_files_changed = False
    alert_messages = ""
    shown_alert_messages = ""

    processed_configs = {}

    def __init__( self, dependencies_src, vars = default_vars ):
        self.is_last_file_changed = self.are_files_changed = False
        self.line_num = 0
        self.uritemplate = host_templates['github']
        self.set_vars( vars )
        self.versions = {}  # Each entry is <string of space separated strand names> : <string to use as strand in uri template>
        self.sought_condition = True
        self.default_dest = None
        if isinstance( dependencies_src, str ):
            if self.is_config_already_processed( dependencies_src ):
                return
            self.file = dependencies_src
            self.process_dependency_file()
        elif isinstance( dependencies_src, io.StringIO ):    # Primarily for testing
            self.file = "<StringIO>"
            self.process_dependency_stream( dependencies_src )
        else:
            self.error( "Unrecognised dependencies_src type format" )

    def get_vars( self ):
        return self.vars

    def set_vars( self, vars ):
        self.vars = vars.copy()
        # Remove non-exportable vars
        self.vars.pop( '__authority', None )

    def is_config_already_processed( self, dependencies_src ):
        abs_dependencies_src = os.path.abspath( dependencies_src )
        if abs_dependencies_src in ProcessDeps.processed_configs:
            return True
        ProcessDeps.processed_configs[abs_dependencies_src] = True
        return False

    def process_dependency_file( self ):
        try:
            with open(self.file) as f:
                self.process_dependency_stream( f )
        except FileNotFoundError:
            self.error( "Unable to open exodep file: " + self.file )

    def process_dependency_stream( self, f ):
        for line in f:
            self.line_num += 1
            self.sought_condition = True
            self.process_line( line )

    def process_line( self, line ):
        line = line.strip()
        line = remove_comments( line )
        if is_blank_line( line ):
            return
        command, arguments = split_in_2( line )
        if not (self.consider_include( command, arguments ) or
                self.consider_sinclude( command, arguments ) or
                self.consider_hosting( command, arguments ) or
                self.consider_uritemplate( command, arguments ) or
                self.consider_versions( command, arguments ) or
                self.consider_authority( command, arguments ) or
                self.consider_uses( command, arguments ) or
                self.consider_variable( command, arguments ) or
                self.consider_default_variable( command, arguments ) or
                self.consider_showvars( command, arguments ) or
                self.consider_lcvars( command, arguments ) or
                self.consider_autovars( command, arguments ) or
                self.consider_dest( command, arguments ) or
                self.consider_get( command, arguments ) or
                self.consider_bget( command, arguments ) or
                self.consider_file_ops( command, arguments ) or
                self.consider_exec( command, arguments ) or
                self.consider_subst( command, arguments ) or
                self.consider_on_conditional( command, arguments ) or
                self.consider_ondir( command, arguments ) or
                self.consider_onfile( command, arguments ) or
                self.consider_onlastchanged( command, arguments ) or
                self.consider_onchanged( command, arguments ) or
                self.consider_onanychanged( command, arguments ) or
                self.consider_onalerts( command, arguments ) or
                self.consider_os_conditional( command, arguments ) or
                self.consider_not( command, arguments ) or
                self.consider_echo( command, arguments ) or
                self.consider_pause( command, arguments ) or
                self.consider_alert( command, arguments ) or
                self.consider_showalerts( command, arguments ) or
                self.consider_alertstofile( command, arguments ) or
                self.consider_stop( command, arguments ) ):
            self.report_unrecognised_command( line )

    def consider_include( self, command, arguments ):
        if command == 'include' and  arguments != None:
            file_name = self.script_relative_path( arguments )
            if not os.path.isfile( file_name ):
                self.error( "'include' file not found: " + file_name )
                return True     # It was an 'include' command, even though it was a bad one
            ProcessDeps( file_name, self.vars )
            return True
        return False

    def consider_sinclude( self, command, arguments ):        # This method is used to support testing
        if command == 'sinclude' and arguments != None:
            ProcessDeps( io.StringIO( arguments.replace( '\t', '\n' ) ), self.vars )
            return True
        return False

    def script_relative_path( self, src ):
        return os.path.normpath( os.path.join( os.path.dirname( self.file ), src ) ).replace( '\\', '/' )

    def consider_hosting( self, command, arguments ):
        if command == 'hosting' and arguments != None:
            host = arguments
            if host in host_templates:
                self.uritemplate = host_templates[host]
            else:
                self.error( "Unrecognised hosting server provider: " + host )
            return True
        return False

    def consider_uritemplate( self, command, arguments ):
        if command == 'uritemplate' and arguments != None:
            self.uritemplate = arguments
            return True
        return False

    def consider_authority( self, command, arguments ):
        if command == 'authority' and arguments != None:
            src = arguments
            from_uri = self.make_uri( src )
            self.vars['__authority'] = from_uri
            if re.match( 'https?://', from_uri ):
                tmp_name = TextDownloadHandler().download_to_temp_file( from_uri )
            else:
                tmp_name = self.local_copy_to_temp_file( from_uri )     # Taking a local copy is not optimal, but keeps the subsequent update logic the same
            if not tmp_name:
                self.error( "Unable to retrieve authority exodep file from: " + from_uri )
                return True
            if self.file[0] != "<" and not text_filecmp( tmp_name, self.file ):
                self.error( "local exodep file out of sync with authority: " + self.file )
            os.unlink( tmp_name )
            return True
        return False

    def consider_uses( self, command, arguments ):
        if command == 'uses' and arguments != None:
            exodep_file = os.path.basename( arguments )
            if not exodep_file in exodep_file_set:
                self.error( "uses command specifies unfound exodep file: " + exodep_file )
            return True
        return False

    def consider_versions( self, command, arguments ):
        if command == 'versions':
            file_name = arguments if arguments else 'versions.exodep'
            uri = self.make_master_strand_uri( file_name )
            try:
                if re.match( 'https?://', uri ):
                    with urllib.request.urlopen( uri ) as fin:
                        self.parse_versions_info( fin )
                else:
                    with open( uri, "rt" ) as fin:
                        self.parse_versions_info( fin )
            except:
                self.error( "Unable to retrieve: " + uri )
            return True
        return False

    def parse_versions_info( self, fin ):
        for line in fin:
            if isinstance( line, bytes ):
                line = line.decode( 'utf-8' )
            line = line.rstrip()
            line = remove_comments( line )
            if not is_blank_line( line ):
                m = re.match( '^(\S+)\s+(.*)', line )
                if m != None:
                    self.versions[m.group(2)] = m.group(1)

    def consider_variable( self, command, arguments ):
        if command[0] == '$':
            self.set_single_variable( command[1:], arguments )
            return True
        return False

    def consider_default_variable( self, command, arguments ):
        if command == 'default' and arguments != None and arguments[0] == '$':
            var, value = split_in_2( arguments )
            var_name = var[1:]
            if var_name not in self.vars:
                self.set_single_variable( var_name, value )
            return True
        return False

    def set_single_variable( self, name, value ):
        self.vars[name] = value if value else ''
        if name == 'project':
            self.vars['lcproject'] = value.lower() if value else ''
        
    def consider_showvars( self, command, arguments ):
        if command == 'showvars':
            for var in sorted( self.vars.keys() ):
                raw = self.vars[var]
                expanded = self.expand_variables( raw )
                expansion = '' if expanded == raw else (' -> ' + expanded)
                print( var + ": " + raw + expansion )
            return True
        return False

    def consider_lcvars( self, command, arguments ):
        if command == 'lcvars':
            self.process_line( 'default $proj_inc_dst        ${inc_dst}${lcproject}/' )
            self.process_line( 'default $proj_src_dst        ${src_dst}${lcproject}/' )
            self.process_line( 'default $proj_code_dst       ${code_dst}${lcproject}/' )
            self.process_line( 'default $proj_test_inc_dst   ${test_inc_dst}${lcproject}/' )
            self.process_line( 'default $proj_test_src_dst   ${test_src_dst}${lcproject}/' )
            self.process_line( 'default $proj_test_code_dst  ${test_code_dst}${lcproject}/' )
            self.process_line( 'default $proj_build_dst      ${build_dst}${lcproject}/' )
            self.process_line( 'default $proj_lib_dst        ${lib_dst}${lcproject}/' )
            self.process_line( 'default $proj_bin_dst        ${bin_dst}${lcproject}/' )
            self.process_line( 'default $proj_scripts_dst    ${scripts_dst}${lcproject}/' )
            return True
        return False

    def consider_autovars( self, command, arguments ):
        if command == 'autovars':
            if 'project' not in self.vars:
                self.error( "`$project` variable must be set before calling `autovars` command" )
                return True
            project = self.vars['project']
            safe_project = project.replace( '-', '_' )
            if 'strand' in self.vars and self.vars['strand'] != 'master':
                self.process_line( 'versions' )

            self.process_line( 'default $ext_home' )
            self.process_line( 'default $ext_test_home    test/' )

            # These arethe top level of the various include/src directories etc.
            self.process_line( 'default $inc_dst       ${ext_home}include/' )
            self.process_line( 'default $src_dst       ${ext_home}src/' )
            self.process_line( 'default $code_dst      ${ext_home}' )
            self.process_line( 'default $test_inc_dst  ${ext_test_home}include/' )
            self.process_line( 'default $test_src_dst  ${ext_test_home}src/' )
            self.process_line( 'default $test_code_dst ${ext_test_home}' )
            self.process_line( 'default $build_dst     ${ext_home}build/' )
            self.process_line( 'default $lib_dst       ${ext_home}lib/' )
            self.process_line( 'default $bin_dst       ${ext_home}bin/' )
            self.process_line( 'default $scripts_dst   ${ext_home}scripts/' )

            # These allow the format of project specified files to be changed. e.g. whether it should be "include/myproj/myfile.h" or just "include/myfile.h"
            self.process_line( 'default $proj_inc_dst        ${inc_dst}${project}/' )
            self.process_line( 'default $proj_src_dst        ${src_dst}${project}/' )
            self.process_line( 'default $proj_code_dst       ${code_dst}${project}/' )
            self.process_line( 'default $proj_test_inc_dst   ${test_inc_dst}${project}/' )
            self.process_line( 'default $proj_test_src_dst   ${test_src_dst}${project}/' )
            self.process_line( 'default $proj_test_code_dst  ${test_code_dst}${project}/' )
            self.process_line( 'default $proj_build_dst      ${build_dst}${project}/' )
            self.process_line( 'default $proj_lib_dst        ${lib_dst}${project}/' )
            self.process_line( 'default $proj_bin_dst        ${bin_dst}${project}/' )
            self.process_line( 'default $proj_scripts_dst    ${scripts_dst}${project}/' )

            self.process_line( 'default $' + safe_project + '_inc_dst        ${proj_inc_dst}' )
            self.process_line( 'default $' + safe_project + '_src_dst        ${proj_src_dst}' )
            self.process_line( 'default $' + safe_project + '_code_dst       ${proj_code_dst}' )
            self.process_line( 'default $' + safe_project + '_test_inc_dst   ${proj_test_inc_dst}' )
            self.process_line( 'default $' + safe_project + '_test_src_dst   ${proj_test_src_dst}' )
            self.process_line( 'default $' + safe_project + '_test_code_dst  ${proj_test_code_dst}' )
            self.process_line( 'default $' + safe_project + '_build_dst      ${proj_build_dst}' )
            self.process_line( 'default $' + safe_project + '_lib_dst        ${proj_lib_dst}' )
            self.process_line( 'default $' + safe_project + '_bin_dst        ${proj_bin_dst}' )
            self.process_line( 'default $' + safe_project + '_scripts_dst    ${proj_scripts_dst}' )

            lc_safe_project = safe_project.lower()
            if lc_safe_project != safe_project:
                self.process_line( 'default $' + lc_safe_project + '_inc_dst        ${inc_dst}${lcproject}/' )
                self.process_line( 'default $' + lc_safe_project + '_src_dst        ${src_dst}${lcproject}/' )
                self.process_line( 'default $' + lc_safe_project + '_code_dst       ${code_dst}${lcproject}/' )
                self.process_line( 'default $' + lc_safe_project + '_test_inc_dst   ${test_inc_dst}${lcproject}/' )
                self.process_line( 'default $' + lc_safe_project + '_test_src_dst   ${test_src_dst}${lcproject}/' )
                self.process_line( 'default $' + lc_safe_project + '_test_code_dst  ${test_code_dst}${lcproject}/' )
                self.process_line( 'default $' + lc_safe_project + '_build_dst      ${build_dst}${lcproject}/' )
                self.process_line( 'default $' + lc_safe_project + '_lib_dst        ${lib_dst}${lcproject}/' )
                self.process_line( 'default $' + lc_safe_project + '_bin_dst        ${bin_dst}${lcproject}/' )
                self.process_line( 'default $' + lc_safe_project + '_scripts_dst    ${scripts_dst}${lcproject}/' )

            return True
        return False

    def consider_dest( self, command, arguments ):
        if command == 'dest':
            self.default_dest = arguments
            return True
        return False

    def consider_get( self, command, arguments ):
        if (command == 'get' or command == 'copy') and arguments != None:
            src, dest_spec = split_in_2( arguments )    # dest_spec maybe = None
            self.retrieve_text_file( src, dest_spec )
            return True
        return False

    def consider_bget( self, command, arguments ):
        if (command == 'bget' or command == 'bcopy') and arguments != None:
            src, dest_spec = split_in_2( arguments )    # dest_spec maybe = None
            self.retrieve_binary_file( src, dest_spec )
            return True
        return False

    def retrieve_text_file( self, src, dst ):
        self.retrieve_file( src, dst, TextDownloadHandler() )

    def retrieve_binary_file( self, src, dst ):
        self.retrieve_file( src, dst, BinaryDownloadHandler() )

    def retrieve_file( self, src, dst, handler ):
        self.is_last_file_changed = False
        if dst == None:
            if self.default_dest != None:
                dst = self.default_dest
            else:
                if re.match( 'https?://', src ):
                    self.error( "Explicit uri not supported with commands of the form 'get src_and_dst'" )
                    return
                dst = src
                if self.uritemplate.find( '${path}' ) >= 0:
                    dst = self.vars['path'] + dst   # If present in the uri template, the ${path} variable will be included in the uri, so include it in the dst for symmetry
        from_uri = self.make_uri( src )
        to_file = self.make_destination_file_name( src, dst )
        if from_uri == '':
            self.error( "Unable to evaluate source of: " + src )
            return
        if to_file == '':
            self.error( "Unable to evaluate destination of: " + dst )
            return
        if self.is_file_already_downloaded( from_uri, to_file ):
            print( 'Repeat....', to_file )
            return
        if re.match( 'https?://', from_uri ):
            tmp_name = handler.download_to_temp_file( from_uri )
        else:
            tmp_name = self.local_copy_to_temp_file( from_uri )     # Taking a local copy is not optimal, but keeps the subsequent update logic the same
        if not tmp_name:
            self.error( "Unable to retrieve: " + from_uri )
            return
        self.conditionally_update_dst_file( tmp_name, to_file )

    processed_downloads = {}

    def is_file_already_downloaded( self, src, dst ):
        key = src + "\n" + dst
        if os.path.isfile( dst ) and key in ProcessDeps.processed_downloads:    # Allow for file being deleted between downloads for some reason
            return True
        ProcessDeps.processed_downloads[key] = True
        return False

    def conditionally_update_dst_file( self, tmp_name, to_file ):
        if not os.path.isfile( to_file ):
            if os.path.dirname( to_file ):
                os.makedirs( os.path.dirname( to_file ), exist_ok=True )
            shutil.move( tmp_name, to_file )
            self.is_last_file_changed = self.are_files_changed = ProcessDeps.are_any_files_changed = True
            print( 'Created...', to_file )
        elif not filecmp.cmp( tmp_name, to_file ):
            shutil.move( tmp_name, to_file )
            self.is_last_file_changed = self.are_files_changed = ProcessDeps.are_any_files_changed = True
            print( 'Updated...', to_file )
        else:
            os.unlink( tmp_name )
            print( 'Same......', to_file )

    def make_master_strand_uri( self, file_name ):
        # Override ${master} and ${path} variable
        uri = re.compile( '\$\{strand\}' ).sub( 'master', self.uritemplate )
        uri = re.compile( '\$\{path\}' ).sub( '', uri )
        return self.make_uri( file_name, uri )

    def make_uri( self, file_name, uri = None ):
        if re.match( 'https?://', file_name ):
            return self.expand_variables( file_name )
        if uri == None:
            uri = self.uritemplate
        uri = re.compile( '\$\{file\}' ).sub( file_name, uri )
        return self.expand_variables( uri )

    def make_destination_file_name( self, src, dst ):
        # dst in a get command may refer to a folder, in which case the base file name from the src needs to be incorporated
        dst = self.expand_variables( dst )
        if dst.endswith( '/' ) or os.path.isdir( dst ):
            if not dst.endswith( '/' ):
                dst = dst + '/'
            return dst + os.path.basename( src )
        return dst

    def expand_variables( self, uri ):
        while( True ):
            m = re.search( '\$\{(\w+)\}', uri )
            if m == None:
                return uri
            var_name = m.group(1)
            if var_name == 'strand':        # The strand variable has 'magic' properties (it can be mutated by a versions file) so we need to do something special with it
                uri = re.compile( '\$\{strand\}' ).sub( self.select_strand(), uri )
            elif var_name in self.vars:
                uri = re.compile( '\$\{' + var_name + '\}' ).sub( self.vars[var_name], uri )
            else:
                self.error( "Unrecognised substitution variable: " + var_name )
                return ''

    def select_strand( self ):
        if 'strand' not in self.vars:
            self.error( "No suitable 'strand' variable available for substitution" )
            return ''
        strand = self.vars['strand']
        for supported_strands in self.versions:
            if strand in supported_strands.split():
                return self.versions[supported_strands]
        return self.vars['strand']

    def local_copy_to_temp_file( self, file ):
        try:
            with open( file, 'rb' ) as fin:
                fout = tempfile.NamedTemporaryFile( mode='wb', delete=False )
                while True:
                    data = fin.read( 1000 )
                    if not data:
                        break
                    fout.write( data )
                fout.close()
                return fout.name
            return ''
        except FileNotFoundError:
            return ''

    def consider_subst( self, command, arguments ):
        if command == 'subst' and arguments != None:
            src, dst = split_in_2( arguments )    # dst maybe = None
            if dst == None:
                dst = src
            try:
                with open( src, 'rt', encoding='utf-8' ) as fin:
                    fout = tempfile.NamedTemporaryFile( mode='wt', delete=False, encoding='utf-8' )
                    for line in fin:
                        fout.write( self.subst_expand_variables( line ) )
                    fout.close()
                    self.conditionally_update_dst_file( fout.name, dst )
            except FileNotFoundError:
                self.error( "Unable to open file for 'subst' command: " + src )
            return True
        return False

    def subst_expand_variables( self, line ):
        while( True ):
            m = re.search( '\$\{exodep:(\w+)\}', line )
            if m == None:
                return line
            var_name = m.group(1)
            if var_name == 'strand':        # The strand variable has 'magic' properties (it can be mutated by a versions file) so we need to do something special with it
                line = re.compile( '\$\{strand\}' ).sub( self.select_strand(), line )
            elif var_name in self.vars:
                line = re.compile( '\$\{exodep:' + var_name + '\}' ).sub( self.vars[var_name], line )
            else:
                self.error( "Unrecognised variable in 'subst' command: " + var_name )
                return line

    def consider_file_ops( self, command, arguments ):
        if (command == 'cp' or command == 'mv') and arguments != None:
            src_spec, dst_spec = split_in_2( arguments )    # dst_spec maybe = None
            if dst_spec == None:
                return False
            op = command
            src = self.expand_variables( src_spec )
            dst = self.make_destination_file_name( src, dst_spec )
            if op == 'cp':
                try:
                    if self.is_copy_needed( src, dst ):
                        shutil.copy( src, dst )
                        print( 'cp........', dst )
                except:
                    self.error( "Unable to 'cp' file '" + src + "' to '" + dst + "'" )
            elif op == 'mv':
                try:
                    shutil.move( src, dst )
                    print( 'mv........', dst )
                except:
                    self.error( "Unable to 'mv' file '" + src + "' to '" + dst + "'" )
            return True

        if (command == 'mkdir' or command == 'rmdir' or command == 'rm') and arguments != None:
            op = command
            path = self.expand_variables( arguments )
            if op == 'mkdir':
                try:
                    os.makedirs( path, exist_ok=True )
                    print( 'mkdir.....', path )
                except:
                    self.error( "Unable to 'mkdir' for '" + path + "'" )
            elif op == 'rmdir':
                try:
                    shutil.rmtree( path )
                    print( 'rmdir.....', path )
                except:
                    self.error( "Unable to 'rmdir' on '" + path + "'" )
            elif op == 'rm':
                try:
                    os.unlink( path )
                    print( 'rm........', path )
                except:
                    self.error( "Unable to 'rm' file '" + path + "'" )
            return True

        if command == 'touch' and arguments != None:
            op = command
            file = self.expand_variables( arguments )
            open( file, 'a' ).close()
            return True
        return False

    def is_copy_needed( self, src, dst ):
        return not os.path.isfile( dst ) or not filecmp.cmp( src, dst )

    def consider_exec( self, command, arguments ):
        if command == 'exec' and arguments != None:
            cmd = arguments
            org_cwd = os.getcwd()
            file_dirname = os.path.dirname( self.file )
            if file_dirname:
                os.chdir( file_dirname )
            os.system( self.expand_variables( cmd ) )
            os.chdir( org_cwd )
            return True
        return False

    def consider_on_conditional( self, command, arguments ):
        if command == 'on' and arguments != None and arguments[0] == '$':
            var, instruction = split_in_2( arguments )
            var_name = var[1:]
            if instruction == None:
                return False
            if self.is_sought_condition( \
                    var_name in self.vars and \
                    self.vars[var_name] != '' and \
                    self.vars[var_name] != '0' and \
                    self.vars[var_name].lower() != 'false' ):
                self.process_line( instruction )
            return True
        return False

    def consider_ondir( self, command, arguments ):
        if command == 'ondir' and arguments != None:
            dir, instruction = split_in_2( arguments )
            if instruction == None:
                return False
            if self.is_sought_condition( os.path.isdir( dir ) ):
                self.process_line( instruction )
            return True
        return False

    def consider_onfile( self, command, arguments ):
        if command == 'onfile' and arguments != None:
            file, instruction = split_in_2( arguments )
            if instruction == None:
                return False
            if self.is_sought_condition( os.path.isfile( file ) ):
                self.process_line( instruction )
            return True
        return False

    def consider_onlastchanged( self, command, arguments ):
        if command == 'onlastchanged' and arguments != None:
            instruction = arguments
            if self.is_sought_condition( self.is_last_file_changed ):
                self.process_line( instruction )
            return True
        return False

    def consider_onchanged( self, command, arguments ):
        if command == 'onchanged' and arguments != None:
            instruction = arguments
            if self.is_sought_condition( self.are_files_changed ):
                self.process_line( instruction )
            return True
        return False

    def consider_onanychanged( self, command, arguments ):
        if command == 'onanychanged' and arguments != None:
            instruction = arguments
            if self.is_sought_condition( ProcessDeps.are_any_files_changed ):
                self.process_line( instruction )
            return True
        return False

    def consider_onalerts( self, command, arguments ):
        if command == 'onalerts' and arguments != None:
            instruction = arguments
            if self.is_sought_condition( ProcessDeps.shown_alert_messages != "" or ProcessDeps.alert_messages != "" ):
                self.process_line( instruction )
            return True
        return False

    os_names = { 'windows': 'win32', 'linux': 'linux', 'osx': 'darwin' }

    def consider_os_conditional( self, command, arguments ):
        if (command == 'windows' or command == 'linux' or command == 'osx') and arguments != None:
            os_key = command
            instruction = arguments
            if self.is_sought_condition( sys.platform.startswith( ProcessDeps.os_names[os_key] ) ):
                self.process_line( instruction )
            return True
        return False

    def consider_not( self, command, arguments ):
        if command == 'not' and arguments != None:
            instruction = arguments
            self.sought_condition = not self.sought_condition
            self.process_line( instruction )
            return True
        return False

    def is_sought_condition( self, condition ):
        my_sought_condition = self.sought_condition
        self.sought_condition = True    # Reset sought_condition so it doesn't affect conditions later in the same command line
        if condition:
            return my_sought_condition
        return not my_sought_condition

    def consider_echo( self, command, arguments ):
        if command == 'echo':
            message = arguments
            if message:
                print( self.expand_variables( message ) )
            else:
                print( "" )
            return True
        return False

    def consider_pause( self, command, arguments ):
        if command == 'pause':
            message = arguments
            if message:
                message = self.expand_variables( message )
            pause( message )
            return True
        return False

    def consider_alert( self, command, arguments ):
        if command == 'alert' and arguments != None:
            message = self.expand_variables( arguments )
            alert = "ALERT: " + self.file + " (" + str(self.line_num) + "):\n" + "       " + message
            print( alert )
            if ProcessDeps.alert_messages != "":
                ProcessDeps.alert_messages += "\n"
            ProcessDeps.alert_messages += alert
            return True
        return False

    def consider_showalerts( self, command, arguments ):
        if command == 'showalerts':
            if ProcessDeps.alert_messages != "":
                print( "RECORDED ALERTS:" )
                print( ProcessDeps.alert_messages )
                if ProcessDeps.shown_alert_messages != "":
                    ProcessDeps.shown_alert_messages += "\n"
                ProcessDeps.shown_alert_messages = ProcessDeps.alert_messages
                ProcessDeps.alert_messages = ""
            return True
        return False

    def consider_alertstofile( self, command, arguments ):
        if command == 'alertstofile' and arguments != None:
            file = arguments
            if os.path.isfile( file ):
                shutil.move( file, file + ".old" )
            if ProcessDeps.shown_alert_messages != "" or ProcessDeps.alert_messages != "":
                with open( file, 'w') as fout:
                    if ProcessDeps.shown_alert_messages != "":
                        fout.write( ProcessDeps.shown_alert_messages + "\n" )
                    if ProcessDeps.alert_messages != "":
                        fout.write( ProcessDeps.alert_messages + "\n" )
            return True
        return False

    def consider_stop( self, command, arguments ):
        if command == 'stop':
            message = arguments # May be None
            print( "STOPPED: " + self.file + " (" + str(self.line_num) + "):" )
            if message:
                print( "      " + self.expand_variables( message ) )
            if self.file != onstop_exodep and os.path.isfile( onstop_exodep ):
                ProcessDeps( onstop_exodep, self.vars )
            raise StopException
        return False

    def report_unrecognised_command( self, line ):
        self.error( "Unrecognised command: " + line )

    def error( self, what ):
        print( "Error:", self.file + ", line " + str(self.line_num) + ":" )
        print( "      ", what )

def remove_comments( line ):
    return line.split( '#', 1 )[0].rstrip()

def is_blank_line( line ):
    return line.strip() == ''

def split_in_2( text ):
    parts = text.split( maxsplit=1 )
    if( len(parts) == 1 ):
        return [ parts[0], None ]
    return parts

def pause( message = None ):
    print( "" )
    if message:
        print( message )
    print( ">>> Press <Return> to continue <<<" )
    input()

def text_filecmp( file1, file2 ):
    try:
        with open( file1 ) as f1, open( file2 ) as f2:
            for line in f1:
                if( line.rstrip() != f2.readline().rstrip() ):
                    return False
            for line in f2:   # Check no more data available
                return False
        return True
    except IOError:
        return False

class TextDownloadHandler:
    def download_to_temp_file( self, uri ):
        try:
            with urllib.request.urlopen( uri ) as fin:
                fout = tempfile.NamedTemporaryFile( mode='wt', delete=False, encoding='utf-8' )
                for line in fin:
                    fout.write( self.normalise_line_ending( line.decode('utf-8') ) )
                fout.close()
                return fout.name
            return ''
        except urllib.error.URLError:
            return ''

    def normalise_line_ending( self, line ):
        org_len = len( line )
        line = line.rstrip( '\r\n' )
        if org_len > len( line ):
            line = line + '\n'
        return line

class BinaryDownloadHandler:
    def download_to_temp_file( self, uri ):
        try:
            with urllib.request.urlopen( uri ) as fin:
                fout = tempfile.NamedTemporaryFile( mode='wb', delete=False )
                while True:
                    data = fin.read( 1000 )
                    if not data:
                        break
                    fout.write( data )
                fout.close()
                return fout.name
            return ''
        except urllib.error.URLError:
            return ''

if __name__ == "__main__":
    main()
