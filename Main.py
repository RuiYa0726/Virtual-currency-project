from UI.Ui_GUI import *
import time
from PyQt5 import QtCore, QtWidgets,QtGui
import sys
import os
import csv
from PyQt5.QtCore import *#信号相关
from PyQt5.QtWidgets import *#窗体相关
import ViewFunction.view1,ViewFunction.view1put,ViewFunction.view3,ViewFunction.Dview3,ViewFunction.view5,ViewFunction.Dview5
import ViewFunction.view2,ViewFunction.Dview2,ViewFunction.view8,ViewFunction.view9,ViewFunction.HView,ViewFunction.view4
import ViewFunction.view2P,ViewFunction.Dview2P
import matplotlib
from PyQt5.QtGui import QPainter,QPixmap,QIcon
matplotlib.use("Qt5Agg")  # 声明使用QT5
import matplotlib.pyplot as plt
import datetime

class MainWindow(QMainWindow,Ui_MainWindow):#括号内为继承的父类
    switch_window1 = pyqtSignal()  # 跳转信号
    switch_window2 = pyqtSignal()  # 跳转信号
    switch_window3 = pyqtSignal()  # 跳转信号
    switch_window4 = pyqtSignal()  # 跳转信号
    def __init__(self):
        super(MainWindow,self).__init__()#调用父类的方法
        self.setupUi(self)
        self.pushButton.clicked.connect(self.goDataUp)
        self.pushButton_2.clicked.connect(self.goAddrClus)
        self.pushButton_3.clicked.connect(self.goAnoDet)
        self.pushButton_4.clicked.connect(self.goVisual)

        self.switch_window1.connect(self.show_DataUp)
        self.switch_window2.connect(self.show_AddrClus)
        self.switch_window3.connect(self.show_AnoDet)
        self.switch_window4.connect(self.show_Visual)
    def paintEvent(self, event):# 设置背景图片，平铺到整个窗口，随着窗口改变而改变
        painter = QPainter(self)
        pixmap = QPixmap("/home/tr/background.png")
        painter.drawPixmap(self.rect(), pixmap)

    def goDataUp(self):
        self.switch_window1.emit()
    def goAddrClus(self):
        self.switch_window2.emit()
    def goAnoDet(self):
        self.switch_window3.emit()
    def goVisual(self):
        self.switch_window4.emit()
    # 跳转到数据更新窗口, 不关闭原页面
    def show_DataUp(self):
        self.DataUp = DataUpWindow()
        self.DataUp.show()
    # 跳转到地址聚类窗口, 注意关闭原页面
    def show_AddrClus(self):
        self.AddrClus= AddrClusWindow()
        self.close()
        self.AddrClus.show()
    # 跳转到异常检测窗口, 注意关闭原页面
    def show_AnoDet(self):
        self.AnoDet = AnoDetWindow()
        self.close()
        self.AnoDet.show()
    # 跳转到可视化窗口, 注意关闭原页面
    def show_Visual(self):
        self.Visual= VisualWindow()
        self.close()
        self.Visual.show()

