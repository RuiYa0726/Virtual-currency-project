"""
作者: Santu
单位: SEU
"""
__author__ = 'Santu'

"""
该文件作用为执行数据同步功能
"""
import time
import sys
import os
import subprocess
import pymysql
from PyQt5.QtCore import * #信号相关
from PyQt5.QtWidgets import * #窗体相关
from PyQt5 import QtCore, QtGui

class DataUpdate(object):
    def __init__(self):
        """
        创建数据库连接
        """
        conn = pymysql.connect( # 创建数据库连接
            host='127.0.0.1', # 要连接的数据库所在主机ip
            user='root', # 数据库登录用户名
            password='123', # 登录用户密码
            charset='utf8', # 编码，注意不能写成utf-8
            local_infile=True
        )
        self.cursor = conn.cursor(pymysql.cursors.DictCursor)

    def queryDate(self):
        SQL = "select from_unixtime(block_timestamp) from BTCData.TEST_bh_dat order by blockID DESC limit 1;"
        self.cursor.execute(SQL)
        result = self.cursor.fetchone()
        year = result['from_unixtime(block_timestamp)'].year
        month = result['from_unixtime(block_timestamp)'].month
        day = result['from_unixtime(block_timestamp)'].day
        res = "[+]数据已更新到 %s年%s月%s日" % (year, month, day)
        return res
    
    def outputData(self):
        # 插入bh_dat
        SQL = "select blockID from BTCData.TEST_bh_dat order by blockID DESC limit 1;"
        self.cursor.execute(SQL)
        result = self.cursor.fetchone()
        shell = "echo '123' | sudo -S sed -n '%s,$'p /home/hmy/code/Blockchain/MIT_dataset/dump_data/bh.dat > /home/hmy/code/Blockchain/MIT_dataset/dump_data/update_dat/bh.dat.tsv" % (result['blockID'] + 2)
        os.system(shell)
        print("[+]bh_dat表数据已提取！")

        # 插入txh_dat, tx_dat
        SQL = "select txID from BTCData.TEST_txh_dat order by txID DESC limit 1;"
        self.cursor.execute(SQL)
        result = self.cursor.fetchone()
        shell = "echo '123' | sudo -S sed -n '%s,$'p /home/hmy/code/Blockchain/MIT_dataset/dump_data/txh.dat > /home/hmy/code/Blockchain/MIT_dataset/dump_data/update_dat/txh.dat.tsv" % (result['txID'] + 2)
        os.system(shell)
        print("[+]txh_dat表数据已提取！")
        shell = "echo '123' | sudo -S sed -n '%s,$'p /home/hmy/code/Blockchain/MIT_dataset/dump_data/tx.dat > /home/hmy/code/Blockchain/MIT_dataset/dump_data/update_dat/tx.dat.tsv" % (result['txID'] + 2)
        os.system(shell)
        print("[+]tx_dat表数据已提取！")

        # 插入addresses_dat
        SQL = "select addrID from BTCData.TEST_addresses_dat_2 order by addrID DESC limit 1;"
        self.cursor.execute(SQL)
        result = self.cursor.fetchone()
        shell = "echo '123' | sudo -S sed -n '%s,$'p /home/hmy/code/Blockchain/MIT_dataset/dump_data/addresses.dat > /home/hmy/code/Blockchain/MIT_dataset/dump_data/update_dat/addresses.dat.tsv" % (result['addrID'] + 2)
        os.system(shell)
        print("[+]addresses_dat表数据已提取！")

        # 插入txout_dat
        SQL = "select count(*) from BTCData.txout_dat;"
        self.cursor.execute(SQL)
        result = self.cursor.fetchone()
        shell = "echo '123' | sudo -S sed -n '%s,$'p /home/hmy/code/Blockchain/MIT_dataset/dump_data/txout.dat > /home/hmy/code/Blockchain/MIT_dataset/dump_data/update_dat/txout.dat.tsv" % (result['count(*)'] + 1)
        os.system(shell)
        print("[+]txout_dat表数据已提取！")

        # 插入txin_dat
        SQL = "select count(*) from BTCData.txin_dat;"
        self.cursor.execute(SQL)
        result = self.cursor.fetchone()
        shell = "echo '123' | sudo -S sed -n '%s,$'p /home/hmy/code/Blockchain/MIT_dataset/dump_data/txin.dat > /home/hmy/code/Blockchain/MIT_dataset/dump_data/update_dat/txin.dat.tsv" % (result['count(*)'] + 1)
        os.system(shell)
        print("[+]txin_dat表数据已提取！")

        print("[+]所有数据均已完成提取!")
        print("[+]数据导入数据库中......")

        self.insertData()

    def insertData(self):
        nameList = [
            ('bh.dat', 'bh_dat'), ('txh.dat', 'txh_dat'), ('tx.dat', 'tx_dat'),
            ('addresses.dat', 'addresses_dat_2'), ('txout.dat', 'txout_dat'), ('txin.dat', 'txin_dat')
        ]
        for (a, b) in nameList:
            try:
                SQL = "LOAD DATA LOCAL INFILE '/home/hmy/code/Blockchain/MIT_dataset/dump_data/update_dat/%s.tsv' INTO TABLE BTCData.TEST_%s;" % (a, b)
                self.cursor.execute(SQL)
                print("[+]表%s插入成功!" % (a))
            except:
                print("[!]插入数据库错误！")
        print("[+]所有数据均插入成功！")

class BackendThread(QObject):

    # 通过类成员对象定义信号
    update_date = pyqtSignal(str)
    stop_signal = pyqtSignal()
    auto_stop_signal = pyqtSignal()

    # 处理业务逻辑
    def run(self):
        self._running = True
        # 首先暂停数据同步
        os.system("ps -u root | grep 'bitcoind' > ps.txt")
        with open("ps.txt", "r") as f:
            data = f.readlines()
        PID = eval(data[0].lstrip().split(' ')[0])
        os.system("echo '123' | sudo -S kill -9 %s" % (PID))
        proc = subprocess.Popen("bash dumpData.sh &", shell=True)
        print("[+]进程号：", proc.pid)
        
        # 获取数据更新进程号
        os.system("ps -u root | grep 'bitcoind' > ps.txt")
        logfile = open('dumpData.log', 'r')
        loglines = self.follow(logfile)
        for line in loglines:
            if self._running == True:
                self.update(line)
            else:
                break
        logfile.close()
        with open("ps.txt", "r") as f:
            data = f.readlines()
        PID = eval(data[0].lstrip().split(' ')[0])
        os.system("echo '123' | sudo -S kill -9 %s" % (PID))
        os.system("echo '123' | sudo -S rm dumpData.log")
        os.system("rm ps.txt")
        print("[+]已完成!")

    def terminate(self):
        self._running = False

    def update(self, text):
        self.update_date.emit(str(text))

    def follow(self, thefile):
        thefile.seek(0, 1)
        while True and self._running:
            line = thefile.readline()
            if not line:
                self.status()
                time.sleep(0.5)
                continue
            yield line

    def status(self):
        fileList = os.listdir("/code/tr/ProjectView_santu")
        if 'stop.txt' in fileList:
            self.auto_stop_signal.emit()
