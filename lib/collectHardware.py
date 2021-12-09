#encoding=utf-8
from netmiko import ConnectHandler
from lib import base
import csv
import datetime
import threading
import queue
import textfsm
StartTime = datetime.datetime.now()
Fail_List = []

#配置程序
def start(Path,Size,que):
    q = queue.Queue(Size)  #队列大小
    DevicesPath = Path
    result = []


    #收集信息，并存储
    def Collect(Host):
        try:
            q.put(Host)
            IP = Host.get('host')
            templates = open("templates/huawei_display_hardware")
            Connect = base.dev_login(Host,que)
            Sysname = Connect.find_prompt().strip('<>')
            Output = Connect.send_command('display cpu')
            #Output += '\n'+Connect.send_command('display cpu-usage')
            Output += '\n'+Connect.send_command('display memory')
            Connect.disconnect()
            with open('log/CollectHardware/{}-{}.log'.format(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss"),IP),'w',newline='',encoding='utf-8') as OutFile:
                OutFile.write(Output)
            fsm = textfsm.TextFSM(templates)#调用TextFSM模板
            fsm_results = fsm.ParseText(Output)#提取设备版本补丁信息
            if fsm_results:
                for data_str in fsm_results:
                    data_str = [Sysname,IP]+data_str
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
        alldevice = base.DevicesInfo(Path,que)
        alldevicenum = len(alldevice)
        que.put(alldevicenum)
        print('当前已开启多线程，同时最大线程数：%s'%Size)
        que.put('[硬件信息收集]\n登录设备数量：%s 线程数：%s\n'%(alldevicenum,Size))
        for Host in alldevice:   #遍历所有设备
            task = threading.Thread(target=Collect,args=(Host,))   #创建多线程
            task.setDaemon(True)
            task.start()
        q.join()  #等待所有线程任务完成
        print('失败：{}'.format(Fail_List))
        with open(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss")+'硬件信息收集.csv','a',newline='') as AllFile:
            f=csv.writer(AllFile,dialect='excel')
            f.writerow(["设备名称","IP","内存使用率","CPU","CPU 5S","CPU 1M","CPU 5M","CPU MAX","CPU最高值发生时间"])
            for i in result:
                if i:
                    f.writerow(i)
        EndTime = datetime.datetime.now()
        print('全部收集完成！用时：{}'.format(EndTime - StartTime))
        que.put('失败：{}\n全部收集完成！用时：{}\n'.format(Fail_List,EndTime - StartTime))
    except:
        que.put('Error:收集异常中止！\n')
