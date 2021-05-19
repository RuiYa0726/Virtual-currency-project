from pyvis.network import Network
import pymysql
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import colors
import time
colors.CSS4_COLORS
#交易溯源

class Json2Mongo(object):
    def __init__(self):
        conn = pymysql.connect(  # 创建数据库连接
            host='127.0.0.1',  # 要连接的数据库所在主机ip
            user='root',  # 数据库登录用户名
            password='123',  # 登录用户密码
            charset='utf8'  # 编码，注意不能写成utf-8
        )
        self.cursor = conn.cursor(pymysql.cursors.DictCursor)

    def traceBTC_bytime_num(self, tx, start_time, num):  # num表示层数，表示溯源到第几层
        sstart_time = time.time()  # 函数开始运行时间
        SQL="select txID from BTCData.txh_dat where hash='%s';"%(tx)
        self.cursor.execute(SQL)
        result = self.cursor.fetchone()
        if result==None:#查询失败，搜不到此交易信息
            return False
        else:
            G = nx.MultiDiGraph()
            InfoList=[]
            tx_id = result['txID']
            G.add_node(tx, attr='TXID', degree=0.1, title=tx)
            SQL = "select * from BTCData.txin_dat where txID=%s;" % (tx_id)
            self.cursor.execute(SQL)
            results = self.cursor.fetchall()
            if results==():#coinbase交易，输入为0
                print('此交易是coinbase交易，查询结束！')
                return 'C'
            for row in results:
                prev_txID=row['prev_txID']
                addrID=row['addrID']
                SQL="select address from BTCData.addresses_dat_1 where addrID=%s union select address from BTCData.addresses_dat_2 where addrID=%s;"%(addrID,addrID)
                self.cursor.execute(SQL)
                addrinfo = self.cursor.fetchone()
                addr_in=addrinfo['address']
                value=row['sum']
                G.add_node(addr_in, attr='addr', title=addr_in)
                G.add_edge(addr_in, tx, io='in', title=value)
                InfoList.append({'层数':1,'TXhash':tx,'上笔TXID':prev_txID,'地址':addr_in,'金额':value,'iscoinbase':'no'})
            init=0
            for i in range(2,num):#第i层
                L=len(InfoList)
                for j in range(init,len(InfoList)):#对于上一层的第j条数据
                    if InfoList[j]['iscoinbase'] == 'yes':
                        continue
                    tx_id = InfoList[j]['上笔TXID']
                    SQL="select blockID from BTCData.tx_dat where txID=%s;" %(tx_id)
                    self.cursor.execute(SQL)
                    result = self.cursor.fetchone()
                    blockID=result['blockID']
                    SQL="select block_timestamp from BTCData.bh_dat where blockID=%s;" %(blockID)
                    self.cursor.execute(SQL)
                    result = self.cursor.fetchone()
                    block_timestamp=result['block_timestamp']
                    if block_timestamp < start_time:
                        print('超出最早溯源时间！')
                        continue
                    SQL = "select hash from BTCData.txh_dat where txID=%s;" % (tx_id)
                    self.cursor.execute(SQL)
                    result = self.cursor.fetchone()
                    tx=result['hash']
                    G.add_node(tx, attr='TXID', degree=0.1, title=tx)
                    G.add_edge(InfoList[j]['地址'], tx, io='out', title=InfoList[j]['金额'])
                    SQL = "select * from BTCData.txin_dat where txID=%s;" % (tx_id)
                    self.cursor.execute(SQL)
                    results = self.cursor.fetchall()
                    if results == ():  # coinbase交易，输入为0
                        InfoList.append({'层数': i, 'TXhash': tx, 'iscoinbase':'yes'})
                        continue
                    for row in results:
                        prev_txID = row['prev_txID']
                        addrID = row['addrID']
                        SQL="select address from BTCData.addresses_dat_1 where addrID=%s union select address from BTCData.addresses_dat_2 where addrID=%s;"%(addrID,addrID)
                        self.cursor.execute(SQL)
                        addrinfo = self.cursor.fetchone()
                        addr_in = addrinfo['address']
                        value = row['sum']
                        G.add_node(addr_in, attr='addr', title=addr_in)
                        G.add_edge(addr_in, tx, io='in', title=value)
                        InfoList.append({'层数': i, 'TXhash': tx, '上笔TXID': prev_txID, '地址': addr_in, '金额': value,'iscoinbase':'no'})
                init=L
            #for n in range(len(InfoList)):
             #   print(InfoList[n])
            pos = nx.random_layout(G)
            # 返回图中的地址节点
            addrlist = []
            TXID = []
            for node, data in G.nodes(data=True):
                if (data['attr'] == 'addr'):
                    addrlist.append(node)  # 在列表末尾添加内容
                    data['color'] = '#FFB6C1'
                else:
                    TXID.append(node)  # 在列表末尾添加内容
                    data['color'] = '#87CEEB'
                data['label'] = ' '
                data['size'] = 20
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
            # 节点的大小根据度的大小而变化；
            degree = nx.get_node_attributes(G, 'degree')
            de1 = []
            for v in degree.keys():
                if G.nodes[v]['attr'] == 'addr':
                    de1.append(degree[v] * 20)
                # G.nodes[v]['size'] = degree[v]
            # 节点的颜色根据度的大小而变化
            de2 = []
            degree = nx.get_node_attributes(G, 'degree')
            for v in degree.keys():
                if G.nodes[v]['attr'] == 'addr':
                    de2.append(1 - (degree[v]) / max(m))
            # 度的大小排名前三的显示其地址
            a = sorted(de.items(), key=lambda x: x[1], reverse=True)
            labels = {}
            labels['' + a[0][0] + ''] = a[0][0]
            if len(a)==2:
               labels['' + a[1][0] + ''] = a[1][0]
            if len(a)>=3:
               labels['' + a[1][0] + ''] = a[1][0]
               labels['' + a[2][0] + ''] = a[2][0]

            nx.draw_networkx_labels(G, pos, labels, font_size=10, font_color='black')
            nx.draw_networkx_nodes(G, pos, nodelist=TXID, node_shape='s', node_size=30, node_color='#48D1CC',
                                   alpha=0.9)  # 结点为方形
            nx.draw_networkx_edges(G, pos,
                                   edgelist=None,
                                   width=0.5,
                                   edge_color='#C0C0C0',
                                   style='solid',
                                   alpha=1.0,
                                   edge_cmap=None,
                                   edge_vmin=None,
                                   edge_vmax=None,
                                   ax=None,
                                   arrows=True,
                                   label=None, )
            nx.draw_networkx_nodes(G, pos, nodelist=addrlist, node_shape='o', node_color=de2, node_size=de1, alpha=0.9,
                                   cmap='Reds_r',
                                   vmin=0.9,  # 节点映射颜色尺度的最小值和最大值
                                   vmax=1,
                                   ax=None,
                                   linewidths=None)
            #plt.show()
            g = Network()
            g.from_nx(G)
            #g.show_buttons(filter_=['physics'])
            # G1.Network.set_options()
            
            eend_time = time.time()  # 函数结束时间
            print("函数运行时间为：%.8f" % ( eend_time - sstart_time)) 
            g.show("nx.html")


if __name__ == "__main__":
    jm = Json2Mongo()
    # 下面为例子
    tx = 'e8f6a0aa74155470ad54daa17f08c23d39eec05ce69c160e2826765ec5c48f47'
    tx = '2d27f40e25ad9575e4455b24ae0779f27470cb9e33a3688df29e7ab61d9a55ba'
    #tx='9b6f64f9770ab83b2d7d2d99f4f5cf8d65f369b848221bffbd97022721323ccf'#coinbase交易
    start_time = 1231006445
    trace = jm.traceBTC_bytime_num(tx, start_time, 7)
