# This is a sample Python script.
import json
from itertools import filterfalse

from PyQt5.QtCore import QMetaEnum

from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QIODevice

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from station_widget4 import Ui_formMain

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

from utility import findPresetByName, findNextFrequencyFromPreset, getRecievedFromStr, getRecievedOfRange, \
    findNextFrequencyByStep, getRecievedFromSerial


class IteratorMode(QMetaEnum):
    WithinPreset = 'Within Preset'
    ByStep = 'By Step'

class MainForm(qtw.QWidget):

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

        #This is Main config, there is only comPort
        with open('valkiria_config.json') as stationConfigFile:
            self.config = json.load(stationConfigFile)

        #Here you can find the settings fjr each antenna
        with open('valkiria_config_1.json') as stationConfigFile:
            self.config_1 = json.load(stationConfigFile)

        with open('valkiria_config_2.json') as stationConfigFile:
            self.config_2 = json.load(stationConfigFile)

        with open('valkiria_config_3.json') as stationConfigFile:
            self.config_3 = json.load(stationConfigFile)

        with open('valkiria_config_4.json') as stationConfigFile:
            self.config_4 = json.load(stationConfigFile)

        self.stationWidget = Ui_formMain()

        self.stationWidget.setupUi(self)

        self.playIcon = qtg.QIcon(qtg.QPixmap(':/img/play2.png'))
        self.stopIcon = qtg.QIcon(qtg.QPixmap(':/img/stop2.png'))

        self.frequencyStepOptions = ['1', '5', '10', '20', '40']
        self.stationWidget.periodComboBox.addItems(self.frequencyStepOptions)

        self.stationName = self.config["stationName"]
        self.isLocalModeActive = not self.isStationMode
        self.frequencyStep = 10
        self.iteratorDelay = self.defaultIteratorDelay
        self.frequencyStepOptions = ['1', '5', '10', '20', '40']

        self.currentPreset_1 = findPresetByName(self.config_1["frequencyRange"], self.config_1, self.presets)
        self.presetFrequencies_1 = self.currentPreset_1["presetFrequencies"]
        self.frequency_1 = self.currentPreset_1["presetFrequencies"][0]
        self.iteratorMode_1 = self.defaultIteratorMode
        self.frequencySpinnerMinimum_1 = int(self.currentPreset_1["minFrequency"])
        self.frequencySpinnerMaximum_1 = int(self.currentPreset_1["maxFrequency"])
        self.stationWidget.frequencyComboBox_1.addItems(self.presetFrequencies_1)
        self.stationWidget.groupBox_1.setTitle(self.config_1["stationName"])
        #------------------------------------------------------------------------
        self.currentPreset_2 = findPresetByName(self.config_2["frequencyRange"], self.config_2, self.presets)
        self.presetFrequencies_2 = self.currentPreset_2["presetFrequencies"]
        self.frequency_2 = self.currentPreset_2["presetFrequencies"][0]
        self.iteratorMode_2 = self.defaultIteratorMode
        self.frequencySpinnerMinimum_2 = int(self.currentPreset_2["minFrequency"])
        self.frequencySpinnerMaximum_2 = int(self.currentPreset_2["maxFrequency"])
        self.stationWidget.frequencyComboBox_2.addItems(self.presetFrequencies_2)
        self.stationWidget.groupBox_2.setTitle(self.config_2['stationName'])
        #------------------------------------------------------------------------
        self.currentPreset_3 = findPresetByName(self.config_3["frequencyRange"], self.config_3, self.presets)
        self.presetFrequencies_3 = self.currentPreset_3["presetFrequencies"]
        self.frequency_3 = self.currentPreset_3["presetFrequencies"][0]
        self.iteratorMode_3 = self.defaultIteratorMode
        self.frequencySpinnerMinimum_3 = int(self.currentPreset_3["minFrequency"])
        self.frequencySpinnerMaximum_3 = int(self.currentPreset_3["maxFrequency"])
        self.stationWidget.frequencyComboBox_3.addItems(self.presetFrequencies_3)
        self.stationWidget.groupBox_3.setTitle(self.config_3['stationName'])

        self.timerIsStarted_1 = False
        self.timerIsStarted_2 = False
        self.timerIsStarted_3 = False

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
        if self.iteratorMode_1 == IteratorMode.WithinPreset:
            self.stationWidget.channelRadioButton_1.setChecked(True)
        elif self.iteratorMode_1 == IteratorMode.ByStep:
            self.stationWidget.periodRadioButton_1.setChecked(True)
        self.stationWidget.frequencyLCD_1.display(self.frequency_1)
        #-------------------------------------------------------------------------
        if self.iteratorMode_2 == IteratorMode.WithinPreset:
            self.stationWidget.channelRadioButton_2.setChecked(True)
        elif self.iteratorMode_2 == IteratorMode.ByStep:
            self.stationWidget.periodRadioButton_2.setChecked(True)
        self.stationWidget.frequencyLCD_2.display(self.frequency_2)
        #-------------------------------------------------------------------------
        if self.iteratorMode_3 == IteratorMode.WithinPreset:
            self.stationWidget.channelRadioButton_3.setChecked(True)
        elif self.iteratorMode_3 == IteratorMode.ByStep:
            self.stationWidget.periodRadioButton_3.setChecked(True)
        self.stationWidget.frequencyLCD_3.display(self.frequency_3)

    def setupHandlers(self):
        self.stationWidget.updateListComPort.clicked.connect(self.updateComport)
        #self.stationWidget.openComPortButton.clicked.connect(self.openComPort)

        self.stationWidget.openComPortButton.clicked.connect(self.openSerialPort)
        self.stationWidget.closeComPortButton.clicked.connect(self.closeSerialPort)
        self.stationWidget.periodComboBox.currentIndexChanged.connect(self.periodComboBoxChanged)
        #------------------------------------------------------------------------------------------
        self.stationWidget.upPushButton_1.clicked.connect(self.nextFrequency_1)
        self.stationWidget.downPushButton_1.clicked.connect(self.prevFrequency_1)
        self.stationWidget.frequencyComboBox_1.currentIndexChanged.connect(self.frequencyComboBoxChanged_1)
        self.stationWidget.playStopPushButton_1.clicked.connect(self.playStop_1)
        self.stationWidget.channelRadioButton_1.clicked.connect(self.checkRadioButton_1)
        self.stationWidget.periodRadioButton_1.clicked.connect(self.checkRadioButton_1)
        #------------------------------------------------------------------------------------------
        self.stationWidget.upPushButton_2.clicked.connect(self.nextFrequency_2)
        self.stationWidget.downPushButton_2.clicked.connect(self.prevFrequency_2)
        self.stationWidget.frequencyComboBox_2.currentIndexChanged.connect(self.frequencyComboBoxChanged_2)
        self.stationWidget.playStopPushButton_2.clicked.connect(self.playStop_2)
        self.stationWidget.channelRadioButton_2.clicked.connect(self.checkRadioButton_2)
        self.stationWidget.periodRadioButton_2.clicked.connect(self.checkRadioButton_2)
        #------------------------------------------------------------------------------------------
        self.stationWidget.upPushButton_3.clicked.connect(self.nextFrequency_3)
        self.stationWidget.downPushButton_3.clicked.connect(self.prevFrequency_3)
        self.stationWidget.frequencyComboBox_3.currentIndexChanged.connect(self.frequencyComboBoxChanged_3)
        self.stationWidget.playStopPushButton_3.clicked.connect(self.playStop_3)
        self.stationWidget.channelRadioButton_3.clicked.connect(self.checkRadioButton_3)
        self.stationWidget.periodRadioButton_3.clicked.connect(self.checkRadioButton_3)

    def nextFrequency(self):
        if self.timerIsStarted_1:
            self.getFrequencyFromPreset_1(self.frequency_1, 1, False)
        if self.timerIsStarted_2:
            self.getFrequencyFromPreset_2(self.frequency_2, 1, False)
        if self.timerIsStarted_3:
            self.getFrequencyFromPreset_3(self.frequency_3, 1, False)

    def nextFrequency_1(self, updateUi=True):
        self.getFrequencyFromPreset_1(self.frequency_1, 1, True)

    def nextFrequency_2(self, updateUi=True):
        self.getFrequencyFromPreset_2(self.frequency_2, 1, True)

    def nextFrequency_3(self, updateUi=True):
        self.getFrequencyFromPreset_3(self.frequency_3, 1, True)

    def prevFrequency_1(self):
        self.getFrequencyFromPreset_1(self.frequency_1, -1, True)

    def prevFrequency_2(self):
        self.getFrequencyFromPreset_2(self.frequency_2, -1, True)

    def prevFrequency_3(self):
        self.getFrequencyFromPreset_3(self.frequency_3, -1, True)

    def frequencyComboBoxChanged_1(self):
        frequency = self.stationWidget.frequencyComboBox_1.currentText()
        self.getFrequencyFromPreset_1(frequency, 0, True)

    def frequencyComboBoxChanged_2(self):
        frequency = self.stationWidget.frequencyComboBox_2.currentText()
        self.getFrequencyFromPreset_2(frequency, 0, True)

    def frequencyComboBoxChanged_3(self):
        frequency = self.stationWidget.frequencyComboBox_3.currentText()
        self.getFrequencyFromPreset_3(frequency, 0, True)

    def periodComboBoxChanged(self):
        self.frequencyStep = self.stationWidget.periodComboBox.currentText()

    #--------------------------------------------------------------------------------------------
    def getFrequencyFromPreset_1(self, frequency, direction, updateUi):
        if self.stationWidget.channelRadioButton_1.isChecked():
            self.frequency_1 = findNextFrequencyFromPreset(self.presetFrequencies_1, frequency, direction)
        else:
            self.frequency_1 = findNextFrequencyByStep(frequency, self.stationWidget.periodComboBox.currentText(),
                                                     direction, self.currentPreset_1)
        if updateUi:
            self.syncUI()
        #self.sendDataToSerial()

    #--------------------------------------------------------------------------------------------
    def getFrequencyFromPreset_2(self, frequency, direction, updateUi):
        if self.stationWidget.channelRadioButton_2.isChecked():
            self.frequency_2 = findNextFrequencyFromPreset(self.presetFrequencies_2, frequency, direction)
        else:
            self.frequency_2 = findNextFrequencyByStep(frequency, self.stationWidget.periodComboBox.currentText(),
                                                     direction, self.currentPreset_2)
        if updateUi:
            self.syncUI()
        #self.sendDataToSerial()

    #--------------------------------------------------------------------------------------------
    def getFrequencyFromPreset_3(self, frequency, direction, updateUi):
        if self.stationWidget.channelRadioButton_3.isChecked():
            self.frequency_3 = findNextFrequencyFromPreset(self.presetFrequencies_3, frequency, direction)
        else:
            self.frequency_3 = findNextFrequencyByStep(frequency, self.stationWidget.periodComboBox.currentText(),
                                                     direction, self.currentPreset_3)
        if updateUi:
            self.syncUI()
            self.sendDataToSerial()

    def checkRadioButton_1(self):
        if self.stationWidget.channelRadioButton_1.isChecked():
            self.iteratorMode_1 = IteratorMode.WithinPreset
        else:
            self.iteratorMode_1 = IteratorMode.ByStep

    def checkRadioButton_2(self):
        if self.stationWidget.channelRadioButton_2.isChecked():
            self.iteratorMode_2 = IteratorMode.WithinPreset
        else:
            self.iteratorMode_2 = IteratorMode.ByStep

    def checkRadioButton_3(self):
        if self.stationWidget.channelRadioButton_3.isChecked():
            self.iteratorMode_3 = IteratorMode.WithinPreset
        else:
            self.iteratorMode_3 = IteratorMode.ByStep

    def updateTimer(self):
        '''
        if self.timerIsStarted:
            self.timer.start(self.stationWidget.delaySpinBox.value()*1000)
        else:
            self.timer.stop()
        '''
        self.timer.stop()
        self.timer.start(self.stationWidget.delaySpinBox.value() * 1000)

    def playStop_1(self):
        self.timerIsStarted_1 = not self.timerIsStarted_1
        if self.timerIsStarted_1:
            icon1 = qtg.QIcon()
            icon1.addPixmap(qtg.QPixmap("img/stop.png"), qtg.QIcon.Active, qtg.QIcon.On)
            self.stationWidget.playStopPushButton_1.setIcon(icon1)
        else:
            icon1 = qtg.QIcon()
            icon1.addPixmap(qtg.QPixmap("img/play.png"), qtg.QIcon.Active, qtg.QIcon.On)
            self.stationWidget.playStopPushButton_1.setIcon(icon1)
        self.updateTimer()

    def playStop_2(self):
        self.timerIsStarted_2 = not self.timerIsStarted_2
        if self.timerIsStarted_2:
            icon1 = qtg.QIcon()
            icon1.addPixmap(qtg.QPixmap("img/stop.png"), qtg.QIcon.Active, qtg.QIcon.On)
            self.stationWidget.playStopPushButton_2.setIcon(icon1)
        else:
            icon1 = qtg.QIcon()
            icon1.addPixmap(qtg.QPixmap("img/play.png"), qtg.QIcon.Active, qtg.QIcon.On)
            self.stationWidget.playStopPushButton_2.setIcon(icon1)
        self.updateTimer()

    def playStop_3(self):
        self.timerIsStarted_3 = not self.timerIsStarted_3
        if self.timerIsStarted_3:
            icon1 = qtg.QIcon()
            icon1.addPixmap(qtg.QPixmap("img/stop.png"), qtg.QIcon.Active, qtg.QIcon.On)
            self.stationWidget.playStopPushButton_3.setIcon(icon1)
        else:
            icon1 = qtg.QIcon()
            icon1.addPixmap(qtg.QPixmap("img/play.png"), qtg.QIcon.Active, qtg.QIcon.On)
            self.stationWidget.playStopPushButton_3.setIcon(icon1)
        self.updateTimer()

    def timerEvent(self):
        self.nextFrequency()
        self.syncUI()
        self.sendDataToSerial()
        #print("Frequency 1 - " + self.frequency_1)
        #print("Frequency 2 - " + self.frequency_2)
        #print("Frequency 3 - " + self.frequency_3)

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
            if self.frequency_1 != 0 and self.frequency_2 != 0 and self.frequency_3 != 0:
                data = self.getDataForSerial()

                #txs = ','.join(map(str, data)) + '\n'
                txs = ','.join(map(str, data))

                self.serial.write(data.encode()) #txs.encode()
                #print(data)

    def getDataForSerial(self):
        dataForDoubleAntenna = '{#SET ' + str(int(self.frequency_2)) + ' ' + str(int(self.frequency_1)) + '} '
        dataForSingleAntenna = '[#SET ' + str(int(self.frequency_3)) + ']'
        dataForAntennfs = dataForDoubleAntenna + dataForSingleAntenna

        return dataForAntennfs

    def getDataFromSerial(self):
        rx = self.serial.readAll()
        '''
        try:
            # rxs = str(rx, 'utf-8')
            rxs = str(rx)
            recieved = getRecievedOfRange(rxs, self.config['frequencyRange'])
            #print(rxs)
            #print(f'frequency - {recieved['frequency']}; rssi - {recieved['rssi']}')
            self.stationWidget.rssiLCD.display(recieved['rssi'])
        except:
            self.stationWidget.rssiLCD.display('error')
        '''
        try:
            rxs = str(rx)
            recieved = getRecievedFromSerial(rxs)
            self.stationWidget.rssiLCD_1.display(recieved['rssi1'])
            self.stationWidget.rssiLCD_2.display(recieved['rssi2'])
            self.stationWidget.rssiLCD_3.display(recieved['rssi3'])

        except:
            self.stationWidget.rssiLCD_1.display('error')
            self.stationWidget.rssiLCD_2.display('error')
            self.stationWidget.rssiLCD_3.display('error')
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = qtw.QApplication([])
    widget = MainForm()
    widget.show()

    app.exec_()