# coding=utf-8
import session
import os
import Global_Variables
import jieba
import multiprocessing

jieba.load_userdict('user_dic.txt')
"""
----------handle_scipt.py-------------
             记录整个剧本信息
"""
if not os.path.exists('out'):
    os.mkdir('out')


class shunjingbiao:
    '''存储顺景表信息的类'''

    def __init__(self, script_id=-1, script_num=-1, script_content='', main_content="", time='', role=[]):
        self.script_id = script_id
        self.script_num = script_num
        self.script_content = script_content
        self.main_content = main_content
        self.time = time
        self.role = role
        self.pagenum = float(len(self.script_content.split('\n'))) / 50.0


class Script:
    '''
    记录整个剧本的信息，包含多个场景（session）的类的实例
    '''

    def __init__(self, filename):
    

        self.script_name = ''
        self.save_path = ""
        self.session_list = []  # 存放所有场次信息的list
        self.charactor_overrall_word_count_dic = {}  # 角色台词数
        self.charactor_overral_apear_in_session = {}  # 角色出现场次数
        self.charactor_emetion_word_in_session = {}  # 角色情感词
        self.filename=filename
        self.shunjingbiao = {}
        self.shunchangbiao = {}
        self.all_ad_count = []
        self.session_ad_count = []
        self.all_sensitive_word_count_dic = {}
        self.charactor = Global_Variables.name_list
        # for i in Global_Variables.name_list:
        #     self.charactor_overrall_word_count_dic[i] = 0
        self.all_charactor_count = {}

    def cal_all_info(self):
        print('读取剧本')
        self.file_text = self.read_script_file(self.filename)
        Global_Variables.name_list = []
        print('程序推测主角')
        self.find_main_charactor(self.file_text)
        main_role = ''
        for name in Global_Variables.name_list:
            main_role += name + ","
        main_role = main_role[:-1]
        print('推测主角为' + main_role)
        print('处理场次信息')
        self.handle_session(self.file_text)
        print('统计角色台词数')
        self.cal_overrall_count()
        print('计算非主角出场次数')
        self.cal_all_character()
        print('计算主要角色出场次数')
        self.cal_character_apear_count()
        print("计算敏感词信息")
        self.cal_all_senstive_word_count()
        print("计算广告信息")
        self.session_ad_count = self.cal_ad_words_count()

    def write_info(self):
        self.write_script_detail()
        self.write_script_role()
        self.write_session_role_word()
        self.write_participle()
        self.write_session_ad_args()
        self.wrtie_script_sensitive_args()

    def test_muiltiprocess(self):
        self.cal_all_info()
        self.write_info()

    def find_main_charactor(self, file_text, mode=1):
        """
        两种剧本模式的推测主角方法不一
        1、简版剧本使用统计剧本中说话的频次数（即xxx说中的xxx出现次数的排序，前五个即为主角）
        2、标准版剧本使用一个开源大规模预料分析的额库，可以猜测没有在词库的情况下推测词（在剧本中，主角们被提到的次数通常是最多的，所以可以用来推测主角）
        但在推测主角过程中，如果跟人物小传中所记录的内容不一样（比如万人膜拜这个剧本人物小传和剧本中姓名并不对应）会导致统计出来的结果出现问题
        所以暂时没有启用这个推测功能（人物小传中应到加入一个别名，在别名内所有的称呼、昵称都应为这个角色，功能未做）
        """
        if mode == 0:
            a = 1
            # result = hibiscusMain.Hibiscus().analyseNovel(self.file_text)
            # for c in result:
            #     Global_Variables.name_list.append(c)
        elif mode == 1:
            user_dic = {}
            session_list = file_text.split('\n\n')
            for session in session_list:
                session = session.split('\n')
                for line in session:
                    line = line.replace('：', ":").replace(' ', '').replace('\n', '').replace('\ufeff', '')
                    if ':' in line:
                        if mode == 1:
                            charactor = line.split(':')[0]
                            user_dic.setdefault(charactor, 0)
                            user_dic[charactor] += 1
                        elif mode == 0:
                            info_list = Global_Variables.session_info_title
                            info_list.extend(Global_Variables.character_biographies)
                            if line.split(':')[0] in info_list:
                                continue
                            else:
                                charactor = line.split(':')[0]
                                user_dic.setdefault(charactor, 0)
                                user_dic[charactor] += 1
                                # elif mode==0:
                                #
            user_dic = sorted(user_dic.items(), key=lambda x: x[1], reverse=True)
            # print(user_dic)
            Global_Variables.name_list = []
            character_range = 5
            for i in range(0, character_range):
                Global_Variables.name_list.append(user_dic[i][0])
                # print(Global_Variables.name_list)

        for word in Global_Variables.name_list:
            jieba.add_word(word, 10000)

    # def read_script_file(self, filename):
    #     """
    #     读取剧本，并处理剧本名字（剧本名字是带有剧本名字+时间戳的）转化为 script类的script_name
    #     :param filename: 上传的剧本的路径
    #     :return: 读取的剧本文本内容
    #     """
    #     name = os.path.splitext(filename)[0]
    #     self.script_name = name.split('\\')[len(name.split('\\')) - 1]
    #     script = ""
    #     self.save_path += self.script_name + "\\"
    #     if not os.path.exists(self.save_path):
    #         os.mkdir(self.save_path)
    #     # script=open(filename,encoding='utf-8').read()
    #     document = Document(filename)
    #     for para in document.paragraphs:
    #         script += para.text + '\n'
    #     # print(script)
    #     return script
    def read_script_file(self, filename):
        """
        读取剧本，并处理剧本名字（剧本名字是带有剧本名字+时间戳的）转化为 script 类的 script_name
        :param filename: 上传的剧本的路径
        :return: 读取的剧本文本内容
        """
        name = os.path.splitext(filename)[0]
        self.script_name = name.split('\\')[-1]  # 获取文件名部分作为剧本名
        script = ""
        self.save_path += self.script_name + "\\"
        if not os.path.exists(self.save_path):
            os.mkdir(self.save_path)
        
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                script += line.strip() + '\n'  # 读取每一行并添加到剧本文本中
        
        return script

    def handle_session(self, script):
        count = 0
        split_script = script.split('\n\n')  # 以双回车判断是否为一个场
        for s in split_script:
            if (len(s) <= 7):
                continue
            ss = session.Session(s)
            self.session_list.append(ss)
            count += 1
            # ss.show_info()
            if count % 20 == 0:
                print('已处理' + str(count) + '场')

    def cal_overrall_count(self):
        """
        统计每个角色的台词数
        """
        for session in self.session_list:
            for keys, session_charactor_info in session.session_charactor_dic.items():
                self.charactor_overrall_word_count_dic.setdefault(keys,0)
                self.charactor_overrall_word_count_dic[keys] += session_charactor_info.charactor_world_amount

    def cal_all_character(self):
        """
        计算角色（包含非主要角色）出场次数
        """
        for session in self.session_list:
            for name in session.session_all_charactor_set:
                self.all_charactor_count.setdefault(name, 0)
                self.all_charactor_count[name] += 1

        '''输出所有角色出现次数的排序（未分词）到屏幕，可以发现主要人物'''
        # print(sorted(self.all_charactor_count.items(), key=lambda x: x[1], reverse=True))

    def cal_character_apear_count(self):
        """
        计算主要角色的出场次数
        """
        for session in self.session_list:
            for name, apear in session.session_charactor_dic.items():
                self.charactor_overral_apear_in_session.setdefault(name, 0)
                if apear.appearance:
                    self.charactor_overral_apear_in_session[name] += 1
                    # print(self.charactor_overral_apear_in_session)

    def cal_ad_words_count(self):
        """
        统计广告词广告词
        return:返回（场次编号、广告词、广告词计数）
        """
        args = []
        self.all_ad_count = {}  # 先转换为字典方便存储
        for session in self.session_list:
            for word, count in session.session_ad_word_count_dic.items():
                args.append((session.session_number, word, count))
                self.all_ad_count.setdefault(word, 0)
                self.all_ad_count[word] += 1
        self.all_ad_count = sorted(self.all_ad_count.items(), key=lambda x: x[1], reverse=True)
        # for i in self.all_ad_count:
        #     print(i)
        # print(args)
        return args

    def cal_all_senstive_word_count(self):
        for session in self.session_list:
            for key, word_count in session.session_sensitive_word_count_dic.items():
                self.all_sensitive_word_count_dic.setdefault(key, 0)
                self.all_sensitive_word_count_dic[key] += word_count

    def write_script_detail(self):
        '''输出剧本场景详情'''
        script_detail_args = ""
        for session in self.session_list:
            '''此处变量名与数据库中字段名对应，方便使用'''
            script_number = session.session_number
            content = session.session_content
            role = ""
            role_number = 0
            for character in session.session_charactor_dic.values():
                if character.appearance:
                    role_number += 1
                    role += character.name + '|'
            role = role[:-1]
            if len(session.session_time) > 0:
                if session.session_time not in Global_Variables.time:
                    Global_Variables.time.append(session.session_time)
                period = session.session_time
            else:
                period = 0
            scene = session.session_location
            if len(session.session_place) > 0:
                if session.session_place not in Global_Variables.place:
                    Global_Variables.place.append(session.session_place)
                surroundings = session.session_place
            else:
                surroundings = 0
            # role_number = len(session.session_all_charactor_set)
            script_detail_args += str(script_number) + '\t' + str(period) + '\t' + str(scene) + '\t' + str(
                surroundings) + '\t' + role + '\t' + str(role_number) + '\t' + session.session_main_content + '\n'
        # for i in script_detail_args:
        #     print(i)
        return script_detail_args

    def write_script_role(self):
        '''输出剧本角色信息'''
        script_roles = ""
        for role_name, word_count in self.charactor_overrall_word_count_dic.items():
            # print(role_name,self.charactor_overral_apear_in_session[role_name],word_count)
            script_roles += role_name + '\t' + str(word_count) + '\t' + str(
                self.charactor_overral_apear_in_session[role_name]) + '\n'
        f = open(self.save_path + '角色信息.txt', 'w', encoding="utf8")
        f.write(script_roles)
        f.close()

    def write_session_role_word(self):
        '''输出剧本角色情感词'''
        args = ""
        for session in self.session_list:
            self.charactor_emetion_word_in_session.setdefault(session.session_number, [])
            for Charactor in session.session_charactor_dic.values():
                self.charactor_emetion_word_in_session[session.session_number].append(Charactor)
                # print(self.charactor_emetion_word_in_session)
                for key, value in Charactor.charactor_emotion_dic.items():
                    for word in value:
                        args += key + '\t' + word + '\t' + Charactor.name + '\t' + str(session.session_number) + '\n'
        # print(args)
        return args

    def write_participle(self):
        '''输出情感词分词内容'''
        participle_args = ""
        word_dic = {}
        for session in self.session_list:
            for type, word_list in session.session_emotion_words_dic.items():
                for word in word_list:
                    word_dic.setdefault((word, session.session_number, type), 0)
                    word_dic[(word, session.session_number, type)] += 1
        for word_item, count in word_dic.items():
            participle_args += str(word_item[0]) + '\t' + str(word_item[1]) + '\t' + str(word_item[2]) + '\t' + str(
                count) + '\n'
        for i in participle_args:
            print(i)
        return participle_args

    def write_session_ad_args(self):
        """输出剧本广告词信息"""
        args = ""
        for info in self.session_ad_count:
            args += str(info[0]) + '\t' + str(info[1]) + '\t' + str(info[2]) + '\n'
        return args

    def wrtie_script_sensitive_args(self):
        """输出剧本敏感词信息"""
        args = ""
        sensitive_word_sort = sorted(self.all_sensitive_word_count_dic.items(), key=lambda x: x[1], reverse=True)
        for word, count in sensitive_word_sort:
            args += word + '\t' + str(count) + '\n'
        return args

    def showinfo(self, show_session_detail=0, show_line_detail=0):
        for k, v in self.charactor_overrall_word_count_dic.items():
            print(k + str(v))
        if show_session_detail == 1:
            for i in self.session_list:
                i.show_info(show_line_detail=show_line_detail)


if __name__ == "__main__":
    script = Script('泰坦尼克号.txt')
    p1=multiprocessing.Process(target=script.test_muiltiprocess)
    p1.start()

