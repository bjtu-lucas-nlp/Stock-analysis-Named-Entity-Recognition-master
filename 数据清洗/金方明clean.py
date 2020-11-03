# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 10:21:25 2020

@author: Mency
"""

import re
import sys
import pandas as pd
import os
from pathlib import Path
from pyltp import SentenceSplitter
from pyltp import Segmentor
from pyltp import Postagger
from pyltp import NamedEntityRecognizer
import fool
import datetime
import requests
import csv
import numpy as np
import collections
import math
import time
import logging
import logging
import signal

def fool_ner(text):  # 识别机构名-foolnltk 返回公司名列表
    words, ners = fool.analysis(text)
    company = []
    for ner_list in ners:
        for tups in ner_list:
            if tups[2] == 'company':
                temp = re.sub(' ', '', tups[3])
                company.append(temp)
    company = list(set(company))
    return company

def pyltp_ner(text, segmentor, postagger, recognizer):  # 识别机构名-pyltp
    words = segmentor.segment(text)
    words_list = list(words)
    postags = postagger.postag(words)
    postags_list = list(postags)
    netags = recognizer.recognize(words, postags)
    netags_list = list(netags)

    # 去除非命名实体
    a = len(words_list)
    words_list_1 = []
    postags_list_1 = []
    netags_list_1 = []
    for i in range(a):
        if netags_list[i] != 'O':
            words_list_1.append(words_list[i])
            postags_list_1.append(postags_list[i])
            netags_list_1.append(netags_list[i])

    # 提取机构名
    a1 = len(words_list_1)
    organizations = []
    for i in range(a1):
        if netags_list_1[i] == 'S-Ni':
            organizations.append(words_list_1[i])
        elif netags_list_1[i] == 'B-Ni':
            temp_s = ""
            temp_s += words_list_1[i]
            j = i + 1
            while j < a1 and (netags_list_1[j] == 'I-Ni' or netags_list_1[j] == 'E-Ni'):
                temp_s += words_list_1[j]
                j = j + 1
            organizations.append(temp_s)
    organizations = list(set(organizations))  # 对公司名去重
    return organizations

def get_citys(text, segmentor, postagger, recognizer):  # 分词、词性标注，用于地名识别

    words = segmentor.segment(text)
    words_list = list(words)

    # 词性标注
    postags = postagger.postag(words)
    postags_list = list(postags)

    return words_list, postags_list

def text_city(text, city_names, segmentor, postagger, recognizer):
    pro_city = {}
    address_item=[]
    words_list, postags_list = get_citys(text, segmentor, postagger, recognizer)
    for i in range(len(words_list)):
        if postags_list[i] == "ns":
            address_item.append(words_list[i])
    address_item = [i.replace("省", "").replace("市", "") for i in address_item]  # 先去除地名中的“省”和"市"
    address_item = list(set(address_item))
    if len(address_item) == 0:
        return {}
    else:
        return address_item

def find_lcsubstr(s1, s2):  #获取最长公共子串
    m=[[0 for i in range(len(s2)+1)] for j in range(len(s1)+1)] #生成0矩阵，为方便后续计算，比字符串长度多了一列
    mmax=0  #最长匹配的长度
    p=0 #最长匹配对应在s1中的最后一位
    for i in range(len(s1)):
        for j in range(len(s2)):
            if s1[i]==s2[j]:
                m[i+1][j+1]=m[i][j]+1
            if m[i+1][j+1]>mmax:
                mmax=m[i+1][j+1]
                p=i+1
    return s1[p-mmax:p]  #返回最长子串及其长度

'''
translate chinese_money to float type, the maximum number  is "万亿"
amount: str of chinese_money
return:
	amount_float： float, translated chinese_money
'''
def aoligeiganle(amount):
    chinese_num = {'零': 0, '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6,'柒': 7, '捌': 8, '玖': 9,'拾': 10}
    chinese_amount = {'分': 0.01, '角': 0.1, '元': 1, '圆': 1, '拾': 10, '佰': 100,'仟': 1000}
    amount_float = 0
    if '亿' in amount:
        yi = re.match(r'(.+)亿.*', amount).group(1) #获取亿部分的大写金额
        amount_yi = 0
        for i in chinese_amount: #对每个单位，从小到大计算 
            if i in yi: 
                # 取单位前面的数字乘上单位
                amount_yi += chinese_num[yi[yi.index(i) - 1]] * chinese_amount[i]
        if yi[-1] in chinese_num.keys(): #计算“亿”前面的数字
            amount_yi += chinese_num[yi[-1]]
        amount_float += amount_yi * 100000000
        amount = re.sub(r'.+亿', '', amount, count=1)
    if '万' in amount: #同上处理思路 
        wan = re.match(r'(.+)万.*', amount).group(1)
        amount_wan = 0
        for i in chinese_amount:
            if i in wan:
                amount_wan += chinese_num[wan[wan.index(i) - 1]] * chinese_amount[i]
        if wan[-1] in chinese_num.keys():
            amount_wan += chinese_num[wan[-1]]
        amount_float += amount_wan * 10000
        amount = re.sub(r'.+万', '', amount, count=1)

    amount_yuan = 0
    for i in chinese_amount: #“千”以内的金额转换
        if i in amount:
            if amount[amount.index(i) - 1] in chinese_num.keys():
                amount_yuan += chinese_num[amount[amount.index(i) - 1]] * chinese_amount[i]
    amount_float += amount_yuan

    return amount_float

"""
clean the money result
ids: list, id of html data
money: list, result of extracted money info
return:
	money: list, cleaned money result
