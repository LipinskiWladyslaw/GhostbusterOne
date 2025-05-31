# This is a sample Python script.
import json
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice, QMetaEnum

from station_widget import Ui_formMain

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

from utility import findPresetByName, findNextFrequencyFromPreset, getRecievedFromStr, getRecievedOfRange, \
    verificationDataFromStr, findNextFrequencyByStep

from reader_thread import FileReaderThread

class IteratorMode(QMetaEnum):
    WithinPreset = 'Within Preset'
    ByStep = 'By Step'

class MainForm(qtw.QWidget):

    updateUI = qtc.pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.iteratorDelayMinimum = 1
        self.iteratorDelayMaximum = 10
        self.defaultIteratorDelay = 3
        self.defaultIteratorMode = IteratorMode.WithinPreset

        self.stationConfig = None
        self.stationWidgets = None
        self.presets = None
        self.isStationMode = False
        self.portlist = []

        with open('frequency_presets.json') as presets_file:
            self.presets = json.load(presets_file)

        with open('valkiria_config.json') as stationConfigFile:
            self.config = json.load(stationConfigFile)

        self.stationWidget = Ui_formMain()

        self.stationWidget.setupUi(self)

        self.playIcon = qtg.QIcon(qtg.QPixmap(':/img/play2.png'))
        self.stopIcon = qtg.QIcon(qtg.QPixmap(':/img/stop2.png'))

        self.frequencyStepOptions = ['1', '5', '10', '20', '40']
        self.stationWidget.periodComboBox.addItems(self.frequencyStepOptions)



        self.currentPreset = findPresetByName(self.config["frequencyRange"], self.config, self.presets)
        self.stationWidget.frequencyComboBox.addItems(self.currentPreset["presetFrequencies"])

        self.stationWidget.rxs = ''
        self.presetFrequencies = self.currentPreset["presetFrequencies"]

        self.stationName = self.config["stationName"]

        self.isLocalModeActive = not self.isStationMode
        self.frequency = self.currentPreset["presetFrequencies"][0]
        self.frequencyHistory = []
        self.frequencyStep = 10
        self.isFrequencyIteratorActive = False
        self.iteratorMode = self.defaultIteratorMode
        self.iterator = None
        self.iteratorDelay = self.defaultIteratorDelay

        self.frequencyStepOptions = ['1', '5', '10', '20', '40']

        self.frequencySpinnerMinimum = int(self.currentPreset["minFrequency"])
        self.frequencySpinnerMaximum = int(self.currentPreset["maxFrequency"])
        self.frequencySpinnerDefaultStep = 10

        self.timerIsStarted = False

        # Sync UI with data
        self.syncUI()


