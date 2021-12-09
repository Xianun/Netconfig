#encoding=utf-8
from netmiko import ConnectHandler
from netmiko import NetMikoTimeoutException
import csv
import queue



def DevicesInfo(DevicesPath,que):
    Device={}
    Devices=[]
    k = 0
    try:
        with open(DevicesPath,'r') as InFile:
            line = csv.reader(InFile)
            next(line) #迭代器去掉首行
            for host in line:
                k += 1
                if host[5] == "1":
                    Device={'device_type':host[0],'host':host[1],'username':host[2],'password':host[3],'port':host[4]}
                    Devices.append(Device)
                        
            print('设备信息文件查找完成，共%d台登录设备，准备登录……' %len(Devices))
            #que.put('设备信息文件查找完成，共%d台设备，准备登录……\n' %k)
            return Devices
    except FileNotFoundError as e:
        print('找不到设备登录信息文件，请导入设备登录信息文件。')
        que.put(0)
        que.put('找不到设备登录信息，请导入设备登录信息文件\n')
    except IndexError as e:
        print('设备登录信息内容格式有误！请按6列填写以下内容：设备类型|IP|用户名|密码|端口|是否登录')
        que.put(0)
        que.put('设备登录信息内容格式有误！请按6列填写以下内容\n设备类型|IP|用户名|密码|端口|是否登录\n')

#收集信息，并存储
def dev_login(Host,que):
    try:
        IP = Host.get('host')
        Connect = ConnectHandler(**Host)
        que.put(IP+"登录成功\n")
        return Connect
        print(Connect)
    except NetMikoTimeoutException as e:
        print(IP+"登录超时,请检查连通性")
        print(e)
        que.put(IP+"登录超时,请检查连通性！\n")
    except Exception as e:
    #finally:
        print(IP+"登录失败，请检查原因！")
        print(e)
        que.put(IP+"登录失败，请检查原因！\n")
