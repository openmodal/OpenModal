
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


'''

Setup script for OpenModal.

Lines under multiprocessing import have to be uncommented first. Then ...


Run the following command to build application exe:
        python setup.py build

Run the following command to build msi installer:
        python setup.py bdist_msi

'''
import os
import sys
from cx_Freeze import setup, Executable

os.environ['TCL_LIBRARY'] = "C:\\Users\\Matjaz\\Anaconda3\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Users\\Matjaz\\Anaconda3\\tcl\\tk8.6"

base = None
# if sys.platform == 'win32':
#     base = 'Win32GUI'

def include_OpenGL():
    path_base = "C:\\Users\\Matjaz\\Anaconda3\\Lib\\site-packages\\OpenGL"
    skip_count = len(path_base)
    zip_includes = [(path_base, "OpenGL")]
    for root, sub_folders, files in os.walk(path_base):
        for file_in_root in files:
            zip_includes.append(
                    ("{}".format(os.path.join(root, file_in_root)),
                     "{}".format(os.path.join("OpenGL", root[skip_count+1:], file_in_root))
                    )
            )
    return zip_includes

zip_includes=include_OpenGL()

shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "Open Modal",     # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]openmodal.exe",   # Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     r'OpenModal/gui/icons/limes_logo.ico',                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     ),
    #
    # ("StartupShortcut",        # Shortcut
    #  "StartupFolder",          # Directory_
    #  "program",     # Name
    #  "TARGETDIR",              # Component_
    #  "[TARGETDIR]main.exe",   # Target
    #  None,                     # Arguments
    #  None,                     # Description
    #  None,                     # Hotkey
    #  None,                     # Icon
    #  None,                     # IconIndex
    #  None,                     # ShowCmd
    #  'TARGETDIR'               # WkDir
    #  ),

    ]

bdist_msi_options = {
    'upgrade_code': '{111111-TROLOLO-FIRST-VERSION-CODE}',
    'add_to_path': False,
    'initial_target_dir': r'[ProgramFiles64Folder]\Open Modal',
    'data': dict(Shortcut=shortcut_table)
}

options = {
    'build_exe': {
        'packages': ['traceback','numpy','matplotlib','qtawesome','six','tkinter','pandas','bisect',
                     'multiprocessing'],
        'includes': ['PyQt4'],
        'path': sys.path + ['OpenModal'],
        'zip_includes': zip_includes,
        'include_files' : [('C:\\Users\\Matjaz\\Anaconda3\\Lib\\site-packages\\scipy\\special\\_ufuncs.cp35-win_amd64.pyd','_ufuncs.cp35-win_amd64.pyd'),
                           ('C:\\Users\\Matjaz\\Anaconda3\\Lib\\bisect.py','bisect.py'),
                           ('C:\\Users\\Matjaz\\Anaconda3\\Lib\\site-packages\\scipy\\special\\_ufuncs_cxx.cp35-win_amd64.pyd','_ufuncs_cxx.cp35-win_amd64.pyd'),
                           'C:\\Users\\Matjaz\\Anaconda3\\Lib\\site-packages\\qtawesome',
                           #'C:\\_MPirnat\\Python\\pycharm\\OpenModalAlpha_freeze_v3\\OpenModal\\gui',
                           ('C:\\Users\\Matjaz\\Anaconda3\\Lib\\site-packages\\numpy\\core\\mkl_intel_thread.dll','mkl_intel_thread.dll'),
                           ('C:\\Users\\Matjaz\\Anaconda3\\Lib\\site-packages\\numpy\\core\\mkl_core.dll','mkl_core.dll'),
                           ('C:\\Users\\Matjaz\\Anaconda3\\Lib\\site-packages\\numpy\\core\\mkl_avx.dll','mkl_avx.dll'),
                           ('C:\\Users\\Matjaz\\Anaconda3\\Lib\\site-packages\\numpy\\core\\libiomp5md.dll','libiomp5md.dll'),
                           (r'OpenModal/gui/styles', r'gui/styles'),
                           (r'OpenModal/gui/icons', r'gui/icons')]
    },
    'bdist_msi': bdist_msi_options

}




executables = [
    Executable('OpenModal\openmodal.py', base=base)
               # shortcutName="OpenModal", shortcutDir="DesktopFolder",
               # icon=r'OpenModal/gui/icons/limes_logo.ico')
]

setup(name='OpenModal',
      version='0.1',
      description='OpenModal first freeze',
      options=options,
      executables=executables
      )
