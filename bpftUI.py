from io import BytesIO
from PIL import Image
import random
import time
import json
import re
import base64
import tempfile
import threading
import webbrowser
import zlib
# noinspection PyCompatibility
from tkinter import *

import requests
import urllib3
from retrying import retry
import sys

'''
软件名: BaiduPanFilesTransfers
版本: 1.2
更新时间: 2020.7.7
打包命令: pyinstaller -F -w -i bpftUI.ico bpftUI.py
'''

# 实例化TK
root = Tk()

# 运行时替换图标
ICON = zlib.decompress(base64.b64decode('eJxjYGAEQgEBBiDJwZDBysAgxsDAoAHEQCEGBQaIOAg4sDIgACMUj4JRMApGwQgF/ykEAFXxQRc='))
_, ICON_PATH = tempfile.mkstemp()
with open(ICON_PATH, 'wb') as icon_file:
    icon_file.write(ICON)
    
# if ( sys.platform.startswith('win')): 
#     root.iconbitmap(default=ICON_PATH)
# else:
#     logo = PhotoImage(file=ICON_PATH)
#     root.call('wm', 'iconphoto', root._w, logo)

# root.iconbitmap(ICON_PATH)

# 主窗口配置
root.wm_title("度盘转存 1.2 by Alice & Asu")
root.wm_geometry('350x426+240+240')
root.wm_attributes("-alpha", 0.98)
root.resizable(width=False, height=False)

# 定义标签和文本框
Label(root, text='1.下面填入百度Cookies,以BAIDUID=开头到结尾,不带引号').grid(row=1, column=0, sticky=W)
entry_cookie = Entry(root, width=48, )
entry_cookie.grid(row=2, column=0, sticky=W, padx=4)
Label(root, text='2.下面填入文件保存位置(默认根目录),不能包含<,>,|,*,?,,/').grid(row=3, column=0, sticky=W)
entry_folder_name = Entry(root, width=48, )
entry_folder_name.grid(row=4, column=0, sticky=W, padx=4)
Label(root, text='3.下面粘贴链接,每行一个,支持秒传.格式为:链接 提取码').grid(row=5, sticky=W)

# 链接输入框
text_links = Text(root, width=48, height=10, wrap=NONE)
text_links.grid(row=6, column=0, sticky=W, padx=4, )
scrollbar_links = Scrollbar(root, width=5)
scrollbar_links.grid(row=6, column=0, sticky=S + N + E, )
scrollbar_links.configure(command=text_links.yview)
text_links.configure(yscrollcommand=scrollbar_links.set)

# 日志输出框
text_logs = Text(root, width=48, height=10, wrap=NONE)
text_logs.grid(row=8, column=0, sticky=W, padx=4, )
scrollbar_logs = Scrollbar(root, width=5)
scrollbar_logs.grid(row=8, column=0, sticky=S + N + E, )
scrollbar_logs.configure(command=text_logs.yview)
text_logs.configure(yscrollcommand=scrollbar_logs.set)

# 定义按钮和状态标签
bottom_run = Button(root, text='4.点击运行', command=lambda: thread_it(main, ), width=10, height=1, relief='solid')
bottom_run.grid(row=7, pady=6, sticky=W, padx=4)
label_state = Label(root, text='检查更新', font=('Arial', 9, 'underline'), foreground="#0000ff", cursor='heart')
label_state.grid(row=7, sticky=E, padx=4)
label_state.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/hxz393/BaiduPanFilesTransfers", new=0))

