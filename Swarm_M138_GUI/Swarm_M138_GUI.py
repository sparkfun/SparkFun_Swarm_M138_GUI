"""
A simple Python3 PyQt5 GUI for the Swarm M138 Modem

Written by: Paul Clark, SparkFun
Date: March 4th, 2023

MIT license

Please see the LICENSE.md for more details

"""

import darkdetect
import sys
import os
import os.path
import platform

from typing import Iterator, Tuple

from PyQt5.QtCore import QSettings, QProcess, QTimer, Qt, QIODevice, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, QPushButton, \
    QApplication, QLineEdit, QFileDialog, QPlainTextEdit
from PyQt5.QtGui import QCloseEvent, QTextCursor, QIcon, QFont
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

_APP_NAME = "Swarm M138 GUI"

# sub folder for our resource files
_RESOURCE_DIRECTORY = "resource"

#https://stackoverflow.com/a/50914550
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, _RESOURCE_DIRECTORY, relative_path)

def get_version(rel_path: str) -> str:
    try: 
        with open(resource_path(rel_path), encoding='utf-8') as fp:
            for line in fp.read().splitlines():
                if line.startswith("__version__"):
                    delim = '"' if '"' in line else "'"
                    return line.split(delim)[1]
            raise RuntimeError("Unable to find version string.")
    except:
        raise RuntimeError("Unable to find _version.py.")

_APP_VERSION = get_version("_version.py")

# ----------------------------------------------------------------
# hack to know when a combobox menu is being shown. Helpful if contents
# of list are dynamic -- like serial ports.

class AUxComboBox(QComboBox):

    popupAboutToBeShown = pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super().showPopup()

#----------------------------------------------------------------
# ux_is_darkmode()
#
# Helpful function used during setup to determine if the Ux is in
# dark mode
_is_darkmode = None
def ux_is_darkmode() -> bool:
    global _is_darkmode

    if _is_darkmode is not None:
        return _is_darkmode

    osName = platform.system()

    if osName == "Darwin":
        _is_darkmode = darkdetect.isDark()

    elif osName == "Windows":
        # it appears that the Qt interface on Windows doesn't apply DarkMode
        # So, just keep it light
        _is_darkmode = False
    elif osName == "Linux":
        # Need to check this on Linux at some pont
        _is_darkmod = False

    else:
        _is_darkmode = False

    return _is_darkmode

# Setting constants
SETTING_PORT_NAME = 'port_name'
SETTING_FILE_LOCATION = 'file_location'

def gen_serial_ports() -> Iterator[Tuple[str, str, str]]:
    """Return all available serial ports."""
    ports = QSerialPortInfo.availablePorts()
    return ((p.description(), p.portName(), p.systemLocation()) for p in ports)

# noinspection PyArgumentList

