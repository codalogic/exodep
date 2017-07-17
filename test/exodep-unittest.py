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

def main():
    pre_clean()
    unittest.main()

def pre_clean():
    if os.path.isdir( 'download' ):
        shutil.rmtree( 'download' )
    if os.path.isdir( 'file-ops-test-dir' ):
        shutil.rmtree( 'file-ops-test-dir' )
    if os.path.isdir( 'dir1' ):
        shutil.rmtree( 'dir1' )
    if os.path.isfile( 'file1.txt' ):
        os.remove( 'file1.txt' )

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

    def test_download_copy_with_only_one_arg(self):
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "get file1.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-file1-reference.txt', 'file1.txt' ) )

        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "get dir1/file2.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dir1/file2.txt' ) )

        os.remove( 'dir1/file2.txt' )
        make_ProcessDeps( "$path nothing\n" +       # $path should be ignored because it's not in the uritemplate
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "get dir1/file2.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dir1/file2.txt' ) )

        os.remove( 'dir1/file2.txt' )
        make_ProcessDeps( "$path dir1/\n" +
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${path}${file}\n" +
                            "get file2.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dir1/file2.txt' ) )

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
        pd = make_ProcessDeps( 'uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\n' +
                            'alert This is an ALERT ${strand}\n' +
                            'alert Another ALERT\n' +
                            'onalerts $has_alerts 1' )
        print( exodep.ProcessDeps.alert_messages )
        self.assertTrue( exodep.ProcessDeps.alert_messages == "ALERT: <StringIO> (2):\n       This is an ALERT master\nALERT: <StringIO> (3):\n       Another ALERT" )
        self.assertTrue( 'has_alerts' in pd.vars )

    # def test_error_visually(self):
    #     make_ProcessDeps( '# blank line\n\ninclude woops' )

def make_ProcessDeps( s ):
    return exodep.ProcessDeps( io.StringIO( s ) )

if __name__ == '__main__':
    main()