class DataUpWindow(QWidget,DataUpdate_Ui_Form):#数据更新页面
    def __init__(self):
        super(DataUpWindow,self).__init__()
        self.setupUi(self)
        
        # 显示区块时间
        self.db = ViewFunction.view9.DataUpdate()
        res = self.db.queryDate()
        print(res)
        self.label.setText(res)

        # 创建线程
        self.backend = ViewFunction.view9.BackendThread()
        # 连接信号
        self.pushButton.clicked.connect(self.db.outputData) # 数据入库
        self.pushButton_2.clicked.connect(self.dataUpdate)  # 数据更新
        self.pushButton_3.clicked.connect(self.stop)        # 更新停止
        self.backend.update_date.connect(self.handleDisplay)
        self.backend.stop_signal.connect(self.stopThread)
        self.backend.auto_stop_signal.connect(self.stopThread)
        self.thread = QThread()
        self.backend.moveToThread(self.thread)
        # 开始线程
        self.thread.started.connect(self.backend.run)

    # 开始更新
    def dataUpdate(self):
        self.thread.start()
        self.label.setText("[+]数据更新中......")
        self.pushButton.setEnabled(False)
        self.pushButton_3.setEnabled(True) # 新添加

    # 停止更新
    def stop(self):
        self.backend.stop_signal.emit()

    # 将shell内容输出到文本框
    def handleDisplay(self, text):
        cursor = self.textBrowser.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.textBrowser.setTextCursor(cursor)
        self.textBrowser.ensureCursorVisible()

    # 停止线程
    def stopThread(self):
        self.backend.terminate()
        self.thread.quit()
        self.thread.wait()
        self.clean()
        res = self.db.queryDate()
        self.label.setText(res)
        self.pushButton.setEnabled(True)
        self.pushButton_3.setEnabled(False)
        # 打开比特币客户端继续同步
        os.system("echo '123' | sudo -S /home/hmy/code/Blockchain/MIT_dataset/bitcoin-0.19/src/bitcoind -datadir='/home/hmy/code/Blockchain/MIT_dataset/BTC_database' &")

    # 文件清理
    def clean(self):
        fileList = os.listdir("/code/tr/ProjectView_santu")
        if 'stop.txt' in fileList:
            os.system("rm stop.txt")

class AddrClusWindow(QWidget, AddrClus_Ui_Form):#地址聚类页面
    switch_window2 = pyqtSignal(int)  # 跳转到地址聚类页面信号
    def __init__(self):
        super(AddrClusWindow,self).__init__()
        self.setupUi(self)
        # self.BTCaddr = self.lineEdit.text()
        self.pushButton.clicked.connect(self.query_BTC)
        self.pushButton_2.clicked.connect(self.output_txs)
        self.pushButton_6.clicked.connect(self.Return)

    def query_BTC(self):
        ADC = ViewFunction.view8.AddrClustering()
        self.addrIDs, res = ADC.query_addrs(self.lineEdit.text())
        if self.addrIDs == 'N':  # 如果这个地址查不到
            s = '输入BTC地址不合法或者该BTC地址不存在！'
            reply = QMessageBox.critical(self, '错误', s, QMessageBox.Yes, QMessageBox.Yes)
        else:
            self.textBrowser.setText(res)
 
    def output_txs(self):
        ADC = ViewFunction.view8.AddrClustering()
        res, res_csv = ADC.query_txs(self.addrIDs)   # 这边两个res格式不太一样，这边可以变成双返回
        self.show_sheet(res_csv)
        self.textBrowser_2.setText(res)
    
    def Return(self):
        self.main = MainWindow()
        self.main.show()
        self.close()

    def show_sheet(self, data):
        # 打开csv界面
        self.form_widget = ViewFunction.view8.MyTable(0, 4)
        # self.setCentralWidget(self.form_widget)
        col_headers = ["日期", "交易ID", "地址", "支出/收入金额(BTC)"]
        self.form_widget.setHorizontalHeaderLabels(col_headers)
        self.form_widget.open_sheet(data)
        self.show()




