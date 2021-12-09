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

  def testGetFailedList(self):
    mover =  Mover()
    failed_lists = ['src/test/test1/test.txt','src/test/test.exe']
    sourcePath = 'src'
    destPath = 'dest'
    lists = mover.getFailedList(failed_lists, sourcePath, destPath, False)
    expected = []
    expected.append({'source': 'src/test/test1/test.txt', 'dest': 'dest/test/test1/test.txt'})
    expected.append({'source': 'src/test/test.exe', 'dest': 'dest/test/test.exe'})
    self.assertEqual(lists, expected)
    print('getFailedList work correctly')

  def testRemoveFromList(self):
    mover = Mover()
    lists = ['src/test/test1/test.txt','src/test/test.exe','src/test/test1/test1.txt','src/test/test1/test2.txt']
    removedlists = mover.removeFromList(lists, 'test.txt')
    expected = ['src/test/test.exe','src/test/test1/test1.txt','src/test/test1/test2.txt']
    self.assertEqual(removedlists, expected)
    removedlists = mover.removeFromList(lists, 'test/test1/test.txt')
    expected = ['src/test/test.exe','src/test/test1/test1.txt','src/test/test1/test2.txt']
    self.assertEqual(removedlists, expected)
    print('removeFromList work correctly')

  def testGetAlgo(self):
    mover = Mover()
    algo = mover.getAlgo()
    expected = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512', 'blake2b', 'blake2s']
    self.assertEqual(algo, expected)
    print('getAlgo work correctly')

  def testGetFileHashMD5(self):
    mover = Mover()
    file = 'LICENSE'
    hash = mover.getFileHash(file, 'md5')
    self.assertEqual(hash, '8264535c0c4e9c6c335635c4026a8022')
    print('getFileHash MD5 work correctly')

  def testGetFileHashSHA1(self):
    mover = Mover()
    file = 'LICENSE'
    hash = mover.getFileHash(file, 'sha1')
    self.assertEqual(hash, '23a1f87d806ce0330b3d85485e399a5f9f553409')
    print('getFileHash SHA1 work correctly')
  
  def testGetFileHashSHA224(self):
    mover = Mover()
    file = 'LICENSE'
    hash = mover.getFileHash(file, 'sha224')
    self.assertEqual(hash, '3a29388be4d4f55eb38725b0f242b2ab2d6e76cf49e884855f255e8c')
    print('getFileHash SHA224 work correctly')

  def testGetFileHashSHA256(self):
    mover = Mover()
    file = 'LICENSE'
    hash = mover.getFileHash(file, 'sha256')
    self.assertEqual(hash, 'a45d0bb572ed792ed34627a72621834b3ba92aab6e2cc4e04301dee7a728d753')
    print('getFileHash SHA256 work correctly')

  def testGetFileHashSHA384(self):
    mover = Mover()
    file = 'LICENSE'
    hash = mover.getFileHash(file, 'sha384')
    self.assertEqual(hash, 'b38d216a2ff1a3a08b9e0b111a974109a59a3fd203fb49ae978de0ada283594a30501c0e1c1991c7b7c962d55ffb5468')
    print('getFileHash SHA384 work correctly')
  
  def testGetFileHashsha512(self):
    mover = Mover()
    file = 'LICENSE'
    hash = mover.getFileHash(file, 'sha512')
    self.assertEqual(hash, 'd281feecb7d1218e1aea8269f288fcd63385da1a130681fadae77262637cb65fed33c8f24a30bcebdac728a359e84044cfc8776eb184571db9af0f6cab1f2579')
    print('getFileHash SHA512 work correctly')
  
  def testGetFileHashBLAKE2B(self):
    mover = Mover()
    file = 'LICENSE'
    hash = mover.getFileHash(file, 'blake2b')
    self.assertEqual(hash, '3f5068ac43801ea81096944c6109f1dfc6f84c42cd206d790756e9123095dd93af27cf67cd5624b485e3242504cfa2260f241ee88f7ef081c6d1b8917f99d89d')
    print('getFileHash BLAKE2B work correctly')
  
  def testGetFileHashBLAKE2S(self):
    mover = Mover()
    file = 'LICENSE'
    hash = mover.getFileHash(file, 'blake2s')
    self.assertEqual(hash, 'a2b6796b6800ca54f2de31e53f2a2fa66c98125e78476663dd95f7f401689338')
    print('getFileHash BLAKE2S work correctly')

  def testGetMetadata(self):
    mover = Mover()
    file = 'LICENSE'
    access, modify, create, mode, size = mover.getMetadata(file)
    self.assertRegex(access, '([A-Z][a-z][a-z]) ([A-Z][a-z][a-z]) \s?([0-3]?[0-9]) ([0-2][0-9]):([0-9][0-9]):([0-9][0-9]) ([0-9][0-9][0-9][0-9])$')
    self.assertRegex(modify, '([A-Z][a-z][a-z]) ([A-Z][a-z][a-z]) \s?([0-3]?[0-9]) ([0-2][0-9]):([0-9][0-9]):([0-9][0-9]) ([0-9][0-9][0-9][0-9])$')
    self.assertRegex(create, '([A-Z][a-z][a-z]) ([A-Z][a-z][a-z]) \s?([0-3]?[0-9]) ([0-2][0-9]):([0-9][0-9]):([0-9][0-9]) ([0-9][0-9][0-9][0-9])$')
    self.assertRegex(str(mode), '^[0-7][0-7][0-7]$')
    self.assertGreater(size, 0)
    print('getMetadata work correctly')

  def testReadableTime(self):
    mover = Mover()
    timestamp = 1555555555
    timestr = mover.readableTime(timestamp)
    self.assertEqual(timestr, 'Thu Apr 18 14:45:55 2019')
    print('readableTime work correctly')

  @patch('platform.system', MagicMock(return_value='Windows'))
  def testExtractPath(self):
    mover = Mover()
    converted = mover.extractPath('C:\\User\\testfolder\\test.txt','C:\\User\\')
    expected = 'testfolder\\test.txt'
    self.assertEqual(converted, expected)
    print('extractPath work correctly')

  @patch('platform.system', MagicMock(return_value='Windows'))
  def testAppendPath(self):
    mover = Mover()
    converted = mover.appendPath('testfolder/test.txt','C:/User')
    expected = 'C:\\User\\testfolder\\test.txt'
    self.assertEqual(converted, expected)
    print('appendPath work correctly')

if __name__ == '__main__':
  unittest.main()