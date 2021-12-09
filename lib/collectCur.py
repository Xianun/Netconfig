#encoding=utf-8
from netmiko import ConnectHandler
from lib import base
import datetime
import threading
import queue

StartTime = datetime.datetime.now()
Fail_List = []
#配置程序
def start(Path,Size,que):
    q = queue.Queue(Size)  #队列大小
    #que.put("开始收集配置\n")
    
    #收集信息，并存储信息
    def Collect(Host):
        try:
            q.put(Host)
            IP = Host.get('host')
            Connect = base.dev_login(Host,que)
            Sysname = Connect.find_prompt().strip('<>')
            Output = Connect.send_command('dis cur')  #不同设备注意更换收集命令
            Connect.disconnect()
            with open('log/CollectCur/{}-{}.log'.format(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss"),IP),'w',newline='',encoding='utf-8') as OutFile:
                OutFile.write(Output)
            que.put(IP+"收集完成！\n")
        except Exception as e:
            Connect.disconnect()
            print(IP+"收集失败，请检查原因！")
            print(e)
        finally:
            q.get(Host)
            q.task_done()

    try:
        alldevice = base.DevicesInfo(Path,que)
        alldevicenum = len(alldevice)
        que.put(alldevicenum)
        print('当前已开启多线程，同时最大线程数：%s'%Size)
        que.put('[设备配置收集]\n登录设备数量：%s 线程数：%s\n'%(alldevicenum,Size))
        for Host in alldevice:   #遍历所有设备
            task = threading.Thread(target=Collect,args=(Host,))   #创建多线程
            task.setDaemon(True)
            task.start()
        q.join()  #等待所有线程任务完成
        EndTime = datetime.datetime.now()
        print('全部收集完成！用时：{}'.format(EndTime - StartTime))
        que.put('失败：{}\n全部收集完成！用时：{}\n'.format(Fail_List,EndTime - StartTime))
    except:
        que.put('Error:收集异常中止！\n')
