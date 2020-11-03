import csv
import re


def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
        return True
    else:
        return False


def is_number(uchar):
    """判断一个unicode是否是数字"""
    if uchar >= u'\u0030' and uchar <= u'\u0039':
        return True
    else:
        return False


def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    if (uchar >= u'\u0041' and uchar <= u'\u005a') or (uchar >= u'\u0061' and uchar <= u'\u007a'):
        return True
    else:
        return False

# 将字符串中内容按照长度进行排序
def get_sorted_subset(original):
    subset = original.split("、")
    subset.sort(key = lambda i:len(i),reverse=True)
    return subset

# 查看当前的起始时间是否和已经保存的起始时间表有重合
def check_inMiddle_spans(startPos,endPos,finishedSpans):
    for span in finishedSpans:
        if startPos >= span[0] and startPos <= span[1]:
            return True
        if endPos >= span[0] and endPos <= span[1]:
            return True
    return False

# 实现对字符串中满足标注结果的标签进行统计finished_spans：[startpos,endpos,labelname]
def get_content_ner_statistics(content, target_nes, cur_label, finished_spans):
    pass
    # 每一个实体去目标文件中进行匹配查找原文的位置信息，进行维护到finished_statistic中
    for cur_ne in target_nes:
        for m in re.finditer(cur_ne,content):
            # 匹配的起始位置 print(m.span())
            # 匹配的原文 print(m.group())
            cur_startPos = m.span()[0]
            cur_endPos = m.span()[1]
            if check_inMiddle_spans(cur_startPos,cur_endPos,finished_spans) == False:
                finished_spans.append([cur_startPos,cur_endPos,cur_label])

    return finished_spans

# 处理特殊的英文和数字字符
# 如果一连串英文字母的，就连着输出
def special_chac_dispose(cur_content,cur_line,save_file_writer,i):
    if cur_content[i].isdigit() == True:  # 是否为数字字符
        cur_line = cur_line + cur_content[i]
    # elif cur_content[i].isalpha() == True:   #是否为字母字符
    if is_alphabet(cur_content[i]) == True:  # 是否为字母字符
        cur_line = cur_line + cur_content[i]
    elif cur_content[i] == ".":  # 因为有的数字是10.23，带小数点
        if len(cur_line) > 0:
            if cur_line[-1].isdigit() == True:
                cur_line = cur_line + cur_content[i]
    else:
        if len(cur_line) > 0:  # 如果之前还有内容，先输出，再进行输出此处内容
            save_file_writer.writerow([cur_line + " O"])
            save_file_writer.writerow([cur_content[i] + " O"])
            cur_line = ""
        else:  # 没有遗留的需要输出，那么只输出此处
            save_file_writer.writerow([cur_content[i] + " O"])
    return cur_line

# 查看字符是否是句号"。"、分号";"、"；"
def check_isEndSentence(checkChar):
    if checkChar == "。":
        return True
    elif checkChar == ";":
        return True
    elif checkChar == "；":
        return True
    else:
        return False

# 将原文中标记好的结果进行标准化输出
def write_standard_dataset(save_file_writer,cur_content,finished_spans,total_sentence_num):
    pass
    #先将finished_spans中位置信息的结果按照startpos进行排序
    # sorted_finished_spans = finished_spans.sort(lambda x,y: cmp(x[0],y[0]), reverse=False)
    # sorted_finished_spans = finished_spans.sort(key = lambda x: cmp(x[0], y[0]), reverse=False)
    finished_spans.sort(key = lambda x:x[0], reverse=False)

    # 在依据排序好的结果依次将content中标注结果按照BIO方式写入文件
    cur_line = ""
    cur_spans_index = 0
    # 依次读取content中内容
    for i in range(len(cur_content)):
        if cur_spans_index < len(finished_spans):  # 还有待检索的实体记录
            if i < finished_spans[cur_spans_index][0]: #i < startPos, 没有标签打上O
                pass
                # cur_line = special_chac_dispose(cur_content,cur_line,save_file_writer,i)
                save_file_writer.writelines([cur_content[i] + " O\n"])
                # 判断是否句子结束
                if check_isEndSentence(cur_content[i]) == True:
                    save_file_writer.writelines("\n")
                    total_sentence_num += 1
            elif i == finished_spans[cur_spans_index][0]:   #i==startPos
                pass
                cur_line_temp = cur_content[i] + " B-" + finished_spans[cur_spans_index][2]  # 更新输出的字符串+" B-label"
                save_file_writer.writelines([cur_line_temp+"\n"])
            elif i < finished_spans[cur_spans_index][1]:   # startPos < i < endPos
                pass
                cur_line_temp = cur_content[i] + " I-" + finished_spans[cur_spans_index][2]  # 更新输出的字符串+" I-label"
                save_file_writer.writelines([cur_line_temp+"\n"])
            elif i == finished_spans[cur_spans_index][1]:   # i == endPos
                # cur_line_temp = cur_content[i] + " I-" + finished_spans[cur_spans_index][2]  # 更新输出的字符串+" I-label"
                pass
                # cur_line = special_chac_dispose(cur_content, cur_line, save_file_writer, i)
                save_file_writer.writelines([cur_content[i] + " O"+"\n"])
                cur_spans_index += 1    #下一个标记数据
                # 判断是否句子结束
                if check_isEndSentence(cur_content[i]) == True:
                    save_file_writer.writelines("\n")
                    total_sentence_num += 1
            else:   #i > endPos
                pass
                print("Error: cur line: ",i," 大于当前")
        else:   # 内容中没有需要待检索使用的实体标记信息
            # cur_line = special_chac_dispose(cur_content, cur_line, save_file_writer, i)
            save_file_writer.writelines([cur_content[i] + " O"+"\n"])
            # 判断是否句子结束
            if check_isEndSentence(cur_content[i]) == True:
                save_file_writer.writelines("\n")
                total_sentence_num += 1
    # 一个公告处理完，结束就加上换行
    save_file_writer.writelines("\n")
    return total_sentence_num


