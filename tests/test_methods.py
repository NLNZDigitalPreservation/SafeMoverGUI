import unittest
import os, platform
import shutil
from unittest.mock import MagicMock, patch
from mover import Mover

class TestMethods(unittest.TestCase):

  def testStringCleaner(self):
    mover = Mover()
    str = u'test string'
    cleanedstr = mover.string_cleaner(str)
    self.assertEqual(cleanedstr, 'test string')
    print('String cleaner work correctly')

  def testIllegalCharsHandler(self):
    mover = Mover()
    str = 'test^123*abc:def>ghi<jkl|mno pqr?st'
    safestr = mover.illegal_chars_handler(str)
    self.assertEqual(safestr, 'test_123_abc_def_ghi_jkl_mno_pqr_st')
    print('Illegal chars handler work correctly')

  def testGetListOfFiles(self):
    os.makedirs('testfolder1/testfolder2/testfolder3', exist_ok=True)
    open('testfolder1/test1', 'a').close()
    open('testfolder1/testfolder2/test2', 'a').close()
    open('testfolder1/testfolder2/testfolder3/test3', 'a').close()
    open('testfolder1/.hiddenfile', 'a').close()
    mover = Mover()
    files = mover.getListOfFiles('testfolder1')
    expected = ['testfolder1/.hiddenfile','testfolder1/testfolder2/test2','testfolder1/testfolder2/testfolder3/test3','testfolder1/test1']
    self.assertEqual(files, expected)
    print('Get list of files work correctly')
    shutil.rmtree('testfolder1')

  @patch('platform.system', MagicMock(return_value='Windows'))
  def testConvertPath(self):
    mover = Mover()
    converted = mover.convertPath('C:/User/testfolder/test')
    expected = 'C:\\User\\testfolder\\test'
    self.assertEqual(converted, expected)
    print('convertPath work correctly')

  def testExtractFilename(self):
    mover = Mover()
    path1 = '/test/test1/test2.txt'
    path2 = '/test/test1/test3'
    file1 = mover.extractFilename(path1)
    file2 = mover.extractFilename(path2)
    self.assertEqual(file1, 'test2.txt')
    self.assertEqual(file2, 'test3')
    print('extractFilename work correctly')

  def testCheckExclusive(self):
    mover = Mover()
    exclusive = ['*.exe','test.txt']
    file1 = '/test/test1/test.txt'
    file2 = '/test/test.exe'
    file3 = '/test/test.ppt'
    check1 = mover.checkExclusive(file1, exclusive)
    check2 = mover.checkExclusive(file2, exclusive)
    check3 = mover.checkExclusive(file3, exclusive)
    self.assertTrue(check1)
    self.assertTrue(check2)
    self.assertFalse(check3)
    print('checkExclusive work correctly')

  def testGetSourceDestList(self):
    mover = Mover()
    mover.getListOfFiles = MagicMock(return_value=['src/test/test1/test.txt','src/test/test.exe','src/test/test.ppt','src/test/test^123*abc:def>ghi<jkl|mno pqr?st.docx'])
    sourcePath = 'src'
    destPath = 'dest'
    exclusive = ['*.exe','test.txt']
    lists = mover.getSourceDestList(sourcePath, destPath, True, exclusive)
    expected = []
    expected.append({'source': 'src/test/test1/test.txt', 'dest': 'dest/test/test1/test.txt', 'skip': True})
    expected.append({'source': 'src/test/test.exe', 'dest': 'dest/test/test.exe', 'skip': True})
    expected.append({'source': 'src/test/test.ppt', 'dest': 'dest/test/test.ppt', 'skip': False})
    expected.append({'source': 'src/test/test^123*abc:def>ghi<jkl|mno pqr?st.docx', 'dest': 'dest/test/test_123_abc_def_ghi_jkl_mno_pqr_st.docx', 'skip': False})
    self.assertEqual(lists, expected)
    print('getSourceDestList work correctly')

if __name__ == '__main__':
  unittest.main()