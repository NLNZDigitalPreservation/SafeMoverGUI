from posixpath import realpath
import sys, string, os, shutil, time, stat, platform, csv, math
from hashlib import md5, sha1, sha224, sha256, sha384, sha512, blake2b, blake2s
import progressbar
from tqdm import tqdm

success_files = []
failed_files = []
bar = progressbar.ProgressBar(maxval=100, redirect_stdout=True, widgets=[progressbar.Bar('=','[',']'), ' ', progressbar.Percentage()])
threadStop = False

def string_cleaner(original_str):
    clean_string = str(original_str)
    if clean_string.startswith("u'") and clean_string.endswith("'"):
        clean_string = clean_string[2:-1]
    return clean_string

def illegal_chars_handler(original_str):
    special_chars = ['?','<','>',':','*','|','^']
    printable = set(string.printable)
    replace_chars = {ord(c):'_' for c in special_chars}
    final_str = [original_str.translate(replace_chars), original_str[:2]+original_str[2:].translate(replace_chars)][platform.system() == 'Windows']
    final_str = ''.join(filter(lambda x: x in printable, final_str))
    return final_str

def getListOfFiles(root_path):
    files = []
    if os.path.isdir(root_path):
        listOfFile = os.listdir(root_path)
        for file in listOfFile:
            fullPath = os.path.join(root_path, file)
            if os.path.isdir(fullPath):
                files += getListOfFiles(convertPath(fullPath))
            else:
                files.append(convertPath(fullPath))
    else:
        files.append(convertPath(root_path))
    return files

def convertPath(originalPath):
    if platform.system() == 'Windows':
        p = originalPath.replace('/','\\')
    else:
        p = originalPath
    return p

def getSourceDestList(source, dest):
    source_files = getListOfFiles(source)
    lists = []
    for item in source_files:
        if item == source:
            lists.append({'source': convertPath(item), 'dest': convertPath(illegal_chars_handler(string_cleaner(dest)))})
        else:
            lists.append({'source': convertPath(item), 'dest': convertPath(illegal_chars_handler(string_cleaner(appendPath(extractPath(item, source), dest))))})
    return lists

def getFailedList(failed_lists, source, dest):
    lists = []
    for item in failed_lists:
        if item == source:
            lists.append({'source': convertPath(item), 'dest': convertPath(illegal_chars_handler(string_cleaner(dest)))})
        else:
            lists.append({'source': convertPath(item), 'dest': convertPath(illegal_chars_handler(string_cleaner(appendPath(extractPath(item, source), dest))))})
    return lists

def removeFromList(lists, item):
    return list(filter(lambda x: x!=item and not x.endswith('/'+item), lists))

def getAlgo():
    return ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512', 'blake2b', 'blake2s']

def getFileHash(filename, checksum='md5'):
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

def getMetadata(file):
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
    return readableTime(access), readableTime(modify), readableTime(create), mode, size

def readableTime(timestamp):
    return time.ctime(timestamp)

def extractPath(file, path):
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

def appendPath(file, path):
    if path[-1] != '/':
        path += '/'
    return path+file

def copy(source, dest):
    try:
        if os.path.isdir(os.path.dirname(dest)) is not True:
            foldermode = stat.S_IMODE(os.stat(os.path.dirname(source)).st_mode)
            os.makedirs(os.path.dirname(dest), mode = foldermode)
        shutil.copy2(source, dest)
        global success_files
        success_files.append(source)
        return True
    except:
        global failed_files
        failed_files.append(source)
        return False

def compare(source, dest, checksum='md5'):
    checksum1 = getFileHash(source, checksum)
    checksum2 = getFileHash(dest, checksum)
    access1, modify1, create1, size1 = getMetadata(source)
    access2, modify2, create2, size2 = getMetadata(dest)
    if checksum1 == checksum2 and modify1 == modify2 and size1 == size2:
        return True
    else:
        return False

def terminate(value):
    global threadStop
    if value:
        threadStop = True
    else:
        threadStop = False

def filenameCheck(source, dest):
    if os.path.basename(source) == os.path.basename(dest):
        return True
    else:
        return False

def countFileFolder(folderpath):
    totalFiles = 0
    totalDirs = 0
    for base, dirs, files in os.walk(folderpath):
        for dir in dirs:
            totalDirs += 1
        for file in files:
            totalFiles += 1
    return totalFiles, totalDirs

def getETA(t):
    if t > 60:
        return '{} min {} sec'.format(math.floor(t/60), t%60)
    else:
        return '{} sec'.format(t)

