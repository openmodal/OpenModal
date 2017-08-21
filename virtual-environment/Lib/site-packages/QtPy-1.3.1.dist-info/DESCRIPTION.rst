.. image:: https://img.shields.io/pypi/v/QtPy.svg
   :target: https://pypi.python.org/pypi/QtPy/
   :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/QtPy.svg
   :target: https://pypi.python.org/pypi/QtPy/
   :alt: Number of PyPI downloads

QtPy: Abtraction layer for PyQt5/PyQt4/PySide
=============================================

**QtPy** (pronounced *'cutie pie'*) is a small abstraction layer that lets you
write applications using a single api call to either PyQt or PySide.

It provides support for PyQt5, PyQt4 and PySide using the PyQt5 layout (where
the QtGui module has been split into QtGui and QtWidgets).

Basically, you write your code as if you were using PyQt5 but import qt from
``qtpy`` instead of ``PyQt5``.

- `Issue tracker`_
- `Changelog`_


Attribution and acknowledgements
--------------------------------

This project is based on the `pyqode.qt`_ project and the `spyderlib.qt`_
module from the `spyder`_ project.

Unlike **pyqode.qt** this is not a namespace package so it is not *tied*
to a particular project, or namespace.

.. _spyder: https://github.com/spyder-ide/spyder
.. _spyderlib.qt: https://github.com/spyder-ide/spyder/tree/master/spyderlib/qt
.. _pyqode.qt: https://github.com/pyQode/pyqode.qt
.. _Changelog: https://github.com/spyder-ide/qtpy/blob/master/CHANGELOG.md
.. _Issue tracker: https://github.com/spyder-ide/qtpy/issues


