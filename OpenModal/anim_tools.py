
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



import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

from pyqtgraph.opengl.shaders import *

import pyqtgraph.opengl as gl

import pyqtgraph as pg

import sys, traceback

import pandas as pd

import OpenModal.gui.widgets.prototype as prot

COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'w']
CUBE = np.array([[[-1.0, -1.0, -1.0],
                  [-1.0, -1.0, 1.0],
                  [-1.0, 1.0, 1.0]],
                 [[1.0, 1.0, -1.0],
                  [-1.0, -1.0, -1.0],
                  [-1.0, 1.0, -1.0]],
                 [[1.0, -1.0, 1.0],
                  [-1.0, -1.0, -1.0],
                  [1.0, -1.0, -1.0]],
                 [[1.0, 1.0, -1.0],
                  [1.0, -1.0, -1.0],
                  [-1.0, -1.0, -1.0]],
                 [[-1.0, -1.0, -1.0],
                  [-1.0, 1.0, 1.0],
                  [-1.0, 1.0, -1.0]],
                 [[1.0, -1.0, 1.0],
                  [-1.0, -1.0, 1.0],
                  [-1.0, -1.0, -1.0]],
                 [[-1.0, 1.0, 1.0],
                  [-1.0, -1.0, 1.0],
                  [1.0, -1.0, 1.0]],
                 [[1.0, 1.0, 1.0],
                  [1.0, -1.0, -1.0],
                  [1.0, 1.0, -1.0]],
                 [[1.0, -1.0, -1.0],
                  [1.0, 1.0, 1.0],
                  [1.0, -1.0, 1.0]],
                 [[1.0, 1.0, 1.0],
                  [1.0, 1.0, -1.0],
                  [-1.0, 1.0, -1.0]],
                 [[1.0, 1.0, 1.0],
                  [-1.0, 1.0, -1.0],
                  [-1.0, 1.0, 1.0]],
                 [[1.0, 1.0, 1.0],
                  [-1.0, 1.0, 1.0],
                  [1.0, -1.0, 1.0]]])

SHADER='OpenModal'


GLOPTS= {
        GL_DEPTH_TEST: True,
        GL_BLEND: False,
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False}
        #'glLightModeli':(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)}
SMOOTH=False # If TRUE then normals are recomputed when new triangles are added
COMPUTENORMALS=True
DRAW_EDGES_NODES=False
DRAW_EDGES_ELEMENTS=True
DRAW_EDGES_GCS=False
DRAW_EDGES_LCS=False

class CustomGLMeshItem(gl.GLMeshItem):
    def __init__(self, **kwds):
        super(CustomGLMeshItem, self).__init__(**kwds)

        self.add_shader()

    def add_shader(self):
        """
        Infiltrate custom shader code into GLMeshItem
        """

        module=pg.opengl.shaders

        shader_name='OpenModal'
        vertex_shader="""
                        varying vec4 diffuse,ambient,color2;
                        varying vec3 normal,halfVector;


                        void main()
                        {

                            gl_LightSource[0].position=(10,10,10);

                            gl_LightSource[0].ambient=(1,1,1,0.1); /* responsible for whiteout */

                            gl_LightSource[0].diffuse=(.01,.01,.01,0.7); /* responsible for whiteout */

                            gl_LightSource[0].specular=(0.01,0.01,0.01,1);

                            gl_LightSource[0].spotDirection=(0,0,0);




                            color2 = gl_Color;
                            /* first transform the normal into eye space and
                            normalize the result */
                            normal = normalize(gl_NormalMatrix * gl_Normal);

                            /* pass the halfVector to the fragment shader */
                            halfVector = gl_LightSource[0].halfVector.xyz;

                            /* Compute the diffuse, ambient and globalAmbient terms */
                            diffuse = gl_FrontMaterial.diffuse * gl_LightSource[0].diffuse;
                            ambient = gl_FrontMaterial.ambient * gl_LightSource[0].ambient;
                            ambient += gl_LightModel.ambient * gl_FrontMaterial.ambient;
                            gl_Position = ftransform();

                        }
            """

        fragment_shader="""
                            varying vec4 diffuse,ambient,color2;
                            varying vec3 normal,halfVector;

                            void main()
                            {
                                vec3 n,halfV,lightDir;
                                float NdotL,NdotHV;

                                gl_FrontMaterial.specular=0.001;
                                gl_FrontMaterial.shininess=0.001;

                                lightDir = vec3(gl_LightSource[0].position);

                                /* The ambient term will always be present */
                                vec4 color = ambient;
                                /* a fragment shader can't write a varying variable, hence we need
                                a new variable to store the normalized interpolated normal */
                                /* n = normalize(normal); */
                                /* compute the dot product between normal and ldir */

                               if (gl_FrontFacing) // is the fragment part of a front face?
                                {
                                    n = normalize(normal);

                                    NdotL = max(dot(n,lightDir),0.0);
                                    if (NdotL > 0.0) {
                                        color += diffuse * NdotL;
                                        halfV = normalize(halfVector);
                                        NdotHV = max(dot(n,halfV),0.0);
                                        color += gl_FrontMaterial.specular *
                                                gl_LightSource[0].specular *
                                                pow(NdotHV, gl_FrontMaterial.shininess);
                                    }

                                    gl_FragColor = color2 + color;
                                }
                              else // fragment is part of a back face
                                {
                                    n = normalize(-normal);

                                    NdotL = max(dot(n,lightDir),0.0);
                                    if (NdotL > 0.0) {
                                        color += diffuse * NdotL;
                                        halfV = normalize(halfVector);
                                        NdotHV = max(dot(n,halfV),0.0);
                                        color += gl_FrontMaterial.specular *
                                                gl_LightSource[0].specular *
                                                pow(NdotHV, gl_FrontMaterial.shininess);
                                    }

                                    gl_FragColor = color2 + color;
                                }

                            }

            """

        module.Shaders.append(module.ShaderProgram(shader_name,[module.VertexShader(vertex_shader),module.FragmentShader(fragment_shader)]))



