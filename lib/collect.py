#encoding=utf-8
from netmiko import ConnectHandler
from lib import base
import csv
import datetime
import threading
import queue
import re
StartTime = datetime.datetime.now()
Fail_List = []

#配置程序
def start(Path,Size,que):
    q = queue.Queue(Size)  #队列大小
    result = []

    def is_normal(value,top,low):
        warr = (top-low)*0.05
        res = ""
        if value > top:
            res = "超上限"
        elif top >= value >= top-warr:
            res = "过高"
        elif low+warr > value >= low:
            res = "过低"
        elif low > value > -40:
            res = "超下限"
        elif value == -40:
            res = "无收光"
        else:
            res = "正常"
        return res

    #收集信息，并存储
    def Collect(Host):
        try:
            q.put(Host)
            IP = Host.get('host')
            Connect = base.dev_login(Host,que)
            Sysname = Connect.find_prompt().strip('<>')
            #Output = Connect.send_command('dis int tra ver',use_textfsm=True)
            Output = Connect.send_command('dis tra ver',use_textfsm=True)
            Connect.disconnect()
            print(Output)
            result.append(Output)
            que.put(IP+"收集完成！\n")
        except Exception as e:
            print(IP+"收集失败，请检查原因！")
            que.put(IP+"收集失败，请检查原因！\n")
            Fail_List.append(IP)
        finally:
            q.get(Host)
            q.task_done()

    try:
        alldevice = base.DevicesInfo(Path,que)
        alldevicenum = len(alldevice)
        que.put(alldevicenum)
        print('当前已开启多线程，同时最大线程数：%s'%Size)
        que.put('[光模块信息收集]\n登录设备数量：%s 线程数：%s\n'%(alldevicenum,Size))
        for Host in alldevice:   #遍历所有设备
            task = threading.Thread(target=Collect,args=(Host,))   #创建多线程
            task.setDaemon(True)
            task.start()
        q.join()  #等待所有线程任务完成
        print('失败：{}'.format(Fail_List))
        with open(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss")+'光模块信息收集.csv','a',newline='') as AllFile:
            f=csv.writer(AllFile,dialect='excel')
            f.writerow(["设备名称","IP地址","接口","模块类型","光纤类型","波长","光纤长度","厂家","当前收光","收光上限","收光下限","当前发光","发光上限","发光下限","收光是否正常"])
            for i in result:
                if i:
                    f.writerow(i)
        EndTime = datetime.datetime.now()
        print('全部收集完成！用时：{}'.format(EndTime - StartTime))
        que.put('失败：{}\n全部收集完成！用时：{}\n'.format(Fail_List,EndTime - StartTime))
    except:
        que.put('Error:收集异常中止！\n')