# 公共请求头
request_header = {
    'Host': 'pan.baidu.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36',
    'Sec-Fetch-Dest': 'document',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-site',
    'Sec-Fetch-Mode': 'navigate',
    'Referer': 'https://pan.baidu.com',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cookie': '''BAIDUID=B8CE8F13323648199D15E1AADC87FAA8:FG=1; H_WISE_SIDS=148077_149390_150185_109775_142019_149355_150074_147091_141748_150087_148193_148866_147685_148714_148434_147279_150041_149531_149540_150154_148439_148754_147890_146575_148523_147347_127969_148794_147351_149718_150345_146734_138425_149558_145996_131423_100806_132550_149008_147527_145596_107319_147137_148186_147717_149251_150399_146396_144966_149279_145608_148049_148424_148751_147547_146053_148868_110085; STOKEN=bf8f78c0dad90a7e27fa743b0a03f1215db1639a5a31f1327cd0c62f75fd63dd; SCRC=f91991f1a9072fe77af33e32ceb001fa; cflag=13%3A3; ZD_ENTRY=google; BDCLND=oMkK%2Fo1NQiQVqASoeRiTd5QtpcHY9Y%2BA; Hm_lvt_7a3960b6f067eb0085b7f96ff5e660b0=1595237581,1595237700,1595238519,1595240321; Hm_lpvt_7a3960b6f067eb0085b7f96ff5e660b0=1595256261; PANPSC=5142017323306576694%3ACU2JWesajwA9L7226RJlszuv496EomYGrFsbUd3ehrTPzW21GgvS0MKFw3Ww%2Fpq%2Bmn%2BJhdPwvbnjBmRBn1u2%2F22n7K8%2B7H%2FNiVleys3zxXZFah9uWgECZxt0GEZyVdQnrWefqB28LP2i%2BY1X7udr9G2gud9gLjYtRogbeq4A%2FVImU589kUerfkfbyt4Ev2n6fPVXoOSO8Qs7qAHgpfUwRg%3D%3D; PSTM=1568516374; BIDUPSID=0014E097ED6A42C05BC6DCD6D65D2D3E; BDUSS=cxbGpwLWVhaDVxT0p-QXlhbENhT2NaZWdpNlV0Snk5fnNzMEE2WnJWNC1xVzllRVFBQUFBJCQAAAAAAAAAAAEAAAAPDOwAR29sZGlvcmwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD4cSF4-HEheVU; PANWEB=1;''',
}
urllib3.disable_warnings()
s = requests.session()


# 获取bdstoken函数
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def get_bdstoken():
    url = 'https://pan.baidu.com/disk/home'
    response = s.get(url=url, headers=request_header, timeout=20, allow_redirects=True, verify=False)
    bdstoken_list = re.findall('"bdstoken":"(\\S+?)",', response.text)
    return bdstoken_list[0] if bdstoken_list else 1


# 获取目录列表函数
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def get_dir_list(bdstoken):
    url = 'https://pan.baidu.com/api/list?order=time&desc=1&showempty=0&web=1&page=1&num=1000&dir=%2F&bdstoken=' + bdstoken
    response = s.get(url=url, headers=request_header, timeout=15, allow_redirects=False, verify=False)
    return response.json()['errno'] if response.json()['errno'] != 0 else response.json()['list']


# 新建目录函数
@retry(stop_max_attempt_number=5, wait_fixed=1000)
def create_dir(dir_name, bdstoken):
    url = 'https://pan.baidu.com/api/create?a=commit&bdstoken=' + bdstoken
    post_data = {'path': dir_name, 'isdir': '1', 'block_list': '[]', }
    response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
    return response.json()['errno']


# 检测链接种类
def check_link_type(link_list_line):
    if link_list_line.find('https://pan.baidu.com/s/') >= 0:
        link_type = '/s/'
    elif bool(re.search('(bdlink=|bdpan://|BaiduPCS-Go)', link_list_line, re.IGNORECASE)):
        link_type = 'rapid'
    elif link_list_line.count('#') == 3:
        link_type = 'rapid'
    else:
        link_type = 'unknown'
    return link_type


# 验证链接函数
@retry(stop_max_attempt_number=20, wait_fixed=2000)
def check_links(link_url, pass_code, bdstoken):
    pass_code = ''
    # 验证提取码
    check_url = 'https://pan.baidu.com/share/verify?surl=' + link_url[25:48] + '&bdstoken=' + bdstoken
    post_data = {'pwd': pass_code, 'vcode': '', 'vcode_str': '', }
    post_data = {'vcode': '', 'vcode_str': '', }
    post_data = {}
    print(check_url)
    print(post_data)
    response_post = s.post(url=check_url, headers=request_header, data=post_data, timeout=10, allow_redirects=False,
                           verify=False)
    print(response_post.json())
    if response_post.json()['errno'] == 0:
        bdclnd = response_post.json()['randsk']
        request_header['Cookie'] = re.sub(r'BDCLND=(\S+?);', r'BDCLND=' + bdclnd + ';', request_header['Cookie'])
    else:
        return response_post.json()['errno']
    # 获取文件信息
    response = s.get(url=link_url, headers=request_header, timeout=15, allow_redirects=True,
                     verify=False).content.decode("utf-8")
    shareid_list = re.findall('"shareid":(\\d+?),"', response)
    user_id_list = re.findall('"uk":(\\d+?),"', response)
    fs_id_list = re.findall('"fs_id":(\\d+?),"', response)
    if not shareid_list:
        return 1
    elif not user_id_list:
        return 2
    elif not fs_id_list:
        return 3
    else:
        return [shareid_list[0], user_id_list[0], fs_id_list[0]]


# 转存文件函数
@retry(stop_max_attempt_number=200, wait_fixed=2000)
def transfer_files(check_links_reason, dir_name, bdstoken):
    print("in transfer function")
    url = 'https://pan.baidu.com/share/transfer?shareid=' + check_links_reason[0] + '&from=' + check_links_reason[
        1] + '&bdstoken=' + bdstoken
    post_data = {'fsidlist': '[' + check_links_reason[2] + ']', 'path': '/' + dir_name, }
    print(f"Going to post {url}")
    print(post_data)
    response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
    return response.json()['errno']


# 转存秒传链接函数
@retry(stop_max_attempt_number=100, wait_fixed=1000)
def transfer_files_rapid(rapid_data, dir_name, bdstoken):
    url = 'https://pan.baidu.com/api/rapidupload?bdstoken=' + bdstoken
    post_data = {'path': dir_name + '/' + rapid_data[3], 'content-md5': rapid_data[0].lower(),
                 'slice-md5': rapid_data[1].lower(), 'content-length': rapid_data[2]}
    response = s.post(url=url, headers=request_header, data=post_data, timeout=15, allow_redirects=False, verify=False)
    return response.json()['errno']


# 状态标签变化函数
def label_state_change(state, task_count=0, task_total_count=0):
    label_state.unbind("<Button-1>")
    label_state['font'] = ('Arial', 9)
    label_state['foreground'] = "#000000"
    label_state['cursor'] = "arrow"
    if state == 'error':
        label_state['text'] = '发生错误,错误日志如下:'
    elif state == 'running':
        label_state['text'] = '下面为转存结果,进度:' + str(task_count) + '/' + str(task_total_count)


# 多线程
def thread_it(func, *args):
    t = threading.Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()
    # t.join()


# 主程序
def main():
    # 获取和初始化数据
    text_logs.delete(1.0, END)
    test_cookie= '''BAIDUID=B8CE8F13323648199D15E1AADC87FAA8:FG=1; H_WISE_SIDS=148077_149390_150185_109775_142019_149355_150074_147091_141748_150087_148193_148866_147685_148714_148434_147279_150041_149531_149540_150154_148439_148754_147890_146575_148523_147347_127969_148794_147351_149718_150345_146734_138425_149558_145996_131423_100806_132550_149008_147527_145596_107319_147137_148186_147717_149251_150399_146396_144966_149279_145608_148049_148424_148751_147547_146053_148868_110085; STOKEN=bf8f78c0dad90a7e27fa743b0a03f1215db1639a5a31f1327cd0c62f75fd63dd; SCRC=f91991f1a9072fe77af33e32ceb001fa; cflag=13%3A3; BDCLND=oMkK%2Fo1NQiQVqASoeRiTd5QtpcHY9Y%2BA; Hm_lvt_7a3960b6f067eb0085b7f96ff5e660b0=1595257181,1595257377,1595257892,1595383987; Hm_lpvt_7a3960b6f067eb0085b7f96ff5e660b0=1595383987; PANPSC=14571009530832443580%3ACU2JWesajwA9L7226RJlszuv496EomYGrFsbUd3ehrTPzW21GgvS0MKFw3Ww%2Fpq%2BnWeMPDUM0J7jBmRBn1u2%2F22n7K8%2B7H%2FNiVleys3zxXZFah9uWgECZxt0GEZyVdQnrWefqB28LP2i%2BY1X7udr9G2gud9gLjYtRogbeq4A%2FVImU589kUerfkfbyt4Ev2n6fPVXoOSO8Qs7qAHgpfUwRg%3D%3D;PSTM=1568516374; BIDUPSID=0014E097ED6A42C05BC6DCD6D65D2D3E; BDUSS=cxbGpwLWVhaDVxT0p-QXlhbENhT2NaZWdpNlV0Snk5fnNzMEE2WnJWNC1xVzllRVFBQUFBJCQAAAAAAAAAAAEAAAAPDOwAR29sZGlvcmwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD4cSF4-HEheVU; PANWEB=1;'''
    cookie = "".join(test_cookie.split())
    request_header['Cookie'] = cookie
    dir_name = entry_folder_name.get()
    dir_name = "".join(dir_name.split())
    text_input = text_links.get(1.0, END).split('\n')
    link_list = [link for link in text_input if link]
    link_list = open("output.txt", 'r').read().splitlines()
    # link_list = ["https://pan.baidu.com/s/1v5lyBsTMeKNJGbbdlz8NRA"]
    link_list = [link + ' ' for link in link_list]
    task_count = 0
    task_total_count = len(link_list)
    bottom_run['state'] = 'disabled'
    bottom_run['relief'] = 'groove'
    bottom_run['text'] = '运行中...'

    # 开始运行函数
    try:
        # 检查cookie输入是否正确
        if cookie[:8] != 'BAIDUID=':
            label_state_change(state='error')
            text_logs.insert(END, '百度网盘cookie输入不正确,请检查cookie后重试.' + '\n')
            sys.exit()

        # 执行获取bdstoken
        bdstoken = get_bdstoken()
        if bdstoken == 1:
            label_state_change(state='error')
            text_logs.insert(END, '没获取到bdstoken,请检查cookie和网络后重试.' + '\n')
            sys.exit()

        # 执行获取目录列表
        dir_list_json = get_dir_list(bdstoken)
        if type(dir_list_json) != list:
            label_state_change(state='error')
            text_logs.insert(END, '没获取到网盘目录列表,请检查cookie和网络后重试.' + '\n')
            sys.exit()

        # 执行新建目录
        dir_list = [dir_json['server_filename'] for dir_json in dir_list_json]
        if dir_name and dir_name not in dir_list:
            create_dir_reason = create_dir(dir_name, bdstoken)
            if create_dir_reason != 0:
                label_state_change(state='error')
                text_logs.insert(END, '文件夹名带非法字符,请改正文件夹名称后重试.' + '\n')
                sys.exit()

        # 执行转存
        for url_code in link_list:
            # 处理用户输入
            link_type = check_link_type(url_code)
            # 处理(https://pan.baidu.com/s/1tU58ChMSPmx4e3-kDx1mLg lice)格式链接
            if link_type == '/s/':
                share_res = s.get(url_code, headers=request_header)
                print("result good")
                share_page = share_res.content.decode("utf-8")
                share_data = json.loads(re.search("yunData.setData\(({.*})\)", share_page).group(1))
                # bdstoken = share_data['bdstoken']
                shareid = share_data['shareid']
                _from = share_data['uk']
                file_list = share_data['file_list']['list']
                fsidList = ','.join([str(item['fs_id'])
                                           for item in file_list])
                meta_tuple = (str(shareid), str(_from), fsidList)
                # print(meta_tuple)
                transfer_files_reason = transfer_files(
                    meta_tuple, dir_name, bdstoken)
                # print("outside transfer function")
                if transfer_files_reason == 12:
                    text_logs.insert(END, '转存失败,目录中已有同名文件存在:' + url_code + '\n')
                elif transfer_files_reason == 0:
                    text_logs.insert(END, '转存成功:' + url_code + '\n')
                else:
                    text_logs.insert(END, '转存失败,错误代码(' + str(transfer_files_reason) + '):' + url_code + '\n')
            # if link_type == '/s/':
                # link_url, pass_code = re.sub(r'提取码*[：:](.*)', r'\1', url_code).split(' ', maxsplit=1)
                # pass_code = pass_code.strip()[:4]
                # # 执行检查链接有效性
                # check_links_reason = check_links(link_url, pass_code, bdstoken)
                # if check_links_reason == 1:
                #     text_logs.insert(END, '链接失效,没获取到shareid:' + url_code + '\n')
                # elif check_links_reason == 2:
                #     text_logs.insert(END, '链接失效,没获取到user_id:' + url_code + '\n')
                # elif check_links_reason == 3:
                #     text_logs.insert(END, '链接失效,文件已经被删除:' + url_code + '\n')
                # elif check_links_reason == -12:
                #     text_logs.insert(END, '提取码错误:' + url_code + '\n')
                # elif check_links_reason == -62:
                #     text_logs.insert(END, '错误尝试次数过多,请稍后再试:' + url_code + '\n')
                # else:
                #     # 执行转存文件
                #     transfer_files_reason = transfer_files(check_links_reason, dir_name, bdstoken)
                #     if transfer_files_reason == 12:
                #         text_logs.insert(END, '转存失败,目录中已有同名文件存在:' + url_code + '\n')
                #     elif transfer_files_reason == 0:
                #         text_logs.insert(END, '转存成功:' + url_code + '\n')
                #     else:
                #         text_logs.insert(END, '转存失败,错误代码(' + str(transfer_files_reason) + '):' + url_code + '\n')
            # 处理秒传格式链接
            elif link_type == 'rapid':
                # 处理梦姬标准(4FFB5BC751CC3B7A354436F85FF865EE#797B1FFF9526F8B5759663EC0460F40E#21247774#秒传.rar)
                if url_code.count('#') == 3:
                    rapid_data = url_code.split('#')
                # 处理游侠 v1标准(bdlink=)
                elif bool(re.search('bdlink=', url_code, re.IGNORECASE)):
                    rapid_data = base64.b64decode(re.findall(r'bdlink=(.+)', url_code)[0]).decode(
                        "utf-8").strip().split('#')
                # 处理PanDL标准(bdpan://)
                elif bool(re.search('bdpan://', url_code, re.IGNORECASE)):
                    bdpan_data = base64.b64decode(re.findall(r'bdpan://(.+)', url_code)[0]).decode(
                        "utf-8").strip().split('|')
                    rapid_data = [bdpan_data[2], bdpan_data[3], bdpan_data[1], bdpan_data[0]]
                # 处理PCS-Go标准(BaiduPCS-Go)
                elif bool(re.search('BaiduPCS-Go', url_code, re.IGNORECASE)):
                    go_md5 = re.findall(r'-md5=(\S+)', url_code)[0]
                    go_md5s = re.findall(r'-slicemd5=(\S+)', url_code)[0]
                    go_len = re.findall(r'-length=(\S+)', url_code)[0]
                    go_name = re.findall(r'-crc32=\d+\s(.+)', url_code)[0].replace('"', '').replace('/', '\\').strip()
                    rapid_data = [go_md5, go_md5s, go_len, go_name]
                else:
                    rapid_data = []
                transfer_files_reason = transfer_files_rapid(rapid_data, dir_name, bdstoken)
                if transfer_files_reason == 0:
                    text_logs.insert(END, '转存成功:' + url_code + '\n')
                elif transfer_files_reason == -8:
                    text_logs.insert(END, '转存失败,目录中已有同名文件存在:' + url_code + '\n')
                elif transfer_files_reason == 404:
                    text_logs.insert(END, '转存失败,秒传无效:' + url_code + '\n')
                elif transfer_files_reason == 2:
                    text_logs.insert(END, '转存失败,非法路径:' + url_code + '\n')
                elif transfer_files_reason == -10:
                    text_logs.insert(END, '转存失败,容量不足:' + url_code + '\n')
                elif transfer_files_reason == 114514:
                    text_logs.insert(END, '转存失败,接口调用失败:' + url_code + '\n')
                else:
                    text_logs.insert(END, '转存失败,错误代码(' + str(transfer_files_reason) + '):' + url_code + '\n')
            elif link_type == 'unknown':
                text_logs.insert(END, '不支持链接:' + url_code + '\n')
                task_count = task_count + 1
                label_state_change(state='running', task_count=task_count, task_total_count=task_total_count)
                continue
            task_count = task_count + 1
            label_state_change(state='running', task_count=task_count, task_total_count=task_total_count)
    except Exception as e:
        text_logs.insert(END, '运行出错,请重新运行本程序.错误信息如下:' + '\n')
        text_logs.insert(END, str(e) + '\n\n')
        text_logs.insert(END, '用户输入内容:' + '\n')
        text_logs.insert(END, '百度Cookies:' + cookie + '\n')
        text_logs.insert(END, '文件夹名:' + dir_name + '\n')
        text_logs.insert(END, '链接输入:' + '\n' + str(text_input))
    # 恢复按钮状态
    finally:
        bottom_run['state'] = 'normal'
        bottom_run['relief'] = 'solid'
        bottom_run['text'] = '4.点击运行'


# coding="utf-8"

# coding="utf-8"

# 解决验证码问题，经过测试实际使用过程中不会出验证码，所以没装的话可以屏蔽掉
# import pytesseract


'''
初次使用时，请先从浏览器的开发者工具中获取百度网盘的Cookie，并设置在init方法中进行配置，并调用verifyCookie方法测试Cookie的有效性
已实现的方法：
1.获取登录Cookie有效性；
2.获取网盘中指定目录的文件列表；
3.获取加密分享链接的提取码；
4.转存分享的资源；
5.重命名网盘中指定的文件；
6.删除网盘中的指定文件；
7.移动网盘中指定文件至指定目录；
8.创建分享链接；
'''

class BaiDuPan(object): 
    def __init__(self):
        # 创建session并设置初始登录Cookie
        self.session = requests.session()
        self.session.cookies['BDUSS'] = ''
        self.session.cookies['STOKEN'] = ''
        self.headers = {
            'Host': 'pan.baidu.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
        }

    '''
    验证Cookie是否已登录
    返回值errno代表的意思：
    0 有效的Cookie；1 init方法中未配置登录Cookie；2 无效的Cookie
    '''

    def verifyCookie(self):
        if(self.session.cookies['BDUSS'] == '' or self.session.cookies['STOKEN'] == ''):
            return {'errno': 1, 'err_msg': '请在init方法中配置百度网盘登录Cookie'}
        else:
            response = self.session.get(
                'https://pan.baidu.com/', headers=self.headers)
            home_page = response.content.decode("utf-8")
            if('<title>百度网盘-全部文件</title>' in home_page):
                user_name = re.findall(
                    r'initPrefetch\((.+?)\'\)', home_page)[0]
                user_name = re.findall(r'\, \'(.+?)\'\)', home_page)[0]
                return {'errno': 0, 'err_msg': '有效的Cookie，用户名：%s' % user_name}
            else:
                return {'errno': 2, 'err_msg': '无效的Cookie！'}

    '''
    获取指定目录的文件列表，直接返回原始的json
    '''

    def getFileList(self, dir='/', order='time', desc=0, page=1, num=100):
        '''
        构造获取文件列表的URL：
        https://pan.baidu.com/api/list?
        bdstoken=  从首页中可以获取到
        &dir=/  需要获取的目录
        &order=name  可能值：name，time，size
        &desc=0  0表示正序，1表示倒序
        &page=  第几页
        &num=100  每页文件数量
        &t=0.8685513844705777  推测为随机字符串
        &startLogTime=1581862647373  时间戳
        &logid=MTU4MTg2MjY0NzM3MzAuMzM2MTAzMzk5MTg3NzYyOQ==  固定值
        &clienttype=0  固定值
        &showempty=0  固定值
        &web=1  固定值
        &channel=chunlei  固定值
        &app_id=250528  固定值
        '''
        # 访问首页获取bdstoken
        response = self.session.get(
            'https://pan.baidu.com/', headers=self.headers)
        bdstoken = re.findall(
            r'initPrefetch\(\'(.+?)\'\,', response.content.decode("utf-8"))[0]
        t = random.random()
        startLogTime = str(int(time.time()) * 1000)
        url = 'https://pan.baidu.com/api/list?bdstoken=%s&dir=%s&order=%s&desc=%s&page=%s&num=%s&t=%s&startLogTime=%s\
                &logid=MTU4MTg2MjY0NzM3MzAuMzM2MTAzMzk5MTg3NzYyOQ==&clienttype=0&showempty=0&web=1&channel=chunlei&app_id=250528'\
                % (bdstoken, dir, order, desc, page, num, t, startLogTime)
        headers = self.headers
        headers['Referer'] = 'https://pan.baidu.com/disk/home?'
        response = self.session.get(url, headers=headers)
        return response.json()

    '''
    获取分享链接的提取码
    返回值errno代表的意思：
    0 提取码获取成功；1 提取码获取失败；
    '''
    @staticmethod
    def getSharePwd(surl):
        # 云盘精灵的接口
        ypsuperkey_headers = {
            'Host': 'ypsuperkey.meek.com.cn',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
        }
        response = requests.get(
            'https://ypsuperkey.meek.com.cn/api/v1/items/BDY-%s?client_version=2019.2' % surl, headers=ypsuperkey_headers)
        pwd = response.json().get('access_code', '')
        if(not pwd):
            # 小鸟云盘搜索接口
            aisou_headers = {
                'Host': 'helper.aisouziyuan.com',
                'Origin': 'https://pan.baidu.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
                'Referer': 'https://pan.baidu.com/share/init?surl=%s' % surl,
            }
            form_data = {
                'url': surl,
                'wrong': 'false',
                'type': 'baidu',
                'v': '3.132',
            }
            response = requests.post(
                'https://helper.aisouziyuan.com/Extensions/Api/ResourcesCode?v=3.132', headers=aisou_headers, data=form_data)
            pwd = response.text
        errno, err_msg = (0, '提取码获取成功') if pwd else (
            1, '提取码获取失败：%s' % response.text)
        return {'errno': errno, 'err_msg': err_msg, 'pwd': pwd}

    '''
    识别 验证加密分享时的验证码
    返回值errno代表的意思：
    0 识别成功；1 识别失败；其他值 获取验证码失败；
    '''

    def vcodeOCR(self):
        # 获取验证码
        vcode_res = requests.get(
            'https://pan.baidu.com/api/getcaptcha?prod=shareverify&web=1&channel=chunlei&web=1&app_id=250528&bdstoken=null&clienttype=0', headers=self.headers)
        vcode_json = vcode_res.json()
        if(vcode_json['errno'] == 0):
            # 获取验证码图片
            genimage = requests.get(
                vcode_json['vcode_img'], headers=self.headers)
            # 非自动化脚本，可以改为人工识别，并且将人工识别的验证码保存，用于后续的CNN训练
            vcode_image = BytesIO(genimage.content)
            image = Image.open(vcode_image)
            image.show()
            vcode = input('请输入验证码：')
            f = open('./vcodeImg/%s - %s.jpg' %
                     (vcode, str(int(time.time()) * 1000)), 'wb')
            f.write(genimage.content)
            f.close()

            '''
            将验证码图片加载至内存中进行自动识别
            由于验证码旋转和紧贴，所以导致pytesseract识别率非常底！
            考虑基于CNN深度学习识别，筹备数据集需要一定的时间
            临时解决方案是：识别失败进行重试，加大重试次数
            '''
            # vcode_image = BytesIO(genimage.content)
            # image = Image.open(vcode_image)
            # vcode = pytesseract.image_to_string(image)
            errno, err_msg = (1, '识别失败') if(len(vcode) != 4) else (0, '识别成功')
            vcode_str = vcode_json['vcode_str']
        else:
            errno = vcode_json['errno']
            err_msg = '获取验证码失败'
            vcode_str = ''
        return {'errno': errno, 'err_msg': err_msg, 'vcode': vcode, 'vcode_str': vcode_str}

    '''
    验证加密分享
    返回值errno代表的意思：
    0 加密分享验证通过；1 验证码获取失败；2 提取码不正确；3 加密分享验证失败；4 重试几次后，验证码依旧不正确；
    '''

    def verifyShare(self, surl, bdstoken, pwd, referer):
        '''
        构造密码验证的URL：https://pan.baidu.com/share/verify?
        surl=62yUYonIFdKGdAaueOkyaQ  从重定向后的URL中获取
        &t=1572356417593  时间戳
        &channel=chunlei  固定值
        &web=1  固定值
        &app_id=250528  固定值
        &bdstoken=742aa0d6886423a5503bbc67afdb2a7d  从重定向后的页面中可以找到，有时候会为空，经过验证，不要此字段也可以
        &logid=MTU0ODU4MzUxMTgwNjAuNDg5NDkyMzg5NzAyMzY1MQ==  不知道什么作用，暂时为空或者固定值都可以
        &clienttype=0  固定值
        '''
        t = str(int(time.time()) * 1000)
        url = 'https://pan.baidu.com/share/verify?surl=%s&t=%s&channel=chunlei&web=1&app_id=250528&bdstoken=%s\
                &logid=MTU0ODU4MzUxMTgwNjAuNDg5NDkyMzg5NzAyMzY1MQ==&clienttype=0' % (surl, t, bdstoken)
        form_data = {
            'pwd': pwd,
            'vcode': '',
            'vcode_str': '',
        }
        # 设置重试机制
        is_vcode = False
        for n in range(1, 166):
            # 自动获取并识别验证码，使用pytesseract自动识别时，可加大重试次数
            if is_vcode:
                ocr_result = self.vcodeOCR()
                if(ocr_result['errno'] == 0):
                    form_data['vcode'] = ocr_result['vcode']
                    form_data['vcode_str'] = ocr_result['vcode_str']
                elif(ocr_result['errno'] == 1):
                    continue
                else:
                    return {'errno': 1, 'err_msg': '验证码获取失败：%d' % ocr_result['errno']}
            headers = self.headers
            headers['referer'] = referer
            # verify_json['errno']：-9表示提取码不正确；-62表示需要验证码/验证码不正确（不输入验证码也是此返回值）
            verify_res = self.session.post(
                url, headers=headers, data=form_data)
            verify_json = verify_res.json()
            if(verify_json['errno'] == 0):
                return {'errno': 0, 'err_msg': '加密分享验证通过'}
            elif(verify_json['errno'] == -9):
                return {'errno': 2, 'err_msg': '提取码不正确'}
            elif(verify_json['errno'] == -62):
                is_vcode = True
            else:
                return {'errno': 3, 'err_msg': '加密分享验证失败：%d' % verify_json['errno']}
        return {'errno': 4, 'err_msg': '重试多次后，验证码依旧不正确：%d' % (verify_json['errno'] if("verify_json" in locals()) else -1)}

    '''
    返回值errno代表的意思：
    0 转存成功；1 无效的分享链接；2 分享文件已被删除；
    3 分享文件已被取消；4 分享内容侵权，无法访问；5 找不到文件；6 分享文件已过期
    7 获取提取码失败；8 获取加密cookie失败； 9 转存失败；
    '''

    def saveShare(self, url, pwd=None, path='/'):
        share_res = self.session.get(url, headers=self.headers)
        share_page = share_res.content.decode("utf-8")
        '''
        1.如果分享链接有密码，会被重定向至输入密码的页面；
        2.如果分享链接不存在，会被重定向至404页面https://pan.baidu.com/error/404.html，但是状态码是200；
        3.如果分享链接已被删除，页面会提示：啊哦，你来晚了，分享的文件已经被删除了，下次要早点哟。
        4.如果分享链接已被取消，页面会提示：啊哦，你来晚了，分享的文件已经被取消了，下次要早点哟。
        5.如果分享链接涉及侵权，页面会提示：此链接分享内容可能因为涉及侵权、色情、反动、低俗等信息，无法访问！
        6.啊哦！链接错误没找到文件，请打开正确的分享链接!
        7.啊哦，来晚了，该分享文件已过期
        '''
        if('error/404.html' in share_res.url):
            return {"errno": 1, "err_msg": "无效的分享链接", "extra": "", "info": ""}
        if('你来晚了，分享的文件已经被删除了，下次要早点哟' in share_page):
            return {"errno": 2, "err_msg": "分享文件已被删除", "extra": "", "info": ""}
        if('你来晚了，分享的文件已经被取消了，下次要早点哟' in share_page):
            return {"errno": 3, "err_msg": "分享文件已被取消", "extra": "", "info": ""}
        if('此链接分享内容可能因为涉及侵权、色情、反动、低俗等信息，无法访问' in share_page):
            return {"errno": 4, "err_msg": "分享内容侵权，无法访问", "extra": "", "info": ""}
        if('链接错误没找到文件，请打开正确的分享链接' in share_page):
            return {"errno": 5, "err_msg": "链接错误没找到文件", "extra": "", "info": ""}
        if('啊哦，来晚了，该分享文件已过期' in share_page):
            return {"errno": 6, "err_msg": "分享文件已过期", "extra": "", "info": ""}

        # 提取码校验的请求中有此参数
        bdstoken = re.findall(r'bdstoken\":\"(.+?)\"', share_page)
        bdstoken = bdstoken[0] if(bdstoken) else ''
        # 如果加密分享，需要验证提取码，带上验证通过的Cookie再请求分享链接，即可获取分享文件
        if('init' in share_res.url):
            surl = re.findall(r'surl=(.+?)$', share_res.url)[0]
            if(pwd == None):
                pwd_result = self.getSharePwd(surl)
                if(pwd_result['errno'] != 0):
                    return {"errno": 7, "err_msg": pwd_result['err_msg'], "extra": "", "info": ""}
                else:
                    pwd = pwd_result['pwd']
            referer = share_res.url
            verify_result = self.verifyShare(surl, bdstoken, pwd, referer)
            if(verify_result['errno'] != 0):
                return {"errno": 8, "err_msg": verify_result['err_msg'], "extra": "", "info": ""}
            else:
                # 加密分享验证通过后，使用全局session刷新页面（全局session中带有解密的Cookie）
                share_res = self.session.get(url, headers=self.headers)
                share_page = share_res.content.decode("utf-8")
        # 更新bdstoken，有时候会出现 AttributeError: 'NoneType' object has no attribute 'group'，重试几次就好了
        share_data = json.loads(
            re.search("yunData.setData\(({.*})\)", share_page).group(1))
        bdstoken = share_data['bdstoken']
        shareid = share_data['shareid']
        _from = share_data['uk']
        '''
        构造转存的URL，除了logid不知道有什么用，但是经过验证，固定值没问题，其他变化的值均可在验证通过的页面获取到
        '''
        save_url = 'https://pan.baidu.com/share/transfer?shareid=%s&from=%s&ondup=newcopy&async=1&channel=chunlei&web=1&app_id=250528&bdstoken=%s\
                    &logid=MTU3MjM1NjQzMzgyMTAuMjUwNzU2MTY4MTc0NzQ0MQ==&clienttype=0' % (shareid, _from, bdstoken)
        file_list = share_data['file_list']['list']
        form_data = {
            # 这个参数一定要注意，不能使用['fs_id', 'fs_id']，谨记！
            'fsidlist': '[' + ','.join([str(item['fs_id']) for item in file_list]) + ']',
            'path': path,
        }
        headers = self.headers
        headers['Origin'] = 'https://pan.baidu.com'
        headers['referer'] = url
        '''
        用带登录Cookie的全局session请求转存
        如果有同名文件，保存的时候会自动重命名：类似xxx(1)
        暂时不支持超过文件数量的文件保存
        '''
        save_res = self.session.post(save_url, headers=headers, data=form_data)
        save_json = save_res.json()
        errno, err_msg, extra, info = (0, '转存成功', save_json['extra'], save_json['info']) if(
            save_json['errno'] == 0) else (9, '转存失败：%d' % save_json['errno'], '', '')
        return {'errno': errno, 'err_msg': err_msg, "extra": extra, "info": info}

    '''
    重命名指定文件
    0 重命名成功；1 重命名失败；
    '''

    def rename(self, path, newname):
        '''
        构造重命名的URL：https://pan.baidu.com/api/filemanager?
        bdstoken=  从首页可以获取到
        &opera=rename  固定值
        &async=2  固定值
        &onnest=fail  固定值
        &channel=chunlei  固定在
        &web=1  固定值
        &app_id=250528  固定值
        &logid=MTU4MTk0MzY0MTQwNzAuNDA0MzQxOTM0MzE2MzM4Ng==  固定值
        &clienttype=0  固定值
        '''
        response = self.session.get(
            'https://pan.baidu.com/', headers=self.headers)
        bdstoken = re.findall(
            r'initPrefetch\(\'(.+?)\'\,', response.content.decode("utf-8"))[0]
        url = 'https://pan.baidu.com/api/filemanager?bdstoken=%s&opera=rename&async=2&onnest=fail&channel=chunlei&web=1&app_id=250528\
                &logid=MTU4MTk0MzY0MTQwNzAuNDA0MzQxOTM0MzE2MzM4Ng==&clienttype=0' % bdstoken
        form_data = {
            "filelist": "[{\"path\":\"%s\",\"newname\":\"%s\"}]" % (path, newname)}
        response = self.session.post(url, headers=self.headers, data=form_data)
        if(response.json()['errno'] == 0):
            return {'errno': 0, 'err_msg': '重命名成功！'}
        else:
            return {'errno': 1, 'err_msg': '重命名失败！', 'info': response.json()}

    '''
    删除指定文件
    0 删除成功；1 删除失败；
    '''

    def delete(self, path):
        '''
        构造重命名的URL：https://pan.baidu.com/api/filemanager?
        bdstoken=  从首页可以获取到
        &opera=delete  固定值
        &async=2  固定值
        &onnest=fail  固定值
        &channel=chunlei  固定在
        &web=1  固定值
        &app_id=250528  固定值
        &logid=MTU4MTk0MzY0MTQwNzAuNDA0MzQxOTM0MzE2MzM4Ng==  固定值
        &clienttype=0  固定值
        '''
        response = self.session.get(
            'https://pan.baidu.com/', headers=self.headers)
        bdstoken = re.findall(
            r'initPrefetch\(\'(.+?)\'\,', response.content.decode("utf-8"))[0]
        url = 'https://pan.baidu.com/api/filemanager?bdstoken=%s&opera=delete&async=2&onnest=fail&channel=chunlei&web=1&app_id=250528\
                &logid=MTU4MTk0MzY0MTQwNzAuNDA0MzQxOTM0MzE2MzM4Ng==&clienttype=0' % bdstoken
        form_data = {"filelist": "[\"%s\"]" % path}
        response = self.session.post(url, headers=self.headers, data=form_data)
        if(response.json()['errno'] == 0):
            return {'errno': 0, 'err_msg': '删除成功！'}
        else:
            return {'errno': 1, 'err_msg': '删除失败！', 'info': response.json()}

    '''
    移动文件至指定目录
    0 删除成功；1 删除失败；
    '''

    def move(self, path, destination, newname=False):
        '''
        构造重命名的URL：https://pan.baidu.com/api/filemanager?
        bdstoken=  从首页可以获取到
        &opera=move  固定值
        &async=2  固定值
        &onnest=fail  固定值
        &channel=chunlei  固定在
        &web=1  固定值
        &app_id=250528  固定值
        &logid=MTU4MTk0MzY0MTQwNzAuNDA0MzQxOTM0MzE2MzM4Ng==  固定值
        &clienttype=0  固定值
        '''
        response = self.session.get(
            'https://pan.baidu.com/', headers=self.headers)
        bdstoken = re.findall(
            r'initPrefetch\(\'(.+?)\'\,', response.content.decode("utf-8"))[0]
        url = 'https://pan.baidu.com/api/filemanager?bdstoken=%s&opera=move&async=2&onnest=fail&channel=chunlei&web=1&app_id=250528\
                &logid=MTU4MTk0MzY0MTQwNzAuNDA0MzQxOTM0MzE2MzM4Ng==&clienttype=0' % bdstoken
        if(not newname):
            newname = path.split('/')[-1]
        form_data = {"filelist": "[{\"path\":\"%s\",\"dest\":\"%s\",\"newname\":\"%s\"}]" % (
            path, destination, newname)}
        response = self.session.post(url, headers=self.headers, data=form_data)
        if(response.json()['errno'] == 0):
            return {'errno': 0, 'err_msg': '移动成功！'}
        else:
            return {'errno': 1, 'err_msg': '移动失败！', 'info': response.json()}

    '''
    随机生成4位字符串
    '''
    @staticmethod
    def generatePwd(n=4):
        pwd = ""
        for i in range(n):
            temp = random.randrange(0, 3)
            if temp == 0:
                ch = chr(random.randrange(ord('A'), ord('Z') + 1))
                pwd += ch
            elif temp == 1:
                ch = chr(random.randrange(ord('a'), ord('z') + 1))
                pwd += ch
            else:
                pwd = str((random.randrange(0, 10)))
        return pwd

    '''
    创建分享链接
    fid_list为列表，例如：[1110768251780445]
    0 创建成功；1 创建失败；
    '''

    def createShareLink(self, fid_list, period=0, pwd=False):
        '''
        构造重命名的URL：https://pan.baidu.com/share/set?
        bdstoken=  从首页可以获取到
        &channel=chunlei  固定在
        &web=1  固定值
        &app_id=250528  固定值
        &logid=MTU4MTk0MzY0MTQwNzAuNDA0MzQxOTM0MzE2MzM4Ng==  固定值
        &clienttype=0  固定值
        '''
        response = self.session.get(
            'https://pan.baidu.com/', headers=self.headers)
        bdstoken = re.findall(
            r'initPrefetch\(\'(.+?)\'\,', response.content.decode("utf-8"))[0]
        url = 'https://pan.baidu.com/share/set?bdstoken=%s&channel=chunlei&web=1&app_id=250528\
                &logid=MTU4MTk0MzY0MTQwNzAuNDA0MzQxOTM0MzE2MzM4Ng==&clienttype=0' % bdstoken
        if(not pwd):
            pwd = self.generatePwd()
        '''
        schannel=4  不知道什么意思，固定为4
        channel_list=[]  不知道什么意思，固定为[]
        period=0  0表示永久，7表示7天
        pwd=w4y5  分享链接的提取码，可自定义
        fid_list=[1110768251780445]  分享文件的id列表，可调用getFileList方法获取文件列表，包含fs_id
        '''
        form_data = {
            'schannel': 4,
            'channel_list': '[]',
            'period': period,
            'pwd': pwd,
            'fid_list': str(fid_list),
        }
        response = self.session.post(url, headers=self.headers, data=form_data)
        if(response.json()['errno'] == 0):
            return {'errno': 0, 'err_msg': '创建分享链接成功！', 'info': {'link': response.json()['link'], 'pwd': pwd}}
        else:
            return {'errno': 1, 'err_msg': '创建分享链接失败！', 'info': response.json()}

test_cookie= '''BAIDUID=B8CE8F13323648199D15E1AADC87FAA8:FG=1; H_WISE_SIDS=148077_149390_150185_109775_142019_149355_150074_147091_141748_150087_148193_148866_147685_148714_148434_147279_150041_149531_149540_150154_148439_148754_147890_146575_148523_147347_127969_148794_147351_149718_150345_146734_138425_149558_145996_131423_100806_132550_149008_147527_145596_107319_147137_148186_147717_149251_150399_146396_144966_149279_145608_148049_148424_148751_147547_146053_148868_110085; STOKEN=bf8f78c0dad90a7e27fa743b0a03f1215db1639a5a31f1327cd0c62f75fd63dd; SCRC=f91991f1a9072fe77af33e32ceb001fa; cflag=13%3A3; ZD_ENTRY=google; BDCLND=oMkK%2Fo1NQiQVqASoeRiTd5QtpcHY9Y%2BA; Hm_lvt_7a3960b6f067eb0085b7f96ff5e660b0=1595237581,1595237700,1595238519,1595240321; Hm_lpvt_7a3960b6f067eb0085b7f96ff5e660b0=1595256261; PANPSC=5142017323306576694%3ACU2JWesajwA9L7226RJlszuv496EomYGrFsbUd3ehrTPzW21GgvS0MKFw3Ww%2Fpq%2Bmn%2BJhdPwvbnjBmRBn1u2%2F22n7K8%2B7H%2FNiVleys3zxXZFah9uWgECZxt0GEZyVdQnrWefqB28LP2i%2BY1X7udr9G2gud9gLjYtRogbeq4A%2FVImU589kUerfkfbyt4Ev2n6fPVXoOSO8Qs7qAHgpfUwRg%3D%3D; PSTM=1568516374; BIDUPSID=0014E097ED6A42C05BC6DCD6D65D2D3E; BDUSS=cxbGpwLWVhaDVxT0p-QXlhbENhT2NaZWdpNlV0Snk5fnNzMEE2WnJWNC1xVzllRVFBQUFBJCQAAAAAAAAAAAEAAAAPDOwAR29sZGlvcmwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD4cSF4-HEheVU; PANWEB=1;'''

root.mainloop()