# lucas将命名实体构建标准数据集
def standard_NER_dataset(ner_file,standard_ner_file):
    save_file = open(standard_ner_file,"w",encoding="utf-8")
    # save_file_writer = csv.writer(save_file)

    # lucas20200804解决一条公告可能出现多行的标注结果，需要进行汇总然后再回原文标注
    content_label_dict = {}
    with open(ner_file,"r") as f:
        cur_reader = csv.reader(f)
        cur_reader_list = list(cur_reader)
        for row in cur_reader_list[1:]:
            cur_index = int(row[0])
            cur_content = row[1]
            cur_buyer = row[2]
            cur_sorted_buyer = get_sorted_subset(cur_buyer)
            cur_seller = row[3]
            cur_sorted_seller = get_sorted_subset(cur_seller)
            cur_target = row[4]
            cur_sorted_target = get_sorted_subset(cur_target)
            # 如果之前已经记录了该公告，那么将结果合并统计到dict中
            if cur_index in content_label_dict:
                # 将当前的买方信息进行更新到字典中
                exist_buyer = content_label_dict[cur_index][2]
                exist_seller = content_label_dict[cur_index][3]
                exist_target = content_label_dict[cur_index][4]
                # 更新买方信息
                for buyer in cur_sorted_buyer:
                    if buyer not in exist_buyer:
                        exist_buyer.append(buyer)
                # 更新卖方信息
                for seller in cur_sorted_seller:
                    if seller not in exist_seller:
                        exist_seller.append(seller)
                # 更新标的信息
                for target in cur_sorted_target:
                    if target not in exist_target:
                        exist_target.append(buyer)
                # 将结果再保存到content_label_dict中
                content_label_dict[cur_index][2] = exist_buyer
                content_label_dict[cur_index][3] = exist_seller
                content_label_dict[cur_index][4] = exist_target
            else:
                content_label_dict[cur_index] = [cur_index,cur_content,cur_sorted_buyer,cur_sorted_seller,cur_sorted_target]

        # 将更新完成的content_label_dict进行遍历
        total_sentence_num = 0    # 统计语料库句子个数
        for key,value in content_label_dict.items():
            cur_content = value[1]
            cur_sorted_buyer = value[2]
            cur_sorted_buyer.sort(key=lambda i: len(i), reverse=True)
            cur_sorted_seller = value[3]
            cur_sorted_seller.sort(key=lambda i: len(i), reverse=True)
            cur_sorted_target = value[4]
            cur_sorted_target.sort(key=lambda i: len(i), reverse=True)
            # 对买方、卖方、和标的依次进行原文的查找
            finished_spans = get_content_ner_statistics(cur_content, cur_sorted_buyer, "buyer", [])
            finished_spans = get_content_ner_statistics(cur_content, cur_sorted_seller, "seller", finished_spans)
            finished_spans = get_content_ner_statistics(cur_content, cur_sorted_target, "target", finished_spans)

            # 对统计好的所有的实体标记结果回到原文进行标准数据格式整理输出
            total_sentence_num = write_standard_dataset(save_file,cur_content,finished_spans,total_sentence_num)
        print("该语料库最终共计形成：",len(content_label_dict.keys()),"条公告; ",total_sentence_num,"条句子")

if __name__ == "__main__":
    pass
    standard_NER_dataset("inputData/content_ret_1000new.csv",
                         "outputData/standard_NER_dataset/standard_ner_file.txt")

    # test
    # get_content_ner_statistics("james and lucas like wade, james, lucas",["lucas","james"],[])