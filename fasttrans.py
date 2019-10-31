# -*- coding: utf-8 -*-
# fasttrans v0.01

import sys
from PyQt5 import QtWidgets, QtCore, Qt
import http.client
import hashlib
import json
import urllib.parse
import random
import re
import ctypes
from pathlib import Path

from aip import AipOcr  # baidu ai接口
errormsg = {
    0 : '未找到配置文件!',
    1 : 'AppID或秘钥配置错误!',
    2 : '无网络连接!',
    3 : ''
}

class baidu_translate(QtCore.QObject):

    transresult = QtCore.pyqtSignal(str)
    ocrresult = QtCore.pyqtSignal(str)
    ocrinit = False
    appid = ''
    secretKey = ''
    apiKey = ''

    def __init__(self):
        super(baidu_translate, self).__init__()
        self.httpClient = None
        self.url = '/api/trans/vip/translate'
        self.q = ''
        self.fromLang = ''
        self.toLang = ''

    def getcfgdata(self):
        cfgfile = Path('config.json')
        if cfgfile.is_file():
            with open("config.json", 'r') as conf:
                config = json.load(conf)
            self.appid = config['AppID']
            self.secretKey = config['SecretKey']
            self.apiKey = config['APIKey']
            return 1
        else:
            return 0

    def savecfgdata(self):
        file =  open("config.json", 'w+')
        config = {
            'AppID' : self.appid,
            'SecretKey' : self.secretKey,
            'APIKey' : self.apiKey
        }
        json.dump(config,file,ensure_ascii=False)
        file.close()


    def showDialog(self, errcode):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg = errormsg[errcode]
        msgBox.setText(msg)
        msgBox.exec()

    def imagetotext(self, filePath):
        # image = self.get_file_content(filePath)
        client = AipOcr(self.appid, self.apiKey, self.secretKey)
        try:
            image = self.get_file_content(filePath)
            texts = client.basicGeneral(image)
            ret = ""
            for words in texts["words_result"]:
                ret = ret + "".join(words.get("words", ""))
            self.ocrresult.emit(ret)  # 返回OCR结果
        except Exception as e:
            self.ocrresult.emit('error')

    def get_file_content(self, filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

    def transstart(self, paras: dict):
        self.q = paras['src']
        self.fromLang = paras['fromlang']
        self.toLang = paras['tolang']
        self.trans(paras)

    def trans(self):
        appid = '20151113000005349'
        secretKey = 'osubCEzlGjzvw8qdQc41'
        salt = random.randint(32768, 65536)
        sign = appid + self.q + str(salt) + secretKey
        sign = hashlib.md5(sign.encode()).hexdigest()
        myurl = self.url + '?appid=' + appid + '&q=' + urllib.parse.quote(
            self.q) + '&from=' + self.fromLang + '&to=' + self.toLang + '&salt=' + str(salt) + '&sign=' + sign
        try:
            httpClient = http.client.HTTPConnection('api.fanyi.baidu.com')
            httpClient.request('GET', myurl)
            # response是HTTPResponse对象
            response = httpClient.getresponse()
            jsonResponse = response.read().decode("utf-8")  # 获得返回的结果，结果为json格式
            js = json.loads(jsonResponse)  # 将json格式的结果转换字典结构
            if 'trans_result' in js:
                self.transresult.emit(str(js["trans_result"][0]["dst"]))  # 取得翻译后的文本结果
            elif 'error_code' in js:
                self.transresut.emit('error:' + str(js['error_code']) + str(js['error_msg']))
        except Exception as e:
            self.transresult.emit('网络连接错误')

class setting(QtWidgets.QWidget):

    def __init__(self):
        super(setting,self).__init__()
        self.label1 = QtWidgets.QLabel('设置百度云OCR参数',self)
        self.label2 = QtWidgets.QLabel('AppID:',self)
        self.label3 = QtWidgets.QLabel('APIKey:',self)
        self.label4 = QtWidgets.QLabel('SecretKey:',self)
        self.label5 = QtWidgets.QLabel('',self)
        self.text_appid = QtWidgets.QLineEdit()
        self.text_apikey = QtWidgets.QLineEdit()
        self.text_seckey = QtWidgets.QLineEdit()

        self.btn_ok = QtWidgets.QPushButton('确定',self)
        self.btn_ok.clicked.connect(self.confirm)
        self.btn_cancel = QtWidgets.QPushButton('取消',self)
        self.btn_cancel.clicked.connect(self.cancel)
        self.groupbox = QtWidgets.QGroupBox('百度云OCR参数',self)
        self.v_box = QtWidgets.QVBoxLayout()
        self.h_box1 = QtWidgets.QHBoxLayout()
        self.h_box2 = QtWidgets.QHBoxLayout()
        self.h_box3 = QtWidgets.QHBoxLayout()
        self.h_box4 = QtWidgets.QHBoxLayout()
        self.h_box0 = QtWidgets.QHBoxLayout()

        self.trans = baidu_translate()
        self.initlayout()
        self.fillingtextbox()

    def initlayout(self):
        self.label5.setOpenExternalLinks(True)
        self.label5.setText("<a href=\"https://login.bce.baidu.com/?account=&redirect=http%3A%2F%2Fconsole.bce.baidu.com%2Fai%2F%3Ffromai%3D1#/ai/ocr/overview/index\">单击注册百度AIP")
        self.h_box1.addWidget(self.label2)
        self.h_box1.addStretch(1)
        self.h_box1.addWidget(self.text_appid)
        self.h_box2.addWidget(self.label3)
        self.h_box2.addStretch(1)
        self.h_box2.addWidget(self.text_apikey)
        self.h_box3.addWidget(self.label4)
        self.h_box3.addStretch(1)
        self.h_box3.addWidget(self.text_seckey)
        self.h_box4.addWidget(self.btn_ok)
        self.h_box4.addWidget(self.btn_cancel)
        self.v_box.addWidget(self.label1)
        self.v_box.addLayout(self.h_box1)
        self.v_box.addLayout(self.h_box2)
        self.v_box.addLayout(self.h_box3)
        self.v_box.addWidget(self.label5)
        self.v_box.addStretch(1)
        self.v_box.addLayout(self.h_box4)
        self.groupbox.setLayout(self.v_box)
        self.groupbox.alignment = 0
        # self.groupbox.resize(300,300)
        self.h_box0.addWidget(self.groupbox, stretch=0)
        self.setLayout(self.h_box0)
        self.setWindowTitle("翻译助手 v0.1")
        self.resize(300, 250)

    def fillingtextbox(self):
        if self.trans.getcfgdata():
            self.text_appid.setText(self.trans.appid)
            self.text_seckey.setText(self.trans.secretKey)
            self.text_apikey.setText(self.trans.apiKey)
            return 1
        else:
            return 0

    def confirm(self):
        self.trans.savecfgdata()
        self.close()

    def cancel(self):
        self.close()


class fasttrans(QtWidgets.QWidget):

    src_lang_show = ['英语', '自动检测', '中文', '日语']
    src_lang_code = ['en', 'auto', 'zh', 'jp']
    dst_lang_show = ['中文', '英语', '日语']
    dst_lang_code = ['zh', 'en', 'jp']
    starttranssignal = QtCore.pyqtSignal(dict)
    errorsignal = QtCore.pyqtSignal(str)
    imagesignal = QtCore.pyqtSignal(str)

    def __init__(self):
        super(fasttrans, self).__init__()
        self.recent_clip = ""
        self.trans_text = ""
        # self.logo = "icon/logo.ico"
        self.transparas = {'src': '', 'fromlang': '', 'tolang': ''}
        self.text_src = QtWidgets.QTextEdit()
        self.text_dst = QtWidgets.QTextEdit()
        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.update)
        self.clipboard = QtWidgets.QApplication.clipboard()
        self.btn_trans = QtWidgets.QPushButton("翻译", self)
        self.btn_trans.setToolTip('使用百度翻译引擎翻译')
        self.btn_trans.clicked.connect(self.translate)
        self.btn_shotscrn = QtWidgets.QPushButton("截图翻译", self)
        self.btn_shotscrn.setToolTip('点击框选文字进行翻译')
        self.btn_shotscrn.clicked.connect(self.shootScreen)
        self.btn_setting = QtWidgets.QPushButton('截图翻译设置',self)
        self.lb1 = QtWidgets.QLabel('源语言')
        self.lb2 = QtWidgets.QLabel('目标语言')
        self.lb3 = QtWidgets.QLabel('原文字:')
        self.lb4 = QtWidgets.QLabel('翻译结果:')
        self.cbox_src = QtWidgets.QComboBox()
        self.cbox_dst = QtWidgets.QComboBox()
        self.v_box1 = QtWidgets.QVBoxLayout()
        self.v_box2 = QtWidgets.QVBoxLayout()
        self.h_box = QtWidgets.QHBoxLayout()
        self.check_box1 = QtWidgets.QCheckBox('监视剪贴板', self)
        self.check_box1.setToolTip('监视剪贴板内容发生改变时自动进行翻译')
        self.check_box1.toggle()
        self.check_box2 = QtWidgets.QCheckBox('文字去回车', self)
        self.check_box2.setToolTip('自动去除剪贴板内文字中的回车(多用于从pdf文件复制的内容)')
        self.check_box2.toggle()
        # self.systray = QtWidgets.QSystemTrayIcon(self) #创建托盘
        # self.systray.setIcon(QtGui.QIcon(self.logo))
        # self.systray.activated.connect(self.iconActivated)
        # self.systray.setToolTip('FastTrans')

        self.initlayout() # 输出布局
        self.setWindowTitle("翻译助手 v0.1")
        self.resize(600, 600)

        self.transobj = baidu_translate() # 创建一个百度翻译对象

        if self.transobj.getcfgdata():
            self.btn_shotscrn.setEnabled(True)
        else:
            self.btn_shotscrn.setEnabled(False)
        self.transthread = QtCore.QThread()  # 创建一个翻译线程
        self.transobj.moveToThread(self.transthread)
        self.starttranssignal.connect(self.transobj.transstart) # 开始翻译信号连接至翻译函数
        self.transobj.transresult.connect(self.text_dst.setPlainText)   # 连接翻译结果同文本框
        self.transobj.ocrresult.connect(self.reciveocr)  # 连接OCR结果

        self.imagesignal.connect(self.transobj.imagetotext)
        self.clipboard.dataChanged.connect(self.clipboardchanged)

        self.transthread.start()

    def initlayout(self):
        self.cbox_src.addItems(self.src_lang_show)
        self.cbox_dst.addItems(self.dst_lang_show)

        self.text_src.setPlainText(self.recent_clip)
        self.text_dst.setPlainText(self.trans_text)

        self.v_box1.addWidget(self.lb3)
        self.v_box1.addWidget(self.text_src)
        self.v_box1.addWidget(self.lb4)
        self.v_box1.addWidget(self.text_dst)

        self.v_box2.addStretch(1)
        self.v_box2.addWidget(self.check_box1)
        self.v_box2.addWidget(self.check_box2)
        self.v_box2.addStretch(1)
        self.v_box2.addWidget(self.lb1)
        self.v_box2.addWidget(self.cbox_src)
        self.v_box2.addWidget(self.lb2)
        self.v_box2.addWidget(self.cbox_dst)
        self.v_box2.addStretch(1)
        self.v_box2.addWidget(self.btn_trans)
        self.v_box2.addWidget(self.btn_shotscrn)
        self.v_box2.addWidget(self.btn_setting)
        self.v_box2.addStretch(1)
        self.h_box.addLayout(self.v_box1)
        self.h_box.addLayout(self.v_box2)
        self.setLayout(self.h_box)

    def clipboardchanged(self):
        if self.check_box1.isChecked():
            mimeData = self.clipboard.mimeData()
            if mimeData.hasImage():  # 判断剪贴板内容类型
                clipimage = self.clipboard.image()
                clipimage.save('temp.png','PNG')
                self.imagesignal.emit('temp.png')
            elif mimeData.hasText():
                cliptext = self.clipboard.text()
                if self.check_box2.isChecked():
                    form_text = self.formattext(cliptext)
                    self.text_src.setPlainText(form_text)
                else:
                    self.text_src.setPlainText(cliptext)

    def reciveocr(self, text):  # 收到OCR结果
        self.text_src.setPlainText(text)
        self.translate()

    def formattext(self, text):  # 从剪贴板获得文字调整格式
        form_text =  re.sub(r"\s{2,}", " ", text)
        return form_text

    def capture(self):  # 调用微信截图
        # 未完成的功能，现在暂时调用微信的截图dll，无法获取其回调函数，无法实现隐藏窗口
        try:
            dll = ctypes.cdll.LoadLibrary('PrScrn.dll')
        except Exception:
            self.errorsignal.emit("PrScrn.Dll加载出错!")
            return
        else:
            try:
                dll.PrScrn(0)
            except Exception:
                self.errorsignal.emit("截图错误!")
                return

    def shootScreen(self):  # 调用微信截图模块prscrn.dll
        # 未完成的功能，现在暂时调用微信的截图dll，无法获取其回调函数，无法实现隐藏窗口
        #self.hide()
        #QtTest.QTest.qWait(10)
        self.capture()
        #self.show()

    def translate(self):  # 发送翻译参数调用翻译
        self.transparas['src'] = self.text_src.toPlainText()
        self.transparas['fromlang'] = self.src_lang_code[self.cbox_src.currentIndex()]
        self.transparas['tolang'] = self.dst_lang_code[self.cbox_dst.currentIndex()]
        self.starttranssignal.emit(self.transparas)  # 启动翻译

    def closeEvent(self, event):
        sys.exit(app.exec_())

if __name__ =='__main__':
    app = QtWidgets.QApplication(sys.argv)
    ft = fasttrans()
    setting = setting()
    ft.btn_setting.clicked.connect(setting.show)
    ft.show()
    sys.exit(app.exec_())

