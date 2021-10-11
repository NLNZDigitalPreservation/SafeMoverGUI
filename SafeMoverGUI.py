import sys, os, time, platform
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import mover

class Worker(QThread):

    def __init__(self, parent):
        super(Worker, self).__init__()

        self.signals = WorkerSignals()
        self.finished = self.signals.finished
        self.delay = 3

    def setDelay(self, delay):
        self.delay = delay 

    @pyqtSlot()
    def run(self):
        time.sleep(self.delay)
        self.finished.emit()

class WorkerSignals(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    logger = pyqtSignal(object)
    ETA = pyqtSignal(object)
    progressText = pyqtSignal(object)

class MoverWorker(QThread):

    def __init__(self, parent):
        super(MoverWorker, self).__init__()

        self.signals = WorkerSignals()
        self.finished = self.signals.finished
        self.progress = self.signals.progress
        self.logger = self.signals.logger
        self.ETA = self.signals.ETA
        self.progressText = self.signals.progressText
        self.checkDuplicate = False
        self.rename = True
        self.exclusive = ''
        self.mover = mover.Mover()

    def setParams(self, source, dest, logs, algo, checkDuplicate, autoRename, disRename, exclusive):
        self.source = source
        self.dest = dest
        self.logs = logs
        self.algo = algo
        self.checkDuplicate = checkDuplicate
        if autoRename:
            self.rename = True
        if disRename:
            self.rename = False
        self.exclusive = exclusive

    @pyqtSlot()
    def run(self):
        self.mover.terminate(False)
        self.mover.move(self.source, self.dest, self.logs, self.algo, self.checkDuplicate, self.rename, self.exclusive, updateProgressQT=self.progress, logger=self.logger, ETA=self.ETA, progressText=self.progressText)
        self.finished.emit()

    def terminate(self):
        self.mover.terminate(True)

class CheckableComboBox(QComboBox):
    class Delegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(20)
            return size

    def __init__(self, parent):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        palette = qApp.palette()
        palette.setBrush(QPalette.Base, palette.button())
        self.lineEdit().setPalette(palette)
        self.setItemDelegate(CheckableComboBox.Delegate())
        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False
        self.view().viewport().installEventFilter(self)

    def resizeEvent(self, event):
        self.updateText()
        super().resizeEvent(event)

    def eventFilter(self, object, event):
        if object == self.lineEdit():
            if event.type() == QEvent.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return False

        if object == self.view().viewport():
            if event.type() == QEvent.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                item = self.model().item(index.row())

                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                return True
        return False

    def showPopup(self):
        super().showPopup()
        self.closeOnLineEditClick = True

    def hidePopup(self):
        super().hidePopup()
        self.startTimer(100)
        self.updateText()

    def timerEvent(self, event):
        self.killTimer(event.timerId())
        self.closeOnLineEditClick = False

    def updateText(self):
        texts = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                texts.append(self.model().item(i).text())
        text = ",".join(texts)
        metrics = QFontMetrics(self.lineEdit().font())
        elidedText = metrics.elidedText(text, Qt.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elidedText)

    def setPlaceholderText(self, placeholder):
        self.lineEdit().setPlaceholderText(placeholder)

    def addItem(self, text, data=None):
        item = QStandardItem()
        item.setText(text)
        if data is None:
            item.setData(text)
        else:
            item.setData(data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts, datalist=None):
        for i, text in enumerate(texts):
            try:
                data = datalist[i]
            except (TypeError, IndexError):
                data = None
            self.addItem(text, data)

    def text(self):
        res = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                res.append(self.model().item(i).data())
        return res

class Window(QWidget):
    def __init__(self):
        super().__init__()
        
        self.copyFlag = False
        self.sourcePath = ''
        self.destPath = ''
        self.logsPath = ''
        self.icon_file = b'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'
        self.icon_folder = b'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'

        self.msgWorker = None

        self.setWindowTitle('Safe Mover')
        self.setFixedWidth(580)
        self.setFixedHeight(350)

        self.algoSelector()
        self.SourceDestUI()
        self.duplicateUI()
        self.nameCleanUI()
        self.fileExclusion()
        self.logsUI()
        self.progressBar()
        self.msgUI()
        self.copyUI()

    def algoSelector(self):
        self.algo = mover.Mover().getAlgo()
        self.selected_algo = 'md5'
        self.algoLabel = QLabel('Checksum', self)
        self.algoLabel.move(10, 10)
        self.algoLabel.resize(80,30)
        self.algoCombo = QComboBox(self)
        self.algoCombo.addItems(self.algo)
        self.algoCombo.activated.connect(self.switchAlgo)
        self.algoCombo.move(100, 10)
        self.algoCombo.resize(120, 30)

    def SourceDestUI(self):
        self.sourceLabel = QLabel('Source', self)
        self.sourceLabel.move(10, 50)
        self.sourceLabel.resize(80,30)
        self.sourceInput = QLineEdit(self)
        self.sourceInput.setStyleSheet("border: 1px solid grey; border-radius: 5px;")
        self.sourceInput.textChanged.connect(self.setSourcePath)
        self.sourceInput.move(100, 50)
        self.sourceInput.resize(120, 30)
        self.sourceBtn = QPushButton(self)
        self.sourceBtn.setIcon(self.iconFromBase64(self.icon_file))
        self.sourceBtn.clicked.connect(self.sourceSelector)
        self.sourceBtn.move(230, 50)
        self.sourceBtn.resize(30, 30)
        self.openSourceBtn = QPushButton(self)
        self.openSourceBtn.setIcon(self.iconFromBase64(self.icon_folder))
        self.openSourceBtn.clicked.connect(self.sourceOpen)
        self.openSourceBtn.move(265, 50)
        self.openSourceBtn.resize(30, 30)

        self.destLabel = QLabel('Destination', self)
        self.destLabel.move(10, 90)
        self.destLabel.resize(80,30)
        self.destInput = QLineEdit(self)
        self.destInput.setStyleSheet("border: 1px solid grey; border-radius: 5px;")
        self.destInput.textChanged.connect(self.setDestPath)
        self.destInput.move(100, 90)
        self.destInput.resize(120, 30)
        self.destBtn = QPushButton(self)
        self.destBtn.setIcon(self.iconFromBase64(self.icon_file))
        self.destBtn.clicked.connect(self.destSelector)
        self.destBtn.move(230, 90)
        self.destBtn.resize(30, 30)
        self.openDestBtn = QPushButton(self)
        self.openDestBtn.setIcon(self.iconFromBase64(self.icon_folder))
        self.openDestBtn.clicked.connect(self.destOpen)
        self.openDestBtn.move(265, 90)
        self.openDestBtn.resize(30, 30)

    def duplicateUI(self):
        self.dupliLabel = QLabel('Duplication', self)
        self.dupliLabel.move(10, 165)
        self.dupliLabel.resize(80,26)

        self.d1 = QCheckBox("Identify", self)
        self.d1.setChecked(True)
        self.d1.move(100, 165)
        self.d1.resize(80,26)

        self.d2 = QCheckBox("Keep Only One", self)
        self.d2.setVisible(False)
        self.d2.move(175, 165)
        self.d2.resize(130,26)

    def nameCleanUI(self):
        self.cleanLabel = QLabel('Filename Cleaning', self)
        self.cleanLabel.setWordWrap(True)
        self.cleanLabel.move(10, 190)
        self.cleanLabel.resize(80, 35)

        self.autoCleanBtn = QRadioButton(self)
        self.autoCleanBtn.setText('Auto')
        self.autoCleanBtn.setChecked(True)
        self.autoCleanBtn.move(100, 190)
        self.autoCleanBtn.resize(60, 30)

        self.disCleanBtn = QRadioButton(self)
        self.disCleanBtn.setText('Disabled')
        self.disCleanBtn.move(175, 190)
        self.disCleanBtn.resize(100, 30)

        self.cleanBtnGrp = QButtonGroup(self)
        self.cleanBtnGrp.addButton(self.autoCleanBtn, 1)
        self.cleanBtnGrp.addButton(self.disCleanBtn, 2)        

    def fileExclusion(self):
        self.excludeLabel = QLabel('Exclusive', self)
        self.excludeLabel.move(10, 225)
        self.excludeLabel.resize(80, 26)

        # self.excludeInput = QLineEdit(self)
        # self.excludeInput.setStyleSheet("border: 1px solid grey; border-radius: 5px;")
        # self.excludeInput.setPlaceholderText('*.exe,*.txt')
        # self.excludeInput.move(100, 225)
        # self.excludeInput.resize(120, 30)
        exclusive = ['hidden/system files', '.thumbs_db', '.exe']
        self.excludeInput = CheckableComboBox(self)
        self.excludeInput.addItems(exclusive)
        self.excludeInput.setPlaceholderText('Empty')
        self.excludeInput.move(100, 225)
        self.excludeInput.resize(195, 30)

    def logsUI(self):
        self.logsPath = mover.Mover().convertPath(os.getcwd())
        self.logsLabel = QLabel('Logs', self)
        self.logsLabel.move(10, 130)
        self.logsLabel.resize(80,30)
        self.logsInput = QLineEdit(self)
        self.logsInput.setStyleSheet("border: 1px solid grey; border-radius: 5px;")
        self.logsInput.textChanged.connect(self.setLogsPath)
        self.logsInput.move(100, 130)
        self.logsInput.resize(120, 30)
        self.logsInput.setText(self.logsPath)
        self.logsBtn = QPushButton(self)
        self.logsBtn.setIcon(self.iconFromBase64(self.icon_file))
        self.logsBtn.clicked.connect(self.logsSelector)
        self.logsBtn.move(230, 130)
        self.logsBtn.resize(30, 30)
        self.openLogsBtn = QPushButton(self)
        self.openLogsBtn.setIcon(self.iconFromBase64(self.icon_folder))
        self.openLogsBtn.clicked.connect(self.logsOpen)
        self.openLogsBtn.move(265, 130)
        self.openLogsBtn.resize(30, 30)

        self.log_text_box = QPlainTextEdit(self)
        self.log_text_box.setReadOnly(True)
        self.log_text_box.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.log_text_box.move(300, 10)
        self.log_text_box.resize(260, 320)

    def progressBar(self):
        self.pBar = QProgressBar(self)
        self.pBar.setGeometry(10, 280, 200, 20)
        self.pBar.setStyleSheet("QProgressBar::chunk {background-color: green;}")
        self.pBar.setStyleSheet("QProgressBar {background-color: transparent; border: 1px solid grey; border-radius: 5px;}")
        self.pBar.setAlignment(Qt.AlignCenter)
        self.pBar.setVisible(False)

        self.ETA = QLabel(self)
        self.ETA.move(220, 280)
        self.ETA.resize(120, 20)
        self.ETA.setText('')

        self.progressText = QLabel(self)
        self.progressText.move(10, 250)
        self.progressText.resize(560, 30)
        self.progressText.setText('')

    def msgUI(self):
        self.msgLabel = QLabel(self)
        self.msgLabel.move(10, 255)
        self.msgLabel.resize(260,30)
        self.msgLabel.setAlignment(Qt.AlignCenter)
        self.msgLabel.setVisible(False)

    def copyUI(self):
        self.copyBtn = QPushButton(self)
        self.copyBtn.setText('Start')
        self.copyBtn.move(90, 305)
        self.copyBtn.resize(80, 36)
        self.copyBtn.clicked.connect(self.copyFolders)

    def iconFromBase64(self, base64):
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray.fromBase64(base64))
        icon = QIcon(pixmap)
        return icon

    def setSourcePath(self, text):
        self.sourcePath = text
    
    def setDestPath(self, text):
        self.destPath = text
    
    def setLogsPath(self, text):
        self.logsPath = text

    def sourceSelector(self):
        self.sourcePath = self.getOpenFilesAndDirs()
        if len(self.sourcePath) > 0:
            self.sourcePath = self.sourcePath[0]
            self.sourceInput.setText(mover.Mover().convertPath(self.sourcePath))

    def sourceOpen(self):
        if self.sourcePath != '':
            if os.path.isfile(self.sourcePath):
                filepath = os.path.dirname(self.sourcePath)
            else:
                filepath = self.sourcePath
            if platform.system() == 'Windows':
                os.system(f'start {os.path.realpath(filepath)}')
            else:
                os.system('xdg-open "%s"' % filepath)
        else:
            if platform.system() == 'Windows':
                os.system(f'start {os.path.realpath(os.getcwd())}')
            else:
                os.system('xdg-open "%s"' % os.getcwd())

    def destSelector(self):
        self.destPath = self.getOpenFilesAndDirs()
        if len(self.destPath) > 0:
            self.destPath = self.destPath[0]
            self.destInput.setText(mover.Mover().convertPath(self.destPath))

    def destOpen(self):
        if self.destPath != '':
            if os.path.isfile(self.destPath):
                filepath = os.path.dirname(self.destPath)
            else:
                filepath = self.destPath
            if platform.system() == 'Windows':
                os.system(f'start {os.path.realpath(filepath)}')
            else:
                os.system('xdg-open "%s"' % filepath)
        else:
            if platform.system() == 'Windows':
                os.system(f'start {os.path.realpath(os.getcwd())}')
            else:
                os.system('xdg-open "%s"' % os.getcwd())
            

    def logsSelector(self):
        self.logsPath = self.getOpenDirs()
        if len(self.logsPath) > 0:
            self.logsPath = self.logsPath[0] 
            self.logsInput.setText(mover.Mover().convertPath(self.logsPath))
    
    def logsOpen(self):
        if self.logsPath != '':
            if os.path.isfile(self.logsPath):
                filepath = os.path.dirname(self.logsPath)
            else:
                filepath = self.logsPath
            if platform.system() == 'Windows':
                os.system(f'start {os.path.realpath(filepath)}')
            else:
                os.system('xdg-open "%s"' % filepath)

    def getOpenFilesAndDirs(parent=None, caption='', directory='', filter='', initialFilter='', options=None):
        def updateText():
            selected = []
            for index in view.selectionModel().selectedRows():
                selected.append('{}'.format(index.data()))
            lineEdit.setText(' '.join(selected))

        dialog = QFileDialog(parent, windowTitle=caption)
        dialog.setFileMode(dialog.ExistingFiles)
        if options:
            dialog.setOptions(options)
        dialog.setOption(dialog.DontUseNativeDialog, True)
        if directory:
            dialog.setDirectory(directory)
        if filter:
            dialog.setNameFilter(filter)
            if initialFilter:
                dialog.selectNameFilter(initialFilter)
        dialog.accept = lambda: QDialog.accept(dialog)
        stackedWidget = dialog.findChild(QStackedWidget)
        view = stackedWidget.findChild(QListView)
        view.selectionModel().selectionChanged.connect(updateText)

        lineEdit = dialog.findChild(QLineEdit)
        dialog.directoryEntered.connect(lambda: lineEdit.setText(''))

        dialog.exec_()
        return dialog.selectedFiles()

    def getOpenDirs(parent=None, caption='', directory='', filter='', initialFilter='', options=None):
        def updateText():
            selected = []
            for index in view.selectionModel().selectedRows():
                selected.append('{}'.format(index.data()))
            lineEdit.setText(' '.join(selected))

        dialog = QFileDialog(parent, windowTitle=caption)
        dialog.setFileMode(dialog.DirectoryOnly)
        if options:
            dialog.setOptions(options)
        dialog.setOption(dialog.DontUseNativeDialog, True)
        if directory:
            dialog.setDirectory(directory)
        if filter:
            dialog.setNameFilter(filter)
            if initialFilter:
                dialog.selectNameFilter(initialFilter)
        dialog.accept = lambda: QDialog.accept(dialog)
        stackedWidget = dialog.findChild(QStackedWidget)
        view = stackedWidget.findChild(QListView)
        view.selectionModel().selectionChanged.connect(updateText)

        lineEdit = dialog.findChild(QLineEdit)
        dialog.directoryEntered.connect(lambda: lineEdit.setText(''))

        dialog.exec_()
        return dialog.selectedFiles()

    def switchAlgo(self):
        self.selected_algo = self.algo[self.algoCombo.currentIndex()]

    def setCopyFlag(self, value):
        self.copyFlag = value

    def progressUpdate(self, value):
        self.pBar.setValue(value)

    def loggerHandler(self, value):
        self.log_text_box.appendPlainText(value)

    def ETAUpdate(self, value):
        self.ETA.setText('ETA: '+str(value))
    
    def progressTextUpdate(self, value):
        self.progressText.setText(str(value))

    def finishMoverWorker(self):
        self.setCopyFlag(False)
        self.copyBtn.setText('Start')
        self.pBar.setVisible(False)
        self.ETA.setText('')
        self.progressText.setText('')
        self.msgWorker.quit()

    def finishWorker(self):
        self.msgLabel.setVisible(False)
        self.msgLabel.setText('')

    def exclusiveConvert(self, lists):
        pattern = {'hidden/system files':'**/.*','.thumbs_db':'**.thumbs_db','.exe':'**.exe'}
        exclusive = []
        for item in lists:
            exclusive.append(pattern[item])
        return ','.join(exclusive)

    def copyFolders(self):
        if self.copyFlag:
            self.copyBtn.setText('Start')
            self.pBar.setVisible(False)
            self.copyFlag = False
            if self.msgWorker:
                self.msgWorker.terminate()
                self.ETA.setText('')
                self.progressText.setText('')
        else:
            if self.sourcePath != '' and (os.path.isdir(self.sourcePath) or os.path.isfile(self.sourcePath)) and self.destPath != '' and self.logsPath != '':
                if self.msgWorker:
                    self.msgWorker.quit()
                    self.msgWorker = None

                self.msgWorker = MoverWorker(self)
                self.msgWorker.setParams(self.sourcePath, self.destPath, self.logsPath, self.selected_algo, self.d1.isChecked(), self.autoCleanBtn.isChecked(), self.disCleanBtn.isChecked(), self.exclusiveConvert(self.excludeInput.text()))
                self.msgWorker.finished.connect(self.finishMoverWorker)
                self.msgWorker.progress.connect(self.progressUpdate)
                self.msgWorker.logger.connect(self.loggerHandler)
                self.msgWorker.ETA.connect(self.ETAUpdate)
                self.msgWorker.progressText.connect(self.progressTextUpdate)
                
                self.copyBtn.setText('Cancel')
                self.pBar.setVisible(True)
                self.copyFlag = True
                self.log_text_box.clear()

                self.msgWorker.start()

            else:
                if self.msgWorker:
                    self.msgWorker.quit()
                    self.msgWorker = None

                self.msgWorker = Worker(self)
                self.msgWorker.setDelay(5)
                self.msgWorker.finished.connect(self.finishWorker)

                self.msgLabel.setText('Please select correct folders/files')
                self.msgLabel.setStyleSheet('color: red;')
                self.msgLabel.setVisible(True)

                self.msgWorker.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
