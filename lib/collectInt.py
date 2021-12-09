#encoding=utf-8
from netmiko import ConnectHandler
from lib import base
import csv
import datetime
import threading
import queue
import textfsm
import time
StartTime = datetime.datetime.now()
Fail_List = []

#配置程序
def start(Path,Size,que):
    q = queue.Queue(Size)  #队列大小
    DevicesPath = Path
    result = []
    
    def is_normal(beforeErr,afterErr):
        res = ""   
        if afterErr[0] == 0 and afterErr[1] == 0                          :res = "正常"
        elif beforeErr[0] < afterErr[0] and beforeErr[1] < afterErr[1]    :res = "出入增长"
        elif beforeErr[0] < afterErr[0]                                   :res = "入增长"
        elif beforeErr[1] < afterErr[1]                                   :res = "出增长"
        elif beforeErr[0] == afterErr[0] and beforeErr[1] == afterErr[1]  :res = "无增长"
        else                                                              :res = "其它"
        return res
    
    #收集信息，并存储
    def Collect(Host):
        try:
            interfaceList = []
            q.put(Host)
            IP = Host.get('host')
            template1 = open("templates/huawei_display_interface_brief")
            template2 = open("templates/huawei_display_lldp_neighbor")
            try:
                Connect = base.dev_login(Host,que)
            except Exception as e:
                print(f"重试{e}")
                Connect = base.dev_login(Host,que)
            try:
                Sysname = Connect.find_prompt().strip('<>')
            except:
                Sysname = ""
            Output1 = Connect.send_command(r'disp int bri | in G|k[0-9]+\s',delay_factor=6, max_loops=2000,expect_string=r'>')
            time.sleep(10)
            Output2 = Connect.send_command(r'disp int bri | in G|k[0-9]+\s',delay_factor=6, max_loops=2000,expect_string=r'>')
            Output3 = Connect.send_command('display lldp nei',delay_factor=6, max_loops=1000,expect_string=r'>')
            Connect.disconnect()
            with open('log/CollectInt/{}-{}.log'.format(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss"),IP),'w',newline='',encoding='utf-8') as OutFile:
                OutFile.write(Output1+Output2+Output3)
            fsm1 = textfsm.TextFSM(template1)#调用TextFSM模板
            fsm_results1 = fsm1.ParseText(Output1)#提取设备Int信息
            fsm2 = textfsm.TextFSM(template1)#调用TextFSM模板
            fsm_results2 = fsm2.ParseText(Output2)#提取设备Int信息
            fsm3 = textfsm.TextFSM(template2)#调用TextFSM模板
            fsm_results3 = fsm3.ParseText(Output3)#提取设备Int信息
            for index in range(len(fsm_results3)):
                interfaceList.append(fsm_results3[index][0])
            if fsm_results1 :
                for data_str1,data_str2 in list(zip(fsm_results1,fsm_results2)):
                    data_str = [Sysname,IP]+data_str1+data_str2[-2:]
                    data_str.append(is_normal(data_str1[-2:],data_str2[-2:]))
                    try:
                        data_str = data_str + fsm_results3[interfaceList.index(data_str1[1])][4:8]   #只需要lldp的4~7个参数
                    except:
                        pass
                    result.append(data_str)
            else:
                result.append([Sysname,IP])
            que.put(IP+"收集完成！\n")
        except Exception as e:
            print(IP+"收集失败，请检查原因！")
            print(e)
            que.put(IP+"收集失败，请检查原因！\n")
            Fail_List.append(IP)
        finally:
            q.get(Host)
            q.task_done()

    try:
        #import logging
        #logging.basicConfig(filename="collectInt.log", level=logging.DEBUG)
        #logger = logging.getLogger("netmiko")
        alldevice = base.DevicesInfo(Path,que)
        alldevicenum = len(alldevice)
        que.put(alldevicenum)
        print('当前已开启多线程，同时最大线程数：%s'%Size)
        que.put('[设备Int收集]\n登录设备数量：%s 线程数：%s\n'%(alldevicenum,Size))
        for Host in alldevice:   #遍历所有设备
            task = threading.Thread(target=Collect,args=(Host,))   #创建多线程
            task.setDaemon(True)
            task.start()
        q.join()  #等待所有线程任务完成
        print('失败：{}'.format(Fail_List))
        with open(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss")+'设备Int收集.csv','a',newline='') as AllFile:
            f=csv.writer(AllFile,dialect='excel')
            f.writerow(["设备名称","IP","ETH","接口","物理状态","协议状态","入方向流量","出方向流量","入方向错包","出方向错包","10S后入方向错包","10S后出方向错包","是否增长","对端接口","对端描述","对端设备","对端管理IP"])
            for i in result:
                if i:
                    f.writerow(i)
        EndTime = datetime.datetime.now()
        print('全部收集完成！用时：{}'.format(EndTime - StartTime))
        que.put('失败：{}\n全部收集完成！用时：{}\n'.format(Fail_List,EndTime - StartTime))
    except:
        que.put('Error:收集异常中止！\n')
