# -*- coding: utf-8 -*-
# fasttrans v0.01

import sys
from PyQt5 import QtWidgets, QtCore
import http.client
import hashlib
import json
import urllib.parse
import random
import re
import ctypes
from aip import AipOcr  # baidu ai接口


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
        self.getuserkeys()

    def getuserkeys(self):
        try:
            with open("config.json", 'r') as conf:
                config = json.load(conf)
            self.appid = config['AppID']
            self.secretKey = config['SecretKey']
            self.apiKey = config['APIKey']
            self.client = AipOcr(self.appid, self.apiKey, self.secretKey)
            self.ocrinit = True
        except Exception:
            self.ocrinit = False

    def imagetotext(self, filePath):
        # image = self.get_file_content(filePath)
        try:
            image = self.get_file_content(filePath)
            texts = self.client.basicGeneral(image)
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

    def trans(self, paras: dict):
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
        self.btn_trans.clicked.connect(self.translate)
        self.btn_shotscrn = QtWidgets.QPushButton("截图识别", self)
        self.btn_shotscrn.clicked.connect(self.shootScreen)
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
        self.check_box1.toggle()
        self.check_box2 = QtWidgets.QCheckBox('文字去回车', self)
        self.check_box2.toggle()
        # self.systray = QtWidgets.QSystemTrayIcon(self) #创建托盘
        # self.systray.setIcon(QtGui.QIcon(self.logo))
        # self.systray.activated.connect(self.iconActivated)
        # self.systray.setToolTip('FastTrans')

        self.initlayout() # 输出布局
        self.setWindowTitle("翻译助手 v0.1")
        self.resize(600, 600)

        self.transobj = baidu_translate() # 创建一个百度翻译对象
        if self.transobj.ocrinit:
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
    ft.show()
    sys.exit(app.exec_())

