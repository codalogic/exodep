#!/usr/bin/python

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

import sys
import re
import io
import os
import urllib.request
import tempfile
import shutil
import filecmp

def main() :
    ProcessDeps( sys.argv[1] if len( sys.argv ) >= 2 else "mydeps.exodep" )

class ProcessDeps:
    def __init__( self, dependencies_src, vars = { 'strand' : 'master' } ):
        self.uritemplate = 'https://raw.githubusercontent.com/${user}/${project}/${strand}/${file}'
        self.vars = vars.copy()
        self.versions = {}  # Each entry is <string of space separated strand names> : <string to use as strand in uri template>
        if isinstance( dependencies_src, str ):
            self.file = dependencies_src
            self.process_dependency_file()
        elif isinstance( dependencies_src, io.StringIO ):    # Primarily for testing
            self.file = "<StringIO>"
            self.process_dependency_stream( dependencies_src )
        else:
            print( "Error: Unrecognised dependencies_src type format" )

    def process_dependency_file( self ):
        try:
            with open(self.file) as f:
                self.process_dependency_stream( f )
        except FileNotFoundError:
            print( "Error: Unable to open exodep file:", self.file )

    def process_dependency_stream( self, f ):
        for line in f:
            self.process_line( line )

    def process_line( self, line ):
        line = line.rstrip()
        line = remove_comments( line )
        if is_blank_line( line ):
            return
        if not (self.consider_include( line ) or
                self.consider_hosting( line ) or
                self.consider_uri_template( line ) or
                self.consider_versions( line ) or
                self.consider_variable( line ) or
                self.consider_default_variable( line ) or
                self.consider_copy( line ) or
                self.consider_bcopy( line ) ):
            self.report_unrecognised_command( line )

    def consider_include( self, line ):
        m = re.match( 'include\s+(.*)', line )
        if m != None and m.group(1) != '':
            ProcessDeps( m.group(1), self.vars )
            return True
        return False

    def consider_hosting( self, line ):
        m = re.match( 'hosting\s+(.*)', line )
        if m != None and m.group(1) != '':
            remote = m.group(1)
            if remote == 'github':
                self.uritemplate = 'https://raw.githubusercontent.com/${user}/${project}/${strand}/${file}'
            elif remote == 'bitbucket':
                self.uritemplate = 'https://bitbucket.org/${user}/${project}/raw/${strand}/${file}'
            else:
                print( "Error: Unrecognised remote server provider:", remote )
            return True
        return False

    def consider_uri_template( self, line ):
        m = re.match( 'uritemplate\s+(.*)', line )
        if m != None:
            self.uritemplate = m.group(1)
            return True
        return False

    def consider_versions( self, line ):
        m = re.match( 'versions\s+(.*)', line )
        if m != None:
            # TODO
            return True
        return False

    def consider_variable( self, line ):
        m = re.match( '\$(\w+)\s+(.*)', line )
        if m != None:
            self.vars[m.group(1)] = m.group(2)
            return True
        return False

    def consider_default_variable( self, line ):
        m = re.match( 'default\s+\$(\w+)\s+(.*)', line )
        if m != None:
            if m.group(1) not in self.vars:
                self.vars[m.group(1)] = m.group(2)
            return True
        return False

    def consider_copy( self, line ):
        m = re.match( 'copy\s+(\S+)\s+(\S+)', line )
        if m != None:
            self.retrieve_text_file( m.group(1), m.group(2) )
            return True
        m = re.match( 'copy\s+(\S+)', line )
        if m != None:
            src_and_dst = m.group(1)
            if re.match( 'http:s?//', src_and_dst ):
                print( "Error: Explicit uri not supported with commands of the form 'copy src_and_dst'" )
                return True    # Even though we haven't executed the command, we do know what it is
            self.retrieve_text_file( src_and_dst, src_and_dst )
            return True
        return False

    def consider_bcopy( self, line ):
        m = re.match( 'bcopy\s+(\S+)\s+(\S+)', line )
        if m != None:
            self.retrieve_binary_file( m.group(1), m.group(2) )
            return True
        m = re.match( 'bcopy\s+(\S+)', line )
        if m != None:
            src_and_dst = m.group(1)
            if re.match( 'http:s?//', src_and_dst ):
                print( "Error: Explicit uri not supported with commands of the form 'bcopy src_and_dst'" )
                return True    # Even though we haven't executed the command, we do know what it is
            self.retrieve_binary_file( src_and_dst, src_and_dst )
            return True
        return False

    def report_unrecognised_command( self, line ):
        print( "Error: Unrecognised command:", line )

    def retrieve_text_file( self, src, dst ):
        self.retrieve_file( src, dst, TextDownloadHandler() )

    def retrieve_binary_file( self, src, dst ):
        self.retrieve_file( src, dst, BinaryDownloadHandler() )

    def retrieve_file( self, src, dst, handler ):
        from_uri = self.make_uri( src )
        to_file = self.make_destination_file_name( src, dst )
        if from_uri == '' or to_file == '':
            return
        tmp_name = handler.download_to_temp_file( from_uri )
        self.conditionally_update_dst_file( tmp_name, to_file )

    def conditionally_update_dst_file( self, tmp_name, to_file ):
        if not os.path.isfile( to_file ):
            if os.path.dirname( to_file ):
                os.makedirs( os.path.dirname( to_file ), exist_ok=True )
            shutil.move( tmp_name, to_file )
            print( 'Created...', to_file )
        elif not filecmp.cmp( tmp_name, to_file ):
            shutil.move( tmp_name, to_file )
            print( 'Updated...', to_file )
        else:
            os.unlink( tmp_name )
            print( 'Same......', to_file )

    def make_master_strand_uri( self, file_name ):
        uri = re.compile( '\$\{strand\}' ).sub( 'master', self.uritemplate )
        return self.make_uri( file_name, uri )

    def make_uri( self, file_name, uri = None ):
        m = re.match( 'https?://', file_name )
        if m != None:
            return self.expand_variables( file_name )
        if uri == None:
            uri = self.uritemplate
        uri = re.compile( '\$\{file\}' ).sub( file_name, uri )
        return self.expand_variables( uri )

    def make_destination_file_name( self, src, dst ):
        # dst in a copy command may refer to a folder, in which case the base file name from the src needs to be incorporated
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
                print( "Error: Unrecognised substitution variable:", var_name )
                return ''

    def select_strand( self ):
        if 'strand' not in self.vars:
            print( "Error: No suitable 'strand' variable available for substitution" )
            return ''
        strand = self.vars['strand']
        for supported_strands in self.versions:
            if strand in supported_strands.split():
                return self.versions[supported_strands]
        return self.vars['strand']

def remove_comments( line ):
    return re.compile( '\s*#.*' ).sub( '', line )

def is_blank_line( line ):
    return re.match( '^\s*$', line )

class TextDownloadHandler:
    def download_to_temp_file( self, uri ):
        try:
            fout = None
            with urllib.request.urlopen( uri ) as fin:
                fout = tempfile.NamedTemporaryFile( mode='wt', delete=False)
                for line in fin:
                    fout.write( line.decode('utf-8').rstrip() + "\n" )  # Fix up to local line ending format
            fout.close()
            return fout.name
        except urllib.error.URLError:
            return ''

class BinaryDownloadHandler:
    def download_to_temp_file( self, uri ):
        try:
            fout = None
            with urllib.request.urlopen( uri ) as fin:
                fout = tempfile.NamedTemporaryFile( mode='wb', delete=False)
                while True:
                    data = fin.read( 10 )
                    if not data:
                        break
                    fout.write( data )
            fout.close()
            return fout.name
        except urllib.error.URLError:
            return ''

if __name__ == "__main__":
    main()