def zyx_euler_to_rotation_matrix_ORIGINAL(th):
    """Convert the ZYX order (the one LMS uses) Euler
        angles to rotation matrix. Angles are given
        in radians.

        Note:
            Actually Tait-Bryant angles.
        """
    # -- Calculate sine and cosine values first.
    sz, sy, sx = [np.sin(value) for value in th]
    cz, cy, cx = [np.cos(value) for value in th]


    # -- Create and populate the rotation matrix.
    rotation_matrix = np.zeros((3, 3), dtype=float)

    #IF roataions are given in right handed CS
    # conversion between left and right handed rotations is done by multiplying rot angles by -1
    rotation_matrix[0, 0] = cy * cz
    rotation_matrix[0, 1] = cy * sz
    rotation_matrix[0, 2] = -sy
    rotation_matrix[1, 0] = sx * sy * cz - cy * sz
    rotation_matrix[1, 1] = sx * sy * sz + cx * cz
    rotation_matrix[1, 2] = sx * cy
    rotation_matrix[2, 0] = cx * sy * cx + sx * sz
    rotation_matrix[2, 1] = cx * sy * sz - sx * cz
    rotation_matrix[2, 2] = cx * cy

    # ## IF roataions are given in left handed CS
    # rotation_matrix[0, 0] = cy*cz
    # rotation_matrix[0, 1] = cz*sx*sy - cx*sz
    # rotation_matrix[0, 2] = cx*cz*sy + sx*sz
    # rotation_matrix[1, 0] = cy*sz
    # rotation_matrix[1, 1] = cx*cz + sx*sy*sz
    # rotation_matrix[1, 2] = -cz*sx + cx*sy*sz
    # rotation_matrix[2, 0] = -sy
    # rotation_matrix[2, 1] = cy*sx
    # rotation_matrix[2, 2] = cx*cy


    return rotation_matrix

def zyx_euler_to_rotation_matrix(th):
    """Convert the ZYX order (the one LMS uses) Euler
        angles to rotation matrix. Angles are given
        in radians.

        Note:
            Actually Tait-Bryant angles.
        """
    # -- Calculate sine and cosine values first.
    sz, sy, sx = [np.sin(value) for value in th]
    cz, cy, cx = [-np.cos(value) for value in th] # '-' sign so that roations behave as in LMS


    # -- Create and populate the rotation matrix.
    rotation_matrix = np.zeros((3, 3), dtype=float)

    #IF roataions are given in right handed CS
    # wikipedia - taint-bryan angles (second from top in table - X1Y2Z3)
    rotation_matrix[0, 0] = cy * cz
    rotation_matrix[0, 1] = -cy * sz
    rotation_matrix[0, 2] = sy
    rotation_matrix[1, 0] = cx * sz + cz * sx * sy
    rotation_matrix[1, 1] = cx * cz - sx * sy * sz
    rotation_matrix[1, 2] = -cy * sx
    rotation_matrix[2, 0] = sx * sz - cx * cz * sy
    rotation_matrix[2, 1] = cz * sx + cx * sy * sz
    rotation_matrix[2, 2] = cx * cy

    # wikipedia - taint-bryan angles (fifth from top in table - Z1Y2X3)
    # rotation_matrix[0, 0] = cx * cy
    # rotation_matrix[0, 1] = cx * sy * sz - cz * sx
    # rotation_matrix[0, 2] = sx * sz + cx * cz * sy
    # rotation_matrix[1, 0] = cy * sx
    # rotation_matrix[1, 1] = cx * cz + sx * sy * sz
    # rotation_matrix[1, 2] = cz * sx * sy - cx * sz
    # rotation_matrix[2, 0] = -sy
    # rotation_matrix[2, 1] = cy * sz
    # rotation_matrix[2, 2] = cy * cz

    # wikipedia - proper euler angles (first from bottom in table - Z1X2Z3)
    # rotation_matrix[0, 0] = cx * cz - cy * sx * sz
    # rotation_matrix[0, 1] = -cx * sz - cy * cz * sx
    # rotation_matrix[0, 2] = sx * sy
    # rotation_matrix[1, 0] = cz * sx + cx * cy * sz
    # rotation_matrix[1, 1] = cx * cy * cz - sx * sz
    # rotation_matrix[1, 2] = -cx * sy
    # rotation_matrix[2, 0] = sy * sz
    # rotation_matrix[2, 1] = cz * sy
    # rotation_matrix[2, 2] = cy

    # wikipedia - proper euler angles (second from bottom in table - Z1Y2Z3)
    # rotation_matrix[0, 0] = cx * cy * cz - sx * sz
    # rotation_matrix[0, 1] = -cz * sx - cx * cy * sz
    # rotation_matrix[0, 2] = cx * sy
    # rotation_matrix[1, 0] = cx * sz + cy * cz * sx
    # rotation_matrix[1, 1] = cx * cz - cy * sx * sz
    # rotation_matrix[1, 2] = sx * sy
    # rotation_matrix[2, 0] = -cz * sy
    # rotation_matrix[2, 1] = sy * sz
    # rotation_matrix[2, 2] = cy

    return rotation_matrix


