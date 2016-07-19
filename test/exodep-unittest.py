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
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\ncopy dl-test-target.txt download/" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target.txt' ) )
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\ncopy dl-test-target.txt download/dl-test-target1.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target1.txt' ) )
        make_ProcessDeps( "copy https://raw.githubusercontent.com/codalogic/exodep/master/test/dl-test-target.txt download/dl-test-target2.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target2.txt' ) )

        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\ncopy dl-test-target-other.txt download/" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target.txt' ) )   # Check file of different name doesn't overwrite existing one
        self.assertTrue( filecmp.cmp( 'dl-test-target-other.txt', 'download/dl-test-target-other.txt' ) )

        make_ProcessDeps( "copy https://raw.githubusercontent.com/codalogic/exodep/master/test/dl-test-target-other.txt download/dl-test-target3.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target-other.txt', 'download/dl-test-target3.txt' ) )    # Check download of different file updates an existing one

    def test_download_copy_with_only_one_arg(self):
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "copy file1.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-file1-reference.txt', 'file1.txt' ) )

        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "copy dir1/file2.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dir1/file2.txt' ) )

        os.remove( 'dir1/file2.txt' )
        make_ProcessDeps( "$path nothing\n" +       # $path should be ignored because it's not in the uritemplate
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${file}\n" +
                            "copy dir1/file2.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dir1/file2.txt' ) )

        os.remove( 'dir1/file2.txt' )
        make_ProcessDeps( "$path dir1/\n" +
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep-test-data/master/${path}${file}\n" +
                            "copy file2.txt" )
        self.assertTrue( filecmp.cmp( 'exodep-test-data-dir1-file2-reference.txt', 'dir1/file2.txt' ) )

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
                            "copy test/dl-test-target.txt download/dl-test-target11.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target11.txt' ) )

        make_ProcessDeps( "$strand alto\n" +
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep/${strand}/${file}\n" +
                            "versions\n" +  # Specify default versions
                            "copy test/dl-test-target.txt download/dl-test-target12.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target12.txt' ) )

        make_ProcessDeps( "versions https://raw.githubusercontent.com/codalogic/exodep/master/versions.exodep\n" +
                            "$strand alto\n" +
                            "uritemplate https://raw.githubusercontent.com/codalogic/exodep/${strand}/${file}\n" +
                            "copy test/dl-test-target.txt download/dl-test-target14.txt" )
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

    def test_on_conditional(self):
        pd = make_ProcessDeps( '$v v1\n$dll true\non $dll $v p2\non $other $v l3' )
        self.assertTrue( 'v' in pd.vars )
        self.assertEqual( pd.vars['v'], 'p2' )

    def test_os_conditional(self):
        pd = make_ProcessDeps( '$v v1\nwindows $v p2\nlinux $v l3' )
        self.assertTrue( 'v' in pd.vars )
        if sys.platform.startswith( 'win32' ):
            self.assertEqual( pd.vars['v'], 'p2' )
        elif sys.platform.startswith( 'linux' ):
            self.assertEqual( pd.vars['v'], 'l3' )

    # def test_exec_visually(self):
    #     make_ProcessDeps( 'windows exec dir\nwindows exec dir' )
    #
    # def test_error_visually(self):
    #     make_ProcessDeps( '# blank line\n\ninclude woops' )

def make_ProcessDeps( s ):
    return exodep.ProcessDeps( io.StringIO( s ) )

if __name__ == '__main__':
    main()
