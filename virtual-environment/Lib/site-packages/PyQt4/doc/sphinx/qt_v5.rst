PyQt4 and Qt v5
===============

Building Against Qt v5
----------------------

PyQt4 can be built against Qt v5 in exactly the same way that it is built
against Qt v4.  However only a Qt v4 compatible subset of Qt v5 is supported,
specifically:

- any classes added in Qt v5 *are not* supported
- any new features added in Qt v5 to classes that exist in Qt v4 *are*
  supported
- any features that are marked as deprecated in Qt v5 *are* supported.

Qt v5 handles connections to signals with optional arguments in a slightly
different way than Qt v4.  PyQt4 works around this as best it can but cannot do
so in the case where signals that have optional arguments in Qt v5 (but not in
Qt v4) are emitted using old-style signals (i.e. using :meth:`QObject.emit`).
Instead you should use new-style signals (i.e. use the :meth:`emit` method of
the bound signal).

The :option:`--no-deprecated <configure.py --no-deprecated>` option to PyQt4's
:program:`configure.py` can be used to disable the support for the deprecated
features.  This can be useful in the porting of PyQt4 applications to PyQt5.