def get_gcs_meshitem(gcs_meshitem, scale, alpha=0):
    """
    Take existing global coordinate system meshitem and scale it
    :return:
    """
    zero = np.array((0, 0, 0))
    x = np.array((1, 0, 0))
    y = np.array((0, 1, 0))
    z = np.array((0, 0, 1))

    verts = np.zeros((3, 3, 3))
    colors = np.zeros((3, 3, 4))

    # x dir triangle
    verts[0, 0, :] = zero
    verts[0, 1, :] = scale * x
    verts[0, 2, :] = scale / 5 * z
    colors[0, :, :] = (1, 0, 0, alpha)

    # y dir triangle
    verts[1, 0, :] = zero
    verts[1, 1, :] = scale * y
    verts[1, 2, :] = scale / 5 * z
    colors[1, :, :] = (0, 1, 0, alpha)

    # z dir triangle
    verts[2, 0, :] = zero
    verts[2, 1, :] = scale * z
    verts[2, 2, :] = scale / 5 * x
    colors[2, :, :] = (0, 0, 1, alpha)

    gcs_meshitem.setMeshData(vertexes=verts, vertexColors=colors, shader='balloon')
    gcs_meshitem.meshDataChanged()
    return gcs_meshitem

class ClickedSignal(QtCore.QObject):

    clicked = QtCore.pyqtSignal()