"""
def process_money(ids,money):
    for i in range(len(money)):
        m = money[i]
        #去除无关字符，只留下数字和大写金额
        new_m = re.sub("[^0-9壹贰叁肆伍陆柒捌玖零拾佰仟万亿圆元.]","",m) 
        m = new_m
        if m.startswith("万元"): #去掉以单位开头
            m = m[2:]
        elif m.startswith("元"): 
            m = m[1:]
        
        num_yuan = re.search("([0-9.]+)元",m) #数字+元
        num_wanyuan = re.search("([0-9.]+)(万元|万)",m) #数字+万元
        num_digital = re.search("[^0-9.]",m) #非数字部分
        num_capitals = re.search("[壹贰叁肆伍陆柒捌玖零拾佰仟万亿圆元]+",m) #大写金额
        if num_yuan != None and len(num_yuan.groups()[0])>0 : #以元结尾，只取数字
            number = num_yuan.groups()[0]
            m = number
        elif num_wanyuan != None and len(num_wanyuan.groups()[0])>0 : #以万元结尾，只取数字并乘上万
            try:
                number = float(num_wanyuan.groups()[0]) * 10000.00
                m = number
            except:
                print("error wanyuan ",num_wanyuan,num_wanyuan.groups()[0])
        elif num_digital == None: #只有数字，保留数字
            m = m
        elif num_capitals != None and len(num_capitals.group())>0: #有大写数字的部分，转换
            capitals = num_capitals.group()
            try:
                new_m = aoligeiganle(capitals)
                m = new_m
            except Exception as e:
                print("error m2 ",num_capitals,m,ids[i],capitals,e)
        else:
            print("other money type:",m,"in data of",ids[i])
        try:
            money[i] = float(m)
        except:
            money[i] = m
    return money

def text_split(text):  # 命名体分割,输出字符串
    delimiter = re.search(r"(司|局|院|中心|学|会|室|校|所|队|馆|厅|部|处|台|行|团|区|站|海关|厂|狱|园|社|场|署|庭|军|科|墓|港|组)(\((.*?)\))?( |、|，|,|；|;|和|与|或|#|\\|\||&|\+|/|(([\(（])(主|成|牵头|成员)(办)?(人|方|单位)?([0-9])?([\)）])))( |、|，|,|；|;|和|与|或|#|\\|\||&|\+|/)?", text)
    if delimiter:
        delimiter_c = [e.end() - 1 for e in re.finditer(r"(司|局|院|中心|学|会|室|校|所|队|馆|厅|部|处|台|行|团|区|站|海关|厂|狱|园|社|场|署|庭|军|科|墓|港|组)(\((.*?)\))?( |、|，|,|；|;|和|与|或|#|\\|\||&|\+|/|(([\(（])(主|成|牵头|成员)(办)?(人|方|单位)?([0-9])?([\)）])))( |、|，|,|；|;|和|与|或|#|\\|\||&|\+|/)?", text)]
        print(delimiter_c)
        str = [text[:delimiter_c[0]]]
        for j in range(len(delimiter_c) - 1):
            start = delimiter_c[j] + 1
            end = delimiter_c[j + 1]
            str = str + [text[start:end]]
        str = str + [text[delimiter_c[-1] + 1:]]
        text = str
    else:
        text = [text]
    return text

def text_clean_unreadable(text):
    # 清洗乱码字符及空格
    start_clean = [e for e in re.finditer(r"([^\s@a-zA-Z0-9<>「」,，、\.。:：;；/\\'\"\?？!！”’~～`·|\-\]】}\*&\^%$#]+)(司|局|院|中心|学|会|室|校|所|队|馆|厅|部|处|台|行|团|区|站|海关|厂|狱|园|社|场|署|庭|军|科|墓|港|组)([^\s@a-zA-Z0-9<>「」,，、\.。:：;；/\\'\"\?？!！”’~～`·|\-\]】}\*&\^%$#]+)?",text)][-1]
    if start_clean:
        start_text = start_clean.start()
        end_text = start_clean.end()
        text = text[start_text:end_text]
    else:
        text = ''
    end_clean = [i.end() for i in re.finditer(r'(司|局|院|中心|学|会|室|校|所|队|馆|厅|部|处|台|行|团|区|站|海关|厂|狱|园|社|场|署|庭|军|科|墓|港|组)',text)][-1]
    text = text[:end_clean]
    return text

def text_bracket(text, city_names, segmentor, postagger, recognizer):  # 删除括号内的内容
    text = re.sub(r'((^[^\[\]{}【】]*?)[\]}】])|([\[{【]([^\[\]{}【】]*?)$)', '', text)
    text = re.sub(u"\\[.*?\\]|\\{.*?}|【.*?】", "", text)
    # 分析(（类括号内内容
    text = re.sub(r'（', '(', text)
    text = re.sub(r'）', ')', text)
    # 对括号进行匹配（经修改后能解决嵌套括号问题，用正则则难以避免）
    left_bracket = [e.start() for e in re.finditer(r'\(', text)]
    left_bracket.sort(reverse=True)
    right_bracket = [e.start() for e in re.finditer(r'\)', text)]
    bracket_pair = []
    for l in left_bracket:
        right_pair = [r for r in right_bracket if r > l]
        if right_pair != []:
            r = right_pair[0]
            bracket_pair.append([l, r + 1])
            right_bracket.remove(r)
        else:
            bracket_pair.append([l, len(text) + 1])
    for r in right_bracket:
        bracket_pair.append([0, r + 1])
    bracket_pair.sort(key=lambda i: (i[1] - i[0]), reverse=True)
    # 分析括号内内容
    text_del = []
    for pair in bracket_pair:
        contain = text[pair[0]:pair[1]]
        contain_s = contain.strip('(').strip(')')
        contain_s = re.sub(r'([\(（]([^\(\)（）]*?)$)|(\(.*?\))', '', contain_s)
        if re.search("(司|局|院|中心|学|会|室|校|所|队|馆|厅|部|处|台|行|团|区|站|海关|厂|狱|园|社|场|署|庭|军|科|墓|港|组)$", contain_s) and len(contain_s) >= 6:
            test_start = [e.end() for e in
                          re.finditer(r'(司|局|院|中心|学|会|室|校|所|队|馆|厅|部|处|台|行|团|区|站|海关|厂|狱|园|社|场|署|庭|军|科|墓|港|组)( |、|，|,|；|;|和|与|或|#|\\|\||&|\+|/)', text[:pair[0]])]
            if test_start != []:
                test = text[test_start[-1]:pair[0]]
            else:
                test = text[:pair[0]]
            test = re.sub(r'([\(（]([^\(\)（）]*?)$)|(\(.*?\))', '', test)
            if re.search("(司|局|院|中心|学|会|室|校|所|队|馆|厅|部|处|台|行|团|区|站|海关|厂|狱|园|社|场|署|庭|军|科|墓|港|组)$", test) and len(test) >= 6:
                text_del.append(pair)
            else:
                if test_start != []:
                    text_del.append([test_start[-1], pair[0]])
                else:
                    text_del.append([0, pair[0]])
                if contain.endswith(')'):
                    text_del.append([pair[1] - 1, pair[1]])
                if contain.startswith('('):
                    text_del.append([pair[0], pair[0] + 1])
        elif text_city(contain, city_names, segmentor, postagger, recognizer) == {} and not contain.count(
                '中国') and not contain.count('集团'):
            text_del.append(pair)
    if len(text_del) > 0:
        text_del_r = []
        for del_item in text_del:
            if len([i for i in text_del if del_item[0] >= i[0] and del_item[1] <= i[1]]) > 1:
                text_del_r.append(del_item)
        text_del = [i for i in text_del if i not in text_del_r]
        text_del.sort(key=lambda i: i[0])
        text_left = text[:text_del[0][0]]
        for index in range(len(text_del) - 1):
            text_left = text_left + text[text_del[index][1]:text_del[index + 1][0]]
        text_left = text_left + text[text_del[-1][1]:]
        return text_left
    else:
        return text

def query_search(name):#模糊查询
    url = 'https://api.yonyoucloud.com/apis/yonyoucloudresearch/enterprise/search'
    headers = {'apicode': "a710d1280d4048c193638e09c49d3542"}
    params={"word":name,"size":"5","pageNum":'1'}
    try:
        res = requests.get(url,params,headers=headers)
        result= res.json()
        name = result['result']["items"]
    except:
        return []
    return name
"""
clean the supplier result 
ids: list, id of html data
supplier: list, result of extracted supplier info
return:
	supplier: list, cleaned supplier result
