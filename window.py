import json

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QPushButton, QLineEdit, QComboBox, QGroupBox, \
    QVBoxLayout, QWidget, QLabel, QHBoxLayout, QSpinBox, QTableWidget, QHeaderView, QTableWidgetItem, QMessageBox


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

        submit = QPushButton()
        submit.setText('Add Entry to List')
        submit.clicked.connect(self.process_data)
        vertLeft.addWidget(submit)

        leftHalf.setLayout(vertLeft)
        mainLayout.addWidget(leftHalf)
        self.profileList = QTableWidget(0, 2)

        rightVert = QVBoxLayout()
        rightVert.setSpacing(2)
        self.profiles = QComboBox()
        self.profiles.addItems(self.get_profile_names('driver'))
        self.profiles.currentTextChanged.connect(self.update_list)
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
        self.export = QPushButton("Export to JSON")
        self.export.clicked.connect(self.export_json)
        self.export.setDisabled(True)
        listControls.addWidget(self.export)
        rightVert.addLayout(listControls)

        rightHalf.setLayout(rightVert)
        mainLayout.addWidget(rightHalf)

        self.init_gui(mainLayout)

    def init_gui(self, layout):
        # Init the basic window frame
        self.setWindowTitle('JSON Controller Profile Configuration Tool v.1.0')

        self.setLayout(layout)
        self.show()

    def update_profiles(self):
        self.profiles.clear()
        self.profiles.addItems(
            self.get_profile_names('driver' if self.pilotSource.currentText() == 'Driver' else 'gunner'))
        self.update_list()

    @pyqtSlot()
    def remove_list_item(self):
        model = self.profileList.selectionModel()
        for selection in model.selectedRows():
            self.remove_from_storage(selection)
            self.profileList.removeRow(selection.row())
        if self.profileList.rowCount() == 0:
            self.removeItem.setDisabled(True)
            self.export.setDisabled(True)

    def remove_from_storage(self, selection):
        dictionary = self.get_profile_map(self.controllerSource, self.pilotSource.currentText())
        pilot = self.driverMap if self.pilotSource.currentText() == 'Driver' else self.gunnerMap
        for index, key in enumerate(pilot.keys()):
            if key == self.profiles.currentText():
                dictionary[pilot.get(key)].pop(self.profileList.item(selection.row(), 0).text())

    @pyqtSlot()
    def process_data(self):
        if self.profileName == '' or self.key.text() == '':
            return
        self.export.setDisabled(False)
        self.removeItem.setDisabled(False)
        pilot = (self.driverMap if self.pilot.currentText() == 'Driver' else self.gunnerMap)
        profileIndex = self.set_profile(pilot)
        self.update_dictionary(profileIndex)
        self.pilotSource.setCurrentText('Driver' if self.pilot.currentText() == 'Driver' else 'Gunner')
        self.controllerSource.setCurrentText('Xbox Compatible' if self.controller.currentText() == 'Xbox Compatible' else 'Joystick')
        self.profiles.setCurrentText(self.get_profile_names('driver' if self.pilotSource.currentText() == 'Driver' else 'gunner')[profileIndex])
        self.update_list()
        self.key.setText('')

    def set_profile(self, pilot):
        profileIndex = self.find_profile_index(pilot)
        if profileIndex == -1:
            pilot[self.profileName.text()] = len(pilot)
            profileIndex = len(pilot)-1
        self.update_profiles()
        return profileIndex

    def find_profile_index(self, pilot):
        for index, key in enumerate(pilot.keys()):
            if key == self.profileName.text():
                return index
        return -1

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
        if len(dictionary.keys())-self.profileList.rowCount() > 0:
            for x in range(len(dictionary.keys())-self.profileList.rowCount()):
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
                workingDict[key].get('xbox')['map'+str(x)] = [val, self.dProfileMapXbox[self.driverMap.get(key)].get(val)]
            for x, val in enumerate(self.dProfileMapJoystick[self.driverMap.get(key)].keys()):
                workingDict[key].get('joystick')['map'+str(x)] = [val, self.dProfileMapJoystick[self.driverMap.get(key)].get(val)]

        for key in self.gunnerMap.keys():
            workingDict = jsonExport.get('gunner')
            workingDict[key] = {'xbox': {}, 'joystick': {}}
            for x, val in enumerate(self.gProfileMapXbox[self.gunnerMap.get(key)].keys()):
                workingDict[key].get('xbox')['map' + str(x)] = [val, self.gProfileMapXbox[self.gunnerMap.get(key)].get(val)]
            for x, val in enumerate(self.gProfileMapJoystick[self.gunnerMap.get(key)].keys()):
                workingDict[key].get('joystick')['map' + str(x)] = [val, self.gProfileMapJoystick[self.gunnerMap.get(key)].get(val)]
        with open('data.json', 'w') as out:
            json.dump(jsonExport, out, ensure_ascii=False, indent=4)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("File Information")
        msg.setText("JSON file created successfully.")
        msg.exec()