class GLView(gl.GLViewWidget):
    '''
    Subclass GLViewWidget to use events
    :return:
    '''

    def __init__(self, parent=None):

        self.selection_enabled = True

        super(GLView, self).__init__(parent)
        self.render_text_dict = {}  #for storing node labels
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)



        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground)


        #self.setAttribute(QtCore.Qt.WA_TintedBackground)
        #self.setAttribute(QtCore.Qt.WA_StyledBackground)
        #self.setAttribute(QtCore.Qt.WA_NoBackground)
        #self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        #self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        #self.setStyleSheet("background-color:black;")
        #self.setWindowOpacity(0.5)
        #self.setAutoFillBackground(False)


        self.default_width = 500
        self.default_height = 500
        self.setMinimumSize(QtCore.QSize(self.default_width, self.default_height))

        self.clicked_signal=ClickedSignal()


    def viewMatrix(self):
        tr = QtGui.QMatrix4x4()
        tr.translate( 0.0, 0.0, -self.opts['distance'])
        center = self.opts['center']
        tr.translate(-center.x(), -center.y(), -center.z())

        tr.rotate(self.opts['elevation']-90, 1, 0, 0)
        tr.rotate(self.opts['azimuth']+90, 0, 0, -1)


        return tr

    def orbit(self, azim, elev):
        """Orbits the camera around the center position. *azim* and *elev* are given in degrees."""
        self.opts['azimuth'] += azim
        #self.opts['elevation'] += elev
        self.opts['elevation'] = np.clip(self.opts['elevation'] + elev, -90, 90)
        self.update()

    def pan(self, dx, dy, dz, relative=False):
        """
        Moves the center (look-at) position while holding the camera in place.

        If relative=True, then the coordinates are interpreted such that x
        if in the global xy plane and points to the right side of the view, y is
        in the global xy plane and orthogonal to x, and z points in the global z
        direction. Distances are scaled roughly such that a value of 1.0 moves
        by one pixel on screen.

        """
        if not relative:
            self.opts['center'] += QtGui.QVector3D(dx, dy, dz)
        else:
            cPos = self.cameraPosition()
            cVec = self.opts['center'] - cPos
            dist = cVec.length()  ## distance from camera to center
            xDist = dist * 2. * np.tan(0.5 * self.opts['fov'] * np.pi / 180.)  ## approx. width of view at distance of center point
            xScale = xDist / self.width()



            zVec = QtGui.QVector3D(0,0,1)
            xVec = QtGui.QVector3D.crossProduct(zVec, cVec).normalized()
            yVec = QtGui.QVector3D.crossProduct(xVec, zVec).normalized()

            #print(self.opts['azimuth'],self.opts['elevation'])
            self.opts['center'] = self.opts['center'] + xVec * xScale * dx + yVec * xScale * dy + zVec * xScale * dz
        self.update()

    def mouseMoveEvent(self, ev):
        """
        Change default mouse move behaviour
        :param ev:
        :return:
        """
        diff = ev.pos() - self.mousePos
        self.mousePos = ev.pos()


        tr = QtGui.QMatrix4x4()
        tr.rotate(self.opts['elevation']-90, 1, 0, 0) # rotation angle, x , y , z
        tr.rotate(self.opts['azimuth']+90, 0, 0, -1) # rotation angle, x , y , z
        tr_diff=tr.inverted()[0]*QtGui.QVector4D(diff.x(),diff.y(),0,1)

        if ev.buttons() == QtCore.Qt.LeftButton:
            self.orbit(-diff.x(), diff.y())

            #print self.opts['azimuth'], self.opts['elevation']
        elif ev.buttons() == QtCore.Qt.MidButton:
            # if (ev.modifiers() & QtCore.Qt.ControlModifier):
            #
            #     self.pan(tr_diff.x(), tr_diff.y(), tr_diff.z(), relative=True)
            # else:
            #     self.pan(tr_diff.x(),tr_diff.y(),tr_diff.z() , relative=True)

            if self.opts['elevation']<0:

                #calc transform
                tr = QtGui.QMatrix4x4()
                tr.rotate(self.opts['elevation']+90, 1, 0, 0) # rotation angle, x , y , z
                tr.rotate(self.opts['azimuth']-90, 0, 0, -1) # rotation angle, x , y , z
                tr_diff=tr.inverted()[0]*QtGui.QVector4D(diff.x(),diff.y(),0,1)

                self.pan(-tr_diff.x(),-tr_diff.y(),-tr_diff.z(), relative=True)
            else:
                #calc transform
                tr = QtGui.QMatrix4x4()
                tr.rotate(self.opts['elevation']-90, 1, 0, 0) # rotation angle, x , y , z
                tr.rotate(self.opts['azimuth']+90, 0, 0, -1) # rotation angle, x , y , z
                tr_diff=tr.inverted()[0]*QtGui.QVector4D(diff.x(),diff.y(),0,1)

                self.pan(tr_diff.x(),tr_diff.y(), tr_diff.z(), relative=True)

    def paintGL(self, *args, **kwargs):
        '''
        Extend paintGL in order to plot text 3D
        :return:
        '''
        gl.GLViewWidget.paintGL(self, *args, **kwargs)
        self.qglColor(QtCore.Qt.black)

        #print gcs labels
        for i in [0,1,2]:
            self.renderText(self.csys_labels_loc[i,0], self.csys_labels_loc[i,1], self.csys_labels_loc[i,2],
                                            self.csys_labels_data[i])

        m = 0
        # combine data for render text
        if len(self.render_text_dict) == 0:
            self.node_labels_data = {}
        else:
            for model_id in self.render_text_dict:
                if m == 0:
                    self.node_labels_data = self.render_text_dict[model_id]
                    m = m + 1

                else:
                    self.node_labels_data = np.vstack((self.node_labels_data, self.render_text_dict[model_id]))
                    m = m + 1

        try:
            for i in range(len(self.node_labels_data)):
                # self.renderText(self.node_labels_data[i][1], self.node_labels_data[i][2], self.node_labels_data[i][3],
                #                 str(int(self.node_labels_data[i][0])))
                self.renderText(self.node_labels_data[i][1], self.node_labels_data[i][2], self.node_labels_data[i][3],
                                self.render_text_dict_str[i])


        except:
            print("Exception in user code:")
            print('-' * 60)
            traceback.print_exc(file=sys.stdout)
            print('-' * 60)

    def getCoord(self, x,y):


        region1=(x,y,1,1) #mouse click
        region = (region1[0], self.height()-(region1[1]+region1[3]), region1[2], region1[3])

        x0, y0, w, h = self.getViewport()

        # convert screen coordinates (region) to normalized device coordinates
        left   = ((region[0]-x0) * (2.0/w) - 1)
        bottom = ((region[1]-y0) * (2.0/h) - 1)


        # calculate pos at ndc3=1 and ndc3=-1
        aux=self.viewMatrix().inverted()[0]*self.projectionMatrix().inverted()[0]*QtGui.QVector4D(left,bottom,-1,1)
        start_point=aux/aux.w()

        aux=self.viewMatrix().inverted()[0]*self.projectionMatrix().inverted()[0]*QtGui.QVector4D(left,bottom,1,1)
        end_point=aux/aux.w()

        # get normalized vector
        ray_dir=end_point-start_point
        ray_dir.normalize()

        #convert to numpy array (not pyqt compatible!)
        #ray_dir=np.array(ray_dir.toVector3D().toTuple())
        #start_point=np.array(start_point.toVector3D().toTuple())

        ray_dir=np.array((ray_dir.x(),ray_dir.y(),ray_dir.z()))
        start_point=np.array((start_point.x(),start_point.y(),start_point.z()))

        return start_point,ray_dir


    def getCoord_OLD(self, x,y):

        #region1=(x,y,500,500) #mouse click
        region1=(x,y,1,1) #mouse click
        region = (region1[0], self.height()-(region1[1]+region1[3]), region1[2], region1[3])

        x0, y0, w, h = self.getViewport()
        dist = self.opts['distance']
        fov = self.opts['fov']
        nearClip = dist * 0.001
        farClip = dist * 1000.

        r = nearClip * np.tan(fov * 0.5 * np.pi / 180.)
        t = r * h / w

        # convert screen coordinates (region) to normalized device coordinates
        # Xnd = (Xw - X0) * 2/width - 1
        ## Note that X0 and width in these equations must be the values used in viewport
        # left  = r * ((region[0]-x0) * (2.0/w) - 1)
        # right = r * ((region[0]+region[2]-x0) * (2.0/w) - 1)
        # bottom = t * ((region[1]-y0) * (2.0/h) - 1)
        # top    = t * ((region[1]+region[3]-y0) * (2.0/h) - 1)

        left   = ((region[0]-x0) * (2.0/w) - 1)
        right  = ((region[0]+region[2]-x0) * (2.0/w) - 1)
        bottom = ((region[1]-y0) * (2.0/h) - 1)
        top    = ((region[1]+region[3]-y0) * (2.0/h) - 1)

        # Projection matrix
        #tr = QtGui.QMatrix4x4()
        #tr.frustum(left, right, bottom, top, nearClip, farClip)
        # return tr


        # #ray=np.linspace(-1,1,1000)
        # ray=np.linspace(0.99,1,100)
        #
        # for ndc3 in ray:
        #     aux=self.viewMatrix().inverted()[0]*self.projectionMatrix().inverted()[0]*QtGui.QVector4D(left,bottom,ndc3,1)
        #     fin_pos=aux/aux.w()
        #     print(fin_pos)

        # calculate pos at ndc3=1 and ndc3=-1
        aux=self.viewMatrix().inverted()[0]*self.projectionMatrix().inverted()[0]*QtGui.QVector4D(left,bottom,-1,1)
        start_point=aux/aux.w()

        aux=self.viewMatrix().inverted()[0]*self.projectionMatrix().inverted()[0]*QtGui.QVector4D(left,bottom,1,1)
        end_point=aux/aux.w()

        # get normalized vector
        ray_dir=end_point-start_point
        ray_dir.normalize()

        #convert to numpy array
        ray_dir=np.array(ray_dir.toVector3D().toTuple())
        start_point=np.array(start_point.toVector3D().toTuple())

        return start_point,ray_dir

        # get line eq, pos_ndc1 + t * ()

    def mouseReleaseEvent(self, ev):

        self.mousePos = ev.pos() #needs to be here so that mouseMove works

        # get selection ray
        start_point,ray_dir=self.getCoord(ev.pos().x(),ev.pos().y())

        self.ray=(start_point,ray_dir)
        self.clicked_signal.clicked.emit()

