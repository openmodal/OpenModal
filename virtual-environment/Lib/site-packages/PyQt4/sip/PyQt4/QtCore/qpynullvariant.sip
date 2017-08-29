// This is the SIP specification of the QPyNullVariant class.
//
// Copyright (c) 2015 Riverbank Computing Limited <info@riverbankcomputing.com>
// 
// This file is part of PyQt4.
// 
// This file may be used under the terms of the GNU General Public License
// version 3.0 as published by the Free Software Foundation and appearing in
// the file LICENSE included in the packaging of this file.  Please review the
// following information to ensure the GNU General Public License version 3.0
// requirements will be met: http://www.gnu.org/copyleft/gpl.html.
// 
// If you do not wish to use this file under the terms of the GPL version 3.0
// then you may purchase a commercial license.  For more information contact
// info@riverbankcomputing.com.
// 
// This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
// WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.


class QPyNullVariant /API=QVariant:2 -/
{
%TypeHeaderCode
#include <qvariant.h>

typedef QVariant QPyNullVariant;
%End

public:
    QPyNullVariant(SIP_PYOBJECT type);
%MethodCode
        sipCpp = qpycore_qpynullvariant(a0);
%End

    QVariant::Type type() const;
    int userType() const;
    const char *typeName();
    bool isNull() const;

    int __bool__() const;
%MethodCode
        // This makes QPyNullVariant behave like None when truth testing.
        sipRes = 0;
%End

private:
    QPyNullVariant(const QPyNullVariant &);
};
