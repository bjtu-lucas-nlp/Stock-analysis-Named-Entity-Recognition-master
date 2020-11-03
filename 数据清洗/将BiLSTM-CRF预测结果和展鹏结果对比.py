import csv
import numpy as np

def split_set(infor):
    list_info = infor.strip().split(",")
    infor_set = set()
    for info in list_info:
        infor_set.add(info)
    return infor_set

#lucas计算两个集合的Jaccard相似度
def cal_jaccard_sim(set_a,set_b):
    jiaoji = set_a & set_b
    bingji = set_a | set_b
    jiaoji_num = float(len(jiaoji))
    bingji_num = float(len(bingji))
    jaccard_sim = jiaoji_num/bingji_num

    return jaccard_sim

#lucas将buyer、seller、target三个数据的均值进行数值区间分类
def statis_group(data,data_statistic):
    pass
    if data == 0:
        data_statistic[0] = data_statistic[0] + 1
    elif data > 0 and data <= 0.1:
        data_statistic[1] = data_statistic[1] + 1
    elif data > 0.1 and data <= 0.2:
        data_statistic[2] = data_statistic[2] + 1
    elif data > 0.2 and data <= 0.3:
        data_statistic[3] = data_statistic[3] + 1
    elif data > 0.3 and data <= 0.4:
        data_statistic[4] = data_statistic[4] + 1
    elif data > 0.4 and data <= 0.5:
        data_statistic[5] = data_statistic[5] + 1
    elif data > 0.5 and data <= 0.6:
        data_statistic[6] = data_statistic[6] + 1
    elif data > 0.6 and data <= 0.7:
        data_statistic[7] = data_statistic[7] + 1
    elif data > 0.7 and data <= 0.8:
        data_statistic[8] = data_statistic[8] + 1
    elif data > 0.8 and data <= 0.9:
        data_statistic[9] = data_statistic[9] + 1
    elif data > 0.9 and data < 1:
        data_statistic[10] = data_statistic[10] + 1
    elif data == 1:
        data_statistic[11] = data_statistic[11] + 1



if __name__ == "__main__":
    writer_f = open('outputData/BiLSTM-crf和R-bert结果对比.csv', 'w',newline='')
    writer = csv.writer(writer_f)
    seller_statistic = [0] * 12
    buyer_statistic = [0] * 12
    target_statistic = [0] * 12
    overall_ave_statistic = [0] * 12


    with open('inputData/BertBatch16Epoch30Predict/merge.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
         id = row[0]
         result = []
         result.append(id)
         if id != "id":
             our_seller = row[1]
             their_seller = row[2]
             our_seller_set = split_set(our_seller)
             their_seller_set = split_set(their_seller)
             seller_jaccard_sim = cal_jaccard_sim(our_seller_set,their_seller_set)

             our_buyer = row[3]
             their_buyer = row[4]
             our_buyer_set = split_set(our_buyer)
             their_buyer_set = split_set(their_buyer)
             buyer_jaccard_sim = cal_jaccard_sim(our_buyer_set, their_buyer_set)

             our_target = row[5]
             their_target = row[6]
             our_target_set = split_set(our_target)
             their_target_set = split_set(their_target)
             target_jaccard_sim = cal_jaccard_sim(our_target_set, their_target_set)

             content = row[7]

             result.append(our_seller)
             result.append(their_seller)
             result.append(seller_jaccard_sim)

             result.append(our_buyer)
             result.append(their_buyer)
             result.append(buyer_jaccard_sim)

             result.append(our_target)
             result.append(their_target)
             result.append(target_jaccard_sim)
             result.append(content)

             #lucas将各个数据的相似性进行分组统计
             statis_group(buyer_jaccard_sim,buyer_statistic)
             statis_group(seller_jaccard_sim,seller_statistic)
             statis_group(target_jaccard_sim,target_statistic)
             statis_group(np.mean([buyer_jaccard_sim,seller_jaccard_sim,target_jaccard_sim]),overall_ave_statistic)

             writer.writerow(result)
         else:
             writer.writerow(["id", "bbc_seller", "rb_seller", "seller Coincidence rate", "bbc_buyer", "rb_buyer", "buyer Coincidence rate", "bbc_target", "rb_target", "target Coincidence rate", "content"])

    print("buyer统计：",buyer_statistic)
    print("seller统计：",seller_statistic)
    print("target统计：",target_statistic)
    print("三者均值的统计：",overall_ave_statistic)