class AnoDetWindow(QWidget , AnoDet_Ui_Form) :  # 异常检测页面
    AD = ViewFunction.HView.AnoDection()  # 定义类的对象

    def __init__(self) :
        super(AnoDetWindow , self).__init__()
        self.setupUi(self)
        self.returnBtn.clicked.connect(self.Return)  # 返回主页
        self.singleTheft.clicked.connect(self.AnodetTheft)  # 单条检测的响应函数
        self.singleFraud.clicked.connect(self.AnodetFraud)  # 单条检测的响应函数
        self.singleSilk.clicked.connect(self.AnodetSilk)  # 单条检测的响应函数

        self.startDate.setMinimumDateTime(QDateTime(2009 , 1 , 12 , 11 , 30 , 45))
        self.startDate.setMaximumDateTime(QDateTime(2020 , 7 , 30 , 0 , 15 , 00))
        # self.startDate.setMaximumDateTime(QDateTime(2012 , 7 , 22 , 17 , 38 , 56))

        self.endDate.setMinimumDateTime(QDateTime(2009 , 1 , 12 , 11 , 30 , 45))
        self.endDate.setMaximumDateTime(QDateTime(2020 , 7 , 30 , 0 , 15 , 00))
        # self.endDate.setMaximumDateTime(QDateTime(2012 , 7 , 22 , 17 , 38 , 56))

        self.MultiAD_Btn.clicked.connect(self.MutiAno)  # 控件的响应函数
        self.visualFraudBtn.clicked.connect(self.VisualFraud)
        self.visualTheftBtn.clicked.connect(self.VisualTheft)
        self.visualSilkBtn.clicked.connect(self.VisualSilk)
        # self.df=self.AD.readFile()  # 定义一个全局变量用于存放全部的dataframe(由于内存问题，目前只读取500W条数据）

    def Return(self) :
        self.main = MainWindow()
        self.main.show()
        self.close()

    def AnodetTheft(self) :
        # 盗窃单条检测
        singleTxhash = self.txhashText.text()  # 获取输入的异常交易hash
        AD_type = self.AD.singleTheft(singleTxhash)  # 函数返回的异常类型
        self.sinThText.setText(AD_type)  # 在控件上显示结果

    def AnodetFraud(self) :
        # 欺诈单条检测
        singleTxhash = self.txhashText.text()  # 获取输入的异常交易hash
        AD_type = self.AD.singleFraud(singleTxhash)  # 函数返回的异常类型
        self.sinFrText.setText(AD_type)  # 在控件上显示结果

    def AnodetSilk(self) :
        # 丝绸之路单条检测
        singleTxhash = self.txhashText.text()  # 获取输入的异常交易hash
        AD_type = self.AD.singleSilk(singleTxhash)  # 函数返回的异常类型
        self.sinSilkText.setText(AD_type)  # 在控件上显示结果

    def MutiAno(self) :
        # 防止线程阻塞GUI卡顿
        gui = QtGui.QGuiApplication.processEvents
        """
        以下是批处理返回异常的主逻辑
        """
        t1 = self.startDate.dateTime().toString(Qt.ISODate)  # 时间转换为标准时间
        STime = time.strptime(t1 , "%Y-%m-%dT%H:%M:%S")
        start_time = int(time.mktime(STime))  # int类型的时间戳

        t2 = self.endDate.dateTime().toString(Qt.ISODate)
        ETime = time.strptime(t2 , "%Y-%m-%dT%H:%M:%S")
        end_time = int(time.mktime(ETime))  # int类型的时间戳

        STime = datetime.datetime.fromtimestamp(start_time)
        stime = STime.strftime("%Y_%m_%d_%H:%M:%S")
        ETime = datetime.datetime.fromtimestamp(end_time)
        etime = ETime.strftime("%Y_%m_%d_%H:%M:%S")

        if start_time >= end_time :
            res = '该时间段内没有数据！请重新选择起止时间！'
            self.AnoTxHashTxt.setText(res)
        else :
            Anotype = self.multiAnoClassCombo.currentText()
            if Anotype == '欺诈' :
                res = "正在识别中....\n"
                if ((end_time - start_time) <= 2678400) :  # 时间戳差1个月
                    batch_size = (end_time - start_time) / 10
                    for i in range(10) :
                        res += self.AD.FraudDet(int(start_time + batch_size * i) ,
                                                int(start_time + batch_size * (i + 1)))
                        self.AnoTxHashTxt.setText(res [ 0 :65009 ])  # 界面只显示第一行的文字+(64+1)*1000
                        time.sleep(0.0001)
                        gui()
                        QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                        gui()

                elif ((end_time - start_time) > 2678400 & (end_time - start_time) <= 31536000) :  # 小于一年
                    batch_size = (end_time - start_time) / 1000
                    for i in range(1000) :
                        res += self.AD.FraudDet(int(start_time + batch_size * i) ,
                                                int(start_time + batch_size * (i + 1)))
                        self.AnoTxHashTxt.setText(res [ 0 :65009 ])
                        time.sleep(0.0001)
                        gui()
                        QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                        gui()

                else :
                    batch_size = (end_time - start_time) / 100000
                    for i in range(100000) :
                        res += self.AD.FraudDet(int(start_time + batch_size * i) ,
                                                int(start_time + batch_size * (i + 1)))
                        self.AnoTxHashTxt.setText(res [ 0 :65009 ])
                        time.sleep(0.0001)
                        gui()
                        QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                        gui()

                gui()
                self.AnoTxHashTxt.setText("识别成功！\n" + res [ 10 :65009 ])  # 10是因为最开始返回“正在识别中”
                print("success! Over!")
                time.sleep(0.01)
                gui()

                if (len(res [ 10 : ]) == 0) :  # res初始化为10个字符”正在识别中...\n"
                    self.AnoTxHashTxt.setText("该时间段内没有异常数据！请重新选择！")
                    time.sleep(0.0001)
                    gui()
                else :
                    # 文件写
                    # path1=os.path.abspath('.')
                    # path = path1+"/ADresData/Fraud" +stime + "-" + etime + "_FR.csv"
                    path = "./ADresData/Fraud/" + stime + "-" + etime + "_FR.csv"
                    file = open(path , 'w+')
                    file.write(res [ 10 : ])
                    file.close()

                QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                time.sleep(0.0001)
                gui()

            elif Anotype == '盗窃' :
                res = "正在识别中....\n"
                if ((end_time - start_time) <= 2678400) :  # 时间戳差1个月
                    batch_size = (end_time - start_time) / 10
                    for i in range(10) :
                        res += self.AD.theftDet(int(start_time + batch_size * i) ,
                                                int(start_time + batch_size * (i + 1)))
                        self.AnoTxHashTxt.setText(res [ 0 :65009 ])
                        time.sleep(0.0001)
                        gui()
                        QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                        gui()

                elif ((end_time - start_time) > 2678400 & (end_time - start_time) <= 31536000) :  # 小于一年
                    batch_size = (end_time - start_time) / 1000
                    for i in range(1000) :
                        res += self.AD.theftDet(int(start_time + batch_size * i) ,
                                                int(start_time + batch_size * (i + 1)))
                        self.AnoTxHashTxt.setText(res [ 0 :65009 ])
                        time.sleep(0.0001)
                        gui()
                        QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                        gui()

                else :
                    batch_size = (end_time - start_time) / 100000
                    for i in range(100000) :
                        res += self.AD.theftDet(int(start_time + batch_size * i) ,
                                                int(start_time + batch_size * (i + 1)))
                        self.AnoTxHashTxt.setText(res [ 0 :65009 ])
                        time.sleep(0.0001)
                        gui()
                        QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                        gui()

                gui()
                self.AnoTxHashTxt.setText("识别成功！\n" + res [ 10 :65009 ])  # 10是因为最开始返回“正在识别中”
                print("success! Over!")
                time.sleep(0.01)
                gui()

                if (len(res [ 10 : ]) == 0) :  # res初始化为10个字符”正在识别中...\n"
                    self.AnoTxHashTxt.setText("该时间段内没有异常数据！请重新选择！")
                    time.sleep(0.0001)
                    gui()
                else :
                    # 文件写
                    path = "./ADresData/Theft/" + stime + "-" + etime + "_TH.csv"
                    file = open(path , 'w+')
                    file.write(res [ 10 : ])
                    file.close()

                QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                time.sleep(0.0001)
                gui()

            else :  # 丝绸之路异常
                res = "正在识别中....\n"
                if ((end_time - start_time) <= 2678400) :  # 时间戳差1个月
                    batch_size = (end_time - start_time) / 10
                    for i in range(10) :
                        res += self.AD.SilkDet(int(start_time + batch_size * i) ,
                                               int(start_time + batch_size * (i + 1)))
                        self.AnoTxHashTxt.setText(res [ 0 :65009 ])
                        time.sleep(0.0001)
                        gui()
                        QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                        gui()

                elif ((end_time - start_time) > 2678400 & (end_time - start_time) <= 31536000) :  # 小于一年
                    batch_size = (end_time - start_time) / 1000
                    for i in range(1000) :
                        res += self.AD.SilkDet(int(start_time + batch_size * i) ,
                                               int(start_time + batch_size * (i + 1)))
                        self.AnoTxHashTxt.setText(res [ 0 :65009 ])
                        time.sleep(0.0001)
                        gui()
                        QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                        gui()

                else :
                    batch_size = (end_time - start_time) / 100000
                    for i in range(100000) :
                        res += self.AD.SilkDet(int(start_time + batch_size * i) ,
                                               int(start_time + batch_size * (i + 1)))
                        self.AnoTxHashTxt.setText(res [ 0 :65009 ])
                        time.sleep(0.0001)
                        gui()
                        QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                        gui()

                gui()
                self.AnoTxHashTxt.setText("识别成功！\n" + res [ 10 :65009 ])  # 10是因为最开始返回“正在识别中”
                print("success! Over!")
                time.sleep(0.01)
                gui()

                if (len(res [ 10 : ]) == 0) :  # res初始化为10个字符”正在识别中...\n"
                    self.AnoTxHashTxt.setText("该时间段内没有异常数据！请重新选择！")
                    time.sleep(0.0001)
                    gui()
                else :
                    # 文件写
                    path = "./ADresData/Silk-Road/" + stime + "-" + etime + "_SI.csv"  # SIlk-Road后面要加‘/’
                    file = open(path , 'w+')
                    file.write(res [ 10 : ])
                    file.close()

                QtWidgets.QApplication.processEvents()  # 实时刷新界面显示
                time.sleep(0.0001)
                gui()
                self.refresh()  # 定时刷新

    def refresh(self) :  # 实时刷新界面的函数
        self.timer = QTimer()
        self.timer.start(60)
        QApplication.processEvents()  # 界面刷新函数

    def VisualSilk(self):
        self.AD.visSilk()
    def VisualTheft(self):
        self.AD.visTheft()
    def VisualFraud(self):
        self.AD.visFraud()

