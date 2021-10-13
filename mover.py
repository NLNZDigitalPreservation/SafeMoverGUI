import sys, string, os, shutil, time, stat, platform, csv, math, fnmatch, ntpath, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import md5, sha1, sha224, sha256, sha384, sha512, blake2b, blake2s
from tqdm import tqdm

class Mover():
    def __init__(self):
        self.success_files = []
        self.failed_files = []
        self.hash_list = []
        self.threadStop = False
        self.lock = threading.Lock()

    def string_cleaner(self, original_str):
        clean_string = str(original_str)
        if clean_string.startswith("u'") and clean_string.endswith("'"):
            clean_string = clean_string[2:-1]
        return clean_string

    def illegal_chars_handler(self, original_str):
        special_chars = ['?','<','>',':','*','|','^',' ']
        printable = set(string.printable)
        replace_chars = {ord(c):'_' for c in special_chars}
        final_str = [original_str.translate(replace_chars), original_str[:2]+original_str[2:].translate(replace_chars)][platform.system() == 'Windows']
        final_str = ''.join(filter(lambda x: x in printable, final_str))
        count = final_str.count('.')-1
        final_str = final_str.replace('.','_',count)
        return final_str

    def getListOfFiles(self, root_path):
        files = []
        if os.path.isdir(root_path):
            listOfFile = os.listdir(root_path)
            for file in listOfFile:
                fullPath = os.path.join(root_path, file)
                if os.path.isdir(fullPath):
                    files += self.getListOfFiles(self.convertPath(fullPath))
                else:
                    files.append(self.convertPath(fullPath))
        else:
            files.append(self.convertPath(root_path))
        return files

    def convertPath(self, originalPath):
        if platform.system() == 'Windows':
            p = originalPath.replace('/','\\')
        else:
            p = originalPath
        return p

    def extractFilename(self, path):
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)
    
    def checkExclusive(self, file, exclusive):
        for item in exclusive:
            if fnmatch.fnmatch(file, item) or self.extractFilename(file) == item:
                return True
        return False

    def getSourceDestList(self, source, dest, rename, exclude_files):
        source_files = self.getListOfFiles(source)
        lists = []
        skip = False
        for item in source_files:
            if len(exclude_files) != 0 and self.checkExclusive(item, exclude_files):
                skip = True
            else:
                skip = False
            if item == source:
                if rename:
                    lists.append({'source': self.convertPath(item), 'dest': self.convertPath(self.illegal_chars_handler(self.string_cleaner(dest))), 'skip': skip})
                else:
                    lists.append({'source': self.convertPath(item), 'dest': self.convertPath(dest), 'skip': skip})
            else:
                if rename:
                    lists.append({'source': self.convertPath(item), 'dest': self.convertPath(self.illegal_chars_handler(self.string_cleaner(self.appendPath(self.extractPath(item, source), dest)))), 'skip': skip})
                else:
                    lists.append({'source': self.convertPath(item), 'dest': self.convertPath(self.appendPath(self.extractPath(item, source), dest)), 'skip': skip})
        return lists

    def getFailedList(self, failed_lists, source, dest, rename):
        lists = []
        for item in failed_lists:
            if item == source:
                if rename:
                    lists.append({'source': self.convertPath(item), 'dest': self.convertPath(self.illegal_chars_handler(self.string_cleaner(dest)))})
                else:
                    lists.append({'source': self.convertPath(item), 'dest': self.convertPath(dest)})
            else:
                if rename:
                    lists.append({'source': self.convertPath(item), 'dest': self.convertPath(self.illegal_chars_handler(self.string_cleaner(self.appendPath(self.extractPath(item, source), dest))))})
                else:
                    lists.append({'source': self.convertPath(item), 'dest': self.convertPath(self.appendPath(self.extractPath(item, source), dest))})
        return lists

    def removeFromList(self, lists, item):
        return list(filter(lambda x: x!=item and not x.endswith('/'+item), lists))

    def getAlgo(self):
        return ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512', 'blake2b', 'blake2s']

    def getFileHash(self, filename, checksum='md5'):
        try:
            f = open(filename, mode='rb')
            file = f.read()
            f.close()
        except:
            print('File {} read failed'.format(filename))
        file_checksum = ''
        try:
            if checksum == 'md5':
                file_checksum = md5(file).hexdigest()
            elif checksum == 'sha1':
                file_checksum = sha1(file).hexdigest()
            elif checksum == 'sha224':
                file_checksum = sha224(file).hexdigest()
            elif checksum == 'sha256':
                file_checksum = sha256(file).hexdigest()
            elif checksum == 'sha384':
                file_checksum = sha384(file).hexdigest()
            elif checksum == 'sha512':
                file_checksum = sha512(file).hexdigest()
            elif checksum == 'blake2b':
                file_checksum = blake2b(file).hexdigest()
            elif checksum == 'blake2s':
                file_checksum = blake2s(file).hexdigest()
        except:
            print('Hash file {} failed'.format(filename))
        return file_checksum

    def getMetadata(self, file):
        access = 0
        modify = 0
        create = 0
        mode = 777
        size = 0
        try:
            access = os.path.getatime(file)
        except:
            print('Cannot get file {} last access time'.format(file))
        try:
            modify = os.path.getmtime(file)
        except:
            print('Cannot get file {} last modified time'.format(file))
        try:
            create = os.path.getctime(file)
        except:
            print('Cannot get file {} created time'.format(file))
        try:
            mode = stat.S_IMODE(os.stat(file).st_mode)
        except:
            print('Cannot get file {} mode'.format(file))
        try:
            size = os.path.getsize(file)
        except:
            print('Cannot get file {} size'.format(file))
        return self.readableTime(access), self.readableTime(modify), self.readableTime(create), mode, size

    def readableTime(self, timestamp):
        return time.ctime(timestamp)

    def extractPath(self, file, path):
        if platform.system() == 'Windows':
            if path[-1] != '\\':
                path += '\\'
            length = len(path)
            if file[0:length] == path:
                return file[length:]
            else:
                return file
        else:
            if path[-1] != '/':
                path += '/'
            length = len(path)
            if file[0:length] == path:
                return file[length:]
            else:
                return file

    def appendPath(self, file, path):
        if path[-1] != '/':
            path += '/'
        return path+file

    def copy(self, source, dest):
        try:
            if os.path.isdir(os.path.dirname(dest)) is not True:
                foldermode = stat.S_IMODE(os.stat(os.path.dirname(source)).st_mode)
                os.makedirs(os.path.dirname(dest), mode = foldermode)
            shutil.copy2(source, dest)
            self.success_files.append(source)
            return True
        except:
            self.failed_files.append(source)
            return False

    def compare(self, source, dest, checksum='md5'):
        checksum1 = self.getFileHash(source, checksum)
        checksum2 = self.getFileHash(dest, checksum)
        access1, modify1, create1, size1 = self.getMetadata(source)
        access2, modify2, create2, size2 = self.getMetadata(dest)
        if checksum1 == checksum2 and modify1 == modify2 and size1 == size2:
            return True
        else:
            return False

    def terminate(self, value):
        if value:
            self.threadStop = True
        else:
            self.threadStop = False

    def filenameCheck(self, source, dest):
        if os.path.basename(source) == os.path.basename(dest):
            return True
        else:
            return False

    def countFileFolder(self, folderpath):
        totalFiles = 0
        totalDirs = 0
        for base, dirs, files in os.walk(folderpath):
            for dir in dirs:
                totalDirs += 1
            for file in files:
                totalFiles += 1
        return totalFiles, totalDirs

    def getETA(self, t):
        if t > 60:
            return '{} min {} sec'.format(math.floor(t/60), t%60)
        else:
            return '{} sec'.format(t)

    def transformText(self, text, size):
        result = text
        if len(str(text)) > size and size > 12:
            result = str(text)[:int((size/2)-6)] + ' ... ' + str(text)[int(-1*(size/2)-3):]
        return result

    def findDuplicate(self, hash_list, item):
        return [x for x in hash_list if x['hash'] == item ]

    def copyFile(self, params):
        QTprogressText = None
        QTlogger = None
        log_line = []
        duplicate_log = []
        exclude_log = []
        skip_log = []
        change_log = []
        checkDuplicate = False
        exclude = False
        try:
            source = params[0]
            dest = params[1]
            exclude = params[2]
            checksum = params[3]
            sourcePath = params[4]
            QT = params[5]
            checkDuplicate = params[6]
            if exclude:
                exclude_log = [source]
            else:
                if QT:
                    QTprogressText = 'Copying {}'.format(self.transformText(source, 34))
                else: 
                    print('Copying {}'.format(self.transformText(source, 48)))
                t = time.ctime()
                checksum1 = self.getFileHash(source, checksum)
                access1, modify1, create1, mode1, size1 = self.getMetadata(source)
                if os.path.exists(dest):
                    checksum2 = self.getFileHash(dest, checksum)
                    access2, modify2, create2, mode2, size2 = self.getMetadata(dest)
                    if checksum1 == checksum2 and modify1 == modify2 and mode1 == mode2 and size1 == size2:
                        skip_log = [source, dest]
                    else:
                        change_log = [source, dest, checksum1, checksum2, modify1, modify2, mode1, mode2, size1, size2]
                        self.copy(source, dest)
                        checksum2 = self.getFileHash(dest, checksum)
                        access2, modify2, create2, mode2, size2 = self.getMetadata(dest)
                else:
                    self.copy(source, dest)
                    checksum2 = self.getFileHash(dest, checksum)
                    access2, modify2, create2, mode2, size2 = self.getMetadata(dest)
                if checksum1 == checksum2 and modify1 == modify2 and size1 == size2:
                    if QT:
                        QTlogger = self.transformText('{}'.format(self.extractPath(source, sourcePath)), 36)
                    log_line = 	['SUCCESS', t, source, dest, self.filenameCheck(source, dest), checksum, checksum1, checksum2, checksum1 == checksum2, size1, size2, size1 == size2, mode1, mode2, mode1 == mode2, modify1, modify2, modify1 == modify2, create1, create2, access1, access2]
                    with self.lock:
                        duplicateFile = self.findDuplicate(self.hash_list, checksum1)
                        if checkDuplicate and len(duplicateFile) > 0:
                            duplicate_log = [source, checksum, checksum1, duplicateFile[0]['source']]
                        else:
                            self.hash_list.append({'source':source, 'hash':checksum1})
                else:
                    if QT:
                        QTlogger = self.transformText('{}'.format(self.extractPath(source, sourcePath)), 36)
                    log_line = 	['FAILED', t, source, dest, self.filenameCheck(source, dest), checksum, checksum1, checksum2, checksum1 == checksum2, size1, size2, size1 == size2, mode1, mode2, modify1, modify2, modify1 == modify2, create1, create2, access1, access2]
        except:
            if QT:
                QTlogger = self.transformText('{}'.format(self.extractPath(source, source)), 36)
            log_line = 	['FAILED', t, source, dest, self.filenameCheck(source, dest), '', '', '','','', '', '', '', '', '', '', '', '', '', '', '']
            pass
        return (QTprogressText, QTlogger, exclude, log_line, duplicate_log, exclude_log, skip_log, change_log)

    def move(self, source, dest, logs='logs', checksum='md5', checkDuplicate=False, rename=True, exclusive='', threadnum=10, **kwargs):
        self.success_files = []
        self.failed_files = []
        self.hash_list = []
        self.threadStop = False
        start_time = time.time()
        if os.path.isdir(logs) is not True:
            os.makedirs(logs)
        if exclusive == None or exclusive == '':
            exclude_files = []
        else:
            exclude_files = exclusive.split(',')
        QT = False
        if 'logger' in kwargs and kwargs['logger'] != None:
            kwargs['logger'].emit(self.transformText('Read files in {}'.format(source), 36))
            QT = True
        else:
            print(self.transformText('Read files in {}'.format(source), 48))
        if 'progressText' in kwargs and kwargs['progressText'] != None:
            kwargs['progressText'].emit(self.transformText('Reading source file/folder ...', 36))
            QT = True
        else:
            print(self.transformText('Reading source file/folder ...', 48))
        if 'ETA' in kwargs and kwargs['ETA'] != None:
            kwargs['ETA'].emit('-')
            QT = True
        lists = self.getSourceDestList(source, dest, rename, exclude_files)
        size = len(lists)

        if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
            kwargs['updateProgressQT'].emit(0)
        if 'logger' in kwargs and kwargs['logger'] != None:
            kwargs['logger'].emit('######################')

        source_file_num, source_folder_num = self.countFileFolder(source)

        log_line = 	['Status', 'Time', 'Source_path', 'Dest_path', 'Filename_check', 'Hash_method', 'Source_hash', 'Dest_hash', 'Hash_check', 'Source_size', 'Dest_size', 'Size_check', 'Source_permission', 'Dest_permission', 'Permission_check', 'Source_Modified_Date', 'Dest_Modified_Date', 'Modified_Date_check', 'Source_Created_Date', 'Dest_Created_Date', 'Source_Accessed_Date', 'Dest_Accessed_Date']
        current_time = time.strftime('%Y%m%d%H%M%S')
        try:
            logFile = open(logs+'/transfer_log('+current_time+').csv', "w")
        except:
            if 'progressText' in kwargs and kwargs['progressText'] != None:
                kwargs['progressText'].emit('transfer_log.csv is opened')
            else:
                print('transfer_log.csv is opened')
            return
        writer = csv.writer(logFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        writer.writerow(log_line)
        threads = list()
        threadPool = ThreadPoolExecutor(max_workers=threadnum)
        for i in range(size):
            t = threadPool.submit(self.copyFile, (lists[i]['source'], lists[i]['dest'], lists[i]['skip'], checksum, source, QT, checkDuplicate))
            threads.append(t)
        t = tqdm((thread.result() for thread in as_completed(threads)), total=size)
        duplicate_log = []
        exclude_log = []
        skip_log = []
        change_log = []
        for i in t:
            if i[0] != None and 'progressText' in kwargs and kwargs['progressText'] != None:
                kwargs['progressText'].emit(i[0])
            if i[1] != None and 'logger' in kwargs and kwargs['logger'] != None:
                kwargs['logger'].emit(i[1])
            if i[3] != [] and i[3][0] == 'SUCCESS':
                writer.writerow(i[3])
            if i[4] != []:
                duplicate_log.append(i[4])
            if i[5] != []:
                exclude_log.append(i[5])
            if i[6] != []:
                skip_log.append(i[6])
            if i[7] != []:
                change_log.append(i[7])
            s = str(t).split()
            if len(s) > 4:
                count = int(s[2].split('/')[0])
                remaining = s[3].split('<')[1][:-1]
                if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
                    kwargs['updateProgressQT'].emit(int((count)*100/size))
                if 'ETA' in kwargs and kwargs['ETA'] != None and remaining != '?':
                    kwargs['ETA'].emit(remaining)
            elif len(s) == 4:
                count = int(s[1].split('/')[0])
                remaining = s[2].split('<')[1][:-1]
                if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
                    kwargs['updateProgressQT'].emit(int((count)*100/size))
                if 'ETA' in kwargs and kwargs['ETA'] != None and remaining != '?':
                    kwargs['ETA'].emit(remaining)
            if self.threadStop:
                # shutil.rmtree(dest)
                # shutil.rmtree(logs)
                t.close()
                kwargs['progressText'].emit('Operation interrupted by user')
                break

        retry = 3
        while len(self.failed_files) > 0 and retry > 0:
            if 'progressText' in kwargs and kwargs['progressText'] != None:
                kwargs['progressText'].emit('Retry {} time(s) copy failed files again ...'.format((4-retry)))
            else:
                print('Retry {} time(s) copy failed files again ...'.format((4-retry)))
            if 'ETA' in kwargs and kwargs['ETA'] != None:
                kwargs['ETA'].emit('-')
            lists = self.getFailedList(self.failed_files, source, dest, rename)
            self.failed_files = []
            size = len(lists)
            threads = list()
            threadPool = ThreadPoolExecutor(max_workers=threadnum)
            for i in range(size):
                t = threadPool.submit(self.copyFile, (lists[i]['source'], lists[i]['dest'], False, checksum, source, QT, checkDuplicate))
                threads.append(t)
            t = tqdm((thread.result() for thread in as_completed(threads)), total=size)
            for i in t:
                if i[0] != None:
                    kwargs['progressText'].emit(i[0])
                if i[1] != None:
                    kwargs['logger'].emit(i[1])
                if i[3] != []:
                    writer.writerow(i[3])
                if i[4] != []:
                    duplicate_log.append(i[4])
                if i[5] != []:
                    exclude_log.append(i[5])
                if i[6] != []:
                    skip_log.append(i[6])
                if i[7] != []:
                    change_log.append(i[7])
                s = str(t).split()
                if len(s) > 4:
                    count = int(s[2].split('/')[0])
                    remaining = s[3].split('<')[1][:-1]
                    if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
                        kwargs['updateProgressQT'].emit(int((count)*100/size))
                    if 'ETA' in kwargs and kwargs['ETA'] != None and remaining != '?':
                        kwargs['ETA'].emit(remaining)
                elif len(s) == 4:
                    count = int(s[1].split('/')[0])
                    remaining = s[2].split('<')[1][:-1]
                    if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
                        kwargs['updateProgressQT'].emit(int((count)*100/size))
                    if 'ETA' in kwargs and kwargs['ETA'] != None and remaining != '?':
                        kwargs['ETA'].emit(remaining)
                if self.threadStop:
                #     shutil.rmtree(dest)
                #     shutil.rmtree(logs)
                    t.close()
                    kwargs['progressText'].emit('Operation interrupted by user')
                    break
            retry -= 1

        threadPool.shutdown()
        logFile.close()

        if checkDuplicate:
            try:
                logFile = open(logs+'/duplication_log('+current_time+').csv', "w")
                writer = csv.writer(logFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
                writer.writerow(['Source', 'Hash_method', 'Hash', 'Duplicate file'])
                writer.writerows(duplicate_log)
                logFile.close()
            except:
                if 'progressText' in kwargs and kwargs['progressText'] != None:
                    kwargs['progressText'].emit('duplication_log.csv is opened')
                else:
                    print('duplication_log.csv is opened')
                return
            

        if len(exclude_files) > 0:
            try:
                logFile = open(logs+'/exclude_log('+current_time+').csv', "w")
                writer = csv.writer(logFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
                writer.writerow(['Source_path'])
                writer.writerows(exclude_log)
                logFile.close()
            except:
                if 'progressText' in kwargs and kwargs['progressText'] != None:
                    kwargs['progressText'].emit('exclude_log.csv is opened')
                else:
                    print('exclude_log.csv is opened')
                return

        if len(skip_log) > 0:
            try:
                logFile = open(logs+'/skip_log('+current_time+').csv', "w")
                writer = csv.writer(logFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
                writer.writerow(['Source_path', 'Dest_path'])
                writer.writerows(skip_log)
                logFile.close()
            except:
                if 'progressText' in kwargs and kwargs['progressText'] != None:
                    kwargs['progressText'].emit('skip_log.csv is opened')
                else:
                    print('skip_log.csv is opened')
                return

        if len(change_log) > 0:
            try:
                logFile = open(logs+'/change_log('+current_time+').csv', "w")
                writer = csv.writer(logFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
                writer.writerow(['Source_path', 'Dest_path', 'Source_hash', 'Dest_hash', 'Source_Modified_Date', 'Dest_Modified_Date', 'Source_permission', 'Dest_permission', 'Source_size', 'Dest_size'])
                writer.writerows(change_log)
                logFile.close()
            except:
                if 'progressText' in kwargs and kwargs['progressText'] != None:
                    kwargs['progressText'].emit('change_log.csv is opened')
                else:
                    print('change_log.csv is opened')
                return

        end_time = time.time() 
        dest_file_num, dest_folder_num = self.countFileFolder(dest)
        if 'logger' in kwargs and kwargs['logger'] != None:
            kwargs['logger'].emit('######################')
            kwargs['logger'].emit('Summary')
            kwargs['logger'].emit('Executed %.2f seconds' % (end_time - start_time))
            kwargs['logger'].emit('Number of files in Source: {}'.format(source_file_num))
            kwargs['logger'].emit('Number of files in Dest: {}'.format(dest_file_num))
            kwargs['logger'].emit('Number of folders in Source: {}'.format(source_folder_num))
            kwargs['logger'].emit('Number of folders in Dest: {}'.format(dest_folder_num))
            kwargs['logger'].emit('Files copied succesfully: {}'.format(len(self.success_files)))
            if len(self.failed_files) > 0:
                kwargs['logger'].emit('Files not copied: {}'.format(len(self.failed_files)))
            if len(skip_log) > 0:
                kwargs['logger'].emit('Files without changes: {}'.format(len(skip_log)))
            if len(change_log) > 0:
                kwargs['logger'].emit('Files copied with changes: {}'.format(len(change_log)))
            if checkDuplicate:
                kwargs['logger'].emit('Number of duplicates found: {}'.format(len(duplicate_log)))
            if len(exclude_files) > 0:
                kwargs['logger'].emit('Number of excluded files: {}'.format(len(exclude_log)))
            if len(self.failed_files) > 0:
                kwargs['logger'].emit('Failed files:')
                for item in self.failed_files:
                    kwargs['logger'].emit('   {}'.format(self.transformText(self.extractPath(item, source), 32)))
            kwargs['logger'].emit('######################')
        if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
            kwargs['updateProgressQT'].emit(100)
        if 'logger' not in kwargs:
            print('Copy {} to {} DONE!'.format(self.transformText(source, 28), self.transformText(dest, 48)))
            print('Success:')
            for item in self.success_files:
                print('   {}'.format(self.transformText(self.extractPath(item, source), 48)))
            print('Failed:')
            for item in self.failed_files:
                print('   {}'.format(self.transformText(self.extractPath(item, source), 48)))
            print('Summary')
            print('Executed %.2f seconds' % (end_time - start_time))
            print('Number of files in Source: {}'.format(source_file_num))
            print('Number of files in Dest: {}'.format(dest_file_num))
            print('Number of folders in Source: {}'.format(source_folder_num))
            print('Number of folders in Dest: {}'.format(dest_folder_num))
            print('Files copied succesfully: {}'.format(len(self.success_files)))
            if len(self.failed_files) > 0:
                print('Files copied failed: {}'.format(len(self.failed_files)))
            if len(skip_log) > 0:
                print('Files without changes: {}'.format(len(skip_log)))
            if len(change_log) > 0:
                print('Files copied with changes: {}'.format(len(change_log)))
            if checkDuplicate:
                print('Number of duplicates found: {}'.format(len(duplicate_log)))
            if len(exclude_files) > 0:
                print('Number of excluded files: {}'.format(len(exclude_log)))

if __name__ == '__main__':
    commands = {'source': '', 'dest': '', 'logs': 'logs', 'checksum': 'md5', 'checkDuplicate': False, 'filenameClean': True, 'exclude':'', 'threadnum': 10}
    for i in range(len(sys.argv)-1):
        try:
            params = sys.argv[i+1].split('=', 1)
            commands[params[0]] = params[1]
            if params[1] == 'True':
                commands[params[0]] = True
            elif params[1] == 'False':
                commands[params[0]] = False
        except Exception as e:
            print(e)
    mover = Mover()
    mover.move(commands['source'], commands['dest'], commands['logs'], commands['checksum'], commands['checkDuplicate'], commands['filenameClean'], commands['exclude'], commands['threadnum'])