class AnimWidgBase(prot.SubWidget):
    def __init__(self, *args, **kwargs):
        # Initialize the object as a QWidget and
        # set its title and minimum width
        super(AnimWidgBase, self).__init__(*args, **kwargs)

        self.modaldata.current_model_id=0.0 # default active model_id

        self.preferences=kwargs['preferences']

        self.plot_gcs = True  # by default global coordinte system will be plotted
        #self.current_model_id=None

        self.models = {}
        self.model_buttons={} # dict of model buttons for activation

        # input type in geometry
        self.gcs_type=0 # Global coordinate system type: 0 = cartesian, 1 = cylindrical

        #initialize global coordinate system meshitem
        self.gcs_meshitem = CustomGLMeshItem(vertexes=np.array([[[0, 0, 0], [0, 0, 0], [0, 0, 0]]]),
                                          vertexColors=np.array([[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]]),
                                          shader=SHADER,drawEdges=DRAW_EDGES_GCS,computeNormals=COMPUTENORMALS, glOptions=GLOPTS,smooth=SMOOTH)


        # Create 3D graphics widget
        self.model_view = GLView()
        self.model_view.setBackgroundColor('w')
        self.model_view.wheelEvent = self.wheel_event  #override wheel event for autoscaling
        self.model_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.model_view.customContextMenuRequested.connect(self.model_view_context_menu)
        self.draw_node_labels = False  # node labels are not ploted by default
        self.model_view.addItem(self.gcs_meshitem)

        #plot gcs acis labels
        self.plot_gcs_labels()

        # create actions
        self.create_model_view_actions()
        self.create_toolbar_actions()

        # Create layout and add widgets
        self.create_layout()

        # initialize gcs
        self.manage_gcs_plot()

    def delete_model(self,delete_all=False):

            # remove model data
            remove_ids=[]
            for model_id, model_obj in self.models.items():
                if delete_all:
                    #delete all models
                    #deactivate model and refresh model
                    model_obj.activated=False
                    model_obj.refresh()

                    # next line is commented because we are removing models only from GUI and not from modal_data obj
                    #self.modaldata.remove_model(model_obj.model_id)
                    remove_ids.append(model_obj.model_id)
                else:
                    #remove only activated model
                    if model_obj.activated:
                        #deactivate model and refresh model
                        model_obj.activated=False
                        model_obj.refresh()

                        self.modaldata.remove_model(model_obj.model_id)
                        remove_ids.append(model_obj.model_id)


            # remove model object
            for model_id in remove_ids:
                self.models.pop(model_id, None)

            # delete button associated with model
            for model_id in remove_ids:
                #self.model_buttons[str(model_id)].deleteLater()
                #self.model_buttons.pop(str(model_id), None)
                #find button and delete it from widget
                for child in self.children():
                    if child==self.model_buttons[int(model_id)]:
                        child.deleteLater()
                self.model_buttons[int(model_id)].deleteLater()
                self.model_buttons.pop(int(model_id), None)

            if delete_all:
                #remove models from gui, modal_data obj is overwritten on reload
                pass
            else:
                # reset index of info dataframe (don't reset index when using buttons...due to partial func when creating button)
                self.modaldata.tables['info'] = self.modaldata.tables['info'].reset_index(drop=True)

                # refresh uff tree
                self.build_uff_tree(self.modaldata,refresh=True)

                self.plot_activated_models()


    def create_model_view_actions(self):

        self.plot_node_labels_act = QtWidgets.QAction('Node labels', self, checkable=True,
                                                statusTip='Plot node labels', triggered=self.plot_node_labels)
        self.plot_node_lcs_act = QtWidgets.QAction('Node csys', self, checkable=True,
                                             statusTip='Plot node local coordinate system',
                                             triggered=self.plot_node_lcs_ctxmenu)
        self.plot_gcs_act = QtWidgets.QAction('Global csys', self, checkable=True,
                                        statusTip='Plot global coordinate system', triggered=self.plot_gcs_ctxmenu)
        self.plot_gcs_act.setChecked(True)  # by default gcs is plotted

        self.plot_nodes_act = QtWidgets.QAction('Nodes', self, checkable=True,
                                               statusTip='Plot nodes', triggered=self.plot_nodes)
        self.plot_nodes_act.setChecked(True)  # by default nodes are plotted

        self.plot_lines_act = QtWidgets.QAction('Lines', self, checkable=True,
                                               statusTip='Plot lines', triggered=self.plot_lines)

        self.plot_lines_act.setChecked(True)  # by default lines are plotted

        self.plot_elements_act = QtWidgets.QAction('Elements', self, checkable=True,
                                               statusTip='Plot elements', triggered=self.plot_elements)

        self.plot_elements_act.setChecked(True)  # by default elements are plotted

        self.node_color_act = QtWidgets.QAction('Nodes', self,
                                        statusTip='Choose node color', triggered=self.choose_node_color)
        self.line_color_act = QtWidgets.QAction('Lines', self,
                                        statusTip='Choose line color', triggered=self.choose_line_color)
        self.elem_color_act = QtWidgets.QAction('Elements', self,
                                        statusTip='Choose element color', triggered=self.choose_elem_color)

        self.cart_csys_act = QtWidgets.QAction('Cartesian', self, checkable=True,
                                               statusTip='Change input to cartesian csys', triggered=self.cart_csys)
        self.cart_csys_act.setChecked(True)  # cartesian system is default
        self.cyl_csys_act = QtWidgets.QAction('Cylindrical', self, checkable=True,
                                               statusTip='Change input to cylindrical csys', triggered=self.cyl_csys)

    def cart_csys(self):
        """
        Select cartesian coordinate system
        :return:
        """
        self.gcs_type=0
        self.cart_csys_act.setChecked(True)
        self.cyl_csys_act.setChecked(False)
        self.nodes_data_mode()

    def cyl_csys(self):
        """
        Select cylindrical coordinate system
        :return:
        """
        self.gcs_type=1
        self.cart_csys_act.setChecked(False)
        self.cyl_csys_act.setChecked(True)
        self.nodes_data_mode()

    def create_toolbar_actions(self):


        self.act_fit_view = QtWidgets.QAction(QtGui.QIcon('gui/icons/Icon_fit_view.png'), 'Fit view', self,
                                        statusTip='Fit 3D view', triggered=self.autofit_3d_view)

    def create_layout(self):
        """
        Create layout of the central Qwidget and add widgets
        :return:
        """

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.model_view)
        self.setLayout(vbox)

    def choose_elem_color(self):
        """
        Open color chooser dialogue and change element color
        :return:
        """
        col = QtWidgets.QColorDialog.getColor()

        if col.isValid():
            for model_id, model_obj in self.models.items():
                if model_obj.activated:
                    model_obj.set_elem_color(col,'triangle')
        self.plot_activated_models()

    def choose_node_color(self):
        """
        Open color chooser dialogue and change node color
        :return:
        """
        col = QtWidgets.QColorDialog.getColor()

        if col.isValid():
            for model_id, model_obj in self.models.items():
                if model_obj.activated:
                    model_obj.set_node_color(col)
        self.plot_activated_models()

    def choose_line_color(self):
        """
        Open color chooser dialogue and change node color
        :return:
        """
        col = QtWidgets.QColorDialog.getColor()

        if col.isValid():
            for model_id, model_obj in self.models.items():
                if model_obj.activated:
                    model_obj.set_elem_color(col,'line')
        self.plot_activated_models()

    def wheel_event(self, ev):
        '''
        Override model_view wheelEvent for autoscale of cubes
        :param ev:
        :return:
        '''
        if (ev.modifiers() & QtCore.Qt.ControlModifier):
            self.model_view.opts['fov'] *= 0.999 ** (ev.angleDelta().y())
        else:
            self.model_view.opts['distance'] *= 0.999 ** (ev.angleDelta().y())

        self.model_view.update()
        self.plot_activated_models(wheel_event=True)

    def deactivate_all(self):
        """
        Deactivate all models and uncheck associated buttons
        :return:
        """
        for model_id, model_obj in self.models.items():
            model_obj.activated=False
            model_obj.deactivate()
            self.model_buttons[int(model_id)].setChecked(False)

    def calc_node_lcs_NEW(self):
        """
        Based on euler angles calculate lcs vectors
        Takes values in degrees from modal data object
        :return:
        """
        x = np.array((1, 0, 0))
        y = np.array((0, 1, 0))
        z = np.array((0, 0, 1))

        num_of_nodes = len(self.modaldata.tables['geometry'].index.values)

        lcs_x_data = np.zeros((num_of_nodes, 3))
        lcs_y_data = np.zeros((num_of_nodes, 3))
        lcs_z_data = np.zeros((num_of_nodes, 3))

        lcs = pd.DataFrame(
            columns=['lcs_x1', 'lcs_x2', 'lcs_x3', 'lcs_y1', 'lcs_y2', 'lcs_y3', 'lcs_z1', 'lcs_z2', 'lcs_z3'])


        eul_ang = self.modaldata.tables['geometry'].ix[:, ['thz', 'thy', 'thx']].values * np.pi / 180

        for rot in [0,1,2]:

            for i in range(num_of_nodes):

                #eul_ang = self.modal_data.tables['geometry'][['thz', 'thy', 'thx']].iloc[i].values*np.pi/180
                #eul_ang =self.modal_data.tables['geometry'].ix[i,['thz', 'thy', 'thx']].values*np.pi/180

                if rot==0:
                    rotation_matrix = zyx_euler_to_rotation_matrix([eul_ang[i,rot],0,0])
                if rot==1:
                    rotation_matrix = zyx_euler_to_rotation_matrix([0,eul_ang[i,rot],0])
                if rot==2:
                    rotation_matrix = zyx_euler_to_rotation_matrix([0,0,eul_ang[i,rot]])

                if rot==0:
                    lcs_x_data[i, :] = np.dot(rotation_matrix, x)
                    lcs_y_data[i, :] = np.dot(rotation_matrix, y)
                    lcs_z_data[i, :] = np.dot(rotation_matrix, z)
                else:
                    lcs_x_data[i, :] = np.dot(rotation_matrix, lcs_x_data[i, :])
                    lcs_y_data[i, :] = np.dot(rotation_matrix, lcs_y_data[i, :])
                    lcs_z_data[i, :] = np.dot(rotation_matrix, lcs_z_data[i, :])
            # LCS x-dir
            lcs['lcs_x1'] = lcs_x_data[:, 0]
            lcs['lcs_x2'] = lcs_x_data[:, 1]
            lcs['lcs_x3'] = lcs_x_data[:, 2]

            # LCS y-dir
            lcs['lcs_y1'] = lcs_y_data[:, 0]
            lcs['lcs_y2'] = lcs_y_data[:, 1]
            lcs['lcs_y3'] = lcs_y_data[:, 2]

            # LCS z-dir
            lcs['lcs_z1'] = lcs_z_data[:, 0]
            lcs['lcs_z2'] = lcs_z_data[:, 1]
            lcs['lcs_z3'] = lcs_z_data[:, 2]

        # add local coordinate system data to geometry table
        try:
            self.modaldata.tables['geometry'] = self.modaldata.tables['geometry'].join(lcs)
        except ValueError:
            self.modaldata.tables['geometry'][
                ['lcs_x1', 'lcs_x2', 'lcs_x3', 'lcs_y1', 'lcs_y2', 'lcs_y3', 'lcs_z1', 'lcs_z2', 'lcs_z3']] = lcs

    def calc_node_lcs(self):
        """
        Based on euler angles calculate lcs vectors
        Takes values in degrees from modal data object
        :return:
        """
        x = np.array((1, 0, 0))
        y = np.array((0, 1, 0))
        z = np.array((0, 0, 1))

        num_of_nodes = len(self.modaldata.tables['geometry'].index.values)

        lcs_x_data = np.zeros((num_of_nodes, 3))
        lcs_y_data = np.zeros((num_of_nodes, 3))
        lcs_z_data = np.zeros((num_of_nodes, 3))

        lcs = pd.DataFrame(
            columns=['lcs_x1', 'lcs_x2', 'lcs_x3', 'lcs_y1', 'lcs_y2', 'lcs_y3', 'lcs_z1', 'lcs_z2', 'lcs_z3'])


        eul_ang = self.modaldata.tables['geometry'].ix[:, ['thz', 'thy', 'thx']].values * np.pi / 180

        for i in range(num_of_nodes):

            #eul_ang = self.modal_data.tables['geometry'][['thz', 'thy', 'thx']].iloc[i].values*np.pi/180
            #eul_ang =self.modal_data.tables['geometry'].ix[i,['thz', 'thy', 'thx']].values*np.pi/180

            rotation_matrix = zyx_euler_to_rotation_matrix(eul_ang[i,:])


            lcs_x_data[i, :] = np.dot(rotation_matrix.transpose(), x)
            lcs_y_data[i, :] = np.dot(rotation_matrix.transpose(), y)
            lcs_z_data[i, :] = np.dot(rotation_matrix.transpose(), z)
            # WIKIPEDIA (euler angles - Rotation matrix): transpose the matrices
            # (then each matrix transforms the initial coordinates
            # of a vector remaining fixed to the coordinates of the same vector
            # measured in the rotated reference system; same rotation axis, same angles,
            # but now the coordinate system rotates, rather than the vector).


        # LCS x-dir
        lcs['lcs_x1'] = lcs_x_data[:, 0]
        lcs['lcs_x2'] = lcs_x_data[:, 1]
        lcs['lcs_x3'] = lcs_x_data[:, 2]

        # LCS y-dir
        lcs['lcs_y1'] = lcs_y_data[:, 0]
        lcs['lcs_y2'] = lcs_y_data[:, 1]
        lcs['lcs_y3'] = lcs_y_data[:, 2]

        # LCS z-dir
        lcs['lcs_z1'] = lcs_z_data[:, 0]
        lcs['lcs_z2'] = lcs_z_data[:, 1]
        lcs['lcs_z3'] = lcs_z_data[:, 2]

        # add local coordinate system data to geometry table
        try:
            self.modaldata.tables['geometry'] = self.modaldata.tables['geometry'].join(lcs)
        except ValueError:
            self.modaldata.tables['geometry'][
                ['lcs_x1', 'lcs_x2', 'lcs_x3', 'lcs_y1', 'lcs_y2', 'lcs_y3', 'lcs_z1', 'lcs_z2', 'lcs_z3']] = lcs

    def plot_node_lcs_ctxmenu(self):
        '''
        method to be used for ploting lcs via context menu
        :return:
        '''

        #check if node lcs need to be ploted (via context menu)
        plot_node_lcs = self.plot_node_lcs_act.isChecked()

        for model_id, model_obj in self.models.items():
            model_obj.plot_node_lcs_act = plot_node_lcs

        # models need to be refreshed
        self.plot_activated_models()

    def plot_nodes(self):
        '''
        method to be used for ploting lcs via context menu
        :return:
        '''

        #check if node lcs need to be ploted (via context menu)
        plot_nodes = self.plot_nodes_act.isChecked()


        for model_id, model_obj in self.models.items():
            model_obj.plot_nodes_act = plot_nodes

        # models need to be refreshed
        self.plot_activated_models()

    def plot_lines(self):
        '''
        method to be used for ploting lcs via context menu
        :return:
        '''

        #check if node lcs need to be ploted (via context menu)
        plot_lines = self.plot_lines_act.isChecked()


        for model_id, model_obj in self.models.items():
            model_obj.plot_lines_act = plot_lines

        # models need to be refreshed
        self.plot_activated_models()

    def plot_elements(self):
        '''
        method to be used for ploting lcs via context menu
        :return:
        '''

        #check if node lcs need to be ploted (via context menu)
        plot_elements = self.plot_elements_act.isChecked()


        for model_id, model_obj in self.models.items():
            model_obj.plot_elements_act = plot_elements

        # models need to be refreshed
        self.plot_activated_models()

    def plot_gcs_ctxmenu(self):
        '''
        method to be used for ploting gcs via context menu
        :return:
        '''

        #check if node lcs need to be ploted (via context menu)
        self.plot_gcs = self.plot_gcs_act.isChecked()

        self.manage_gcs_plot()


    def plot_node_labels(self):
        '''
        method to be used for ploting node labels via context menu
        :return:
        '''

        #check if node lcs need to be ploted (via context menu)
        plot_node_labels_act = self.plot_node_labels_act.isChecked()

        # Tell models that labels need to be plotted
        for model_id, model_obj in self.models.items():
            model_obj.plot_node_labels_act = plot_node_labels_act

        # models need to be refreshed in order to store node label data
        self.plot_activated_models()

    def plot_gcs_labels(self):
        '''
        - prepare and paint node csys axis labels
        '''

        # Get current distance from 3D view (for setting cube size)
        dist = self.model_view.opts['distance']

        # Ratio due to app window size changes
        window_width_ratio = self.get_window_width_ratio()

        # scale of global coordinate system triangles
        gcs_scale = dist * 0.03 * 2 / window_width_ratio

        csys_labels_loc=np.array(((1,0,0),
                                  (0,1,0),
                                  (0,0,1)))

        csys_labels_loc=csys_labels_loc*gcs_scale

        #send data to GLview widget
        self.model_view.csys_labels_loc = csys_labels_loc
        self.model_view.csys_labels_data = ['X','Y','Z']


    def get_window_width_ratio(self):
        # Ratio due to app window size changes
        current_width = self.model_view.width()  # current 3d_view width in pixels
        window_width_ratio = current_width / self.model_view.default_width
        return window_width_ratio

    def manage_gcs_plot(self):

        # Get current distance from 3D view (for setting cube size)
        dist = self.model_view.opts['distance']

        # Ratio due to app window size changes
        window_width_ratio = self.get_window_width_ratio()

        # scale of global coordinate system triangles
        gcs_scale = dist * 0.03 * 2 / window_width_ratio

        if self.plot_gcs:
            self.gcs_meshitem = get_gcs_meshitem(self.gcs_meshitem,gcs_scale)
            self.model_view.updateGL()
            if self.gcs_meshitem in self.model_view.items:
                pass
            else:
                self.model_view.addItem(self.gcs_meshitem)
        else:
            if self.gcs_meshitem in self.model_view.items:
                self.model_view.removeItem(self.gcs_meshitem)

    def plot_activated_models(self, wheel_event=False):
        """
        Plot all activated models
        :return:
        """

        for model_id, model_obj in self.models.items():
            model_obj.refresh(wheel_event)

        # plot scaled global coordinate system
        self.manage_gcs_plot()
        # update gcs labels
        self.plot_gcs_labels()

        #TODO: highlight clicked plotitem
    #     import functools
    #     items=self.plot_area.items
    #     for item in items:
    #         if isinstance(item,pg.PlotCurveItem):
    #             #self.connect(item, QtCore.pyqtSignal("pltClicked()"), functools.partial(self.plot_item_clicked, item))
    #             #self.connect(item, QtCore.pyqtSignal("sigClicked()"), functools.partial(self.plot_item_clicked, item))
    #             item.sigClicked.connect(self.plot_item_clicked)
    #
    #
    # def plot_item_clicked(self,item):
    #     print('*')
    #     print(item.name())
    #     print('*')

    def autofit_3d_view(self):
        '''
        Do autofit on 3d view (based on activated models)
        :return:
        '''
        max_dist = 0

        geo_data = self.modaldata.tables['geometry'].set_index('model_id')

        for model_id, model_obj in self.models.items():

            if model_obj.activated:

                # add offset to max coordinate location
                max_dist_ = np.max(np.abs(geo_data.ix[model_id][['x', 'y', 'z']].max().values)) + \
                            np.max(np.abs([model_obj.offset['x'], model_obj.offset['y'], model_obj.offset['z']]))
                if max_dist_ >= max_dist:
                    max_dist = max_dist_

        # Ratio due to app window size changes
        window_width_ratio = self.get_window_width_ratio()

        # Ratio due to fov
        fov = np.tan(self.model_view.opts['fov'] / 2 * np.pi / 180)

        # Factor due to perspective
        fac = 1.1

        # take care of the zoom
        self.model_view.opts['distance'] = max_dist * window_width_ratio / fov * fac

        #reset any movement of center
        self.model_view.opts['center'] = QtGui.QVector3D(0, 0, 0)

        #self.model_view.updateGL()

        #referesh
        self.plot_activated_models(wheel_event=True)
