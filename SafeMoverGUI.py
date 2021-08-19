import sys, os, time
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import mover

class Worker(QObject):

    delay = 3
    finished = pyqtSignal()

    def setDelay(self, delay):
        self.delay = delay 

    def run(self):
        time.sleep(self.delay)
        self.finished.emit()

class MoverWorker(QObject):

    finished = pyqtSignal()
    progress = pyqtSignal(int)
    logger = pyqtSignal(object)

    def setParams(self, source, dest, logs, algo):
        self.source = source
        self.dest = dest
        self.logs = logs
        self.algo = algo

    def run(self):
        mover.terminate(False)
        mover.move(self.source, self.dest, self.logs, self.algo, progress=False, updateProgressQT=self.progress, logger=self.logger)
        self.finished.emit()

    def terminate(self):
        mover.terminate(True)

class Window(QWidget):
    def __init__(self):
        super().__init__()
        
        self.copyFlag = False
        self.sourcePath = ''
        self.destPath = ''
        self.logsPath = ''
        self.icon_logo = b'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'
        self.icon_file = b'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'

        self.setWindowTitle('Safe Mover -- NLNZ')
        self.setWindowIcon(self.iconFromBase64(self.icon_logo))
        self.setFixedWidth(580)
        self.setFixedHeight(250)

        self.algoSelector()
        self.SourceDestUI()
        self.logsUI()
        self.progressBar()
        self.msgUI()
        self.copyUI()

    def algoSelector(self):
        self.algo = mover.getAlgo()
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

    def logsUI(self):
        self.logsPath = mover.convertPath(os.getcwd()+'/logs.csv')
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

        self.log_text_box = QPlainTextEdit(self)
        self.log_text_box.setReadOnly(True)
        self.log_text_box.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.log_text_box.move(300, 10)
        self.log_text_box.resize(260, 160)

    def progressBar(self):
        self.pBar = QProgressBar(self)
        self.pBar.setGeometry(10, 170, 240, 20)
        self.pBar.setStyleSheet("QProgressBar::chunk {background-color: green;}")
        self.pBar.setStyleSheet("QProgressBar {background-color: transparent; border: 1px solid grey; border-radius: 5px;}")
        self.pBar.setAlignment(Qt.AlignCenter)
        self.pBar.setVisible(False)

    def msgUI(self):
        self.msgLabel = QLabel(self)
        self.msgLabel.move(10, 170)
        self.msgLabel.resize(260,30)
        self.msgLabel.setAlignment(Qt.AlignCenter)
        self.msgLabel.setVisible(False)

    def copyUI(self):
        self.copyBtn = QPushButton(self)
        self.copyBtn.setText('Copy')
        self.copyBtn.move(100, 200)
        self.copyBtn.resize(60, 30)
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
        self.sourcePath = QFileDialog.getExistingDirectory(self, 'Source file/folder')
        if self.sourcePath != '':
            self.sourceInput.setText(mover.convertPath(self.sourcePath))

    def destSelector(self):
        self.destPath = QFileDialog.getExistingDirectory(self, 'Destination file/folder')
        if self.destPath != '':
            self.destInput.setText(mover.convertPath(self.destPath))

    def logsSelector(self):
        self.logsPath = QFileDialog.getExistingDirectory(self, 'logs file')
        if self.logsPath != '':
            if os.path.isdir(mover.convertPath(self.logsPath)):
                self.logsPath += '/log.csv' 
            self.logsInput.setText(mover.convertPath(self.logsPath))

    def switchAlgo(self):
        self.selected_algo = self.algo[self.algoCombo.currentIndex()]

    def copyFlagFalse(self):
        self.copyFlag = False

    def progressUpdate(self, value):
        self.pBar.setValue(value)

    def loggerHandler(self, value):
        self.log_text_box.appendPlainText(value)

    def copyFolders(self):
        if self.copyFlag:
            self.copyBtn.setText('Copy')
            self.pBar.setVisible(False)
            self.copyFlag = False
            if self.msgWorker:
                self.msgWorker.terminate()
                self.loggerHandler('[TERMINATE] Operation stopped by user')
        else:
            if self.sourcePath != '' and (os.path.isdir(self.sourcePath) or os.path.isfile(self.sourcePath)) and self.destPath != '' and self.logsPath != '':
                
                self.msgThread = QThread()
                self.msgWorker = MoverWorker()
                self.msgWorker.setParams(self.sourcePath, self.destPath, self.logsPath, self.selected_algo)
                self.msgWorker.moveToThread(self.msgThread)
                self.msgThread.started.connect(self.msgWorker.run)
                self.msgWorker.finished.connect(self.msgThread.quit)
                self.msgWorker.finished.connect(self.msgWorker.deleteLater)
                self.msgThread.finished.connect(self.msgThread.deleteLater)
                self.msgWorker.progress.connect(self.progressUpdate)
                self.msgWorker.logger.connect(self.loggerHandler)
                self.msgThread.start()

                self.copyBtn.setText('Cancel')
                self.pBar.setVisible(True)
                self.copyFlag = True
                self.log_text_box.clear()

                self.msgThread.finished.connect(lambda: self.copyBtn.setText('Copy'))
                self.msgThread.finished.connect(lambda: self.pBar.setVisible(False))
                self.msgThread.finished.connect(lambda: self.copyFlagFalse)

            else:
                self.msgThread = QThread()
                self.msgWorker = Worker()
                self.msgWorker.moveToThread(self.msgThread)
                self.msgThread.started.connect(self.msgWorker.run)
                self.msgWorker.finished.connect(self.msgThread.quit)
                self.msgWorker.finished.connect(self.msgWorker.deleteLater)
                self.msgThread.finished.connect(self.msgThread.deleteLater)
                self.msgThread.start()

                self.msgLabel.setText('Please select correct folders/files')
                self.msgLabel.setStyleSheet('color: red;')
                self.msgLabel.setVisible(True)
                
                self.msgThread.finished.connect(lambda: self.msgLabel.setVisible(False))
                self.msgThread.finished.connect(lambda: self.msgLabel.setText(''))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
