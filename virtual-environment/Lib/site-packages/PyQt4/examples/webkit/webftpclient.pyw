#!/usr/bin/env python

############################################################################
##
## Copyright (C) 2014 Moritz Warning <moritzwarning@web.de>.
## Copyright (C) 2011 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
## Contact: Nokia Corporation (qt-info@nokia.com)
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
############################################################################


# This is only needed for Python v2 but is harmless for Python v3.
import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

from PyQt4 import QtCore, QtGui, QtNetwork, QtWebKit


class FtpView(QtWebKit.QWebView):

    def __init__(self):
        super(FtpView, self).__init__()

        oldManager = self.page().networkAccessManager()
        newManager = NetworkAccessManager(oldManager, self)
        self.page().setNetworkAccessManager(newManager)

        self.page().setForwardUnsupportedContent(True)
        self.downloader = Downloader(self, newManager)

        self.page().unsupportedContent.connect(self.downloader.saveFile)
        self.page().downloadRequested.connect(self.downloader.startDownload)

        self.urlChanged.connect(self.updateWindowTitle)

    def updateWindowTitle(self, url):
        self.setWindowTitle("FTP Client - %s" % url.toString())

    def createWindow(self, _):
        newview = FtpView()
        newview.show()
        return newview


class Downloader(QtCore.QObject):

    def __init__(self, parentWidget, manager):
        super(Downloader, self).__init__(parentWidget)

        self.manager = manager
        self.reply = None
        self.downloads = {}
        self.path = ""
        self.parentWidget = parentWidget

    def chooseSaveFile(self, url):
        fileName = url.path().split("/")[-1]
        if len(self.path) != 0:
            fileName = QDir(path).filePath(fileName)

        return QtGui.QFileDialog.getSaveFileName(self.parentWidget, "Save File", fileName);

    def startDownload(self, request):
        self.downloads[request.url().toString()] = self.chooseSaveFile(request.url())

        reply = self.manager.get(request)
        reply.finished.connect(self.finishDownload)

    def saveFile(self, reply):
        newPath = self.downloads.get(reply.url().toString())

        if not newPath:
            newPath = self.chooseSaveFile(reply.url())

        if len(newPath) != 0:
            file = QtCore.QFile(newPath)
            if file.open(QtCore.QIODevice.WriteOnly):
                file.write(reply.readAll())
                file.close()
                path = QtCore.QDir(newPath).dirName()
                QtGui.QMessageBox.information(self.parentWidget, "Download Completed", "Saved '%s'." % newPath)
            else:
                QtGui.QMessageBox.warning(self.parentWidget, "Download Failed", "Failed to save the file.")

    def finishDownload(self):
        reply = self.sender()
        self.saveFile(reply)
        self.downloads.pop(reply.url().toString(), None)
        reply.deleteLater()


class NetworkAccessManager(QtNetwork.QNetworkAccessManager):

    def __init__(self, manager, parent):
        super(NetworkAccessManager, self).__init__(parent)

        self.setCache(manager.cache())
        self.setCookieJar(manager.cookieJar())
        self.setProxy(manager.proxy())
        self.setProxyFactory(manager.proxyFactory())

    def createRequest(self, operation, request, device):
        if request.url().scheme() != "ftp":
            return QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, device)

        if operation == QtNetwork.QNetworkAccessManager.GetOperation:
            # Handle ftp:// URLs separately by creating custom QNetworkReply objects.
            return FtpReply(request.url(), self)
        else:
            return QtNetwork.QNetworkAccessManager.createRequest(self, operation, request, device)


