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
def start(Path,Size,conf,que,regu):
    q = queue.Queue(Size)  #队列大小
    result = []

    #收集信息，并存储
    def Collect(Host,confi,regu):
        try:
            q.put(Host)
            IP = Host.get('host')
            Connect = base.dev_login(Host,que)
            #print(IP+"正在收集")
            Sysname = Connect.find_prompt().strip('<>')
            Output = Connect.send_config_from_file('config/{}.cfg'.format(confi),cmd_verify=False,enter_config_mode = False)
            print(Output)
            Connect.disconnect()
            with open('log/Conf/{}-{}.log'.format(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss"),IP),'w',newline='',encoding='utf-8') as OutFile:
                OutFile.write(Output)
            que.put(IP+"配置完成！\n")
            out_res = [Sysname,IP]
            regex = re.compile(regu)
            OutFilter = regex.findall(Output)
            #print(OutFilter)
            if type(OutFilter) == str:
                OutFilter = OutFilter.split('\n')
            if len(OutFilter) == 0:
                out_res = out_res
            elif len(OutFilter) == 1:
                out_res += OutFilter[0]
            else:
                for i in OutFilter:
                    if type(i) == tuple:
                        i = list(i)
                        out_res += i
                    else:
                       out_res.append(i)
            result.append(out_res)
        except FileNotFoundError as e:
            Connect.disconnect()
            print(IP+'找不到设备配置文件。')
            print(e)
            que.put(IP+'找不到设备配置文件。')
        except Exception as e:
            print(IP+"收集失败，请检查原因！")
            print(e)
            que.put(IP+"收集失败，请检查原因！\n")
            Fail_List.append(Host)
        finally:
            q.get(Host)
            q.task_done()


    try:
        alldevice = base.DevicesInfo(Path,que)
        alldevicenum = len(alldevice)
        que.put(alldevicenum)
        print('当前已开启多线程，同时最大线程数：%s'%Size)
        que.put('[设备配置]\n登录设备数量：%s 线程数：%s\n'%(alldevicenum,Size))
        for Host in alldevice:   #遍历所有设备
            if conf == 2:
                confi = Host.get('host')
            else:
                confi = 'default'
            task = threading.Thread(target=Collect,args=(Host,confi,regu))   #创建多线程
            task.setDaemon(True)
            task.start()
        q.join()  #等待所有线程任务完成
        if regu:
            with open(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss")+'自定义配置收集.csv','a',newline='') as AllFile:
                f=csv.writer(AllFile,dialect='excel')
                #转置删除空列
                #print(result)
                result = zip(*result)
                #print(result)
                result = [x for x in result if any(x)]
                #print(result)
                result = zip(*result)
                #print(result)
                for i in result:
                    if i:
                        f.writerow(i)
                        print(i)
        print('失败：{}'.format(Fail_List))
        EndTime = datetime.datetime.now()
        print('全部配置完成！用时：{}'.format(EndTime - StartTime))
        with open(datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss")+'配置失败列表.csv','a',newline='') as AllFile:
                f=csv.writer(AllFile,dialect='excel')
                f.writerow(["device_type","host","username","password","port","active"])
                for i in Fail_List:
                    i["active"] = 1
                    f.writerow(i.values())
        que.put('失败数量：{}\n详细请查看目录下的失败列表文件\n全部配置完成！用时：{}\n'.format(len(Fail_List),EndTime - StartTime))
    except Exception as e:
        que.put(f'Error:配置异常中止！{e}\n')