def transformText(text, size):
    result = text
    if len(str(text)) > size and size > 12:
        result = str(text)[:int((size/2)-6)] + ' ... ' + str(text)[int(-1*(size/2)-3):]
    return result

def copyFile(params):
    QTprogressText = None
    QTlogger = None
    log_line = []
    try:
        source = params[0]
        dest = params[1]
        checksum = params[2]
        sourcePath = params[3]
        QT = params[4]
        if QT:
            QTprogressText = 'Copying {}'.format(transformText(source, 24))
        else: 
            print('Copying {}'.format(transformText(source, 48)))
        t = time.ctime()
        copy(source, dest)
        checksum1 = getFileHash(source, checksum)
        checksum2 = getFileHash(dest, checksum)
        access1, modify1, create1, mode1, size1 = getMetadata(source)
        access2, modify2, create2, mode2, size2 = getMetadata(dest)
        if checksum1 == checksum2 and modify1 == modify2 and size1 == size2:
            if QT:
                QTlogger = transformText('{}'.format(extractPath(source, sourcePath)), 28)
            log_line = 	['SUCCES', t, source, dest, filenameCheck(source, dest), checksum, checksum1, checksum2, checksum1 == checksum2, size1, size2, size1 == size2, mode1, mode2, modify1, modify2, modify1 == modify2, create1, create2, access1, access2]
        else:
            if QT:
                QTlogger = transformText('{}'.format(extractPath(source, sourcePath)), 28)
            log_line = 	['FAILED', t, source, dest, filenameCheck(source, dest), checksum, checksum1, checksum2, checksum1 == checksum2, size1, size2, size1 == size2, mode1, mode2, modify1, modify2, modify1 == modify2, create1, create2, access1, access2]
    except:
        if QT:
            QTlogger = transformText('{}'.format(extractPath(source, source)), 28)
        log_line = 	['FAILED', t, source, dest, filenameCheck(source, dest), '', '', '','','', '', '', '', '', '', '', '', '', '', '', '']
        pass
    return (QTprogressText, QTlogger, log_line)

