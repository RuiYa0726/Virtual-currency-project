# -*- coding: utf-8 -*-
"""
作者: Santu
单位: SEU
"""
__author__ = 'Santu'

"""
该文件作用为存放地址聚类界面的事件函数
"""
import pymysql
import time
import sys
import os
from matplotlib import colors
import prettytable as pt
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
colors.CSS4_COLORS

class AddrClustering(object):
    def __init__(self):
        """
        创建数据库连接
        """
        conn = pymysql.connect( # 创建数据库连接
            host='127.0.0.1', # 要连接的数据库所在主机ip
            user='root', # 数据库登录用户名
            password='123', # 登录用户密码
            charset='utf8' # 编码，注意不能写成utf-8
        )
        self.cursor = conn.cursor(pymysql.cursors.DictCursor)

    def query_addrs(self, BTCaddr):
        """
        用于查询该账户下的所有地址
        """
        # 查询addrID
        addrID = self.output_addrID(BTCaddr)
        if addrID == -1:  # 如果查不到的话
            return 'N', -1
        else:
            # 查询userID并返回其他addrID
            addrIDs = self.output_addrIDs(addrID)
            # 查询其他地址
            res = self.output_addrs(addrIDs)
            return addrIDs, res 
    
    def output_addrID(self, addr):
        """
        addr --> 输出其他addrs和addrIDs
        """
        SQL = "select addrID from BTCData.addresses_dat where address=%s;"
        self.cursor.execute(SQL, (addr))
        result = self.cursor.fetchone()
        if result == None:
            return -1
        else:
            # print(result['addrID'])
            return result['addrID']

    def output_addrIDs(self, addrID):
        """
        addrID --> addrIDs
        """
        SQL = """select addrID from BTCData.addr_sccs_dat
                where userID = (
                    select userID from BTCData.addr_sccs_dat where addrID=%s limit 1
                ); 
            """
        # print(addrID)
        self.cursor.execute(SQL, (addrID))
        results = self.cursor.fetchall()
        tmp = []
        if len(results) == 0:
            tmp.append(addrID)
        else:
            for record in results:
                tmp.append(record['addrID'])
        # print(tmp)
        return tmp

    def output_addrs(self, addrIDs):
        """
        addrIDs --> addrs
        """
        # SQL = "select address from BTCData.addresses_dat where addrID=%s;"
        # results = ""
        # for i in range(len(addrIDs)):
        #     self.cursor.execute(SQL, addrIDs[i])
        #     result = self.cursor.fetchone()
        #     results += result["address"] + "\n"
        # return results
        tmp = "(%s"
        for i in range(1, len(addrIDs)):
            tmp += ", %s"
        tmp += ")"
        SQL = "select address from BTCData.addresses_dat_1 where addrID in " + tmp + " union select address from BTCData.addresses_dat_2 where addrID in " + tmp + ";"
        addrIDs = addrIDs * 2
        self.cursor.execute(SQL, addrIDs)        
        results = self.cursor.fetchall()
        result = ""
        for res in results:
            result = result + res["address"] + "\n"
        return result

    def query_txs(self, addrIDs):
        """
        用于输出所有交易, addrIDs --> txs #这里可以采用多线程
        """
        tmp = "(%s"
        for i in range(1, len(addrIDs)):
            tmp += ", %s"
        tmp += ")"    
        SQL = "select txID,addrID,sum from BTCData.txin_dat where addrID in " + tmp + ";"
        self.cursor.execute(SQL, addrIDs)
        results = self.cursor.fetchall()
        final_res = {}
        for res in results:
            if res["txID"] not in final_res:
                final_res[res["txID"]] = res
                final_res[res["txID"]]["sum"] = -(res["sum"]/100000000)
            else:
                final_res[res["txID"]]["sum"] -= res["sum"]/100000000
        SQL = "select txID,addrID,sum from BTCData.txout_dat where addrID in " + tmp + ";"
        self.cursor.execute(SQL, addrIDs)
        results = self.cursor.fetchall()
        for res in results:
            if res["txID"] not in final_res:
                final_res[res["txID"]] = res
                final_res[res["txID"]]["sum"] = res["sum"]/100000000
            else:
                final_res[res["txID"]]["sum"] += res["sum"]/100000000
        ids = final_res.keys()
        ids = list(ids)
        ids.sort()
        tb = pt.PrettyTable()
        tb.field_names = ["日期", "交易ID"]
        csv_data = []
        for i in ids:
            tmp1, tmp2 = self.formal_ouput(final_res[i])
            tb.add_row(tmp1)
            csv_data.append(tmp2)
        return str(tb), csv_data
    
    def query_one_tx(self, txID):
        """
        用于查询单笔交易, txID --> tx
        """
        Input = []
        output = []
        SQL = "select addrID, sum from BTCData.txin_dat where txID=%s;"
        self.cursor.execute(SQL, [txID])
        results = self.cursor.fetchall()
        Input = results
        SQL = "select addrID, sum from BTCData.txout_dat where txID=%s;"
        self.cursor.execute(SQL, [txID])
        results = self.cursor.fetchall()
        output = results
        return {"input": Input, "output": output}

    def formal_ouput(self, tx):
        """
        使交易json数据能够标准化输出
        """
        # text = "="*138 + "\n"
        # text += "日期" + "交易ID" + "地址" + "支出/收入金额(BTC)"
        SQL = "select hash from BTCData.txh_dat where txID=%s;"
        self.cursor.execute(SQL, [tx["txID"]])
        result = self.cursor.fetchone()
        SQL = """
                select block_timestamp from BTCData.bh_dat 
                where blockID=(
                    select blockID from BTCData.tx_dat where txID=%s
                    );
              """
        self.cursor.execute(SQL, [tx["txID"]])
        result2 = self.cursor.fetchone()
        SQL = "select address from BTCData.addresses_dat where addrID=%s;"
        self.cursor.execute(SQL, [tx["addrID"]])
        result3 = self.cursor.fetchone()
        if tx["sum"] > 0:
            money = '+' + str(tx["sum"])
        elif tx["sum"] < 0:
            money = str(tx["sum"])
        else:
            money = "0.00"
        # text = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result2['block_timestamp'])) + 8*" " + result['hash'] + \
        #     8*" " + result3["address"] + 8*" " + money + "\n"
        # return text
        return [time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result2['block_timestamp'])), result['hash']], [time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(result2['block_timestamp'])), result['hash'], result3["address"], money]

class MyTable(QTableWidget):
    def __init__(self, r, c):
        super().__init__(r, c)
        self.check_change = True
        self.init_ui()

    def init_ui(self):
        self.cellChanged.connect(self.c_current)
        self.show()

    def c_current(self):
        if self.check_change:
            row = self.currentRow()
            col = self.currentColumn()
            value = self.item(row, col)
            value = value.text()
            print("当前的单元格是 ", row, ", ", col)
            print("该单元格的值: ", value)

    def open_sheet(self, data):
        self.check_change = False
        # my_file = [
        #     ["2019", "hash", "address", "money"],
        #     ["2020", "hash2", "address", "money"]
        # ]
        for row_data in data:
            row = self.rowCount()
            self.insertRow(row)
            if len(row_data) > 10:
                self.setColumnCount(len(row_data))
            for column, stuff in enumerate(row_data):
                item = QTableWidgetItem(stuff)
                self.setItem(row, column, item)
        self.check_change = True
