#encoding=utf-8
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import filedialog
from tkinter import messagebox as mBox
from multiprocessing import Process,Queue
import threading
import csv
import os
import ctypes
from jinja2 import Environment, FileSystemLoader,meta


def set_win():

    def mkdir(path):
        isExists=os.path.exists(path)        # 判断路径是否存在
        if not isExists:
            os.makedirs(path)             # 如果不存在则创建目录
            return True
        else:
            return False

    def chose_file(entry):  #选择文件路径
        filename = filedialog.askopenfilename()
        if filename != '':
            entry.delete(0,tk.END)
            entry.insert(0,filename)
        else:
            pass

    def log_thread(proces,logtxt,pbar,que): #协程动态加载日志
        devicenum = que.get()
        bar = float(devicenum)*2+2
        pbarvalue = 0.0
        while proces.is_alive():
            if not que.empty():
                logtxt.insert(tk.END,que.get())
                pbarvalue += 100/bar
                pbar.config(value = pbarvalue)
                logtxt.see(tk.END)
                logtxt.update()
        while not que.empty():
            logtxt.insert(tk.END,que.get())
            pbarvalue += 100/bar
            pbar.config(value = pbarvalue)
            logtxt.see(tk.END)
            logtxt.update()

    def conf_start():  #配置页配置按钮动作
        from lib import conf
        mkdir('log/Conf')
        mkdir('config')
        ofp = open('config/default.cfg',"w")
        ofp.write(commscr.get(1.0,tk.END))
        ofp.flush()
        ofp.close()
        answer = mBox.askyesno("操作提示", "警告：该操作会影响目标设备\n请确认配置风险，是否继续：") 
        if answer == True:
            conf_process = Process(target=conf.start,name='配置',args=(file_path1.get(),thread1.get(),radVar.get(),que1,regular1.get()))   #创建新进程
            conf_th = threading.Thread(target=log_thread,args=(conf_process,logtxt1,pbar1,que1))   #创建多线程
            conf_th.setDaemon(True)
            conf_process.start()
            conf_th.start()
        else:
            logtxt1.insert(tk.END,'操作已取消\n')
            #logtxt1.see(tk.END)
            logtxt1.update()

    def conf_stop():  #配置页停止按钮动作
        pro.terminate()
        que.put('操作已停止')
        pro.join()

    def collect_start():  #收集页配置按钮动作
        if modeltxt.get() == '收集光模块信息':
            from lib import collectTransceiver as cT
            mkdir('log/CollectTransceiver')
            model = cT
        elif modeltxt.get() =='收集设备配置信息':
            from lib import collectCur as cC
            mkdir('log/CollectCur')
            model = cC
        elif modeltxt.get() =='收集版本补丁信息':
            from lib import collectVersion as cV
            mkdir('log/CollectVersion')
            model = cV
        elif modeltxt.get() =='收集设备SN信息':
            from lib import collectSN as cS
            mkdir('log/CollectSN')
            model = cS
        elif modeltxt.get() =='收集设备Int信息':
            from lib import collectInt as cI
            mkdir('log/CollectInt')
            model = cI
        elif modeltxt.get() =='收集设备IntVer信息':
            from lib import collectIntver as cIV
            mkdir('log/CollectIntVer')
            model = cIV
        elif modeltxt.get() =='收集设备硬件信息':
            from lib import collectHardware as cH
            mkdir('log/CollectHardware')
            model = cH
        elif modeltxt.get() =='收集设备License信息':
            from lib import collectLicense as cL
            mkdir('log/CollectLicense')
            model = cL
        collect_process = Process(target=model.start,name='收集光衰',args=(file_path2.get(),thread2.get(),que2))   #创建新进程
        collect_th = threading.Thread(target=log_thread,args=(collect_process,logtxt2,pbar2,que2,))   #创建多线程
        collect_th.setDaemon(True)
        collect_process.start()
        collect_th.start()

    def comsame():
        placeholder1.configure(height=0)
        commscr.grid(column=0, row=1,sticky=tk.NSEW,padx=2,pady=1, columnspan=3)
        #commscr.config(state='normal')

    def comdiff():
        #commscr.config(state='disable')
        commscr.grid_forget()
        placeholder1.configure(height=15)

    def regular(*ignoredArgs):
        if coVar.get():
            regular1.configure(state='normal')
        else:
            regular1.delete(0,tk.END)
            regular1.configure(state='disabled')

    def creat_config():
        
        conf_name = name3.get()

        argv_path = file_path3.get()
        argv_dir,_ = os.path.split(argv_path)

        template_file = modulstxt.get()
        #传功能函数数入jinja2
        global_val = {"int" : int,"zip" :zip}
        
        env = Environment(loader=FileSystemLoader("templates/jinja2/"))
        #jinja_template = Environment(loader=FileSystemLoader("templates/jinja2/")).from_string(template_file)
        try:
            jinja_template = env.get_template(template_file)
            jinja_template.globals.update(global_val)
            global_val = to_dict(golbal_scr.get(1.0,tk.END))
            jinja_template.globals.update(global_val)
        except Exception as e:
            logtxt3.insert(tk.END,f"【ERROR1】:{e}\n")
            logtxt3.see(tk.END) 
        #格式化参数主表格
        result_data,_ = csv_to_dict(argv_path)
        data_len = len(result_data)
        file_num = 0
        
        pbarvalue = 0.0
        #外链表缓存
        file_cache = {}
        for index,main_row in enumerate(result_data):
        
            if not "REFERENCES" and "KEY" in main_row:   #主表没有这两个字段时跳出if
                break
            elif main_row.get("REFERENCES", "") and main_row.get("KEY", ""):    #存在两个字段时处理逻辑
                #支持多个外链表
                if isinstance(main_row["REFERENCES"],str):
                    filename_list = [main_row["REFERENCES"]]
                elif isinstance(main_row["REFERENCES"],list):
                    filename_list = main_row["REFERENCES"]
                else:
                    logtxt3.insert(tk.END,"主表REFERENCES字段类型错误\n")
                    logtxt3.see(tk.END)

                try: 
                    #读取外链表数据合并到主表
                    for file in filename_list:
                        dict_REFERENCES = {}
                        arg_count = 1
                        if (file not in file_cache) and file:
                            file_cache[file],fieldnames = csv_to_dict(argv_dir+'/'+file)
                        if file:
                            for row in file_cache[file]:
                                if set(row["KEY"].split(",")) & set(main_row["KEY"].split(",")):
                                    for k,v in row.items():
                                        if arg_count == 1:
                                            v = v
                                        elif arg_count == 2:
                                            v = [dict_REFERENCES[k]] + [v]
                                        else:
                                            v = dict_REFERENCES[k] + [v]
                                        dict_REFERENCES[k] = v
                                    arg_count += 1
                            if not dict_REFERENCES:
                                for k in fieldnames:
                                    dict_REFERENCES[k] = []
                            del dict_REFERENCES["KEY"]
                            main_row.update(dict_REFERENCES)

                except FileNotFoundError as e:
                    logtxt3.insert(tk.END,f"【WARNING】:主表{index+1}行，未找到外链表文件:{file}\n")
                    logtxt3.see(tk.END)

                except Exception as e:
                    logtxt3.insert(tk.END,f"【ERROR2】:{e}\n")
                    logtxt3.see(tk.END)

            else:
                logtxt3.insert(tk.END,f"【WARNING】:主表{index+1}行的外链表定义不完整，请检查表名和外键\n")
                logtxt3.see(tk.END)
        
        
            try:
                #渲染模板并生成配置

                ast = jinja_template.render(str= str,**main_row)
                with open(f"config/{main_row[conf_name]}.cfg",'w',newline='',encoding='utf-8') as f:       
                    f.write(ast)
                    file_num += 1
                
            except Exception as e:
                logtxt3.insert(tk.END,f"【ERROR3】:{e}\n")
                logtxt3.see(tk.END)
                break

            pbarvalue += 100/(data_len-1)
            pbar3.configure(value = pbarvalue)

        if file_num > 0:
            logtxt3.insert(tk.END,f"【完成】已生成[{file_num}]文件\n")
            logtxt3.see(tk.END)
            open_path()
        else:
            logtxt3.insert(tk.END,f"【完成】未生成任何文件\n")
            logtxt3.see(tk.END)


    def csv_to_dict(csvfile):
        csv_list = []
        with open(csvfile, 'r') as f:
            reader = csv.reader(f)
            fieldnames = next(reader)
            for row in reader:
                csv_dict = {}
                for k_v in zip(fieldnames, row):
                    k,v = k_v
                    if fieldnames.count(k) > 1:
                        csv_dict.setdefault(k, []).append(v)
                    else:
                        csv_dict[k] = v
                csv_list.append(csv_dict)
        return csv_list,fieldnames


    def open_path():
        os.startfile(f"{os.getcwd()}/config/")

    def jinja_moduls(file_path):
        files = ()
        for root, dirs, files in os.walk(file_path):
            files = tuple(files)
        moduls['values'] = files
        if len(moduls['values']) > 0:
            moduls.current(1)

    def config_name(entry):
        chose_file(entry)
        moduls_dir = file_path3.get()
        with open(moduls_dir) as f:
            reader = csv.reader(f)
            namechose3['values'] = tuple(next(reader))
        if len(namechose3['values']) > 0:
            namechose3.current(0)


    def to_dict(golbal_str):
        val = filter(None,golbal_str.split('\n'))
        golbal_dict = {}
        for a in val:
            key = a.split("=")
            golbal_dict[key[0].strip()] = eval(key[1].strip())
        return golbal_dict



    #----------------初始化-------------------#
    ctypes.windll.shcore.SetProcessDpiAwareness(1) #调用api设置成由应用程序缩放
    ScaleFactor=ctypes.windll.shcore.GetScaleFactorForDevice(0) 
    win = tk.Tk()   
    win.tk.call('tk', 'scaling', ScaleFactor/75)
    win.title("NetConfig  v1.2.6")  # 增加title 
    screenwidth = win.winfo_screenwidth()
    screenheight = win.winfo_screenheight()
    winwidth = screenwidth*0.45
    winheight = screenheight*0.52
    winsize = '%dx%d+%d+%d' % (winwidth, winheight, (screenwidth - winwidth)/2, (screenheight - winheight)/3)
    win.geometry(winsize)
    win.rowconfigure(0, weight=1)
    win.columnconfigure(0, weight=1)
    win.iconbitmap("data:image/x-icon;base64,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")
    #win.resizable(0,0)  # 禁用调整大小
    que1 = Queue()  #配置页日志消息队列
    que2 = Queue()  #收集页日志消息队列
    #----------------初始化-------------------#

    #----------------标签页-------------------#
    tabControl = ttk.Notebook(win) 
    tab1 = ttk.Frame(tabControl)
    tab1.grid(row=0,column=0,sticky=tk.NSEW)
    tab1.rowconfigure(1,weight=1);tab1.columnconfigure(1,weight=1)
    tabControl.add(tab1, text='配置设备')
    tab2 = ttk.Frame(tabControl) 
    tab2.grid(row=0,column=0,sticky=tk.NSEW)
    tab2.rowconfigure(1,weight=1);tab2.columnconfigure(1,weight=1)
    tabControl.add(tab2, text='收集信息')
    tab3 = ttk.Frame(tabControl)
    tab3.grid(row=0,column=0,sticky=tk.NSEW)
    tab3.rowconfigure(1,weight=1);tab3.columnconfigure(1,weight=1)
    tabControl.add(tab3, text='配置生成')   
    tabControl.grid(row=0,column=0,sticky=tk.NSEW)
    tabControl.rowconfigure(0,weight=1);tabControl.columnconfigure(0,weight=1)
    #----------------标签页-------------------#

    #------------Tab1设备配置控件-------------#
    #选择区
    monty1 = ttk.LabelFrame(tab1, text='选择')
    monty1.grid(column=0, row=0, padx=5, pady=4,ipadx= 2,ipady= 1,sticky=tk.NSEW)

    #设备路径
    ttk.Label(monty1, text="设备:").grid(column=0, row=0,sticky=tk.NSEW)
    file_path1 = tk.StringVar()
    nameEntered1 = ttk.Entry(monty1, width=38, textvariable=file_path1)
    nameEntered1.grid(column=1, row=0,sticky=tk.NSEW)
    chose_file1 = ttk.Button(monty1,text="导入",width=4,command=lambda: chose_file(nameEntered1))
    chose_file1.grid(column=2,row=0,padx=0,sticky=tk.NSEW)
    #线程选择
    ttk.Label(monty1, text="线程:").grid(column=0, row=1,sticky=tk.NSEW)
    thread1 = tk.IntVar()
    threadchose1 = ttk.Combobox(monty1, width=39, textvariable=thread1)
    threadchose1['values'] = (20,50,100)
    threadchose1.grid(column=1, row=1,columnspan=2,pady=1,sticky=tk.NSEW)
    threadchose1.current(1)  #设置初始显示值，值为元组['values']的下标
    threadchose1.config(state='readonly')  #设为只读模式
    #正则
    ttk.Label(monty1, text="正则:").grid(column=0, row=2,sticky=tk.NSEW)
    re1 = tk.StringVar()
    regular1 = ttk.Entry(monty1, width=39, textvariable=re1,state='disabled')
    regular1.grid(column=1, row=2,columnspan=2 ,pady=1,sticky=tk.NSEW)
    #命令区
    comm = ttk.LabelFrame(tab1, text='命令')
    comm.grid(column=0, row=1, padx=5, pady=4,ipadx= 2,ipady= 2,sticky=tk.NSEW)
    comm.rowconfigure(1,weight=1)
    #命令选项
    radVar = tk.IntVar()
    radVar.set(1) 
    commsame = tk.Radiobutton(comm, text="相同配置", variable=radVar, value=1,command=comsame)
    commsame.grid(column=0, row=0,sticky=tk.W)
    commdiff = tk.Radiobutton(comm, text="不同配置", variable=radVar, value=2,command=comdiff)
    commdiff.grid(column=1, row=0,sticky=tk.W)
    coVar = tk.IntVar()
    collect1 = tk.Checkbutton(comm, text="提取", variable=coVar)
    collect1.deselect()
    collect1.grid(column=2, row=0,sticky=tk.W)
    coVar.trace('w', lambda unused0, unused1, unused2: regular()) 

    #命令文体框
    placeholder1 = tk.Label(comm,width=45,text="请以 IP.cfg 格式命名设备配置，\n并放在程序目录的/config下。")
    placeholder1.grid(column=0,  row=1,sticky=tk.NSEW,padx=5,pady=3,columnspan=3)
    commscr = scrolledtext.ScrolledText(comm, width=45, wrap='none')
    commscr.grid(column=0, row=1,sticky=tk.NSEW,padx=2,pady=1, columnspan=3)

    #执行区
    conf1 = ttk.LabelFrame(tab1, text='执行')
    conf1.grid(column=0, row=2, padx=5, pady=4,ipadx= 2,ipady= 2,sticky=tk.NSEW)
    startconf1 = ttk.Button(conf1,text="配置",width=8,command=conf_start)   
    startconf1.pack( side = "left", padx = 15)
    cleanlog1 = ttk.Button(conf1,text="清空日志",width=8,command=lambda:logtxt1.delete(1.0,tk.END))   
    cleanlog1.pack( side = "right", padx = 15)
    stopconf1 = ttk.Button(conf1,text="停止",width=8,state='disabled',command=conf_stop)   
    stopconf1.pack( side = "right", padx = 15)
    #日志区
    logs1 = ttk.LabelFrame(tab1, text='日志')
    logs1.grid(column=1, row=0, rowspan=3,padx=8, pady=4, sticky=tk.NSEW)
    logs1.rowconfigure(0,weight=1);logs1.columnconfigure(0,weight=1)
    #日志文体框
    #log1lW  = 45; log1lH  =  33
    logtxt1 = scrolledtext.ScrolledText(logs1, wrap=tk.WORD)
    logtxt1.grid(column=0, row=0, sticky=tk.NSEW,padx=5,pady=3)
    pbar1 = ttk.Progressbar(logs1, orient = "horizontal",  mode="determinate", value=0.0)
    pbar1.grid(column=0, row=1, sticky=tk.NSEW,padx=5,pady=3)
    #------------Tab1设备配置控件-------------#
     
    #------------Tab2收集信息控件-------------#
    #选择区
    monty2 = ttk.LabelFrame(tab2, text='选择')
    monty2.grid(column=0, row=0, padx=5, pady=4,ipadx= 2,ipady= 1,sticky=tk.NSEW)
    #设备路径
    ttk.Label(monty2, text="设备:").grid(column=0, row=0,sticky=tk.NSEW)
    file_path2 = tk.StringVar()
    nameEntered2 = ttk.Entry(monty2, width=38, textvariable=file_path2)
    nameEntered2.grid(column=1, row=0,sticky=tk.NSEW)
    chose_file2 = ttk.Button(monty2,text="导入",width=4,command=lambda: chose_file(nameEntered2))   
    chose_file2.grid(column=2,row=0,padx=0,sticky=tk.NSEW)
    #选择文件
    ttk.Label(monty2, text="线程:").grid(column=0, row=1,sticky=tk.NSEW)
    thread2 = tk.IntVar()
    threadchose2 = ttk.Combobox(monty2, width=39, textvariable=thread2)
    threadchose2['values'] = (20,50,100)
    threadchose2.grid(column=1, row=1,columnspan=2,pady=1,sticky=tk.NSEW)
    threadchose2.current(1)  #设置初始显示值，值为元组['values']的下标
    threadchose2.config(state='readonly')  #设为只读模式
    #模块选择
    ttk.Label(monty2, text="模块:").grid(column=0, row=2,sticky=tk.NSEW)
    modeltxt = tk.StringVar()
    model = ttk.Combobox(monty2, width=39, textvariable=modeltxt)
    model['values'] = ('收集设备硬件信息','收集光模块信息','收集设备配置信息','收集版本补丁信息','收集设备SN信息','收集设备Int信息','收集设备IntVer信息','收集设备License信息')
    model.grid(column=1, row=2,columnspan=2,pady=1,sticky=tk.NSEW)
    model.current(0)  #设置初始显示值，值为元组['values']的下标
    model.config(state='readonly')  #设为只读模式
    #选项区
    option = ttk.LabelFrame(tab2, text='选项')
    option.grid(column=0, row=1, padx=5, pady=4,ipadx= 2,ipady= 2,sticky=tk.NSEW)
    option.rowconfigure(1,weight=1)
    placeholder2 = tk.Label(option,text="")
    placeholder2.grid(column=0,  row=2,sticky=tk.NSEW,padx=2,pady=8,columnspan=2)
    
    # 执行区
    conf2 = ttk.LabelFrame(tab2, text='执行')
    conf2.grid(column=0, row=2, padx=5, pady=4,ipadx= 2,ipady= 2,sticky=tk.NSEW)
    startconf2 = ttk.Button(conf2,text="收集",width=8,command=collect_start)   
    startconf2.pack( side = "left", padx = 15)
    cleanlog2 = ttk.Button(conf2,text="清空日志",width=8,command=lambda:logtxt2.delete(1.0,tk.END))   
    cleanlog2.pack( side = "right", padx = 15)
    stopconf2 = ttk.Button(conf2,text="停止",width=8,state='disabled')   
    stopconf2.pack( side = "right", padx = 15)
    #日志区
    logs2 = ttk.LabelFrame(tab2, text='日志')
    logs2.grid(column=1, row=0, rowspan=3,padx=8, pady=4,sticky=tk.NSEW)
    logs2.rowconfigure(0,weight=1);logs2.columnconfigure(0,weight=1)
    #日志文体框
    log2lW  = 45; log2lH  =  33
    logtxt2 = scrolledtext.ScrolledText(logs2, width=log2lW, height=log2lH, wrap=tk.WORD)
    logtxt2.grid(column=0, row=0, sticky=tk.NSEW,padx=5,pady=3)
    pbar2 = ttk.Progressbar(logs2, orient = "horizontal",  mode="determinate", value=0.0)
    pbar2.grid(column=0, row=1, sticky=tk.NSEW,padx=5,pady=3)
    #------------Tab2收集信息控件-------------#

    #------------Tab3配置生成控件-------------#
    #选择区
    monty3 = ttk.LabelFrame(tab3, text='选择')
    monty3.grid(column=0, row=0, padx=5, pady=4,ipadx= 2,ipady= 1,sticky=tk.NSEW)
    #设备路径
    ttk.Label(monty3, text="参数:").grid(column=0, row=0,sticky=tk.NSEW)
    file_path3 = tk.StringVar()
    nameEntered3 = ttk.Entry(monty3, width=38, textvariable=file_path3)
    nameEntered3.grid(column=1, row=0,sticky=tk.NSEW)
    chose_file3 = ttk.Button(monty3,text="导入",width=4,command=lambda: config_name(nameEntered3))   
    chose_file3.grid(column=2,row=0,padx=0,sticky=tk.NSEW)
    #选择文件
    ttk.Label(monty3, text="命名:").grid(column=0, row=1,sticky=tk.NSEW)
    name3 = tk.StringVar()
    namechose3 = ttk.Combobox(monty3, width=39, textvariable=name3)
    namechose3['values'] = ()
    namechose3.grid(column=1, row=1,columnspan=2,pady=1,sticky=tk.NSEW)
    namechose3.config(state='readonly')  #设为只读模式
    #模块选择
    ttk.Label(monty3, text="模板:").grid(column=0, row=2,sticky=tk.NSEW)
    modulstxt = tk.StringVar()
    moduls = ttk.Combobox(monty3, width=39, textvariable=modulstxt)
    moduls.grid(column=1, row=2,columnspan=2,pady=1,sticky=tk.NSEW)
    moduls.config(state='readonly')  #设为只读模式
    #moduls.bind("<<ComboboxSelected>>", show_moduls)
    #选项区
    option3 = ttk.LabelFrame(tab3, text='选项')
    option3.grid(column=0, row=1, padx=5, pady=4,ipadx= 2,ipady= 2,sticky=tk.NSEW)
    option3.rowconfigure(1,weight=1)
    placeholder3 = tk.Label(option3,text="全局参数")
    placeholder3.grid(column=0,  row=0,sticky=tk.W)
    golbal_scr = scrolledtext.ScrolledText(option3, width=45, wrap='none')
    golbal_scr.grid(column=0, row=1,sticky=tk.NSEW,columnspan=3)
    #golbal_scr.columnconfigure(0,weight=1)
    # 执行区
    conf3 = ttk.LabelFrame(tab3, text='执行')
    conf3.grid(column=0, row=2, padx=5, pady=4,ipadx= 2,ipady= 2,sticky=tk.NSEW)
    startconf3 = ttk.Button(conf3,text="生成",width=8,command=creat_config)
    startconf3.pack( side = "left", padx = 15)
    cleanlog3 = ttk.Button(conf3,text="清空日志",width=8,command=lambda:logtxt3.delete(1.0,tk.END))
    cleanlog3.pack( side = "right", padx = 15)
    stopconf3 = ttk.Button(conf3,text="打开目录",width=8,command=open_path)   
    stopconf3.pack( side = "right", padx = 15)
    #日志区
    logs3 = ttk.LabelFrame(tab3, text='日志')
    logs3.grid(column=1, row=0, rowspan=3,padx=8, pady=4,sticky=tk.NSEW)
    logs3.rowconfigure(0,weight=1);logs3.columnconfigure(0,weight=1)
    #日志文体框
    logtxt3 = scrolledtext.ScrolledText(logs3, wrap=tk.WORD)
    logtxt3.grid(column=0, row=0, sticky=tk.NSEW,padx=5,pady=3)
    pbar3 = ttk.Progressbar(logs3, orient = "horizontal",  mode="determinate", value=0.0)
    pbar3.grid(column=0, row=1, sticky=tk.NSEW,padx=5,pady=3)
    jinja_moduls("templates/jinja2")
    #------------Tab3配置生成控件-------------#

    nameEntered1.focus()      
    win.mainloop()

if __name__ == '__main__':
    #multiprocessing.freeze_support() #转换成exe在window环境使用时需要添加,其它环境请注释
    set_win()