def move(source, dest, logs='logs.csv', checksum='md5', **kwargs):
    start_time = time.time()
    if 'logger' in kwargs and kwargs['logger'] != None:
        kwargs['logger'].emit(transformText('Read files in {}'.format(source), 28))
    else:
        print(transformText('Read files in {}'.format(source), 28))
    if 'progressText' in kwargs and kwargs['progressText'] != None:
        kwargs['progressText'].emit(transformText('Reading source file/folder ...', 28))
    else:
        print(transformText('Reading source file/folder ...', 28))
    if 'ETA' in kwargs and kwargs['ETA'] != None:
        kwargs['ETA'].emit('-')
    lists = getSourceDestList(source, dest)
    size = len(lists)
    if 'progress' in kwargs and kwargs['progress']:
        bar.start()
        bar.update(0)
    if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
        kwargs['updateProgressQT'].emit(0)
    if 'logger' in kwargs and kwargs['logger'] != None:
        kwargs['logger'].emit('######################')
    copy_speed = 200000000
    source_file_num, source_folder_num = countFileFolder(source)

    log_line = 	['Status', 'Time', 'Source_path', 'Dest_path', 'Filename_check', 'Hash_method', 'Source_hash', 'Dest_hash', 'Hash_check', 'Source_size', 'Dest_size', 'Size_check', 'Source_file_permission', 'Dest_file_permission', 'Source_modified_date', 'Dest_modified_date', 'Modified_check', 'Source_created_date', 'Dest_created_date', 'Source_accessed_date', 'Dest_accessed_date']
    logFile = open(logs, "w")
    writer = csv.writer(logFile, delimiter=',', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
    writer.writerow(log_line)
    t = tqdm(map(copyFile, [(lists[i]['source'], lists[i]['dest'], checksum, source, True) for i in range(size)]), total=size)
    for i in t:
        if i[0] != None:
            kwargs['progressText'].emit(i[0])
        if i[1] != None:
            kwargs['logger'].emit(i[1])
        if i[2] != '':
            writer.writerow(i[2])
        s = str(t).split()
        if len(s) > 4:
            count = int(s[2].split('/')[0])
            remaining = s[3].split('<')[1][:-1]
            if 'progress' in kwargs and kwargs['progress']:
                bar.update(int((count)*100/size))
            if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
                kwargs['updateProgressQT'].emit(int((count)*100/size))
            if 'ETA' in kwargs and kwargs['ETA'] != None and remaining != '?':
                kwargs['ETA'].emit(remaining)
        elif len(s) == 4:
            count = int(s[1].split('/')[0])
            remaining = s[2].split('<')[1][:-1]
            if 'progress' in kwargs and kwargs['progress']:
                bar.update(int((count)*100/size))
            if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
                kwargs['updateProgressQT'].emit(int((count)*100/size))
            if 'ETA' in kwargs and kwargs['ETA'] != None and remaining != '?':
                kwargs['ETA'].emit(remaining)
        if threadStop:
            # shutil.rmtree(dest)
            # shutil.rmtree(logs)
            break
    global failed_files
    retry = 3
    while len(failed_files) > 0 and retry > 0:
        if 'progressText' in kwargs and kwargs['progressText'] != None:
            kwargs['progressText'].emit('Retry {} time(s) copy failed files again ...'.format((4-retry)))
        else:
            print('Retry {} time(s) copy failed files again ...'.format((4-retry)))
        if 'ETA' in kwargs and kwargs['ETA'] != None:
            kwargs['ETA'].emit('-')
        lists = getFailedList(failed_files, source, dest)
        failed_files = []
        size = len(lists)
        t = tqdm(map(copyFile, [(lists[i]['source'], lists[i]['dest'], checksum, source, True) for i in range(size)]), total=size)
        for i in t:
            if i[0] != None:
                kwargs['progressText'].emit(i[0])
            if i[1] != None:
                kwargs['logger'].emit(i[1])
            if i[2] != '':
                writer.writerow(i[2])
            s = str(t).split()
            if len(s) > 4:
                count = int(s[2].split('/')[0])
                remaining = s[3].split('<')[1][:-1]
                if 'progress' in kwargs and kwargs['progress']:
                    bar.update(int((count)*100/size))
                if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
                    kwargs['updateProgressQT'].emit(int((count)*100/size))
                if 'ETA' in kwargs and kwargs['ETA'] != None and remaining != '?':
                    kwargs['ETA'].emit(remaining)
            elif len(s) == 4:
                count = int(s[1].split('/')[0])
                remaining = s[2].split('<')[1][:-1]
                if 'progress' in kwargs and kwargs['progress']:
                    bar.update(int((count)*100/size))
                if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
                    kwargs['updateProgressQT'].emit(int((count)*100/size))
                if 'ETA' in kwargs and kwargs['ETA'] != None and remaining != '?':
                    kwargs['ETA'].emit(remaining)
            if threadStop:
            #     shutil.rmtree(dest)
            #     shutil.rmtree(logs)
                break
        retry -= 1

    logFile.close()
    end_time = time.time()
    
    dest_file_num, dest_folder_num = countFileFolder(source)
    if 'logger' in kwargs and kwargs['logger'] != None:
        kwargs['logger'].emit('######################')
        kwargs['logger'].emit('Summary')
        kwargs['logger'].emit('Executed %.2f seconds' % (end_time - start_time))
        kwargs['logger'].emit('Source files number {}'.format(source_file_num))
        kwargs['logger'].emit('Dest files number {}'.format(dest_file_num))
        kwargs['logger'].emit('Source folders number {}'.format(source_folder_num))
        kwargs['logger'].emit('Dest folders number {}'.format(dest_folder_num))
        kwargs['logger'].emit('Success to copy {} files'.format(len(success_files)))
        kwargs['logger'].emit('Failed to copy {} files'.format(len(failed_files)))
        if len(failed_files) > 0:
            kwargs['logger'].emit('Failed files:')
            for item in failed_files:
                kwargs['logger'].emit('   {}'.format(transformText(extractPath(item, source), 24)))
    if 'progress' in kwargs and kwargs['progress']:
        bar.update(100)
        bar.finish()
    if 'updateProgressQT' in kwargs and kwargs['updateProgressQT'] != None:
        kwargs['updateProgressQT'].emit(100)
    if 'logger' not in kwargs:
        print('Copy {} to {} DONE!'.format(transformText(source, 28), transformText(dest, 28)))
        print('Success:')
        for item in success_files:
            print('   {}'.format(transformText(extractPath(item, source), 48)))
        print('Failed:')
        for item in failed_files:
            print('   {}'.format(transformText(extractPath(item, source), 48)))

if __name__ == '__main__':
    commands = {'source': '', 'dest': '', 'logs': 'logs.csv', 'checksum': 'md5', 'progress': True}
    for i in range(len(sys.argv)-1):
        try:
            params = sys.argv[i+1].split('=', 1)
            commands[params[0]] = params[1]
        except Exception as e:
            print(e)
    move(commands['source'], commands['dest'], commands['logs'], commands['checksum'], progress=commands['progress'])
