import os
import csv
# 读取csv文件中的信息，保存到一个文件中
def extract_companyInfo(file_name,filter_name,all_ZiRanRen_set):
    pass
    read_file = open(file_name,"r",encoding="utf-8")
    read_file_content = list(csv.reader(read_file))
    for cur_content in read_file_content:
        if cur_content[0] != "企业id":
            type = cur_content[5]
            name = cur_content[3]
            if type == filter_name:
                if name not in all_ZiRanRen_set:
                    all_ZiRanRen_set.add(name)

# 保存所有的自然人字典结果
def save_ZiRanRen_name(save_file_writer,all_ZiRanRen_set):
    for ZiRanRen in all_ZiRanRen_set:
        # save_file_writer.writerow([ZiRanRen])
        save_file_writer.write(ZiRanRen+"\n")
if __name__ == "__main__":
    print("lucas")
    folder = "inputData/韩悦query企业信息"
    save_file = "outputData/query_自然人_info.txt"
    savefile_open = open(save_file,"w",encoding="utf-8")
    # save_file_writer = csv.writer(savefile_open)
    file_list = os.listdir(folder)
    all_ZiRanRen_set =set()   #保存所有自然人信息
    for file in file_list:
        filename = folder + '/' + file  # 使用企业姓名查询
        extract_companyInfo(filename,"自然人",all_ZiRanRen_set)
    save_ZiRanRen_name(savefile_open,all_ZiRanRen_set)
        # if not os.path.exists(savefolder + str(file)):
        #     print(filename)