#        if self.isStationMode:
#           self.setupAnthena(self.config["frequencyRange"], self.config["comPort"])

        self.setupHandlers()

        self.timer = qtc.QTimer()
        self.timer.timeout.connect(self.timerEvent)

        self.serial = QSerialPort()
        self.serial.readyRead.connect(self.getDataFromSerial)

        self.updateComport()

    def syncUI(self):
        self.stationWidget.delaySpinBox.setValue(self.iteratorDelay)
        index = self.stationWidget.periodComboBox.findText(str(self.frequencyStep))
        self.stationWidget.periodComboBox.setCurrentIndex(index)

        #-------------------------------------------------------------------------
        if self.iteratorMode == IteratorMode.WithinPreset:
            self.stationWidget.channelRadioButton.setChecked(True)
        elif self.iteratorMode == IteratorMode.ByStep:
            self.stationWidget.periodRadioButton.setChecked(True)
        self.stationWidget.frequencyLCD.display(self.frequency)

    def setupHandlers(self):
        self.stationWidget.updateListComPort.clicked.connect(self.updateComport)
        self.stationWidget.periodComboBox.currentIndexChanged.connect(self.periodComboBoxChanged)
        self.stationWidget.openComPortButton.clicked.connect(self.openSerialPort)
        self.stationWidget.closeComPortButton.clicked.connect(self.closeSerialPort)
        self.stationWidget.saveComPortButton.clicked.connect(self.saveSerialPort)
        #self.stationWidget.openComPortButton.clicked.connect(self.openComPort)

        self.stationWidget.upPushButton.clicked.connect(self.nextFrequency)
        self.stationWidget.downPushButton.clicked.connect(self.prevFrequency)
        self.stationWidget.frequencyComboBox.currentIndexChanged.connect(self.frequencyComboBoxChanged)
        self.stationWidget.playStopPushButton.clicked.connect(self.playStop)
        self.stationWidget.channelRadioButton.clicked.connect(self.checkRadioButton)
        self.stationWidget.periodRadioButton.clicked.connect(self.checkRadioButton)

        self.updateUI.connect(self.syncUI)

    def nextFrequency(self):
        self.nextFrequencyGeneral()
        self.sendDataToSerial()
        #self.getFrequencyFromPreset(self.frequency, 1, True)

    def nextFrequencyGeneral(self):
        self.getFrequencyFromPreset(self.frequency, 1, True)

    def prevFrequency(self):
        self.getFrequencyFromPreset(self.frequency, -1, True)
        self.sendDataToSerial()

    def frequencyComboBoxChanged(self):
        frequency = self.stationWidget.frequencyComboBox.currentText()
        self.getFrequencyFromPreset(frequency, 0, True)
        self.sendDataToSerial()

    def getFrequencyFromPreset(self, frequency, direction, updateUi):
        if self.stationWidget.channelRadioButton.isChecked():
            self.frequency = findNextFrequencyFromPreset(self.presetFrequencies, frequency, direction)
        else:
            self.frequency = findNextFrequencyByStep(frequency, self.stationWidget.periodComboBox.currentText(),
                                                     direction, self.currentPreset)
        if updateUi:
            self.syncUI()
        #self.sendDataToSerial()

    def checkRadioButton(self):
        if self.stationWidget.channelRadioButton.isChecked():
            self.iteratorMode = IteratorMode.WithinPreset
        else:
            self.iteratorMode = IteratorMode.ByStep

    def periodComboBoxChanged(self):
        self.frequencyStep = self.stationWidget.periodComboBox.currentText()

    def updateTimer(self):
        self.timer.stop()
        self.timer.start(self.stationWidget.delaySpinBox.value() * 1000)

    def playStop(self):
        self.timerIsStarted = not self.timerIsStarted
        if self.timerIsStarted:
            icon1 = qtg.QIcon()
            icon1.addPixmap(qtg.QPixmap("img/stop.png"), qtg.QIcon.Active, qtg.QIcon.On)
            self.stationWidget.playStopPushButton.setIcon(icon1)
        else:
            icon1 = qtg.QIcon()
            icon1.addPixmap(qtg.QPixmap("img/play.png"), qtg.QIcon.Active, qtg.QIcon.On)
            self.stationWidget.playStopPushButton.setIcon(icon1)
        self.updateTimer()

    def timerEvent(self):
        if self.timerIsStarted:
            self.nextFrequencyGeneral()
            self.updateUI.emit()
            print(self.frequency)
            self.sendDataToSerial()

    def updateComport(self):
        self.portlist.clear()
        self.stationWidget.comPortComboBox.clear()

        ports = QSerialPortInfo().availablePorts()
        for port in ports:
            self.portlist.append(port.portName())
        self.stationWidget.comPortComboBox.addItems(self.portlist)
        index = self.stationWidget.comPortComboBox.findText(self.config['comPort'])
        if index > -1:
            self.stationWidget.comPortComboBox.setCurrentIndex(index)
            self.openSerialPort()

    def saveSerialPort(self):
        configData = {
            "stationName": self.config["stationName"],
            "location": self.config["location"],
            "frequencyRange": self.config["frequencyRange"],
            "comPort": self.stationWidget.comPortComboBox.currentText(),
        }
        jsonString = json.dumps(configData)
        with open('valkiria_config.json', 'w') as configFile:
            configFile.write(jsonString)

    def openSerialPort(self):
        if self.serial.isOpen():
            self.serial.close()

        port_name = self.stationWidget.comPortComboBox.currentText()
        if self.serial.isOpen():
            self.serial.close()
        self.serial.setPortName(port_name)
        self.serial.setBaudRate(QSerialPort.BaudRate.Baud9600)
        self.serial.setDataBits(QSerialPort.DataBits.Data8)
        self.serial.setParity(QSerialPort.Parity.NoParity)
        self.serial.setStopBits(QSerialPort.StopBits.OneStop)
        self.serial.open(QIODevice.ReadWrite)

    def closeSerialPort(self):
        if self.serial.isOpen():
            self.serial.close()

    def sendDataToSerial(self):
        if self.serial.isOpen():
            if self.frequency != 0:
                data = '#SET ' + str(int(self.frequency))

                #txs = ','.join(map(str, data)) + '\n'
                txs = ','.join(map(str, data))

                self.serial.write(data.encode()) #txs.encode()
                #print(data)

    def getDataFromSerial(self):
        global rxstring, rssi, dataConfig

        indexFirst = -1
        rx = self.serial.readAll()
        try:
            rxs = str(rx)
            rxs = rxs.replace("b", "")
            rxs = rxs.replace("'", "")
            #print(rxs)
            self.stationWidget.rxs = self.stationWidget.rxs + rxs
            verification = verificationDataFromStr(self.stationWidget.rxs)
            #print(self.stationWidget.rxs)
            if verification:
                recieved = getRecievedOfRange(self.stationWidget.rxs, self.config['frequencyRange'])
                self.stationWidget.rxs = ''
                #print(rxs)
                #print(f'frequency - {recieved['frequency']}; rssi - {recieved['rssi']}')
                self.stationWidget.rssiLCD.display(recieved['rssi'])
            if len(self.stationWidget.rxs) > 20:
                self.stationWidget.rxs = ''
        except:
            #rxstring = ''
            print('rx is uncorrect ')
        if self.serial.readBufferSize() > 0:
            self.getDataFromSerial()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = qtw.QApplication([])
    widget = MainForm()
    widget.show()

    app.exec_()