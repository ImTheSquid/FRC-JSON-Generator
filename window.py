import json
import sys

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QPushButton, QLineEdit, QComboBox, QGroupBox, \
    QVBoxLayout, QWidget, QLabel, QHBoxLayout, QSpinBox, QTableWidget, QHeaderView, QTableWidgetItem, QMessageBox, \
    QCheckBox, QApplication


def find_profile_index(pilot, text_key):
    for index, key in enumerate(pilot.keys()):
        if key == text_key:
            return index
    return -1


def add_dict_bulk(dictionary, index, src):
    for val in src.keys():
        if index == len(dictionary):
            dictionary[index].append({})
        dictionary[index].update({src.get(val)[0]: src.get(val)[1]})


# noinspection PyArgumentList
class MainWin(QWidget):

    # Comments will probably be added later

    def __init__(self):
        super().__init__()

        # Data storage
        self.driverMap = {}
        self.gunnerMap = {}
        self.dProfileMapXbox = [{}]
        self.dProfileMapJoystick = [{}]
        self.gProfileMapXbox = [{}]
        self.gProfileMapJoystick = [{}]

        # Init interface
        mainLayout = QHBoxLayout()
        leftHalf = QGroupBox('Controller Info')
        rightHalf = QGroupBox('Assigned Maps')

        vertLeft = QVBoxLayout()
        vertLeft.setStretch(0, 0)
        vertLeft.setSpacing(2)
        vertLeft.addWidget(QLabel('Profile Name'))
        self.profileName = QLineEdit()
        self.profileName.textEdited.connect(self.update_submit)

        vertLeft.addWidget(self.profileName)

        typeChoosers = QHBoxLayout()
        self.pilot = QComboBox()
        self.pilot.addItems(['Driver', 'Gunner'])
        typeChoosers.addWidget(self.pilot)
        self.controller = QComboBox()
        self.controller.addItems(['Xbox Compatible', 'Joystick'])
        typeChoosers.addWidget(self.controller)
        vertLeft.addLayout(typeChoosers)

        keyConfig = QHBoxLayout()
        keys = QVBoxLayout()
        keys.addWidget(QLabel('Key'))
        self.key = QLineEdit()
        self.key.textEdited.connect(self.update_submit)
        keys.addWidget(self.key)
        ports = QVBoxLayout()
        ports.addWidget(QLabel('Port'))
        self.port = QSpinBox()
        self.port.setFixedWidth(110)
        ports.addWidget(self.port)
        keyConfig.addLayout(keys)
        keyConfig.addLayout(ports)
        vertLeft.addLayout(keyConfig)
        vertLeft.addStretch()

        importJSON = QPushButton()
        importJSON.setText('Import from JSON')
        importJSON.clicked.connect(self.import_json)
        self.submit = QPushButton()
        self.submit.setText('Add Entry to List')
        self.submit.clicked.connect(self.process_data)
        self.submit.setEnabled(False)
        vertLeft.addWidget(self.submit)
        vertLeft.addWidget(importJSON)

        leftHalf.setLayout(vertLeft)
        mainLayout.addWidget(leftHalf)
        self.profileList = QTableWidget(0, 2)

        rightVert = QVBoxLayout()
        rightVert.setSpacing(2)
        self.profiles = QComboBox()
        self.profiles.addItems(self.get_profile_names('driver'))
        self.profiles.currentTextChanged.connect(self.update_list)
        self.profiles.setEnabled(False)
        listSelectors = QHBoxLayout()
        listSelectors.addWidget(self.profiles)
        self.pilotSource = QComboBox()
        self.pilotSource.addItems(['Driver', 'Gunner'])
        self.pilotSource.currentTextChanged.connect(self.update_profiles)
        self.controllerSource = QComboBox()
        self.controllerSource.addItems(['Xbox Compatible', 'Joystick'])
        self.controllerSource.currentTextChanged.connect(self.update_list)
        rightVert.addWidget(self.pilotSource)
        listSelectors.addWidget(self.controllerSource)

        rightVert.addLayout(listSelectors)

        # Table
        self.reset_table()
        rightVert.addWidget(self.profileList)
        rightVert.addStretch()

        listControls = QHBoxLayout()
        self.removeItem = QPushButton('Remove Entry')
        self.removeItem.setDisabled(True)
        self.removeItem.clicked.connect(self.remove_list_item)
        listControls.addWidget(self.removeItem)
        self.removeProfile = QPushButton('Remove Profile')
        self.removeProfile.setDisabled(True)
        self.removeProfile.clicked.connect(self.remove_profile)

        listControls.addWidget(self.removeProfile)
        self.export = QPushButton("Export to JSON")
        self.export.clicked.connect(self.export_json)
        self.export.setEnabled(True)
        rightVert.addLayout(listControls)
        rightVert.addWidget(self.export)

        rightHalf.setLayout(rightVert)
        mainLayout.addWidget(rightHalf)

        self.init_gui(mainLayout)

    def init_gui(self, layout):
        # Init the basic window frame
        self.setWindowTitle('JSON Controller Profile Configuration Tool v.2.3')
        self.setWindowIcon(QIcon('icon.png'))
        self.setLayout(layout)
        self.show()

    def update_profiles(self):
        self.profiles.clear()
        self.profiles.addItems(
            self.get_profile_names('driver' if self.pilotSource.currentText() == 'Driver' else 'gunner'))
        self.profiles.setEnabled(len(self.profiles) > 0)
        self.update_list()

    @pyqtSlot()
    def remove_list_item(self):
        model = self.profileList.selectionModel()
        if len(model.selectedRows()) == 0:
            info = QMessageBox()
            info.setWindowIcon(QIcon('icon.png'))
            info.setIcon(QMessageBox.Information)
            info.setWindowTitle('Entry Remover')
            info.setText('Please select a whole row.')
            info.exec()
            return
        for selection in model.selectedRows():
            self.remove_from_storage(selection)
            self.profileList.removeRow(selection.row())
        self.update_buttons()

    def remove_from_storage(self, selection):
        dictionary = self.get_profile_map(self.controllerSource, self.pilotSource.currentText())
        pilot = self.driverMap if self.pilotSource.currentText() == 'Driver' else self.gunnerMap
        for index, key in enumerate(pilot.keys()):
            if key == self.profiles.currentText():
                dictionary[pilot.get(key)].pop(self.profileList.item(selection.row(), 0).text())

    @pyqtSlot()
    def remove_profile(self):
        confirm = QMessageBox()
        confirm.setWindowIcon(QIcon('icon.png'))
        confirm.setWindowTitle('Profile Handler')
        confirm.setText('Are you sure you want to delete "' + self.profiles.currentText() + '"?')
        confirm.setInformativeText('You cannot undo this action!')
        confirm.setIcon(QMessageBox.Question)
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setDefaultButton(QMessageBox.No)
        res = confirm.exec()
        if res == QMessageBox.No:
            return
        pilot = self.driverMap if self.pilotSource.currentText() == 'Driver' else self.gunnerMap
        mapIndex = find_profile_index(pilot, self.profiles.currentText())
        diction = self.get_profile_map(self.controllerSource, self.pilotSource.currentText())
        diction[mapIndex].clear()
        pilot.pop(self.profiles.currentText())
        self.update_profiles()

    def update_submit(self):
        self.submit.setEnabled(len(self.profileName.text()) > 0 and len(self.key.text()) > 0)

    @pyqtSlot()
    def process_data(self):
        if self.profileName == '' or self.key.text() == '':
            return
        pilot = (self.driverMap if self.pilot.currentText() == 'Driver' else self.gunnerMap)
        profileIndex = self.set_profile(pilot, self.profileName.text())
        self.update_dictionary(profileIndex)
        self.pilotSource.setCurrentText('Driver' if self.pilot.currentText() == 'Driver' else 'Gunner')
        self.controllerSource.setCurrentText(
            'Xbox Compatible' if self.controller.currentText() == 'Xbox Compatible' else 'Joystick')
        self.profiles.setCurrentText(
            self.get_profile_names('driver' if self.pilotSource.currentText() == 'Driver' else 'gunner')[profileIndex])
        self.update_list()
        self.key.setText('')
        self.update_buttons()
        self.update_submit()

    def set_profile(self, pilot, text_key):
        profileIndex = find_profile_index(pilot, text_key)
        if profileIndex == -1:
            for x, val in enumerate(pilot.keys()):
                if len(val) == 0:
                    profileIndex = x
                    pilot[text_key] = x
                    self.update_profiles()
                    return profileIndex
            pilot[text_key] = len(pilot)
            profileIndex = len(pilot) - 1
        self.update_profiles()
        return profileIndex

    def get_profile_names(self, assignment):
        pilots = []
        if assignment == 'driver':
            for key in self.driverMap.keys():
                pilots.append(key)
        else:
            for key in self.gunnerMap.keys():
                pilots.append(key)
        return pilots

    def update_dictionary(self, index):
        dictToUse = self.get_profile_map(self.controller, self.pilot.currentText())
        if index == len(dictToUse):
            dictToUse.append({})
        dictToUse[index].update({self.key.text(): self.port.text()})

    def get_profile_map(self, menu, text):
        if text == 'Driver':
            return self.dProfileMapXbox if menu.currentText() == 'Xbox Compatible' else self.dProfileMapJoystick
        else:
            return self.gProfileMapXbox if menu.currentText() == 'Xbox Compatible' else self.gProfileMapJoystick

    def update_list(self):
        self.reset_table()
        self.update_buttons()
        if len(self.profiles) == 0:
            self.profileList.removeRow(0)
            return
        indexA = -1
        tempPilot = self.driverMap if self.pilot.currentText() == 'Driver' else self.gunnerMap
        for key in tempPilot.keys():
            if key == self.profiles.currentText():
                indexA = tempPilot[key]
        if indexA == -1:
            return
        dictionary = self.get_profile_map(self.controllerSource, self.pilotSource.currentText())[indexA]
        if len(dictionary.keys()) - self.profileList.rowCount() > 0:
            for x in range(len(dictionary.keys()) - self.profileList.rowCount()):
                self.profileList.insertRow(0)
        for index, key in enumerate(dictionary.keys()):
            self.profileList.setItem(index, 0, QTableWidgetItem(key))
            self.profileList.setItem(index, 1, QTableWidgetItem(dictionary[key]))

    def reset_table(self):
        self.profileList.setRowCount(0)
        self.profileList.setHorizontalHeaderLabels(['Key', 'Port'])
        self.profileList.setAutoScroll(True)
        header = self.profileList.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

    def export_json(self):
        jsonExport = {'driver': {}, 'gunner': {}}
        for key in self.driverMap.keys():
            workingDict = jsonExport.get('driver')
            workingDict[key] = {'xbox': {}, 'joystick': {}}
            for x, val in enumerate(self.dProfileMapXbox[self.driverMap.get(key)].keys()):
                workingDict[key].get('xbox')['map' + str(x)] = [val,
                                                                self.dProfileMapXbox[self.driverMap.get(key)].get(val)]
            for x, val in enumerate(self.dProfileMapJoystick[self.driverMap.get(key)].keys()):
                workingDict[key].get('joystick')['map' + str(x)] = [val, self.dProfileMapJoystick[
                    self.driverMap.get(key)].get(val)]

        for key in self.gunnerMap.keys():
            workingDict = jsonExport.get('gunner')
            workingDict[key] = {'xbox': {}, 'joystick': {}}
            for x, val in enumerate(self.gProfileMapXbox[self.gunnerMap.get(key)].keys()):
                workingDict[key].get('xbox')['map' + str(x)] = [val,
                                                                self.gProfileMapXbox[self.gunnerMap.get(key)].get(val)]
            for x, val in enumerate(self.gProfileMapJoystick[self.gunnerMap.get(key)].keys()):
                workingDict[key].get('joystick')['map' + str(x)] = [val, self.gProfileMapJoystick[
                    self.gunnerMap.get(key)].get(val)]
        with open('dataOut.json', 'w') as out:
            json.dump(jsonExport, out, ensure_ascii=False, indent=4)

        msg = QMessageBox()
        msg.setWindowIcon(QIcon('icon.png'))
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('File Writer')
        msg.setText('JSON file created successfully.')
        msg.exec()

    def import_json(self):
        confirmation = QMessageBox()
        confirmation.setWindowIcon(QIcon('icon.png'))
        confirmation.setIcon(QMessageBox.Question)
        confirmation.setWindowTitle('File Information')
        confirmation.setText('Are you sure you want to import?')
        check = QCheckBox()
        check.setText('Overwrite current entries')
        confirmation.setCheckBox(check)
        confirmation.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirmation.setInformativeText('Make sure your file is named "dataIn.json" if you accept.')
        if confirmation.exec() == QMessageBox.Yes:
            self.do_import(check.isChecked())

    def do_import(self, overwrite):
        try:
            with open('dataIn.json', 'r') as f:
                jsonIn = json.load(f)
        except FileNotFoundError:
            info = QMessageBox()
            info.setWindowIcon(QIcon('icon.png'))
            info.setWindowTitle('File Loader')
            info.setText('No file named "dataIn.json" found.')
            info.setIcon(QMessageBox.Critical)
            info.exec()
            return
        if overwrite:
            self.driverMap = {}
            self.gunnerMap = {}
            self.dProfileMapJoystick = [{}]
            self.dProfileMapXbox = [{}]
            self.gProfileMapJoystick = [{}]
            self.gProfileMapXbox = [{}]
        self.update_profiles()
        driverData = jsonIn.get('driver')
        for key in driverData.keys():
            profileIndex = self.set_profile(self.driverMap, key)
            xboxDict = driverData.get(key).get('xbox')
            add_dict_bulk(self.dProfileMapXbox, profileIndex, xboxDict)
            joyDict = driverData.get(key).get('joystick')
            add_dict_bulk(self.dProfileMapJoystick, profileIndex, joyDict)
        gunnerData = jsonIn.get('gunner')
        for key in gunnerData.keys():
            profileIndex = self.set_profile(self.gunnerMap, key)
            xboxDict = gunnerData.get(key).get('xbox')
            add_dict_bulk(self.gProfileMapXbox, profileIndex, xboxDict)
            joyDict = driverData.get(key).get('joystick')
            add_dict_bulk(self.gProfileMapJoystick, profileIndex, joyDict)
        self.update_profiles()

    def update_buttons(self):
        currentMap = self.driverMap if self.pilotSource.currentText() == 'Driver' else self.gunnerMap
        index = find_profile_index(currentMap, self.profiles.currentText())
        if index == -1:
            self.removeItem.setEnabled(False)
            self.removeProfile.setEnabled(False)
        else:
            self.removeProfile.setEnabled(True)
            dicti = self.get_profile_map(self.controllerSource, self.pilotSource.currentText())
            self.removeItem.setEnabled(len(dicti[index].keys()) > 0)


if __name__ == '__main__':
    app = QApplication([])
    win = MainWin()
    sys.exit(app.exec_())
