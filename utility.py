from PyQt5 import QtCore

def loadQssFile(file_path):
    """Loads the contents of a styles.qcc file into a string variable.

    Args:
        file_path (str): The path to the styles.qcc file.

    Returns:
        str: The contents of the styles.qcc file as a string.
    """

    try:
        file = QtCore.QFile(file_path)

        if not file.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Text):
            raise IOError("Failed to open styles.qcc file: " + file.errorString())

        data = file.readAll().data()
        file.close()

        return data.decode("utf-8")
    except Exception as e:
        print("Error loading styles.qcc file:", str(e))
        return None

def findPresetByName(presetName, config, presets):
    found = next((preset for preset in presets if preset["name"] == presetName), None)
    if not found:
        raise Exception(
            f'Failed to setup default preset {config["frequencyRange"]}\n'
            f'for {config["location"]} [{config["stationName"]}]\n'
            f'Station\'s "frequencyRange" from stations.json should match existing preset "name" from presets.json'
        )
    return found

def findNextFrequencyFromPreset(preset, frequency, direction):
    foundIndex = preset.index(frequency)
    if foundIndex == -1:
        raise Exception(
            f'Failed to setup default preset for {frequency}'
        )
    nextIndex = foundIndex + direction
    if nextIndex < 0:
        nextIndex = len(preset) - 1
    if nextIndex > (len(preset) - 1):
        nextIndex = 0

    nextFrequency = preset[nextIndex]

    return nextFrequency

def findNextFrequencyByStep(frequency, step, direction, currentPreset):
    intfrequency = int(frequency)
    intstep = int(step)
    nextFrequency = intfrequency + intstep * direction
    minFrequency = int(currentPreset['minFrequency'])
    maxFrequency = int(currentPreset['maxFrequency'])
    if nextFrequency < minFrequency:
        nextFrequency = maxFrequency
    if nextFrequency > maxFrequency:
        nextFrequency = minFrequency

    return str(nextFrequency)

def getRecievedOfRange(recievedStr, range):
    recievedOfRange = dict()
    if range == '1.0':
        recievedFromStr = getRecievedFromStrOld(recievedStr)
        recievedOfRange['frequency'] = ''
        recievedOfRange['rssi'] = recievedFromStr[0]
    else:
        recievedFromStr = getRecievedFromStr(recievedStr)
        if range == '1.2':
            recievedOfRange['frequency'] = recievedFromStr[1][0]
            recievedOfRange['rssi'] = recievedFromStr[1][1]
        if range == '5.8':
            recievedOfRange['frequency'] = recievedFromStr[2][0]
            recievedOfRange['rssi'] = recievedFromStr[2][1]
    return recievedOfRange

def getRecievedFromStr(recievedStr):
    startStr = recievedStr.find('#RSSI')
    startStr2 = recievedStr.find('][')
    lenStr = len(recievedStr)
    recievedList = recievedStr.split('[')
    if len(recievedList) == 3:
        recievedList12 = recievedList[1].split(' ')
        if len(recievedList12) == 2:
            recievedList12[1].replace(']', '')
            recievedList[1] = recievedList12
        endIndex2 = recievedList[2].find(']')
        recievedStr58 = recievedList[2][0:endIndex2]
        recievedList58 = recievedStr58.split(' ')
        if len(recievedList58) == 2:
            recievedList58[1].replace(']', '')
            recievedList[2] = recievedList58
    else:
        recievedList = ['ERORR', '0', '0']
    return recievedList

def getRecievedFromStrOld(recievedStr):
    recievedList = recievedStr.split('\\r\\n')
    if len(recievedList) >= 1:
        recievedList12 = recievedList[0].split(' ')
        if len(recievedList12) == 2:
            #recievedList12[1].replace(']', '')
            recievedList[0] = recievedList12[1]
    else:
        recievedList = ['ERORR', '0', '0']
    return recievedList

def getRecievedFromSerial(recievedStr):
    recievedFromAntennas = dict()
    recievedFromAntennas['rssi1'] = 0
    recievedFromAntennas['rssi2'] = 0
    recievedFromAntennas['rssi3'] = 0

    recievedList = recievedStr.split('&')

    if len(recievedList) > 1:
        recievedStr1 = recievedList[1]
        recievedStr2 = recievedList[2]

    fillrecievedFromAntennas(recievedFromAntennas, recievedStr1)
    fillrecievedFromAntennas(recievedFromAntennas, recievedStr2)

    return recievedFromAntennas

def fillrecievedFromAntennas(recievedFromAntennas, recievedStrIn):
    if recievedStrIn.find('][') > 0:
        #RSSI [1040 1][5865 0]
        recievedStr = recievedStrIn[7:]
        recievedList = recievedStr.split('][')
        recievedStr12 = recievedList[0].split(" ")[1]
        recievedStr58 = recievedList[1].replace("]"," ")
        recievedStr58 = recievedStr58.split(" ")[1]
        recievedFromAntennas['rssi1'] = recievedStr58
        recievedFromAntennas['rssi2'] = recievedStr12
    elif recievedStrIn.find('\\r\\n') > 0:
        #RSSI 928
        recievedStr12 = recievedStrIn.replace("\\r\\n", " ")
        recievedStr12 = recievedStr12.split(" ")[1]
        recievedFromAntennas['rssi3'] = recievedStr12