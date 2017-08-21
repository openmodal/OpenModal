.. image:: https://img.shields.io/pypi/v/QtAwesome.svg
   :target: https://pypi.python.org/pypi/QtAwesome/
   :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/QtAwesome.svg
   :target: https://pypi.python.org/pypi/QtAwesome/
   :alt: Number of PyPI downloads

QtAwesome - Iconic Fonts in PyQt and PySide applications
========================================================

QtAwesome enables iconic fonts such as Font Awesome and Elusive Icons in PyQt and PySide applications.

It is a port to Python - PyQt / PySide of the QtAwesome C++ library by Rick Blommers.

.. code-block:: python

    # Get icons by name.
    fa_icon = qta.icon('fa.flag')
    fa_button = QtGui.QPushButton(fa_icon, 'Font Awesome!')

    asl_icon = qta.icon('ei.asl')
    elusive_button = QtGui.QPushButton(asl_icon, 'Elusive Icons!')


