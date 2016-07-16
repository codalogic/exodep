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

class MyTest(unittest.TestCase):
    def test_default_setup(self):
        pd = make_ProcessDeps( "" )
        self.assertEqual( len( pd.vars ), 1 )
        self.assertTrue( 'strand' in pd.vars )
        self.assertEqual( pd.vars['strand'], 'master' )
        self.assertEqual( pd.uritemplate, 'https://raw.githubusercontent.com/${user}/${project}/${strand}/${file}' )

    def test_set_uritemplate(self):
        pd = make_ProcessDeps( "uritemplate htpp://fiddle.com/${file}" )
        self.assertEqual( pd.uritemplate, 'htpp://fiddle.com/${file}' )

    def test_set_hosting_bitbucket(self):
        pd = make_ProcessDeps( "hosting bitbucket" )
        self.assertEqual( pd.uritemplate, 'https://bitbucket.org/${user}/${project}/raw/${strand}/${file}' )

    def test_set_hosting_github(self):
        pd = make_ProcessDeps( "uritemplate htpp://fiddle.com/${file}\nhosting github" )
        self.assertEqual( pd.uritemplate, 'https://raw.githubusercontent.com/${user}/${project}/${strand}/${file}' )

    def test_set_single_var(self):
        pd = make_ProcessDeps( "$space Mumble" )
        self.assertEqual( len( pd.vars ), 2 )
        self.assertTrue( 'strand' in pd.vars )
        self.assertEqual( pd.vars['strand'], 'master' )
        self.assertTrue( 'space' in pd.vars )
        self.assertEqual( pd.vars['space'], 'Mumble' )

    def test_set_multiple_vars(self):
        pd = make_ProcessDeps( "$plant rose\n$animal sheep" )
        self.assertEqual( len( pd.vars ), 3 )
        self.assertTrue( 'strand' in pd.vars )
        self.assertEqual( pd.vars['strand'], 'master' )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], 'rose' )
        self.assertTrue( 'animal' in pd.vars )
        self.assertEqual( pd.vars['animal'], 'sheep' )

    def test_set_default_vars_1(self):
        pd = make_ProcessDeps( "default $plant tulip" )
        self.assertEqual( len( pd.vars ), 2 )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], 'tulip' )

    def test_set_default_vars_2(self):
        pd = make_ProcessDeps( "$plant rose\ndefault $plant tulip" )
        self.assertEqual( len( pd.vars ), 2 )
        self.assertTrue( 'plant' in pd.vars )
        self.assertEqual( pd.vars['plant'], 'rose' )

    def test_uri_formation(self):
        pd = make_ProcessDeps( "$user marvin\n$strand apple\n$project exodep" )

        formed_uri = pd.make_uri( 'data.dat' )
        self.assertEqual( formed_uri, 'https://raw.githubusercontent.com/marvin/exodep/apple/data.dat' )

        pd.versions = { 'apple banana' : 'zen', 'carrot date' : 'yuka' }
        formed_uri = pd.make_uri( 'data.dat' )
        self.assertEqual( formed_uri, 'https://raw.githubusercontent.com/marvin/exodep/zen/data.dat' )

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
        if os.path.isdir( 'download' ):
            shutil.rmtree( 'download' )
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\ncopy dl-test-target.txt download/" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target.txt' ) )
        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\ncopy dl-test-target.txt download/dl-test-target1.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target1.txt' ) )
        make_ProcessDeps( "copy https://raw.githubusercontent.com/codalogic/exodep/master/test/dl-test-target.txt download/dl-test-target2.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target2.txt' ) )

        make_ProcessDeps( "uritemplate https://raw.githubusercontent.com/codalogic/exodep/master/test/${file}\ncopy dl-test-target-other.txt download/" )
        self.assertTrue( filecmp.cmp( 'dl-test-target.txt', 'download/dl-test-target.txt' ) )   # Check file of different name doesn't overwrite existing one
        self.assertTrue( filecmp.cmp( 'dl-test-target-other.txt', 'download/dl-test-target-other.txt' ) )

        make_ProcessDeps( "copy https://raw.githubusercontent.com/codalogic/exodep/master/test/dl-test-target-other.txt download/dl-test-target2.txt" )
        self.assertTrue( filecmp.cmp( 'dl-test-target-other.txt', 'download/dl-test-target2.txt' ) )    # Check download of different file updates an existing one

def make_ProcessDeps( s ):
    return exodep.ProcessDeps( io.StringIO( s ) )

if __name__ == '__main__':
    unittest.main()