class FtpReply(QtNetwork.QNetworkReply):

    def __init__(self, url, parent):
        super(FtpReply, self).__init__(parent)

        self.items = []
        self.content = QtCore.QByteArray()

        self.ftp = QtNetwork.QFtp(self)
        self.ftp.listInfo.connect(self.processListInfo)
        self.ftp.readyRead.connect(self.processData)
        self.ftp.commandFinished.connect(self.processCommand)

        self.offset = 0
        self.units = ["bytes", "K", "M", "G", "Ti", "Pi", "Ei", "Zi", "Yi"]

        self.setUrl(url)
        self.ftp.connectToHost(url.host())

    def processCommand(self, _, err):
        if err:
            self.setError(QtNetwork.QNetworkReply.ContentNotFoundError, "Unknown command")
            self.error.emit(QtNetwork.QNetworkReply.ContentNotFoundError)

        cmd = self.ftp.currentCommand()
        if cmd == QtNetwork.QFtp.ConnectToHost:
            self.ftp.login()
        elif cmd == QtNetwork.QFtp.Login:
            self.ftp.list(self.url().path())
        elif cmd == QtNetwork.QFtp.List:
            if len(self.items) == 1:
                self.ftp.get(self.url().path())
            else:
                self.setListContent()
        elif cmd == QtNetwork.QFtp.Get:
            self.setContent()

    def processListInfo(self, urlInfo):
        self.items.append(QtNetwork.QUrlInfo(urlInfo))

    def processData(self):
        self.content += self.ftp.readAll()

    def setContent(self):
        self.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Unbuffered)
        self.setHeader(QtNetwork.QNetworkRequest.ContentLengthHeader, len(self.content))
        self.readyRead.emit()
        self.finished.emit()
        self.ftp.close()

    def setListContent(self):
        u = self.url()
        if not u.path().endswith("/"):
            u.setPath(u.path() + "/")

        base_url = self.url().toString()
        base_path = u.path()

        self.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Unbuffered)
        content = (
            '<html>\n'
            '<head>\n'
            '  <title>%s</title>\n'
            '  <style type="text/css">\n'
            '  th { background-color: #aaaaaa; color: black }\n'
            '  table { border: solid 1px #aaaaaa }\n'
            '  tr.odd { background-color: #dddddd; color: black\n }\n'
            '  tr.even { background-color: white; color: black\n }\n'
            '  </style>\n'
            '</head>\n\n'
            '<body>\n'
            '<h1>Listing for %s</h1>\n\n'
            '<table align="center" cellspacing="0" width="90%%">\n'
            '<tr><th>Name</th><th>Size</th></tr>\n' % (QtCore.Qt.escape(base_url), base_path))

        parent = u.resolved(QtCore.QUrl(".."))

        if parent.isParentOf(u):
            content += ('<tr><td><strong><a href="%s">' % parent.toString()
            + 'Parent directory</a></strong></td><td></td></tr>\n')

        i = 0
        for item in self.items:
            child = u.resolved(QtCore.QUrl(item.name()))

            if i == 0:
                content += '<tr class="odd">'
            else:
                content += '<tr class="even">'

            content += '<td><a href="%s">%s</a></td>' % (child.toString(), QtCore.Qt.escape(item.name()))

            size = item.size()
            unit = 0
            while size:
                new_size = size // 1024
                if new_size and unit < len(self.units) - 1:
                    size = new_size
                    unit += 1
                else:
                    break

            if item.isFile():
                content += '<td>%s %s</td></tr>\n' % (str(size), self.units[unit])
            else:
                content += '<td></td></tr>\n'

            i = 1 - i

        content += '</table>\n</body>\n</html>\n'

        self.content = QtCore.QByteArray(content.encode('utf-8'))

        self.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "text/html; charset=UTF-8")
        self.setHeader(QtNetwork.QNetworkRequest.ContentLengthHeader, len(self.content))
        self.readyRead.emit()
        self.finished.emit()
        self.ftp.close()

    def abort(self):
        pass

    def bytesAvailable(self):
        return len(self.content) - self.offset + QtNetwork.QNetworkReply.bytesAvailable(self)

    def isSequential(self):
        return True

    def readData(self, maxSize):
        if self.offset < len(self.content):
            number = min(maxSize, len(self.content) - self.offset)
            data = self.content[self.offset:self.offset+number]
            self.offset += number
            return data.data()

        return None


if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)

    view = FtpView()
    view.setUrl(QtCore.QUrl("ftp://ftp.qt.nokia.com"))
    view.show()

    sys.exit(app.exec_())
