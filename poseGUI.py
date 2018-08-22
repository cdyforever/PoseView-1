#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys
import cv2
from PyQt5 import QtCore, QtGui,QtWidgets
import os
import numpy as np
# reload(sys)
# sys.setdefaultencoding('utf-8')

from tf_pose.estimator import TfPoseEstimator
from tf_pose.networks import get_graph_path, model_wh
from tf_pose.common import convertFloat

#default target size
WIDTH = 320
HEIGHT = 240

SHOW_PAF = False
SHOW_HEATMAP = False

#initialize the network should set the target_size（net input size）
poseModel = TfPoseEstimator(get_graph_path('mobilenet'), target_size=(WIDTH, HEIGHT))

class Ui_MainWindow(QtWidgets.QWidget):

    isPafX = False
    isPafY = False
    isHeat = False

    def __init__(self, parent=None):
        super(Ui_MainWindow, self).__init__(parent)

        # self.face_recong = face.Recognition()
        self.timer_camera = QtCore.QTimer()
        self.cap = cv2.VideoCapture()
        self.CAM_NUM = 0
        self.set_ui()
        self.slot_init()
        self.__flag_work = 0
        self.x =0

    def set_ui(self):
        self.__layout_main = QtWidgets.QHBoxLayout()
        self.__layout_fun_button = QtWidgets.QVBoxLayout()
        self.__layout_data_show = QtWidgets.QVBoxLayout()
        self.button_open_camera = QtWidgets.QPushButton(u'打开相机')
        self.button_open_video = QtWidgets.QPushButton(u'打开视频')
        self.button_pafx = QtWidgets.QPushButton(u'显示水平PAF')
        self.button_pafy = QtWidgets.QPushButton(u'显示垂直PAF')
        self.button_heat = QtWidgets.QPushButton(u'显示HeatMap')
        self.button_close_any = QtWidgets.QPushButton(u'关闭')
        self.button_close = QtWidgets.QPushButton(u'退出')
        self.button_open_video.setMinimumHeight(50)
        self.button_close_any.setMinimumHeight(50)
        self.button_open_camera.setMinimumHeight(50)
        self.button_close.setMinimumHeight(50)
        self.button_close.move(10,100)

        # 信息显示
        self.label_show_camera = QtWidgets.QLabel()
        self.label_move = QtWidgets.QLabel()
        self.label_move.setFixedSize(200, 200)

        self.label_show_camera.setFixedSize(641, 481)
        self.label_show_camera.setAutoFillBackground(False)

        self.__layout_fun_button.addWidget(self.button_open_camera)
        self.__layout_fun_button.addWidget(self.button_open_video)
        self.__layout_fun_button.addWidget(self.button_close_any)
        self.__layout_fun_button.addWidget(self.button_heat)
        self.__layout_fun_button.addWidget(self.button_pafx)
        self.__layout_fun_button.addWidget(self.button_pafy)
        self.button_close_any.setVisible(False)
        self.__layout_fun_button.addWidget(self.button_close)
        self.__layout_fun_button.addWidget(self.label_move)

        self.__layout_main.addLayout(self.__layout_fun_button)
        self.__layout_main.addWidget(self.label_show_camera)

        self.setLayout(self.__layout_main)
        self.label_move.raise_()
        self.setWindowTitle(u'人体姿态估计')

    # def mousePressEvent(self, QMouseEvent):
    #     x = QMouseEvent.x()
    #     y = QMouseEvent.y()
    #     self.label_move.move(0,0)
    #     print(x,y)
    #     print(self.label_move.pos())

    def slot_init(self):
        self.button_open_camera.clicked.connect(self.button_open_camera_click)
        self.timer_camera.timeout.connect(self.show_camera)
        self.button_open_video.clicked.connect(self.button_open_video_click)
        self.button_pafx.clicked.connect(self.button_pafx_click)
        self.button_pafy.clicked.connect(self.button_pafy_click)
        self.button_heat.clicked.connect(self.button_heat_click)
        self.button_close_any.clicked.connect(self.closeVideo)
        self.button_close.clicked.connect(self.close)

    def closeVideo(self):
        if self.cap.isOpened():
            self.cap.release()
        if self.timer_camera.isActive():
            self.timer_camera.stop()
        self.button_open_video.setVisible(True)
        self.button_open_camera.setVisible(True)
        self.button_close_any.setVisible(False)

    def button_pafx_click(self):
        Ui_MainWindow.isPafX = not Ui_MainWindow.isPafX
    
    def button_pafy_click(self):
        Ui_MainWindow.isPafY = not Ui_MainWindow.isPafY
    
    def button_heat_click(self):
        Ui_MainWindow.isHeat = not Ui_MainWindow.isHeat

    def button_open_video_click(self):
        if self.timer_camera.isActive() == False:
            fileName, filetype = QtWidgets.QFileDialog.getOpenFileName(self,
                "选取文件","C:/","All Files (*);;Text Files (*.mp4)")
            print(fileName, filetype)
            flag = self.cap.open(fileName)
            if flag == False:
                msg = QtWidgets.QMessageBox.warning(self, u"Warning", u"请检查视频格式是否正确", buttons=QtWidgets.QMessageBox.Ok,
                                                defaultButton=QtWidgets.QMessageBox.Ok)
            else:
                self.timer_camera.start(30)
                self.button_open_video.setVisible(False)
                self.button_open_camera.setVisible(False)
                self.button_close_any.setVisible(True)
        else:
            self.timer_camera.stop()
            self.cap.release()
            self.label_show_camera.clear()
            self.button_open_video.setText(u'打开视频')

    def button_open_camera_click(self):
        if self.timer_camera.isActive() == False:
            flag = self.cap.open(self.CAM_NUM)
            if flag == False:
                msg = QtWidgets.QMessageBox.warning(self, u"Warning", u"请检测相机与电脑是否连接正确", buttons=QtWidgets.QMessageBox.Ok,
                                                defaultButton=QtWidgets.QMessageBox.Ok)
            # if msg==QtGui.QMessageBox.Cancel:
            #                     pass
            else:
                self.timer_camera.start(30)
                self.button_open_video.setVisible(False)
                self.button_open_camera.setVisible(False)
                self.button_close_any.setVisible(True)
        else:
            self.timer_camera.stop()
            self.cap.release()
            self.label_show_camera.clear()
            self.button_open_camera.setText(u'打开相机')

    # show image on mainwindow
    def show_camera(self):
        flag, self.image = self.cap.read()
        if flag:
            humans = poseModel.inference(self.image ,resize_to_default=(WIDTH > 0 and HEIGHT > 0), upsample_size=4.0)
            if Ui_MainWindow.isPafX:
                print("Now show the pafX")
                self.image = poseModel.pafMat
                self.image = np.amax(np.absolute(self.image[:,:,::2]), axis=2)
                show = convertFloat(self.image)
                print(self.image)
                show = cv2.cvtColor(show, cv2.COLOR_GRAY2RGB)
                print(show)
            elif Ui_MainWindow.isPafY:
                self.image = poseModel.pafMat
                self.image = np.amax(np.absolute(self.image[:,:,1::2]), axis=2)
                show = convertFloat(self.image)
                show = cv2.cvtColor(show, cv2.COLOR_GRAY2RGB)
            elif Ui_MainWindow.isHeat:
                self.image = poseModel.heatMat
                self.image = np.amax(np.absolute(self.image[:,:,:-1]), axis=2)
                show = convertFloat(self.image)
                show = cv2.cvtColor(show, cv2.COLOR_GRAY2RGB)
            else:
                self.image = TfPoseEstimator.draw_humans(self.image, humans, imgcopy=False)
                #show = cv2.resize(self.image, (640, 480))
                show = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            show = cv2.resize(show, (640, 480))
            showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
            self.label_show_camera.setPixmap(QtGui.QPixmap.fromImage(showImage))
        else:
            self.closeVideo()

    def closeEvent(self, event):
        ok = QtWidgets.QPushButton()
        cacel = QtWidgets.QPushButton()
        msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, u"关闭", u"是否关闭！")
        msg.addButton(ok,QtWidgets.QMessageBox.ActionRole)
        msg.addButton(cacel, QtWidgets.QMessageBox.RejectRole)
        ok.setText(u'确定')
        cacel.setText(u'取消')
        # msg.setDetailedText('sdfsdff')
        if msg.exec_() == QtWidgets.QMessageBox.RejectRole:
            event.ignore()
        else:
            #             self.socket_client.send_command(self.socket_client.current_user_command)
            if self.cap.isOpened():
                self.cap.release()
            if self.timer_camera.isActive():
                self.timer_camera.stop()
            event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = Ui_MainWindow()
    ui.show()
    sys.exit(app.exec_())