"""

def process_supplier(ids,supplier,city_names, segmentor, postagger, recognizer):
    company_key = {}
    for i in range(len(supplier)):
        s = supplier[i]
        originalS = s
        print(1,s)
        #对过长文本，认为可能有多个候选供应商导致，选取第一个供应商
        if len(s) > 50:
            if re.search(r'([\(（][A-Z](包)?[\)）])|([A-Z](包))', s):
                kind_bao = list(
                    set([s[bao.start():bao.end()] for bao in re.finditer(r'(\([A-Z](包)?\))|([A-Z](包))', s)]))
                place = []
                for bao in kind_bao:
                    first_place = s.index(bao)
                    place.append(first_place)
                place.sort()
                split_s = [s[place[n]:place[n + 1]] for n in range(len(place) - 1)] + [s[place[-1]:]]
                s_lists = []
                for part_s in split_s:
                    match_supplier = "([\(（][A-Z]包?[\)）])?([A-Z]包)?(（\S+）)?(供应商|人" \
                                     "|单位|候选人|结果|包|名|标段)?(名单|名称|信息)?(为|是)?[1-9]?(：|:|为|是|名称)?(#)*" \
                                     "([^\s，；：。标0-9A-Za-z]+)(公司|经销部|供销社|合作社|联合社|联合会|直营部|经营部|批发部)"
                    match_re = re.search(match_supplier, part_s)
                    if match_re != None:
                        news = match_re.groups()[-2] + match_re.groups()[-1]
                        s_lists.append(news)
                s = ';'.join(s_lists)
            else:
                match_supplier = "(中标|中选|成交|候选|入围|一|二|三|四|五|六|七|八|九|十)(（\S+）)?(供应商|人" \
                                 "|单位|候选人|结果|包|名|标段)(名称|信息)?(为|是)?[1-9]?(：|:|为|是|名称)?(#)*" \
                                 "([^\s，；：。标0-9]+)(公司|经销部|供销社|合作社|联合社|联合会|直营部|经营部|批发部)"
                match_re = re.search(match_supplier, s)
                if match_re != None:
                    news = match_re.groups()[-2] + match_re.groups()[-1]
                    s = news  # 更新清洗后的数据
        print(2,s)
        #处理并列中标（公司之间没有分割符，但是有其他提示词
        if re.search(r'([\(（])(主|成|牵头|成员)(办)?(人|方|单位)?([0-9])?([\)）])', s):
            s = text_split(s)
            text_final = []
            for ss in s:
                text_del = text_bracket(ss, city_names, segmentor, postagger, recognizer)
                cut_index = []
                if len(text_del) > 15:
                    tf = [[e.start(), e.end()] for e in
                          re.finditer(
                              r"(局|公司|院|中心|大学|协会|代表大会|委员会|集团|委会|学会|联合会|工会|分会|总会|红十字会|所|部|银行|总行|支行|厂|供销社|合作社|联合社|校)",
                              text_del)]
                    for ee in range(len(tf) - 1):
                        text_tf0 = text_del[tf[ee][0]:tf[ee][1]]
                        text_tf1 = text_del[tf[ee][1]:tf[ee + 1][1]]
                        tf2 = len(re.sub(
                            r'(县|市|区|省|一|二|三|四|五|六|七|八|九|十|第|科技|股份|技术|有限|项目|公司|研究|测绘|集团|总|分|子|设计|工程|勘察|直营|经营|批发|局|院|中心|大学|协会|代表大会|委员会|委会|学会|联合会|工会|分会|总会|红十字会|所|部|银行|总行|支行|分行|厂|供销社|合作社|联合社|校|建筑|规划|软件)',
                            '', text_tf1))
                        if re.search(r'公司|集团', text_tf1):
                            if re.search(
                                    r'局|院|中心|大学|协会|代表大会|委员会|委会|学会|联合会|工会|分会|总会|红十字会|所|部|银行|总行|支行|分行|厂|供销社|合作社|联合社|校',
                                    text_tf0) and tf2 >= 4 and len(text_tf1) >= 8:
                                cut_index.append(tf[ee][1])
                            elif text_tf1[-1] == text_tf0[-1] and not re.search(r'分公司|子公司', text_tf1):
                                cut_index.append(tf[ee][1])
                            elif re.search(r'集团', text_tf1) and re.search(r'公司', text_tf0):
                                cut_index.append(tf[ee][1])
                        elif re.search(r'大学|校', text_tf1):
                            if not re.search(r'分校', text_tf1) and tf2 >= 2:
                                cut_index.append(tf[ee][1])
                        elif re.search(r'局|院|所|中心', text_tf1):
                            if not re.search(r'(局|院|所|部|中心|集团|大学)', text_tf0) and tf2 >= 2:
                                cut_index.append(tf[ee][1])
                            elif text_tf1[-1] == text_tf0[-1] and not re.search(r'分|子|支', text_tf1[-1]):
                                cut_index.append(tf[ee][1])
                        elif re.search(r'部', text_tf1):
                            if re.search(r'大学|中心|协会|代表大会|委员会|委会|学会|联合会|工会|分会|总会|红十字会|公司|厂|供销社|合作社|联合社|银行|总行|支行|分行|集团',
                                         text_tf0) and tf2 >= 3:
                                cut_index.append(tf[ee][1])
                            elif text_tf1[-1] == '部' and not re.search(r'分|子|支', text_tf1[-1]):
                                cut_index.append(tf[ee][1])
                        elif re.search(r'(厂|供销社|合作社|联合社|协会|代表大会|委员会|委会|学会|联合会|工会|分会|总会|红十字会)', text_tf1) and tf2 >= 6:
                            if not re.search(r'分会', text_tf1) and tf2 >= 4:
                                cut_index.append(tf[ee][1])
                            elif text_tf1[-1] == text_tf0[-1] and not re.search(r'分|子|支', text_tf1[-1]):
                                cut_index.append(tf[ee][1])
                        elif re.search(r'银行|总行|支行|分行', text_tf1):
                            if re.search(r'银行|总行', text_tf1) and tf2 >= 2:
                                cut_index.append(tf[ee][1])
                            elif re.search(r'分行|支行', text_tf1) and text_tf1[-1] == text_tf0[-1]:
                                cut_index.append(tf[ee][1])

                if len(cut_index) > 0:
                    cut_text = [text_del[:cut_index[0]]] + [text_del[cut_index[ee]:cut_index[ee + 1]] for ee in
                                                            range(len(cut_index) - 1)] + [text_del[cut_index[-1]:]]
                else:
                    cut_text = [text_del]
                text_final = text_final + cut_text

            new_text_final = []
            for ss in text_final:
                if re.search(r"[^\s@a-zA-Z0-9<>「」,，、\.。:：;；/\\'\"\?？!！”’~～`·|\-\]】}\*&\^%$#]", ss):
                    ss = text_clean_unreadable(ss)
                    new_text_final.append(ss)
            text_final = new_text_final
            s = ';'.join(text_final)
        print(4,s)

        hasNumber = re.search("[0-9]",s) #一般有数字就说明有混杂数据
        #是否有分隔符和连接符。如果要保留联合体、牵头人等则加在这里
        multcomp = re.findall(r"[^分子](公司|经销部|供销社|合作社|联合社|联合会|直营部|经营部|批发部)",s)
        hasDeli = re.search(r"(公司|经销部|供销社|合作社|联合社|联合会|直营部|经营部|批发部)( |、|，|,|；|;|和|与|或|#|\\|\||&|\+|/)",s)
        #超过一定长度而且没有分隔符（说明不是并列中标） 或 存在数字（候选供应商）
        if (len(multcomp) > 1 and hasDeli ==None) or hasNumber!=None: #非并列中标则选取第一个供应商
            start_re = re.search("([^\s、：:0-9a-z]+)(公司|子公司|分公司|经销部|供销社|合作社|联合社|联合会|直营部|经营部|批发部)", s)
            end_re = re.search("公司|子公司|分公司|经销部|供销社|合作社|联合社|联合会|直营部|经营部|批发部", s)
            start_pos = start_re.start()
            end_pos = end_re.end()
            news = s[start_pos:end_pos]
            if news != s:
                s = news
        #计数供应商的数量
        countKeyw = re.findall("公司|经销部|供销社|合作社|联合社|联合会|直营部|经营部|批发部",s)
        if len(countKeyw) == 1: #对单个公司清洗无关字符，最后得到的结果只包含公司名称
            hasName = re.search("名称|是",s)
            if hasName != None:
                search_re = re.search("(是|名称)(:|：)?#*([\w（）()-]+)(公司|经销部|供销社|合作社|联合社|联合会|直营部|经营部|批发部)",s)
            else:
                search_re = re.search("([\w（）()-]+)(公司|经销部|供销社|合作社|联合社|联合会|直营部|经营部|批发部)",s)
            if search_re != None:
                news = search_re.groups()[-2]+search_re.groups()[-1]
                if news != s:
                    s = news
        else:#仍然出现多个公司的情况
            pass #认为是联合中标，不处理
        #根据分割词处理联合中标公司
        print(5,s)
        s = text_split(s)
        print(6,s)

        s_new = []
        for e in s:
            print(6.1,e)
            #处理括号
            e = text_bracket(e, city_names, segmentor, postagger, recognizer)
            print(6.2,e)
            #判断开头是否是地点，如果不是，则模糊查询，防止出现前端短缺/前端冗余
            city = text_city(e, city_names, segmentor, postagger, recognizer)
            if ([ee for ee in city if e.startswith(ee)] == [] or city == {}) and not e.startswith('中国'):
                if company_key.get(e) != None:
                    e = company_key[e]
                else:
                    if re.search(r'([^分子支])(公司|局|院|中心|小学|中学|大学|部|会|校|行|团|社|处)', e):
                        print(6.3, e)
                        end = [ee.end() for ee in re.finditer(r'([^分子支])(公司|局|院|中心|小学|中学|大学|部|会|校|行|团|社|处)',e)][-1]
                        s_test = e[:end]
                        s_search = []
                        for cut in range(len(s_test) - 8):
                            if s_search == []:
                                s_cut = s_test[cut:]
                                s_search = query_search(s_cut)
                        if s_search != []:
                            s_find = re.sub(r'（', '(', s_search[0]['name'])
                            s_find = re.sub(r'）', ')', s_find)
                            intersect = find_lcsubstr(s_find, s_test)
                            if len(intersect) == len(s_test) or len(intersect) == len(s_find):
                                intersect_end = s_find.index(intersect) + len(intersect)
                                e1 = ''.join([s_find[:intersect_end], e[end:]])
                                company_key[e] = e1
                                e = e1
                        print(6.4,e)
                    else:
                        e = ''
            #去除提取错误的供应商
            if e != '':
                if re.search(r'[^本我向](公司)',e) and len(e) >= 8:
                    s_new.append(e)
                elif re.search(r'(局|公司|院|中心|大学|会|所|部|行|厂|社|校)$',e) and len(e) >= 4:
                    s_new.append(e)
        print(7,s_new)

        s = ';'.join(s_new)

        if s!=originalS:
            supplier[i]=s
   
    return supplier

city_names = pd.read_csv('/Users/fangmingjin/PycharmProjects/Competitiveness-master/get_bids_information/city_names.csv',encoding='utf-8')
LTP_DATA_DIR= 'ltp_data_v3.4.0'
cws_model_path=os.path.join(LTP_DATA_DIR,'cws.model')
segmentor = Segmentor()  # 初始化实例
segmentor.load(cws_model_path)  # 加载分词模型
pos_model_path = os.path.join(LTP_DATA_DIR, 'pos.model')  # 词性标注模型路径，模型名称为`pos.model`
postagger = Postagger()  # 初始化实例
postagger.load(pos_model_path)  # 加载词性标注模型
ner_model_path = os.path.join(LTP_DATA_DIR, 'ner.model')  # 命名实体识别模型路径，模型名称为`pos.model`
recognizer = NamedEntityRecognizer()  # 初始化实例
recognizer.load(ner_model_path)  # 加载命名体识别模型

text = ['龙源电子期刊北京龙源创新信息技术有限公司']
print(process_supplier(1,text,city_names, segmentor, postagger, recognizer))
'''
def main():
    data_path = '/Users/fangmingjin/PycharmProjects/Competitiveness-master/try'
    path_list = os.listdir(data_path)
    for path in path_list:
        if os.path.isfile(data_path + '/' + path) and path.endswith('.csv'):
            dir_path = data_path + '/' + path
            df = pd.read_csv(dir_path)  # 读取CSV文件
            df = df.fillna("")  # 将None的数据填充为空字符串
            ids = df["id"].tolist()  # 将csv属性列转换为list
            money = df["money"].tolist()  # 将csv属性列转换为list
            supplier = df["supplier"].tolist()
            supplier = process_supplier(ids, supplier)  # 清洗供应商
            money = process_money(ids, money)  # 清洗金额
            df['money'] = money
            df['supplier_clean'] = supplier
            save_path = dir_path  # .replace('save_data_new','clean_data_new')
            df.to_csv(save_path, mode="w", index=False, quoting=1, encoding='utf-8-sig')

if __name__ == "__main__":
    main()
'''
'''
        # 防止括号中有分割符，先判断这部分括号
        bracket = re.search(r'[\(（]([^0-9\)）\(（]+)( |、|，|,|;|；|和|与|或|\\)([^0-9\)）\(（]+)[\)）]?', s)
        bracket_s = re.search(r'^([^\(（]*?)([^0-9\(（]+)( |、|，|,|;|；|和|与|或|\\)([^\(（]*?)[\)）]', s)
        if bracket:
            box = s[bracket.start():bracket.end()].strip('(').strip(')').strip('（').strip('）')
        elif bracket_s:
            box = s[bracket_s.start():bracket_s.end()].strip('(').strip(')').strip('（').strip('）')
        if bracket or bracket_s:
            s_left = re.sub(r'((^[^\(\)（）]*?)[\)）])|([\(（]([^\(\)（）]*?)$)', '', s)
            s_left = re.sub(u"\\(.*?\\)|（.*?）", "", s_left)
            tf_l = re.search(r'[^本我向](公司|局|院|中心|小学|中学|大学|部|会|校|行|团|社)$',
                             s_left)
            if not tf_l and re.search(
                    r'(公司|局|院|中心|小学|中学|大学|部|会|校|行|团|社)( |、|，|,|;|；|和|与|或|\\)',
                    box):
                s = box
            else:
                s = re.sub(box, '', s)
                s = re.sub(r'[\(（][\)）]', '', s).strip('(').strip(')').strip('（').strip('）')
'''