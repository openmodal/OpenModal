
def _init_qt4():
    # Create missing qt.conf files if possible
    # See http://qt-project.org/doc/qt-4.8/qt-conf.html
    import sys, os
    try:
        import codecs
        path = os.path.abspath(os.path.dirname(__file__))
        path1 = path.replace("\\", "/")
        content = u"[Paths]\nPrefix = %s\nBinaries = %s\n" % (path1, path1)
        # create qt.conf in the package folder
        qtconf = os.path.join(path, "qt.conf")
        if not os.path.exists(qtconf):
            try:
                fh = codecs.open(qtconf, "w", "utf-8")
                fh.write(content)
                fh.close()
            except Exception:
                pass
        # create qt.conf next to sys.executable
        qtconf = os.path.join(os.path.dirname(sys.executable), "qt.conf")
        if not os.path.exists(qtconf):
            try:
                fh = codecs.open(qtconf, "w", "utf-8")
                fh.write(content)
                fh.close()
            except Exception:
                pass
    except Exception:
        pass

    # Add the PyQt4 directory to the PATH so other extensions can find the DLLs
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        os.environ['PATH'] = '%s;%s' % (path, os.environ['PATH'])
    except Exception:
        pass

_init_qt4()

del _init_qt4
