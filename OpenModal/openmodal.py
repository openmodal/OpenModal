
# Copyright (C) 2014-2017 Matjaž Mršnik, Miha Pirnat, Janko Slavič, Blaž Starc (in alphabetic order)
# 
# This file is part of OpenModal.
# 
# OpenModal is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# 
# OpenModal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with OpenModal.  If not, see <http://www.gnu.org/licenses/>.

import sys, time, os

import multiprocessing as mp
#
# if __name__ == '__main__':
#     executable = os.path.join(os.path.dirname(sys.executable), 'openmodal.exe')
#     mp.set_executable(executable)
#     mp.freeze_support()

from PyQt5 import QtGui, QtWidgets, QtWebEngineWidgets

class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stderr
        self.log = open(filename, 'w')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.close()

if os.path.isdir('log'):
    pass
else:
    os.mkdir('log')

#sys.stderr = Logger('log/{0:.0f}_log.txt'.format(time.time()))

sys.path.append('../')

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    #TODO: do we need the following?
    #app.addLibraryPath('c:/Anaconda3/Lib/site-packages/PyQt5/plugins/')

    #pixmap = QtGui.QPixmap('gui/widgets/splash.png')
    #splash = QtGui.QSplashScreen(pixmap)
    #splash.show()

    #splash.showMessage('Importing modules ...')
    app.processEvents()
    import gui.skeleton as sk

    main_window = sk.FramelesContainer(app.desktop())
    #splash.showMessage('Building environment ...')
    app.processEvents()

    main_window.show()

    #splash.finish(main_window)

    #sys.exit(app.exec_())
    app.exec()
