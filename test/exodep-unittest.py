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

import sys
import io
import os
import unittest
import shutil
import filecmp

sys.path.append("..")
import exodep

exodep_exe = '../exodep.py '
if sys.platform.startswith( 'win32' ):
    exodep_exe = '..\\exodep.py '

def main():
    pre_clean()
    unittest.main()

def pre_clean():
    rmdir( 'download' )
    rmdir( 'file-ops-test-dir' )
    rmdir( 'dir1' )
    rm( 'file1.txt' )
    rmdir( 'stop' )
    rmdir( 'exodep-imports' )
    rmdir( 'dest-dir' )

class MyTest(unittest.TestCase):
    def test_default_setup(self):
        pd = make_ProcessDeps( "" )
        self.assertEqual( len( pd.vars ), 2 )
        self.assertTrue( 'strand' in pd.vars )
        self.assertEqual( pd.vars['strand'], 'master' )
        self.assertTrue( 'path' in pd.vars )
        self.assertEqual( pd.vars['path'], '' )
        self.assertEqual( pd.uritemplate, 'https://raw.githubusercontent.com/${owner}/${project}/${strand}/${path}${file}' )

    def test_set_uritemplate(self):
        pd = make_ProcessDeps( "uritemplate htpp://fiddle.com/${file}" )
        self.assertEqual( pd.uritemplate, 'htpp://fiddle.com/${file}' )

    def test_set_hosting_bitbucket(self):
        pd = make_ProcessDeps( "hosting bitbucket" )
        self.assertEqual( pd.uritemplate, 'https://bitbucket.org/${owner}/${project}/raw/${strand}/${path}${file}' )

    def test_set_hosting_github(self):
        pd = make_ProcessDeps( "uritemplate htpp://fiddle.com/${file}\nhosting github" )
        self.assertEqual( pd.uritemplate, 'https://raw.githubusercontent.com/${owner}/${project}/${strand}/${path}${file}' )

    def test_set_hosting_gitlab(self):
        pd = make_ProcessDeps( "hosting gitlab" )
        self.assertEqual( pd.uritemplate, 'https://gitlab.com/${owner}/${project}/raw/${strand}/${path}${file}' )

    def test_set_single_var(self):
        pd = make_ProcessDeps( "$space Mumble" )
        self.assertEqual( len( pd.vars ), 3 )
        self.assertTrue( 'strand' in pd.vars )
        self.assertEqual( pd.vars['strand'], 'master' )
        self.assertTrue( 'path' in pd.vars )
        self.assertEqual( pd.vars['path'], '' )
        self.assertTrue( 'space' in pd.vars )
        self.assertEqual( pd.vars['space'], 'Mumble' )

    def test_set_multiple_vars(self):
        pd = make_ProcessDeps( "$plant rose\n$animal sheep" )
        self.assertEqual( len( pd.vars ), 4 )
        self.assertTrue( 'strand' in pd.vars )
        self.assertEqual( pd.vars['strand'], 'master' )
        self.assertTrue( 'path' in pd.vars )
        self.assertEqual( pd.vars['path'], '' )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], 'rose' )
        self.assertTrue( 'animal' in pd.vars )
        self.assertEqual( pd.vars['animal'], 'sheep' )

    def test_set_empty_vars_1(self):
        pd = make_ProcessDeps( "$plant\n$animal sheep" )
        self.assertEqual( len( pd.vars ), 4 )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], '' )
        self.assertTrue( 'animal' in pd.vars )
        self.assertEqual( pd.vars['animal'], 'sheep' )

    def test_set_empty_vars_2(self):
        pd = make_ProcessDeps( "$plant \n$animal sheep" )
        self.assertEqual( len( pd.vars ), 4 )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], '' )
        self.assertTrue( 'animal' in pd.vars )
        self.assertEqual( pd.vars['animal'], 'sheep' )

    def test_set_default_vars_1(self):
        pd = make_ProcessDeps( "default $plant tulip" )
        self.assertEqual( len( pd.vars ), 3 )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], 'tulip' )

    def test_set_default_vars_2(self):
        pd = make_ProcessDeps( "$plant rose\ndefault $plant tulip" )
        self.assertEqual( len( pd.vars ), 3 )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], 'rose' )

    def test_set_default_empty_vars_1(self):
        pd = make_ProcessDeps( "default $plant" )
        self.assertEqual( len( pd.vars ), 3 )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], '' )

    def test_set_default_empty_vars_2(self):
        pd = make_ProcessDeps( "$plant rose\ndefault $plant" )
        self.assertEqual( len( pd.vars ), 3 )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], 'rose' )

    def test_showvars(self):
        pd = make_ProcessDeps( "$plant rose\n$animal sheep\n$plant_animal ${plant} ${animal}\nshowvars" )

    def test_uri_formation(self):
        pd = make_ProcessDeps( "$owner marvin\n$strand apple\n$project exodep\n$path bin/" )

        formed_uri = pd.make_uri( 'data.dat' )
        self.assertEqual( formed_uri, 'https://raw.githubusercontent.com/marvin/exodep/apple/bin/data.dat' )

        pd.versions = { 'apple banana' : 'zen', 'carrot date' : 'yuka' }
        formed_uri = pd.make_uri( 'data.dat' )
        self.assertEqual( formed_uri, 'https://raw.githubusercontent.com/marvin/exodep/zen/bin/data.dat' )

        formed_uri = pd.make_master_strand_uri( 'versions.exodep' )
        self.assertEqual( formed_uri, 'https://raw.githubusercontent.com/marvin/exodep/master/versions.exodep' )

    def test_dest_file_name_formation(self):
        pd = make_ProcessDeps( "$cpp exodep/cpp\n$h exodep/h/" )

        formed_name = pd.make_destination_file_name( 'data.dat', '${cpp}/file.dat' )
        self.assertEqual( formed_name, 'exodep/cpp/file.dat' )

        formed_name = pd.make_destination_file_name( 'data.dat', '${cpp}/' )
        self.assertEqual( formed_name, 'exodep/cpp/data.dat' )

        formed_name = pd.make_destination_file_name( 'base/data.dat', '${cpp}/' )
        self.assertEqual( formed_name, 'exodep/cpp/data.dat' )

        formed_name = pd.make_destination_file_name( 'base/data.dat', '${h}' )
        self.assertEqual( formed_name, 'exodep/h/data.dat' )

        fake_dir = 'flubber_temp'
        if not os.path.isdir( fake_dir ):
            os.mkdir( fake_dir )

        formed_name = pd.make_destination_file_name( 'data.dat', fake_dir )
        self.assertEqual( formed_name, fake_dir + '/data.dat' )

        formed_name = pd.make_destination_file_name( 'base/data.dat', fake_dir )
        self.assertEqual( formed_name, fake_dir + '/data.dat' )

        os.rmdir( fake_dir )

    def test_globbing(self):
        rm( 'glob-test-1.txt' )
        rm( 'glob-test-2.txt' )
        ensure_dir( 'exodep-imports' )
        ensure_dir( 'exodep-imports/child' )
        to_file( 'exodep-imports/glob-test-1.exodep',
                'touch glob-test-1.txt\n' )
        to_file( 'exodep-imports/child/glob-test-2.exodep',
                'touch glob-test-2.txt\n' )
        os.system( exodep_exe )
        self.assertTrue( os.path.isfile( 'glob-test-1.txt' ) )
        self.assertTrue( os.path.isfile( 'glob-test-2.txt' ) )

    def test_download(self):
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n" +
                            "get dl-test-target.txt download/" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target.txt' ) )
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n" +
                            "get dl-test-target.txt download/dl-test-target1.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target1.txt' ) )
        make_ProcessDeps( "get https://raw.githubusercontent.com/codalogic/exodep/master/test/dl-test-target.txt download/dl-test-target2.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target2.txt' ) )

        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n" +
                            "get dl-test-target-other.txt download/" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target.txt' ) )   # Check file of different name doesn't overwrite existing one
        self.assertTrue( filecmp.cmp( 'dl-test-target-other.txt', 'download/dl-test-target-other.txt' ) )

        make_ProcessDeps( "copy https://raw.githubusercontent.com/codalogic/exodep/master/test/dl-test-target-other.txt download/dl-test-target3.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target-other.txt', 'download/dl-test-target3.txt' ) )    # Check download of different file updates an existing one

    def test_download_copy_with_only_one_arg_without_dest_command(self):
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "get file1.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-file1-reference.txt', 'file1.txt' ) )

        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "get dir1/file2.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dir1/file2.txt' ) )

        rm( 'dir1/file2.txt' )
        make_ProcessDeps( "$path nothing\n" +       # $path should be ignored because it's not in the uritemplate
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "get dir1/file2.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dir1/file2.txt' ) )

        rm( 'dir1/file2.txt' )
        make_ProcessDeps( "$path dir1/\n" +
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${path}${file}\n" +
                            "get file2.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dir1/file2.txt' ) )

    def test_download_copy_with_dest_command(self):
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "$dest_dir dest-dir/\n" +
                            "dest ${dest_dir}\n" +
                            "get dir1/file2.txt\n" +
                            "dest\n" +  # Reset dest
                            "get file1.txt\n" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dest-dir/file2.txt' ) )
        self.assertTrue( not os.path.isfile( 'dest-dir/file1.txt' ) )   # Should have been put elsewhere

    def test_download_repeat(self):
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n" +
                            "get dl-test-target.txt download/dl-test-target-repeat.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target-repeat.txt' ) )
        shutil.copy( 'dl-test-target-other.txt', 'download/dl-test-target-repeat.txt' )    # Change the file so we can detect whether it has been re-downloaded
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n" +
                            "get dl-test-target.txt download/dl-test-target-repeat.txt" )
        self.assertTrue( not filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target-repeat.txt' ) )

    def test_bcopy(self):
        make_ProcessDeps( "bget https://raw.githubusercontent.com/codalogic/exodep/master/test/dl-test-target.txt download/bcopy-file.txt" )
        self.assertTrue( os.path.isfile( 'download/bcopy-file.txt' ) )

        make_ProcessDeps( "bget https://raw.githubusercontent.com/codalogic/exodep/master/test/dl-test-target.txt download/bget-file.txt" )
        self.assertTrue( os.path.isfile( 'download/bget-file.txt' ) )

    def test_local_file_copying(self):
        make_ProcessDeps( "uritemplate ./${file}\ncopy dl-test-target.txt download/dl-test-target4.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target4.txt' ) )

    def test_versions(self):
        pd = make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/${strand}/${file}\nversions versions.exodep" )
        self.assertTrue( 'apple alto' in pd.versions )
        self.assertTrue( pd.versions['apple alto'] == 'master'  )
        self.assertTrue( 'apple alto' in pd.versions )
        self.assertTrue( pd.versions['first'] == 'd57a45c6737'  )

        pd = make_ProcessDeps( "uritemplate ./${file}\nversions versions-for-local-test.exodep" )
        self.assertTrue( 'apple alto' in pd.versions )
        self.assertTrue( pd.versions['apple alto'] == 'apple'  )
        self.assertTrue( 'apple alto' in pd.versions )
        self.assertTrue( pd.versions['banana'] == 'master'  )

        make_ProcessDeps( "$strand alto\n" +
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep/${strand}/${file}\n" +
                            "versions versions.exodep\n" +
                            "get test/dl-test-target.txt download/dl-test-target11.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target11.txt' ) )

        make_ProcessDeps( "$strand alto\n" +
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep/${strand}/${file}\n" +
                            "versions\n" +  # Specify default versions
                            "get test/dl-test-target.txt download/dl-test-target12.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target12.txt' ) )

        make_ProcessDeps( "versions https://raw.githubusercontent.com/codalogic/exodep/master/versions.exodep\n" +
                            "$strand alto\n" +
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep/${strand}/${file}\n" +
                            "get test/dl-test-target.txt download/dl-test-target14.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target14.txt' ) )

    def test_include(self):
        pd = exodep.ProcessDeps( 'test-include.exodep' )
        self.assertTrue( 'name' in pd.vars )
        self.assertEqual( pd.vars['name'], 'done' )

        pd = exodep.ProcessDeps( 'test-loop.exodep' )
        # If this test doesn't result in an infinite loop, then it's passed!

    def test_include_path_computation(self):
        pd = make_ProcessDeps( "" )
        pd.file = ''
        pd.file = pd.script_relative_path( 'exodep.exodep' )
        self.assertEqual( pd.file, 'exodep.exodep' )

        pd.file = pd.script_relative_path( 'exodep2.exodep' )
        self.assertEqual( pd.file, 'exodep2.exodep' )

        pd.file = pd.script_relative_path( 'dir1/exodep3.exodep' )
        self.assertEqual( pd.file, 'dir1/exodep3.exodep' )

        # A config in 'dir1' calling 'exodep4.exodep' still needs to look in 'dir1'
        pd.file = pd.script_relative_path( 'exodep4.exodep' )
        self.assertEqual( pd.file, 'dir1/exodep4.exodep' )

        pd.file = pd.script_relative_path( '../exodep5.exodep' )
        self.assertEqual( pd.file, 'exodep5.exodep' )

        pd.file = pd.script_relative_path( 'dir2/exodep6.exodep' )
        self.assertEqual( pd.file, 'dir2/exodep6.exodep' )

        pd.file = pd.script_relative_path( '../dir3/exodep7.exodep' )
        self.assertEqual( pd.file, 'dir3/exodep7.exodep' )

    def test_subst(self):
        pd = make_ProcessDeps( '$val v1\n$param p2\nsubst subst-input.txt download/subst-output.txt' )
        self.assertTrue( filecmp.cmp( 'subst-expected-result.txt', 'download/subst-output.txt' ) )

        # Single arg form
        shutil.copy( 'subst-input.txt', 'download/subst-copy.txt' )
        pd = make_ProcessDeps( '$val v1\n$param p2\nsubst subst-input.txt download/subst-copy.txt' )
        self.assertTrue( filecmp.cmp( 'subst-expected-result.txt', 'download/subst-copy.txt' ) )

    def test_onlastchanged_conditional(self):
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n" +
                                "get dl-test-target.txt download/onlastchanged_already_downloaded.txt\n" )
        pd = make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n" +
                                "get dl-test-target.txt download/onlastchanged_already_downloaded.txt\n" +
                                "onlastchanged $onlastchanged_already_should_not_set 1\n" +
                                "get dl-test-target.txt download/onlastchanged_should_be_written.txt\n" +
                                "onlastchanged $onlastchanged_original_should_set 1\n" +
                                "get dl-test-target-other.txt download/onlastchanged_should_be_written.txt\n" +
                                "onlastchanged $onlastchanged_other_should_set 1\n" +
                                "get dl-test-target-other.txt download/onlastchanged_should_be_written.txt\n" +     # Repeat download should not trigger onlastchanged
                                "onlastchanged $onlastchanged_repeat_should_not_set 1\n" )
        self.assertTrue( 'onlastchanged_already_should_not_set' not in pd.vars )
        self.assertTrue( 'onlastchanged_original_should_set' in pd.vars )
        self.assertTrue( 'onlastchanged_other_should_set' in pd.vars )
        self.assertTrue( 'onlastchanged_repeat_should_not_set' not in pd.vars )

    def test_onchanged_conditional(self):
        pd = make_ProcessDeps( 'sinclude ' +
                                        'uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\t' +
                                        'onchanged copy dl-test-target.txt download/onchanged_not_should_be_written.txt\t' +
                                        'copy dl-test-target.txt download/onchanged_file.txt\t' +
                                        'onchanged copy dl-test-target.txt download/onchanged_should_be_written.txt\t' +
                                        '\n' +
                                'onchanged $onchanged_should_not_store 1\n' +
                                'onanychanged $onanychanged_should_store 1\n' )
        self.assertTrue( not os.path.isfile( 'download/onchanged_not_should_be_written.txt' ) )
        self.assertTrue( os.path.isfile( 'download/onchanged_should_be_written.txt' ) )
        self.assertTrue( 'onchanged_should_not_store' not in pd.vars )
        self.assertTrue( 'onanychanged_should_store' in pd.vars )

    def test_on_conditional(self):
        pd = make_ProcessDeps( '$v v1\n$dll true\non $dll $v p2\non $other $v l3' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'p2' )

        pd = make_ProcessDeps( '$v v1\n$dll\non $dll $v p2' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'v1' )

        pd = make_ProcessDeps( '$v v1\n$dll \non $dll $v p2' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'v1' )

        pd = make_ProcessDeps( '$v v1\n$dll 0\non $dll $v p2' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'v1' )

        pd = make_ProcessDeps( '$v v1\n$dll false\non $dll $v p2' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'v1' )

        pd = make_ProcessDeps( '$v v1\n$dll False\non $dll $v p2' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'v1' )

        pd = make_ProcessDeps( '$v v1\n$dll FALSE\non $dll $v p2' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'v1' )

    def test_ondir(self):
        pd = make_ProcessDeps( '$v v1\nondir .. $v p2\nondir non-a-dir $v l3' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'p2' )

    def test_onfile(self):
        pd = make_ProcessDeps( '$v v1\nonfile dl-test-target.txt $v p2\nonfile non-a-file $v l3' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'p2' )

    def test_os_conditional(self):
        pd = make_ProcessDeps( '$v v1\nwindows $v p2\nlinux $v l3' )
        self.assertTrue( 'v' in pd.vars )
        if sys.platform.startswith( 'win32' ):
            self.assertEqual( pd.vars['v'], 'p2' )
        elif sys.platform.startswith( 'linux' ):
            self.assertEqual( pd.vars['v'], 'l3' )

    def test_file_ops(self):
        make_ProcessDeps( '$dir file-ops-test-dir\n' +
                            'mkdir ${dir}\n' )
        self.assertTrue( os.path.isdir( 'file-ops-test-dir' ) )

        make_ProcessDeps( '$src subst-input.txt\n' +
                            '$path file-ops-test-dir/\n' +
                            'cp ${src} ${path}' )
        self.assertTrue( os.path.isfile( 'file-ops-test-dir/subst-input.txt' ) )

        make_ProcessDeps( '$src subst-input.txt\n' +
                            '$path file-ops-test-dir/\n' +
                            'cp ${src} ${path}cp-file2.txt' )
        self.assertTrue( os.path.isfile( 'file-ops-test-dir/cp-file2.txt' ) )

        make_ProcessDeps( '$src subst-input.txt\n' +
                            '$path file-ops-test-dir/\n' +
                            'cp ${src} ${path}cp-file.txt\n' +
                            'mv ${path}cp-file.txt ${path}mv-file.txt' )
        self.assertTrue( os.path.isfile( 'file-ops-test-dir/mv-file.txt' ) )

        # touch test
        make_ProcessDeps( '$tfile touch-file.txt\n' +
                            'touch file-ops-test-dir/${tfile}\n' )
        self.assertTrue( os.path.isfile( 'file-ops-test-dir/touch-file.txt' ) )

        # rm test
        make_ProcessDeps( '$src subst-input.txt\n' +
                            '$path file-ops-test-dir/\n' +
                            'cp ${src} ${path}rm-file.txt' )
        self.assertTrue( os.path.isfile( 'file-ops-test-dir/rm-file.txt' ) )
        make_ProcessDeps( '$path file-ops-test-dir/\n' +
                            'rm ${path}rm-file.txt' )
        self.assertFalse( os.path.isfile( 'file-ops-test-dir/rm-file.txt' ) )

        make_ProcessDeps( '$dir file-ops-test-dir\n' +
                            'rmdir ${dir}\n' )
        self.assertTrue( not os.path.isdir( 'file-ops-test-dir' ) )

    def test_exec(self):
        # Avoid using DOS 'copy' in the test in case exodep copy gets invoked instead
        make_ProcessDeps( 'uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n' +
                            'copy dl-test-target.txt download/exec_file.txt\n' +
                            'windows exec rename download\exec_file.txt exec_renamed_file.txt\n' +
                            'linux exec mv download/exec_file.txt download/exec_renamed_file.txt' )
        self.assertTrue( os.path.isfile( 'download/exec_renamed_file.txt' ) )

        make_ProcessDeps( '$path download\n' +
                            'uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n' +
                            'copy dl-test-target.txt download/exec_file2.txt\n' +
                            'windows exec rename ${path}\exec_file2.txt exec_renamed_file2.txt\n' +
                            'linux exec mv ${path}/exec_file2.txt download/exec_renamed_file2.txt' )
        self.assertTrue( os.path.isfile( 'download/exec_renamed_file2.txt' ) )

    def test_alert(self):
        # This requires visual inspection!
        self.assertTrue( exodep.ProcessDeps.alert_messages == "" )
        if not os.path.isdir( 'alerts' ):
            os.mkdir( 'alerts' )
        rm( 'alerts/alerts.txt.old' )
        pd = make_ProcessDeps( 'uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n' +
                            'alert This is an ALERT ${strand}\n' +
                            'alert Another ALERT\n' +
                            'onalerts $has_alerts 1\n' +
                            'showalerts\n' +
                            'alert Even more alert\n' +
                            'alert Still more alerts\n' +
                            'alertstofile alerts/alerts.txt\n' )
        self.assertTrue( exodep.ProcessDeps.alert_messages == "ALERT: <StringIO> (6):\n       Even more alert\nALERT: <StringIO> (7):\n       Still more alerts" )
        self.assertTrue( 'has_alerts' in pd.vars )
        self.assertTrue( os.path.isfile( 'alerts/alerts.txt.old' ) )
        self.assertTrue( os.path.isfile( 'alerts/alerts.txt' ) )
        self.assertTrue( os.path.getsize( 'alerts/alerts.txt' ) > 100 )

    def test_echo(self):
        make_ProcessDeps(
                    'echo An echo\n' +
                    'echo\n' +
                    'echo Another echo' )

    def test_stop(self):
        ensure_dir( 'stop' )
        to_file( 'stop/test-stop.exodep',
                'touch stop/should-be-made.txt\n' +
                'stop\n' +
                'touch stop/should-not-be-made.txt\n' )
        ensure_dir( 'exodep-imports' )
        to_file( 'exodep-imports/__onstop.exodep',
                'touch stop/onstop-should-be-made.txt\n' )
        os.system( exodep_exe + 'stop/test-stop.exodep' )
        self.assertTrue( os.path.isfile( 'stop/should-be-made.txt' ) )
        self.assertTrue( not os.path.isfile( 'stop/should-not-be-made.txt' ) )
        self.assertTrue( os.path.isfile( 'stop/onstop-should-be-made.txt' ) )

    def test_authority(self):
        pd = make_ProcessDeps( '$v1 p1\n' +
                                'uritemplate https://raw.githubusercontent.com/codalogic/exodep/${strand}/${file}\n' +
                                'authority exodep-exports/exodep.exodep\n' +
                                '$v2 p2' )
        self.assertEqual( pd.vars['v1'], 'p1' )
        self.assertEqual( pd.vars['__authority'], 'https://raw.githubusercontent.com/codalogic/exodep/master/exodep-exports/exodep.exodep' )
        self.assertEqual( pd.vars['v2'], 'p2' )

        pd2 = make_ProcessDeps( '$v1 p1\n' +
                                'authority https://codalogic.com/codalogic/exodep/master/exodep-exports/exodep.exodep\n' +
                                '$v2 p2' )
        self.assertEqual( pd2.vars['v1'], 'p1' )
        self.assertEqual( pd2.vars['__authority'], 'https://codalogic.com/codalogic/exodep/master/exodep-exports/exodep.exodep' )
        self.assertEqual( pd2.vars['v2'], 'p2' )

    def test_authority_different(self):
        os.system( exodep_exe + "authority-different.exodep > authority-different-out.txt" )
        self.assertTrue( filecmp.cmp(  'authority-different-out.txt', 'authority-different-out-reference.txt' ) )

    def test_authority_same(self):
        os.system( exodep_exe + "authority-same.exodep > authority-same-out.txt" )
        self.assertTrue( os.path.getsize( 'authority-same-out.txt' ) == 0 ) # Shouldn't produce any output errors

    def test_not(self):
        pd = make_ProcessDeps( '$v1 p1\n' +
                                'on $v1 $v2 p2\n' +
                                'not on $v1 $v3 p3\n' +
                                'not not on $v1 $v4 p4\n' +
                                'not not not on $v1 $v5 p5\n' +
                                'not on $x1 $x2 y2\n' + # $x1 is not present
                                'not on $x1 on $v1 $x3 y3\n' +
                                'not on $x1 not on $v1 $x4 y4\n' +
                                'not on $x1 not not on $v1 $x5 y5\n' )
        self.assertEqual( pd.vars['v1'], 'p1' )
        self.assertEqual( pd.vars['v2'], 'p2' )
        self.assertTrue( 'v3' not in pd.vars )
        self.assertEqual( pd.vars['v4'], 'p4' )
        self.assertTrue( 'v5' not in pd.vars )
        self.assertEqual( pd.vars['x2'], 'y2' )
        self.assertEqual( pd.vars['x3'], 'y3' )
        self.assertTrue( 'x4' not in pd.vars )
        self.assertEqual( pd.vars['x5'], 'y5' )

    def test_autovars(self):
        pd = make_ProcessDeps( '$project my-proj\nautovars' )
        self.assertTrue( 'ext_home' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['ext_home'] ), '' )
        self.assertTrue( 'ext_test_home' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['ext_test_home'] ), 'test/' )
        self.assertTrue( 'inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['inc_dst'] ), 'include/' )
        self.assertTrue( 'src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['src_dst'] ), 'src/' )
        self.assertTrue( 'code_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['code_dst'] ), '' )
        self.assertTrue( 'test_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['test_inc_dst'] ), 'test/include/' )
        self.assertTrue( 'test_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['test_src_dst'] ), 'test/src/' )
        self.assertTrue( 'test_code_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['test_code_dst'] ), 'test/' )
        self.assertTrue( 'build_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['build_dst'] ), 'build/' )
        self.assertTrue( 'lib_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['lib_dst'] ), 'lib/' )
        self.assertTrue( 'bin_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['bin_dst'] ), 'bin/' )
        self.assertTrue( 'scripts_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['scripts_dst'] ), 'scripts/' )
        self.assertTrue( 'my_proj_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_inc_dst'] ), 'include/my-proj/' )
        self.assertTrue( 'my_proj_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_src_dst'] ), 'src/my-proj/' )
        self.assertTrue( 'my_proj_code_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_code_dst'] ), 'my-proj/' )
        self.assertTrue( 'my_proj_test_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_test_inc_dst'] ), 'test/include/my-proj/' )
        self.assertTrue( 'my_proj_test_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_test_src_dst'] ), 'test/src/my-proj/' )
        self.assertTrue( 'my_proj_test_code_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_test_code_dst'] ), 'test/my-proj/' )
        self.assertTrue( 'my_proj_build_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_build_dst'] ), 'build/my-proj/' )
        self.assertTrue( 'my_proj_lib_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_lib_dst'] ), 'lib/my-proj/' )
        self.assertTrue( 'my_proj_bin_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_bin_dst'] ), 'bin/my-proj/' )
        self.assertTrue( 'my_proj_scripts_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_scripts_dst'] ), 'scripts/my-proj/' )

    def test_autovars_2(self):
        pd = make_ProcessDeps( '$ext_home external/\n$ext_test_home ext/test/\n$build_dst build/\n$lib_dst  lib/\n$project my-proj\nautovars' )
        self.assertTrue( 'ext_home' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['ext_home'] ), 'external/' )
        self.assertTrue( 'ext_test_home' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['ext_test_home'] ), 'ext/test/' )
        self.assertTrue( 'inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['inc_dst'] ), 'external/include/' )
        self.assertTrue( 'src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['src_dst'] ), 'external/src/' )
        self.assertTrue( 'test_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['test_inc_dst'] ), 'ext/test/include/' )
        self.assertTrue( 'test_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['test_src_dst'] ), 'ext/test/src/' )
        self.assertTrue( 'build_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['build_dst'] ), 'build/' )
        self.assertTrue( 'lib_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['lib_dst'] ), 'lib/' )
        self.assertTrue( 'bin_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['bin_dst'] ), 'external/bin/' )
        self.assertTrue( 'my_proj_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_inc_dst'] ), 'external/include/my-proj/' )
        self.assertTrue( 'my_proj_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_src_dst'] ), 'external/src/my-proj/' )
        self.assertTrue( 'my_proj_test_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_test_inc_dst'] ), 'ext/test/include/my-proj/' )
        self.assertTrue( 'my_proj_test_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_test_src_dst'] ), 'ext/test/src/my-proj/' )
        self.assertTrue( 'my_proj_build_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_build_dst'] ), 'build/my-proj/' )
        self.assertTrue( 'my_proj_lib_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_lib_dst'] ), 'lib/my-proj/' )
        self.assertTrue( 'my_proj_bin_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_bin_dst'] ), 'external/bin/my-proj/' )

    def test_autovars_lowercase_project(self):
        pd = make_ProcessDeps( '$project My-Proj\n$ext_home external/\n$ext_test_home ext/test/\n$build_dst build/\n$lib_dst  lib/\nautovars' )
        self.assertTrue( 'My_Proj_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['My_Proj_inc_dst'] ), 'external/include/My-Proj/' )
        self.assertTrue( 'My_Proj_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['My_Proj_src_dst'] ), 'external/src/My-Proj/' )
        self.assertTrue( 'My_Proj_test_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['My_Proj_test_inc_dst'] ), 'ext/test/include/My-Proj/' )
        self.assertTrue( 'My_Proj_test_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['My_Proj_test_src_dst'] ), 'ext/test/src/My-Proj/' )
        self.assertTrue( 'My_Proj_build_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['My_Proj_build_dst'] ), 'build/My-Proj/' )
        self.assertTrue( 'My_Proj_lib_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['My_Proj_lib_dst'] ), 'lib/My-Proj/' )
        self.assertTrue( 'My_Proj_bin_dst' in pd.vars )

        self.assertEqual( pd.expand_variables( pd.vars['my_proj_bin_dst'] ), 'external/bin/my-proj/' )
        self.assertTrue( 'my_proj_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_inc_dst'] ), 'external/include/my-proj/' )
        self.assertTrue( 'my_proj_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_src_dst'] ), 'external/src/my-proj/' )
        self.assertTrue( 'my_proj_test_inc_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_test_inc_dst'] ), 'ext/test/include/my-proj/' )
        self.assertTrue( 'my_proj_test_src_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_test_src_dst'] ), 'ext/test/src/my-proj/' )
        self.assertTrue( 'my_proj_build_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_build_dst'] ), 'build/my-proj/' )
        self.assertTrue( 'my_proj_lib_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_lib_dst'] ), 'lib/my-proj/' )
        self.assertTrue( 'my_proj_bin_dst' in pd.vars )
        self.assertEqual( pd.expand_variables( pd.vars['my_proj_bin_dst'] ), 'external/bin/my-proj/' )

    def test_uses(self):
        os.system( exodep_exe + "uses-unknown.exodep > uses-test-out.txt" )
        self.assertTrue( filecmp.cmp(  'uses-test-out.txt', 'uses-test-out-reference.txt' ) )

    def test_text_filecmp(self):
        self.assertTrue( exodep.text_filecmp(  'file-cmp-text-crlf.txt', 'file-cmp-text-crlf-same.txt' ) )
        self.assertFalse( exodep.text_filecmp(  'file-cmp-text-crlf.txt', 'file-cmp-text-crlf-short.txt' ) )
        self.assertFalse( exodep.text_filecmp(  'file-cmp-text-crlf-short.txt', 'file-cmp-text-crlf.txt' ) )
        self.assertTrue( exodep.text_filecmp(  'file-cmp-text-lf.txt', 'file-cmp-text-crlf.txt' ) )
        self.assertTrue( exodep.text_filecmp(  'file-cmp-text-crlf.txt', 'file-cmp-text-lf.txt' ) )
        self.assertFalse( exodep.text_filecmp(  'file-cmp-text-crlf.txt', 'non-existant-file.txt' ) )
        self.assertFalse( exodep.text_filecmp(  'non-existant-file.txt', 'file-cmp-text-crlf.txt' ) )
        
    # def test_error_visually(self):
    #     make_ProcessDeps( '# blank line\n\ninclude woops' )

def make_ProcessDeps( s ):
    return exodep.ProcessDeps( io.StringIO( s ) )

def rm( file ):
    if os.path.isfile( file ):
        os.unlink( file )

def rmdir( dir ):
    if os.path.isdir( dir ):
        shutil.rmtree( dir )

def ensure_dir( dir ):
    os.makedirs( dir, exist_ok=True )

def to_file( file, content ):
    with open( file, 'w') as fout:
        fout.write( content )

if __name__ == '__main__':
    main()