class MainWidget(QWidget):
    """Main Widget."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
 
        self.fileOpen = False

        self.timer=QTimer()
        self.timer.timeout.connect(self.check_port_still_available)

        # File location line edit
        self.msg_label = QLabel(self.tr('Log File:'))
        self.fileLocation_lineedit = QLineEdit()
        self.msg_label.setBuddy(self.fileLocation_lineedit)
        #self.fileLocation_lineedit.setEnabled(False)
        self.fileLocation_lineedit.returnPressed.connect(self.on_browse_btn_pressed)

        # Browse for new file button
        self.browse_btn = QPushButton(self.tr('Browse'))
        self.browse_btn.setEnabled(True)
        self.browse_btn.clicked.connect(self.on_browse_btn_pressed)

        # Start Logging Button
        self.start_logging_btn = QPushButton(self.tr('Start Logging'))
        self.start_logging_btn.clicked.connect(self.on_start_logging_btn_pressed)

        # Stop Logging Button
        self.stop_logging_btn = QPushButton(self.tr('Stop Logging'))
        self.stop_logging_btn.clicked.connect(self.on_stop_logging_btn_pressed)

        # Port Combobox
        self.port_label = QLabel(self.tr('COM Port:'))
        self.port_combobox = AUxComboBox()
        self.port_label.setBuddy(self.port_combobox)
        self.update_com_ports()
        self.port_combobox.popupAboutToBeShown.connect(self.on_port_combobox)

        # Open Port Button
        self.open_port_btn = QPushButton(self.tr('Open Port'))
        self.open_port_btn.clicked.connect(self.on_open_port_btn_pressed)

        # Close Port Button
        self.close_port_btn = QPushButton(self.tr('Close Port'))
        self.close_port_btn.clicked.connect(self.on_close_port_btn_pressed)

        # Send Message Button
        self.send_message_btn = QPushButton(self.tr('Send Message'))
        self.send_message_btn.clicked.connect(self.on_send_message_btn_pressed)

        # Clear Terminal Button
        self.clear_terminal_btn = QPushButton(self.tr('Clear'))
        self.clear_terminal_btn.clicked.connect(self.on_clear_terminal_btn_pressed)

        # Clear Messages Button
        self.clear_message_btn = QPushButton(self.tr('Clear'))
        self.clear_message_btn.clicked.connect(self.on_clear_message_btn_pressed)

        # Terminal Bar
        self.terminal_label = QLabel(self.tr('Serial Monitor:'))

        # Terminal Window
        self.terminal = QPlainTextEdit()

        # Messages Bar
        self.messages_label = QLabel(self.tr('Information / Warnings / Errors:'))

        # Messages Window
        self.messages = QPlainTextEdit()

        # Config Bar
        self.config_label = QLabel(self.tr('Message:'))
        self.config_label_2 = QLabel(self.tr('(The $, * and checksum are added automatically)'))

        # Config Window
        self.config = QPlainTextEdit()

        # Message Labels
        Messages_header = QLabel(self.tr('Pre-defined Messages:'))
        Messages_header.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.cs_btn = QPushButton(self.tr('Configuration Settings (CS)'))
        self.cs_btn.clicked.connect(lambda: self.on_message_btn_pressed('CS'))
        self.dt_btn = QPushButton(self.tr('Date/Time Status (DT @)'))
        self.dt_btn.clicked.connect(lambda: self.on_message_btn_pressed('DT @'))
        self.fv_btn = QPushButton(self.tr('Firmware Version (FV)'))
        self.fv_btn.clicked.connect(lambda: self.on_message_btn_pressed('FV'))
        self.gj_btn = QPushButton(self.tr('GPS Jamming (GJ @)'))
        self.gj_btn.clicked.connect(lambda: self.on_message_btn_pressed('GJ @'))
        self.gn_btn = QPushButton(self.tr('Geospatial Info (GN @)'))
        self.gn_btn.clicked.connect(lambda: self.on_message_btn_pressed('GN @'))
        self.gs_btn = QPushButton(self.tr('GPS Fix Quality (GS @)'))
        self.gs_btn.clicked.connect(lambda: self.on_message_btn_pressed('GS @'))
        self.gp_read_btn = QPushButton(self.tr('GPIO1 Read Pin (GP @)'))
        self.gp_read_btn.clicked.connect(lambda: self.on_message_btn_pressed('GP @'))
        self.gp_mode_btn = QPushButton(self.tr('GPIO1 Get Mode (GP ?)'))
        self.gp_mode_btn.clicked.connect(lambda: self.on_message_btn_pressed('GP ?'))
        self.gp_mode1_btn = QPushButton(self.tr('GPIO1 Set Mode - Analog (GP 1)'))
        self.gp_mode1_btn.clicked.connect(lambda: self.on_message_btn_pressed('GP 1'))
        self.gp_mode2_btn = QPushButton(self.tr('GPIO1 Set Mode - Input (GP 2)'))
        self.gp_mode2_btn.clicked.connect(lambda: self.on_message_btn_pressed('GP 2'))
        self.gp_mode5_btn = QPushButton(self.tr('GPIO1 Set Mode - Output Low (GP 5)'))
        self.gp_mode5_btn.clicked.connect(lambda: self.on_message_btn_pressed('GP 5'))
        self.gp_mode6_btn = QPushButton(self.tr('GPIO1 Set Mode - Output High (GP 6)'))
        self.gp_mode6_btn.clicked.connect(lambda: self.on_message_btn_pressed('GP 6'))
        self.mm_count_btn = QPushButton(self.tr('Messages Received - Count Unread (MM C=U)'))
        self.mm_count_btn.clicked.connect(lambda: self.on_message_btn_pressed('MM C=U'))
        self.mm_old_btn = QPushButton(self.tr('Messages Received - Read Oldest (MM R=O)'))
        self.mm_old_btn.clicked.connect(lambda: self.on_message_btn_pressed('MM R=O'))
        self.mm_new_btn = QPushButton(self.tr('Messages Received - Read Newest (MM R=N)'))
        self.mm_new_btn.clicked.connect(lambda: self.on_message_btn_pressed('MM R=N'))
        self.mm_notify_on_btn = QPushButton(self.tr('Messages Received - Notify Enable (MM N=E)'))
        self.mm_notify_on_btn.clicked.connect(lambda: self.on_message_btn_pressed('MM N=E'))
        self.mm_notify_off_btn = QPushButton(self.tr('Messages Received - Notify Disable (MM N=D)'))
        self.mm_notify_off_btn.clicked.connect(lambda: self.on_message_btn_pressed('MM N=D'))
        self.mt_count_btn = QPushButton(self.tr('Message Transmit - Count Unsent (MT C=U)'))
        self.mt_count_btn.clicked.connect(lambda: self.on_message_btn_pressed('MT C=U'))
        self.mt_delete_btn = QPushButton(self.tr('Message Transmit - Delete All Unsent (MT D=U)'))
        self.mt_delete_btn.clicked.connect(lambda: self.on_message_btn_pressed('MT D=U'))
        self.po_btn = QPushButton(self.tr('Power Off (PO)'))
        self.po_btn.clicked.connect(lambda: self.on_message_btn_pressed('PO'))
        self.pw_btn = QPushButton(self.tr('Power Status (PW @)'))
        self.pw_btn.clicked.connect(lambda: self.on_message_btn_pressed('PW @'))
        self.rs_btn = QPushButton(self.tr('Restart Device (RS)'))
        self.rs_btn.clicked.connect(lambda: self.on_message_btn_pressed('RS'))
        self.rt_on_btn = QPushButton(self.tr('Receive Test 1Hz (RT 1)'))
        self.rt_on_btn.clicked.connect(lambda: self.on_message_btn_pressed('RT 1'))
        self.rt_off_btn = QPushButton(self.tr('Receive Test Stop (RT 0)'))
        self.rt_off_btn.clicked.connect(lambda: self.on_message_btn_pressed('RT 0'))
        self.td_btn = QPushButton(self.tr('Transmit Text - Hello World! (TD)'))
        self.td_btn.clicked.connect(lambda: self.on_message_btn_pressed('TD \"Hello World!\"'))
        self.td_bin_btn = QPushButton(self.tr('Transmit Binary - 00 01 02 03 04 05 (TD)'))
        self.td_bin_btn.clicked.connect(lambda: self.on_message_btn_pressed('TD 000102030405'))

        # Arrange Layout
        
        layout = QGridLayout()
        
        layout.addWidget(self.msg_label, 0, 0)
        layout.addWidget(self.fileLocation_lineedit, 0, 1)
        layout.addWidget(self.browse_btn, 0, 2)
        layout.addWidget(self.start_logging_btn, 1, 2)
        layout.addWidget(self.stop_logging_btn, 2, 2)
        layout.addWidget(self.port_label, 4, 0)
        layout.addWidget(self.port_combobox, 4, 1)
        layout.addWidget(self.open_port_btn, 4, 2)
        layout.addWidget(self.close_port_btn, 5, 2)
        layout.addWidget(self.terminal_label, 8, 0)
        layout.addWidget(self.clear_terminal_btn, 8, 2)
        layout.addWidget(self.terminal, 9, 0, 10, 3)
        layout.addWidget(self.messages_label, 19, 0)
        layout.addWidget(self.clear_message_btn, 19, 2)
        layout.addWidget(self.messages, 20, 0, 3, 3)
        layout.addWidget(self.config_label, 23, 0)
        layout.addWidget(self.config_label_2, 23, 1)
        layout.addWidget(self.send_message_btn, 23, 2)
        layout.addWidget(self.config, 24, 0, 3, 3)

        layout.addWidget(Messages_header, 0, 4)

        layout.addWidget(self.cs_btn, 1, 4)
        layout.addWidget(self.dt_btn, 2, 4)
        layout.addWidget(self.fv_btn, 3, 4)
        layout.addWidget(self.gj_btn, 4, 4)
        layout.addWidget(self.gn_btn, 5, 4)
        layout.addWidget(self.gs_btn, 6, 4)
        layout.addWidget(self.gp_read_btn, 7, 4)
        layout.addWidget(self.gp_mode_btn, 8, 4)
        layout.addWidget(self.gp_mode1_btn, 9, 4)
        layout.addWidget(self.gp_mode2_btn, 10, 4)
        layout.addWidget(self.gp_mode5_btn, 11, 4)
        layout.addWidget(self.gp_mode6_btn, 12, 4)
        layout.addWidget(self.mm_count_btn, 13, 4)
        layout.addWidget(self.mm_old_btn, 14, 4)
        layout.addWidget(self.mm_new_btn, 15, 4)
        layout.addWidget(self.mm_notify_on_btn, 16, 4)
        layout.addWidget(self.mm_notify_off_btn, 17, 4)
        layout.addWidget(self.mt_count_btn, 18, 4)
        layout.addWidget(self.mt_delete_btn, 19, 4)
        layout.addWidget(self.po_btn, 20, 4)
        layout.addWidget(self.pw_btn, 21, 4)
        layout.addWidget(self.rs_btn, 22, 4)
        layout.addWidget(self.rt_on_btn, 23, 4)
        layout.addWidget(self.rt_off_btn, 24, 4)
        layout.addWidget(self.td_btn, 25, 4)
        layout.addWidget(self.td_bin_btn, 26, 4)

        self.setLayout(layout)

        self.settings = QSettings()
        #self._clean_settings() # This will delete all existing settings! Use with caution!        
        self.load_settings()

        self.setWindowTitle( _APP_NAME + " - " + _APP_VERSION)

        # Make these text edit windows read-only
        self.terminal.setReadOnly(True)
        self.messages.setReadOnly(True)

    def load_settings(self) -> None:
        """Load Qsettings on startup."""
        
        port_name = self.settings.value(SETTING_PORT_NAME)
        if port_name is not None:
            index = self.port_combobox.findData(port_name)
            if index > -1:
                self.port_combobox.setCurrentIndex(index)

        msg = self.settings.value(SETTING_FILE_LOCATION)
        if msg is not None:
            self.fileLocation_lineedit.setText(msg)

    def save_settings(self) -> None:
        """Save Qsettings on shutdown."""
        self.settings.setValue(SETTING_PORT_NAME, self.port)
        self.settings.setValue(SETTING_FILE_LOCATION, self.theFile)

    def _clean_settings(self) -> None:
        """Clean (remove) all existing settings."""
        self.settings.clear()

    def on_browse_btn_pressed(self) -> None:
        """Open dialog to select bin file."""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            None,
            "Select Configuration File",
            "",
            "Log Files (*.txt);;All Files (*)",
            options=options)
        if fileName:
            self.fileLocation_lineedit.setText(fileName)
     
    @pyqtSlot(str)
    def on_message_btn_pressed(self, message: str) -> None:
        """Paste the appropriate message and send it"""

        self.config.clear() # Clear the config window
        self.config.moveCursor(QTextCursor.End)
        self.config.ensureCursorVisible()
        self.config.appendPlainText(message)
        self.config.ensureCursorVisible()
        self.config.repaint()
        
        self.on_send_message_btn_pressed()

    def on_clear_message_btn_pressed(self) -> None:
        """Clear the warnings / errors"""

        self.messages.clear() # Clear the message window
        self.messages.moveCursor(QTextCursor.End)
        self.messages.ensureCursorVisible()
        self.messages.repaint()

    def on_clear_terminal_btn_pressed(self) -> None:
        """Clear the terminal"""

        self.terminal.clear() # Clear the serial terminal window
        self.terminal.moveCursor(QTextCursor.End)
        self.terminal.ensureCursorVisible()
        self.terminal.repaint()

    def chksum_nmea(self, sentence):
        """Calculate the NMEA checksum"""
        # Initializing our first XOR value
        csum = 0 
        # For each char in chksumdata, XOR against the previous XOR'd char.
        # The final XOR of the last char will be our  checksum
        for c in sentence:
            csum ^= ord(c)
        return csum

    def on_send_message_btn_pressed(self) -> None:
        """Send the message to the modem"""

        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            try:
                if (sys == self.port):
                    portAvailable = True
            except:
                pass

        if (portAvailable == False):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Error: Port No Longer Available!")
            self.messages.ensureCursorVisible()
            try:
                self.ser.close()
            except:
                pass
            self.endTimer()
            return
        
        try:
            if self.ser.isOpen():
                portAvailable = True
            else:
                portAvailable = False
        except:
            portAvailable = False

        if (portAvailable == False):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Error: Port Is Not Open!")
            self.messages.ensureCursorVisible()
            try:
                self.ser.close()
            except:
                pass
            self.endTimer()
            return

        if (self.config.toPlainText() == ''):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Warning: Nothing To Do! Message Is Empty!")
            self.messages.ensureCursorVisible()
            return

        self.ser.write(bytes('$','utf-8')) # Send the $
        self.ser.write(bytes(self.config.toPlainText(),'utf-8')) # Send the config message
        self.ser.write(bytes('*','utf-8')) # Send the *
        self.ser.write(str.format('{:02X}', self.chksum_nmea(self.config.toPlainText())).encode('utf-8'))
        self.ser.write(bytes('\n','utf-8'))

        msg = "$"
        msg += self.config.toPlainText()
        msg += "*"
        msg += str.format('{:02X}', self.chksum_nmea(self.config.toPlainText())).encode('utf-8').decode('utf-8')
        msg += "\n"

        self.terminal.moveCursor(QTextCursor.End)
        self.terminal.ensureCursorVisible()        
        self.terminal.appendPlainText(msg)
        self.terminal.ensureCursorVisible()

        if self.fileOpen == True:
            try:
                self.f.write(msg);
            except IOError:
                self.fileOpen = False
                self.messages.moveCursor(QTextCursor.End)
                self.messages.ensureCursorVisible()
                self.messages.appendPlainText("Error: Could Not Write To File!")
                self.messages.ensureCursorVisible()
                try:
                    self.f.close();
                except:
                    pass

    # --------------------------------------------------------------
    # on_port_combobox()
    #
    # Called when the combobox pop-up menu is about to be shown
    #
    # Use this event to dynamically update the displayed ports
    #
    @pyqtSlot()
    def on_port_combobox(self):
        self.update_com_ports()

    def update_com_ports(self) -> None:
        """Update COM Port list in GUI."""

        previousPort = self.port # Record the previous port before we clear the combobox
        
        self.port_combobox.clear()

        index = 0
        indexOfPrevious = -1
        for desc, name, sys in gen_serial_ports():
            longname = desc + " (" + name + ")"
            self.port_combobox.addItem(longname, sys)
            if(sys == previousPort): # Previous port still exists so record it
                indexOfPrevious = index
            index = index + 1

        if indexOfPrevious > -1: # Restore the previous port if it still exists
            self.port_combobox.setCurrentIndex(indexOfPrevious)

    @property
    def port(self) -> str:
        """Return the current serial port."""
        return self.port_combobox.currentData()
    
    @property
    def theFile(self) -> str:
        """Return the current file location."""
        return self.fileLocation_lineedit.text()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle Close event of the Widget."""
        try:
            self.save_settings()
        except:
            pass

        try:
            self.ser.close()
        except:
            pass
        
        try:
            self.f.close()
        except:
            pass

        self.endTimer()
        
        event.accept()

    def on_open_port_btn_pressed(self) -> None:
        """Check if port is available and open it"""

        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            try:
                if (sys == self.port):
                    portAvailable = True
            except:
                pass

        if (portAvailable == False):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Error: Port No Longer Available!")
            self.messages.ensureCursorVisible()
            try:
                self.ser.close()
            except:
                pass
            self.endTimer()
            return

        try:
            if self.ser.isOpen():
                portAvailable = True
            else:
                portAvailable = False
        except:
            portAvailable = False

        if (portAvailable == True):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Port Is Already Open!")
            self.messages.ensureCursorVisible()
            return
        
        try:
            self.ser = QSerialPort()
            self.ser.setPortName(self.port)
            self.ser.setBaudRate(QSerialPort.Baud115200)
            self.ser.open(QIODevice.ReadWrite)
        except:
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Error: Could Not Open The Port!")
            self.messages.ensureCursorVisible()
            try:
                self.ser.close()
            except:
                pass
            self.endTimer()
            return

        self.startTimer()

        self.ser.readyRead.connect(self.receive) # Connect the receiver
        
        self.messages.clear() # Clear the message window
        self.terminal.clear() # Clear the serial terminal window
        
        self.messages.moveCursor(QTextCursor.End)
        self.messages.ensureCursorVisible()
        self.messages.appendPlainText("Port is now open")
        self.messages.ensureCursorVisible()

    @pyqtSlot()
    def receive(self) -> None:
        try:
            while self.ser.canReadLine():
                text = self.ser.readLine().data().decode()
                self.terminal.moveCursor(QTextCursor.End)
                self.terminal.ensureCursorVisible()
                self.terminal.insertPlainText(text)
                self.terminal.ensureCursorVisible()
                self.terminal.repaint()

                if self.fileOpen == True:
                    try:
                        self.f.write(text);
                    except IOError:
                        self.fileOpen = False
                        self.messages.moveCursor(QTextCursor.End)
                        self.messages.ensureCursorVisible()
                        self.messages.appendPlainText("Error: Could Not Write To File!")
                        self.messages.ensureCursorVisible()
                        self.messages.repaint()
                        try:
                            self.f.close();
                        except:
                            pass
        except:
            pass

    def startTimer(self) -> None:
        self.timer.start(1000)

    def endTimer(self) -> None:
        self.timer.stop()

    def check_port_still_available(self) -> None:
        """Check if port is still available"""

        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            try:
                if (sys == self.port):
                    portAvailable = True
            except:
                pass

        if (portAvailable == False):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Error: Port No Longer Available!")
            self.messages.ensureCursorVisible()
            self.messages.repaint()
            try:
                self.ser.close()
            except:
                pass
            self.endTimer()

    def on_close_port_btn_pressed(self) -> None:
        """Close the port"""

        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            try:
                if (sys == self.port):
                    portAvailable = True
            except:
                pass

        if (portAvailable == False):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Error: Port No Longer Available!")
            self.messages.ensureCursorVisible()
            self.messages.repaint()
            try:
                self.ser.close()
            except:
                pass
            self.endTimer()
            return

        try:
            if self.ser.isOpen():
                portAvailable = True
            else:
                portAvailable = False
        except:
            portAvailable = False

        if (portAvailable == False):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Port Is Already Closed!")
            self.messages.ensureCursorVisible()
            self.messages.repaint()
            try:
                self.ser.close()
            except:
                pass
            self.endTimer()
            return

        try:
            self.ser.close()
        except:
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Error: Could Not Close The Port!")
            self.messages.ensureCursorVisible()
            self.messages.repaint()
            return

        self.messages.moveCursor(QTextCursor.End)
        self.messages.ensureCursorVisible()
        self.messages.appendPlainText("Port is now closed")
        self.messages.ensureCursorVisible()
        self.messages.repaint()

    def on_start_logging_btn_pressed(self) -> None:
        """Start logging everything to file"""

        if (self.fileOpen == True):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("File Is Already Open!")
            self.messages.ensureCursorVisible()
            self.messages.repaint()
            return

        try:
            self.f = open(self.fileLocation_lineedit.text(),"a")
            self.fileOpen = True
        except IOError:
            self.fileOpen = False

        if (self.fileOpen == False):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("Error: Could Not Open File!")
            self.messages.ensureCursorVisible()
            self.messages.repaint()
            return

        self.messages.moveCursor(QTextCursor.End)
        self.messages.ensureCursorVisible()
        self.messages.appendPlainText("File open")
        self.messages.ensureCursorVisible()
        self.messages.repaint()

    def on_stop_logging_btn_pressed(self) -> None:
        """Close the log file"""

        if (self.fileOpen == False):
            self.messages.moveCursor(QTextCursor.End)
            self.messages.ensureCursorVisible()
            self.messages.appendPlainText("File Is Already Closed!")
            self.messages.ensureCursorVisible()
            self.messages.repaint()
            return

        try:
            self.f.close()
        except IOError:
            pass

        self.fileOpen = False

        self.messages.moveCursor(QTextCursor.End)
        self.messages.ensureCursorVisible()
        self.messages.appendPlainText("File closed")
        self.messages.ensureCursorVisible()
        self.messages.repaint()

def startGUI():
    """Start the GUI"""
    from sys import exit as sysExit
    app = QApplication([])
    app.setOrganizationName('SparkFun Electronics')
    app.setApplicationName(_APP_NAME + ' - ' + _APP_VERSION)
    app.setWindowIcon(QIcon(resource_path("sfe_logo_med.png")))
    app.setApplicationVersion(_APP_VERSION)
    w = MainWidget()
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    startUploaderGUI()