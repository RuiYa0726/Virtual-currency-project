from pyvis.network import Network
import pymysql
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import colors
import time

colors.CSS4_COLORS


# 创建异构图,pos=random,节点类型不同，形状不同,不建议动态图，很卡，时间很慢，做不了操作
class HeterGraph(object):
    def __init__(self):
        conn = pymysql.connect(  # 创建数据库连接
            host='127.0.0.1',  # 要连接的数据库所在主机ip
            user='root',  # 数据库登录用户名
            password='123',  # 登录用户密码
            charset='utf8'  # 编码，注意不能写成utf-8
        )
        self.cursor = conn.cursor(pymysql.cursors.DictCursor)

    def output_block(self, query_time):  #
        flag = 0
        while (flag == 0):  # 直到读取到区块数据为止
            start_time = query_time
            end_time = query_time + 600
            SQL = "select blockID from BTCData.bh_dat where block_timestamp between %s and %s LIMIT 1;" % (
            start_time, end_time)
            # 限制只输出第一条
            self.cursor.execute(SQL)
            result = self.cursor.fetchone()
            if result == None:
                flag = 0
                query_time = query_time + 600
            else:
                flag=1
                blockID = result['blockID']
        return blockID

    def output_tx(self, blockID, txIDlist, hashlist):  # 返回从第一笔区块开始的2000笔交易的ID,hash
        tx_num = 0
        while (tx_num < 2000):
            SQL = "select * from BTCData.tx_dat where blockID =%s LIMIT 2000;" % (blockID)
            self.cursor.execute(SQL)
            results = self.cursor.fetchall()
            for row in results:
                if tx_num < 2000:
                    txIDlist.append(row['txID'])
                    SQL = "select hash from BTCData.txh_dat where txID=%s;" % (row['txID'])
                    self.cursor.execute(SQL)
                    hashinfo = self.cursor.fetchone()
                    hashlist.append(hashinfo['hash'])
                    tx_num = tx_num + 1
            blockID = blockID + 1

    def GeGraph(self, G, txIDlist, hashlist):
        for i in range(2000):
            print(i)
            tx_id = hashlist[i]
            G.add_node(tx_id, attr='TXID', degree=0.1, title=tx_id)
            SQL = "select * from BTCData.txin_dat where txID=%s;" % (txIDlist[i])  # 求该交易的输入
            self.cursor.execute(SQL)
            results = self.cursor.fetchall()
            if results == None:  # 如果是coinbase交易，输入为空
                flag = 1
            else:
                for row in results:
                    addrID = row['addrID']
                    SQL="select address from BTCData.addresses_dat_1 where addrID=%s union select address from BTCData.addresses_dat_2 where addrID=%s;"%(addrID,addrID)
                    self.cursor.execute(SQL)
                    addrdata = self.cursor.fetchone()
                    addr_in = addrdata['address']
                    value = row['sum']
                    G.add_node(addr_in, attr='addr', title=addr_in)
                    G.add_edge(addr_in, tx_id, io='in', title=value)
            SQL = "select * from BTCData.txout_dat where txID=%s;" % (txIDlist[i])
            self.cursor.execute(SQL)
            results = self.cursor.fetchall()
            for row in results:
                addrID = row['addrID']
                if addrID != -1:
                    SQL="select address from BTCData.addresses_dat_1 where addrID=%s union select address from BTCData.addresses_dat_2 where addrID=%s;"%(addrID,addrID)
                    self.cursor.execute(SQL)
                    addrdata = self.cursor.fetchone()
                    addr_out = addrdata['address']
                    value = row['sum']
                    G.add_node(addr_out, attr='addr', title=addr_out)  # 添加此输出地址节点
                    G.add_edge(tx_id, addr_out, io='out', title=value)  # 每条边添加属性，输出，交易金额

    def view(self, query_time):
        blockID = self.output_block(query_time)
        print(blockID)
        txIDlist = []
        hashlist = []
        self.output_tx(blockID, txIDlist, hashlist)
        G = nx.MultiDiGraph()
        self.GeGraph(G, txIDlist, hashlist)
        pos = nx.random_layout(G)
        # 返回图中的地址节点
        addrlist = []
        for node, data in G.nodes(data=True):
            if (data['attr'] == 'addr'):
                addrlist.append(node)  # 在列表末尾添加内容

        # 求出图中各个地址节点的度,将度添加为地址节点的属性
        de_out = G.out_degree(addrlist)
        de_in = G.in_degree(addrlist)
        m = []
        delist = []
        for v in addrlist:
            delist.append([v, de_out[v] + de_in[v]])
            m.append(de_out[v] + de_in[v])
            G.nodes[v]['degree'] = de_out[v] + de_in[v]
        de = dict(delist)

        # 度的大小排名前三的显示其地址
        a = sorted(de.items(), key=lambda x: x[1], reverse=True)
        LabelRes=[]
        for i in range(0,10):
            LabelRes.append(a[i][0])
        return LabelRes

if __name__ == '__main__':
    hg=HeterGraph()
    query_time = int(time.mktime(time.strptime('2013-5-4 2:15:00', '%Y-%m-%d %H:%M:%S')))
    res=hg.view(query_time)
    print('res:',res)
