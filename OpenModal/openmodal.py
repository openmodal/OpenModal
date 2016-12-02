__author__ = 'Matjaz'

import sys, time, os

import multiprocessing as mp
#
# if __name__ == '__main__':
#     executable = os.path.join(os.path.dirname(sys.executable), 'openmodal.exe')
#     mp.set_executable(executable)
#     mp.freeze_support()

from PyQt4 import QtGui

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

sys.stderr = Logger('log/{0:.0f}_log.txt'.format(time.time()))

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.addLibraryPath('c:/Anaconda3/Lib/site-packages/PyQt4/plugins/')

    pixmap = QtGui.QPixmap('gui/widgets/splash.png')
    splash = QtGui.QSplashScreen(pixmap)
    splash.show()

    splash.showMessage('Importing modules ...')
    app.processEvents()
    import gui.skeleton as sk

    main_window = sk.FramelesContainer(app.desktop())
    splash.showMessage('Building environment ...')
    app.processEvents()

    main_window.show()

    splash.finish(main_window)

    sys.exit(app.exec_())