class VisualWindow(QWidget,visual_Ui_Form):#可视化页面
    switch_window1 = pyqtSignal(int)  # 跳转到局部交易网络图页面信号
    def __init__(self):
        super(VisualWindow,self).__init__()
        self.setupUi(self)
        # window_pale = QtGui.QPalette()
        # window_pale.setBrush(self.backgroundRole(), QtGui.QBrush(QtGui.QPixmap("background1.png")))
        # self.setPalette(window_pale)
        self.dateTimeEdit.setMinimumDateTime(QDateTime(2009,1,4,2,15,00))
        self.dateTimeEdit.setMaximumDateTime(QDateTime.currentDateTime())
        self.dateTimeEdit_2.setMinimumDateTime(QDateTime(2009,1,4,2,15,00))
        self.dateTimeEdit_2.setMaximumDateTime(QDateTime.currentDateTime())
        self.spinBox.setRange(2, 10)

        self.pushButton_3.clicked.connect(self.PartNet)#局部交易网络图
        self.pushButton_4.clicked.connect(self.SCrawler)#爬虫获取某地址的一跳邻居信息并生成静态图
        self.pushButton_6.clicked.connect(self.DCrawler)#爬虫获取某地址的一跳邻居信息并生成动态图
        self.pushButton_5.clicked.connect(self.SBacktrack)#交易回溯，静态
        self.pushButton_7.clicked.connect(self.DBacktrack)#交易回溯，动态
        self.pushButton.clicked.connect(self.Return)  #返回主页

        self.switch_window1.connect(self.show_PartNet)

    def PartNet(self):
        t = self.dateTimeEdit.dateTime().toString(Qt.ISODate)
        timeArray = time.strptime(t, "%Y-%m-%dT%H:%M:%S")
        query_time = int(time.mktime(timeArray))
        self.switch_window1.emit(query_time)
    def SCrawler(self):
        addr=self.lineEdit.text() # 获取文本框内容
        if addr=='':
            reply = QMessageBox.critical(self, '错误', '未输入地址信息', QMessageBox.Yes , QMessageBox.Yes)
        else:
            plt.close()  # 清空窗口
            AR = ViewFunction.view3.AddrRelated()  # 3LEJafsC9L4mLC33QGRjB9X77nn4o2XNzh
            res=AR.view(addr)
            if res!='Y':
                s='地址信息错误/当前数据库中该地址未参与任何交易！'
                reply = QMessageBox.critical(self, '错误', s, QMessageBox.Yes, QMessageBox.Yes)

    def DCrawler(self):
        addr=self.lineEdit.text() # 获取文本框内容
        if addr=='':
            reply = QMessageBox.critical(self, '错误', '未输入地址信息', QMessageBox.Yes , QMessageBox.Yes)
        else:
            AR = ViewFunction.Dview3.AddrRelated()#3LEJafsC9L4mLC33QGRjB9X77nn4o2XNzh
            res=AR.view(addr)
            if res != 'Y':
                s = '地址信息错误/当前数据库中该地址未参与任何交易！' 
                reply = QMessageBox.critical(self, '错误', s, QMessageBox.Yes, QMessageBox.Yes)

    def SBacktrack(self):
        tx=self.lineEdit_2.text()#2d27f40e25ad9575e4455b24ae0779f27470cb9e33a3688df29e7ab61d9a55ba
        #e8f6a0aa74155470ad54daa17f08c23d39eec05ce69c160e2826765ec5c48f47
        #9b6f64f9770ab83b2d7d2d99f4f5cf8d65f369b848221bffbd97022721323ccf #coinbase交易

        if tx=='':
            reply = QMessageBox.critical(self, '错误', '未输入地址信息', QMessageBox.Yes , QMessageBox.Yes)
        else:
            plt.close()  # 清空窗口
            t = self.dateTimeEdit_2.dateTime().toString(Qt.ISODate)
            timeArray = time.strptime(t, "%Y-%m-%dT%H:%M:%S")
            start_time = int(time.mktime(timeArray))
            value = self.spinBox.value()
            jm = ViewFunction.view5.Json2Mongo()
            trace = jm.traceBTC_bytime_num(tx, start_time, value)
            if trace == False:
                reply = QMessageBox.critical(self, '错误', '数据库中查不到此交易，请检查输入交易的正确性！', QMessageBox.Yes, QMessageBox.Yes)
            elif trace == 'C':
                reply = QMessageBox.critical(self, '错误', '此交易是coinbase交易，无更多溯源结果！', QMessageBox.Yes, QMessageBox.Yes)

    def DBacktrack(self):
        tx=self.lineEdit_2.text()#2d27f40e25ad9575e4455b24ae0779f27470cb9e33a3688df29e7ab61d9a55ba
        #e8f6a0aa74155470ad54daa17f08c23d39eec05ce69c160e2826765ec5c48f47
        #9b6f64f9770ab83b2d7d2d99f4f5cf8d65f369b848221bffbd97022721323ccf #coinbase交易
        if tx=='':
            reply = QMessageBox.critical(self, '错误', '未输入地址信息', QMessageBox.Yes , QMessageBox.Yes)
        else:
            t = self.dateTimeEdit_2.dateTime().toString(Qt.ISODate)
            timeArray = time.strptime(t, "%Y-%m-%dT%H:%M:%S")
            start_time = int(time.mktime(timeArray))
            value = self.spinBox.value()
            jm = ViewFunction.Dview5.Json2Mongo()
            trace = jm.traceBTC_bytime_num(tx, start_time, value)
            if trace == False:
                reply = QMessageBox.critical(self, '错误', '数据库中查不到此交易，请检查输入交易的正确性！', QMessageBox.Yes, QMessageBox.Yes)
            elif trace == 'C':
                reply = QMessageBox.critical(self, '错误', '此交易是coinbase交易，无更多溯源结果！', QMessageBox.Yes, QMessageBox.Yes)

    def Return(self):
        self.main = MainWindow()
        self.main.show()
        self.close()

    def show_PartNet(self,query_time):
        self.visual2 = visual2Window(query_time)
        self.visual2.show()
        self.close()


