# -*- coding: utf-8 -*-
import os
import sys
from PySide.QtGui import *
from PySide.QtCore import *

from framework.gui.msgbox import *
from framework.core.uimailbox import *
from framework.gui.widget import ImageWidget

import resources_rc
from settings import RaspiModeManager
from raspi_io.utility import scan_server
from raspi_io import TVService, MmalGraph, RaspiSocketError


class RaspiRemoteDisplay(QWidget):
    Version = "0.1"
    ScanTimeout = 0.05
    DefaultResolution = "1920x1080"
    AcceptFormats = ("bmp", "jpg", "png", "jpeg")

    def __init__(self):
        super(RaspiRemoteDisplay, self).__init__()

        self.tv = None
        self.graph = None
        self.modes = RaspiModeManager()

        self.__initUi()
        self.__initData()
        self.__initSignalAndSlots()

    def __initUi(self):
        self.ui_mail = UiMailBox(self)
        self.ui_reduce_size = QCheckBox()
        self.ui_device_list = QComboBox()
        self.ui_timing_list = QComboBox()
        self.ui_image_preview = ImageWidget(640, 480)
        self.ui_image_preview.drawFromText(self.tr("请先连接树莓派"))
        self.ui_reset_select = QPushButton(self.tr("重新选择"))
        self.ui_reset_timing = QPushButton(self.tr("重置分辨率"))

        for element in (self.ui_timing_list, self.ui_reset_timing, self.ui_reduce_size):
            element.setDisabled(True)

        tools_layout = QHBoxLayout()
        tools_layout.addWidget(QLabel(self.tr("树莓派列表：")))
        tools_layout.addWidget(self.ui_device_list)
        tools_layout.addWidget(self.ui_reset_select)
        tools_layout.addWidget(QSplitter())
        tools_layout.addWidget(QLabel(self.tr("显示器分辨率：")))
        tools_layout.addWidget(self.ui_timing_list)
        tools_layout.addWidget(self.ui_reset_timing)
        tools_layout.addWidget(QSplitter())
        tools_layout.addWidget(QLabel(self.tr("BMP 转为 PNG")))
        tools_layout.addWidget(self.ui_reduce_size)

        layout = QVBoxLayout()
        layout.addLayout(tools_layout)
        layout.addWidget(self.ui_image_preview)
        self.setLayout(layout)
        self.setWindowTitle(self.tr("树莓派远程显示工具 v{}".format(self.Version)))
        self.setWindowIcon(QIcon(QPixmap(":/icon/resources/icon.ico")))
        self.setFixedSize(self.sizeHint())

    def __initData(self):
        self.ui_device_list.addItem(self.tr("请选择树莓派"))
        self.ui_device_list.addItems(scan_server(self.ScanTimeout))
        for res, mode in self.modes.get_modes().items():
            self.ui_timing_list.addItem(res, mode)
        self.ui_timing_list.setCurrentIndex(self.modes.get_index_from_resolution(self.DefaultResolution))

    def __initSignalAndSlots(self):
        self.ui_reset_select.clicked.connect(self.__slotResetDevice)
        self.ui_reset_timing.clicked.connect(self.__slotResetTiming)
        self.ui_device_list.currentIndexChanged.connect(self.__slotSelectDevice)
        self.ui_timing_list.currentIndexChanged.connect(self.__slotSelectTiming)

    def __slotResetDevice(self):
        self.setAcceptDrops(False)
        self.ui_device_list.clear()
        self.ui_device_list.addItem(self.tr("请选择树莓派"))
        self.ui_image_preview.drawFromText(self.tr("请先连接树莓派"))
        self.ui_device_list.addItems(scan_server(self.ScanTimeout))
        self.ui_device_list.setEnabled(True)
        for element in (self.ui_timing_list, self.ui_reset_timing, self.ui_reduce_size):
            element.setDisabled(True)

        del self.tv
        self.tv = None
        del self.graph
        self.graph = None

    def __slotResetTiming(self):
        self.ui_timing_list.setEnabled(True)
        self.ui_reset_timing.setDisabled(True)

    def __slotSelectDevice(self, index):
        try:
            if index <= 0:
                return

            # Get raspberry pi address and resolution
            address = self.ui_device_list.itemText(index)
            mode = self.ui_timing_list.itemData(self.ui_timing_list.currentIndex())

            # Create TVService and MmalGraph object and accept drop
            self.tv = TVService(address)
            self.graph = MmalGraph(address)
            self.tv.set_explicit(TVService.DMT, mode)
            self.setAcceptDrops(True)

            self.ui_image_preview.drawFromText(
                self.tr("拖动图片到此显示\n（{}）".format("、".join(self.AcceptFormats).upper()))
            )
            self.ui_device_list.setDisabled(True)
            self.ui_reset_select.setEnabled(True)
            self.ui_reset_timing.setEnabled(True)
            self.ui_reduce_size.setEnabled(True)
        except RaspiSocketError as err:
            self.ui_mail.send(MessageBoxMail(MB_TYPE_ERR, "连接错误",  "{}".format(err)))

    def __slotSelectTiming(self, item):
        try:

            if item <= 0:
                return

            if not isinstance(self.tv, TVService) or not isinstance(self.graph, MmalGraph):
                raise RuntimeError("请先连接树莓派")

            # Change raspberry pi mode and re-open image
            self.tv.set_explicit(TVService.DMT, self.ui_timing_list.itemData(item))
            self.graph.open(self.graph.uri)

            self.ui_timing_list.setDisabled(True)
            self.ui_reset_timing.setEnabled(True)
        except RuntimeError as err:
            self.ui_mail.send(MessageBoxMail(MB_TYPE_ERR, "运行错误", "{}".format(err)))
        except RaspiSocketError as err:
            self.ui_mail.send(MessageBoxMail(MB_TYPE_ERR, "连接错误",  "{}".format(err)))

    def dragEnterEvent(self, ev):
        for url in ev.mimeData().urls():
            path = url.toLocalFile()
            fmt = os.path.splitext(path)[-1][1:].lower()
            if fmt in self.AcceptFormats:
                # Accept drag, preview image
                ev.acceptProposedAction()
                self.ui_image_preview.drawFromFs(path)

    def dropEvent(self, ev):
        for url in ev.mimeData().urls():
            path = url.toLocalFile()
            reduce_size = self.ui_reduce_size.isChecked()
            if isinstance(self.graph, MmalGraph):
                # Background display
                self.ui_mail.send(CallbackFuncMail(self.graph.open, args=(path.encode("gbk"), reduce_size)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QTextCodec.setCodecForTr(QTextCodec.codecForName("UTF-8"))
    widget = RaspiRemoteDisplay()
    widget.show()
    sys.exit(app.exec_())
