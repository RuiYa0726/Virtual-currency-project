from pyvis.network import Network
import pymysql
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import colors
import time
colors.CSS4_COLORS

#求社团

class Community(object):
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

    def GeGraph(self,G,txIDlist,hashlist):
        for i in range(2000):
            print(i)
            outaddr=[]#输出地址列表
            SQL = "select * from BTCData.txout_dat where txID=%s;" % (txIDlist[i])
            self.cursor.execute(SQL)
            outresults = self.cursor.fetchall()#输出地址id
            for row in outresults:
                addrID = row['addrID']
                if addrID != -1:
                    SQL = "select address from BTCData.addresses_dat_1 where addrID=%s union select address from BTCData.addresses_dat_2 where addrID=%s;" % (
                    addrID, addrID)
                    self.cursor.execute(SQL)
                    addrdata = self.cursor.fetchone()
                    addr_out = addrdata['address']
                    G.add_node(addr_out, title=addr_out)  # 添加此输出地址节点
                    outaddr.append(addr_out)
            SQL = "select * from BTCData.txin_dat where txID=%s;" % (txIDlist[i])  # 求该交易的输入
            self.cursor.execute(SQL)
            inresults = self.cursor.fetchall()
            if inresults ==None:#如果是coinbase交易，输入为空
                flag=1
            else:#不是coinbase交易，存在输入
                for row in inresults:
                    addrID = row['addrID']
                    SQL="select address from BTCData.addresses_dat_1 where addrID=%s union select address from BTCData.addresses_dat_2 where addrID=%s;"%(addrID,addrID)
                    self.cursor.execute(SQL)
                    addrdata = self.cursor.fetchone()
                    addr_in = addrdata['address']
                    G.add_node(addr_in, title=addr_in)
                    for j in range(len(outaddr)):
                        if addr_in != outaddr[j]:
                           G.add_edge(addr_in, outaddr[j])

    def CommExtracion(self,query_time,InputAddr,density,hop):
        #start_time = time.time()  # 函数开始运行时间
        blockID = self.output_block(query_time)#输出第一个查询的区块
        print(blockID)
        txIDlist = []
        hashlist = []
        self.output_tx(blockID, txIDlist, hashlist)#输出2000笔交易
        G = nx.MultiGraph()
        self.GeGraph(G, txIDlist, hashlist)
        res=[]#输出信息
        res.append(InputAddr)
        num = 0
        for i in range(hop):
            for j in range(len(res)-num-1,len(res)):
                num=0
                for n in G[res[j]]:  # 输入节点的一跳邻居
                    if len(G[res[j]][n]) >= density:
                        res.append(n)
                        num=num+1
        Res=list(set(res))
        AllNodes = list(G.nodes())
        RemoveNode = set(AllNodes) ^ set(Res)
        G.remove_nodes_from(RemoveNode)
        pos = nx.random_layout(G)
        for n in G.nodes():
            G.nodes[n]['color'] = '#FFB6C1'
            G.nodes[n]['label'] = ' '
            G.nodes[n]['size'] = 20
        # 节点的颜色根据度的大小而变化
        # 节点的大小根据度的大小而变化；
        Degree = G.degree()
        DE=dict(Degree)
        maxde=[]
        de1 = []
        de2 = []
        for v in DE.keys():
            maxde.append(DE[v])
        for v in DE.keys():
            de1.append(DE[v] * 20)
            de2.append(1-DE[v]/max(maxde))
        #度的大小排名前三的显示其地址
        a = sorted(DE.items(), key=lambda x: x[1], reverse=True)
        labels = {}
        labels['' + a[0][0] + ''] = a[0][0]
        if len(a) == 2:
            labels['' + a[1][0] + ''] = a[1][0]
        if len(a) >= 3:
            labels['' + a[1][0] + ''] = a[1][0]
            labels['' + a[2][0] + ''] = a[2][0]
        g = Network()
        g.from_nx(G)
        # show_buttons(filter_=['physics'])
        # G1.Network.set_options()
        g.show("nx.html")
        #end_time = time.time()  # 函数结束时间
        #print("函数运行时间为：%.8f" % ( end_time - start_time))
       


if __name__ == '__main__':
    ne=Community()
    query_time = int(time.mktime(time.strptime('2018-5-4 2:15:00', '%Y-%m-%d %H:%M:%S')))
    addr='1J37CY8hcdUXQ1KfBhMCsUVafa8XjDsdCn'
    density=3#交易密度
    hop=5#交易跳数
    ne.CommExtracion(query_time,addr,density,hop)