class visual2Window(QWidget,visual2_Ui_Form):
    switch_window1 = pyqtSignal()  # 跳转到可视化页面信号
    query_time=0
    def __init__(self,query_time):
        super(visual2Window, self).__init__()
        self.setupUi(self)
        #window_pale = QtGui.QPalette()
        #window_pale.setBrush(self.backgroundRole(), QtGui.QBrush(QtGui.QPixmap("background1.png")))
        #self.setPalette(window_pale)
        self.switch_window1.connect(self.show_visual)
        plt.close()  # 清空窗口
        hg=ViewFunction.view1.HeterGraph()#输出网络交易图
        hg.view(query_time)
        hgput=ViewFunction.view1put.HeterGraph()#输出度数排前十名的地址
        res = hgput.view(query_time)
        self.comboBox.addItems(res)
        self.query_time=query_time
        self.pushButton.clicked.connect(self.Return)  # 返回可视化页面
        self.pushButton_4.clicked.connect(self.SComView)  # 静态社团图
        self.pushButton_7.clicked.connect(self.DComView)  # 动态社团图
        self.pushButton_5.clicked.connect(self.SSubgraph)  # 静态子图
        self.pushButton_6.clicked.connect(self.DSubgraph)  # 动态子图
         #社团提取代码
        self.pushButton_3.clicked.connect(self.CommExtrac)#社团提取
        self.spinBox.setRange(1, 1000)
        self.spinBox_2.setRange(1, 100)

    def SComView(self):
        addr=self.comboBox.currentText()
        density=self.spinBox.value()
        hop=self.spinBox_2.value()
        Co=ViewFunction.view2P.Community()
        plt.close()  # 清空窗口
        Co.CommExtracion(self.query_time,addr,density,hop)
    def DComView(self):
        addr = self.comboBox.currentText()  # 指定地址
        density = self.spinBox.value()  # 指定交易密度
        hop = self.spinBox_2.value()  # 指定跳数
        Co = ViewFunction.Dview2P.Community()
        plt.close()  # 清空窗口

        Co.CommExtracion(self.query_time, addr, density, hop)
    def CommExtrac(self):
        addr = self.comboBox.currentText()  # 指定地址
        density = self.spinBox.value()  # 指定交易密度
        hop = self.spinBox_2.value()  # 指定跳数
        ne = ViewFunction.view4.Community()
        RES = ne.CommExtracion(self.query_time, addr, density, hop)
        self.textBrowser.setText(RES)
    def Return(self):
        self.switch_window1.emit()
    def show_visual(self):
        self.visual = VisualWindow()
        self.visual.show()
        self.close()
    def SSubgraph(self):
        addr=self.comboBox.currentText()
        plt.close()  # 清空窗口
        ne = ViewFunction.view2.neighbors2()
        ne.view(self.query_time, addr)
    def DSubgraph(self):
        addr=self.comboBox.currentText()
        ne = ViewFunction.Dview2.neighbors2()
        ne.view(self.query_time, addr)


if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)  # 解决了Qtdesigner设计的界面与实际运行界面不一致的问题
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QIcon('/home/tr/logo.ico'))
    mainWindow = MainWindow() # 控制器实例
    mainWindow.show() # 默认展示的是主页面
    sys.exit(app.exec_())

