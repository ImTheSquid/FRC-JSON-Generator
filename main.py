import sys

from PyQt5.QtWidgets import QApplication
from window import MainWin

app = QApplication([])
win = MainWin()
sys.exit(app.exec_())