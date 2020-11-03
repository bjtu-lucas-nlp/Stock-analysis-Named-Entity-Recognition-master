# Stock-analysis-Named-Entity-Recognition
## 本项目主要面向产品竞争类分析中股权关系数据进行分析，本实验通过Bert-BiLSTM-CRF方法进行命名实体识别，本次实验主要识别买方（Buyer）、卖方（Seller）、标的（Target）三种实体。
**编写人：卢克治<br>时间：2020年8月24日<br>项目功能：面向股权关系数据通过Bert-BiLSTM-CRF模型进行命名实体识别<br>**
- The named entity recognition function of stock relationship data, which identify three types of entities: buyer, seller and target.<br>
+ 本模型细节和代码主要参考使用：[BERT-BiLSTM-CRF-NER](https://github.com/macanv/BERT-BiLSTM-CRF-NER)<br>
* 本模型使用的Bert模型主要下载以下资源中的RoBERTa-wwm-ext-large, Chinese模型：[中文Bert模型汇总](https://github.com/ymcui/Chinese-BERT-wwm)<br>

---
## 1：数据清洗：
### 1.1：NER标准数据集构建：
+ 数据清洗功能主要完成对股权关系已标注好的数据进行BIO方式文件的转化。转化好的BIO文件可以作为以下Bert-BiLSTM-CRF进行命名实体识别的模型输入。
+ 输入数据在：[数据清洗/inputData](https://github.com/lgxt/Stock-analysis-Named-Entity-Recognition/tree/master/%E6%95%B0%E6%8D%AE%E6%B8%85%E6%B4%97/inputData)目录下；
+ 输出数据在：[数据清洗/outputData](https://github.com/lgxt/Stock-analysis-Named-Entity-Recognition/tree/master/%E6%95%B0%E6%8D%AE%E6%B8%85%E6%B4%97/outputData)目录下；
+ 脚本运行为：[数据清洗/NER-dataset-按每条公告汇总标注构建数据集-统一公告id.py](https://github.com/lgxt/Stock-analysis-Named-Entity-Recognition/blob/master/%E6%95%B0%E6%8D%AE%E6%B8%85%E6%B4%97/NER-dataset-%E6%8C%89%E6%AF%8F%E6%9D%A1%E5%85%AC%E5%91%8A%E6%B1%87%E6%80%BB%E6%A0%87%E6%B3%A8%E6%9E%84%E5%BB%BA%E6%95%B0%E6%8D%AE%E9%9B%86-%E7%BB%9F%E4%B8%80%E5%85%AC%E5%91%8Aid.py)<br>
```
python NER-dataset-按每条公告汇总标注构建数据集-统一公告id.py
```
**完成以上数据清洗之后，就可以解析来进行NER的数据准备和模型训练工作了：**
### 1.2：NER输入数据：
+ 将数据清洗完成的BIO文件按照80%作为训练集（train.txt）、10%作为验证集（dev.txt）、10%作为测试集（test.txt）放入[NER模型训练输入标准数据集](https://github.com/lgxt/Stock-analysis-Named-Entity-Recognition/tree/master/NERdata)文件夹下。
### 1.3：NER输出数据：
+ 模型训练的结果主要生成与run.py同级目录下的output文件夹中，在模型训练前可以新建下该文件夹，如果没有该目录，模型代码会自动创建该目录。

_ _ _
## 2：模型训练：
**在完成数据处理部分之后，就可以进行模型训练了，在代码中修改当前运行环境的目录信息后，就可以进行如下模型训练工作：**
**环境要求**
+ python >= 3.6
+ tensorflow == 1.15.0
+ cuda == 10.0
+ 注意tensorflow和cuda的版本自己根据自己的环境适配就行，具体版本可参考[tensorflow和cuda版本对应关系](https://blog.csdn.net/qq_31747765/article/details/107958052)
### 2.1：Docker镜像的使用（使用服务器：10.167.3.4）：
```
docker run --runtime nvidia --rm -it -v /home/yonyou/baiqj/lucas:/Share lucas/tensorflow:v1.15.0rc2-gpu-py3-v1.2 bash
```
### 2.2：使用Docker镜像使用gpu进行模型训练：
```
cd /Share
nohup python3 -u run.py > run_log.txt 2>&1 &
```
### 2.3：退出docker镜像：
+ 直接不保存退出docker容器：
```
ctrl + d
```
+ 退出但是后台运行docker容器：
```
ctrl + p + q
```
_ _ _
## 3：模型预测：
```
python3 terminal_predict-original.py
```
_ _ _
## 4：项目进展文档：
+ 本项目进展以及算法详情和实验细节请阅读文档：[股权命名实体识别0925.pptx](https://github.com/lgxt/Stock-analysis-Named-Entity-Recognition/blob/master/%E8%82%A1%E6%9D%83%E5%91%BD%E5%90%8D%E5%AE%9E%E4%BD%93%E8%AF%86%E5%88%AB0925.pptx)<br>
