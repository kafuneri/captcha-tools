
# 关于
代码fork自[luguoyixiazi/test_nine](https://github.com/luguoyixiazi/test_nine)，在此仅添加docker构建配置以方便使用，仅供个人测试使用，不保证可用性
# 食用方法
### 1.安装docker
教程很多，不再赘述，推荐使用
```bash
bash <(curl -sSL https://linuxmirrors.cn/docker.sh)
```
### 2.构建镜像(可选)
```bash
git clone https://github.com/kafuneri/captcha-tools.git 
cd captcha-tools
docker compose build --no-cache && docker compose up -d #构建并运行镜像
```
> PS：国内服务器构建镜像时请注意配置代理或换源
### 3.使用构建好的镜像
使用`docker-compose.yaml`：
```yaml
services:
  captcha-tools:
    image: kafuneri/captcha-tools:latest 
    container_name: captcha-tools
    network_mode: host  # 设置为 host 网络模式
    restart: always
```

### 4.对接[MihoyoBBSTools](https://github.com/Womsxd/MihoyoBBSTools)
修改MihoyoBBSTools中的captcha.py为该项目中的[captcha.py](https://raw.githubusercontent.com/kafuneri/captcha-tools/refs/heads/main/captcha.py)


--------
## 旧版镜像兼容说明

该Fork同步了上游更新，若您仅需要处理基础的九宫格验证码，且希望维持旧版 API 的调用习惯，请使用旧版镜像。该系列镜像已验证具备长期的运行稳定性。  

镜像地址：[kafuneri/captcha-tools](https://hub.docker.com/r/kafuneri/captcha-tools/tags)

### 1. 版本差异矩阵对比

| 镜像分类 | 镜像标签 (Tag) | 目标支持架构 (Arch) | 核心请求端点 | 支持的验证模式 |
| --- | --- | --- | --- | --- |
| **最新智能网关版** | `latest` | 自动适配双架构 | `/pass_uni` | 九宫格、图标点选等 |
| **经典纯九宫格版** | `amd64` | 仅限 **x86_64** | `/pass_nine` | 仅九宫格 |
| **经典纯九宫格版** | `arm64` | 仅限 **ARM64** | `/pass_nine` | 仅九宫格 |

### 2. 旧版容器编排配置

部署旧版时，您必须在编排配置中精准指定与宿主机硬件匹配的架构标签，不可使用自动化标签。

```yaml
services:
  captcha-tools:
    # x86_64 处理器设备请使用 amd64 标签
    # ARM 架构设备请更改为 arm64 标签
    image: kafuneri/captcha-tools:amd64 
    container_name: captcha-tools
    network_mode: host 
    restart: always

```

### 3. 旧版客户端对接代码 (captcha.py)

调用经典版镜像时，禁止向新型多模态网关发起请求。您必须将请求端点显式回退至 **`/pass_nine`** 路由，且在 **httpx** 的请求参数中强制声明 **`use_v3_model`** 的布尔值为 `True`。

修改MihoyoBBSTools中的captcha.py的内容为该项目中的[captcha.py.bak](https://raw.githubusercontent.com/kafuneri/captcha-tools/refs/heads/main/captcha.py.bak)

**该Fork中的model文件来自于原作者，仓库地址：https://github.com/luguoyixiazi/model_save**

以下为原项目说明
---------

# 九宫格+点选测试代码

## **本项目仅供学习交流使用，请勿用于商业用途，否则后果自负。**

## **本项目仅供学习交流使用，请勿用于商业用途，否则后果自负。**

## **本项目仅供学习交流使用，请勿用于商业用途，否则后果自负。**

## 参考项目

resnet模型及V4数据集：https://github.com/taisuii/ClassificationCaptchaOcr

点选检测模型https://github.com/Peterande/D-FINE

另一个点选检测模型https://github.com/facebookresearch/dinov3

另一个点选的检测模型https://github.com/ultralytics/ultralytics

api：https://github.com/ravizhan/geetest-v3-click-crack

感谢 @kissnavel 提供的关于我没玩的那两款的api

## 运行步骤

### 1.安装依赖（本地必选，使用docker跳至[5-b](#docker)）

（可选）a-0. 如果要训练paddle的话还得安装paddlex及图像分类模块，安装看项目[https://github.com/PaddlePaddle/PaddleX](https://github.com/PaddlePaddle/PaddleX)
（可选）a-1. d-fine训练看项目[https://github.com/Peterande/D-FINE](https://github.com/Peterande/D-FINE)
（可选）a-2. dinov3使用看项目[https://github.com/Peterande/D-FINE](https://github.com/facebookresearch/dinov3) 具体分类基于patch token
（可选）a-3. yolo训练看项目[https://github.com/Peterande/D-FINE](https://github.com/ultralytics/ultralytics)
（可选）a-4. 基于dinov3的分类，架构极其简陋，从一组图片中抽取所有已定位的图片的特征图，而后在一组中以下侧作为锚点，设置1正面样本，其余均做负面样本，学习dinov3提取特征中影响相似度比对的维度
（* 必选！）b.模型需要在项目目录下新建一个model文件夹，然后把模型文件放进去，具体命名可以是resnet18.onnx或者PP-HGNetV2-B4.onnx，默认使用PP-HGNetV2-B4模型，如果用resnet则use_v3_model设置为False，因为模型的输入输出不一样，可以自行修改，d-fine的模型同样放置此路径用于通过点选，另外的dinov3和yolo1n和我自己做的任务头整体组合为一个流水线作业，全都要放进去

```
pip install -r requirements.txt
```

仅推理
```
pip install -r requirements_without_train.txt
```

### 2.自行准备数据集，V3和V4有区别（可选），点选可以自己生成，要有旋转、重叠、换色

##### a. 训练resnet18（可选）

- 数据集详情参考上面标注的项目，但是上面项目是V4数据集，V3没有demo，自行发挥吧，用V4练V3不改代码正确率有点感人
- 主要是V4的尺寸和V3有差别，V4的api直接给两张图，一张是目标图，一张是九宫格，V3放在一起要切目标，且V3目标图清晰度很低，V4九宫格切了之后是100 * 86的图（去掉黑边），但是V3九宫格切的是112 * 112，不确定V4九宫格内容在V3基础上做了什么变换，反正改预处理就完事了

##### a-0. 训练PP-HGNetV2-B4（可选）

在paddle上随便找的，数据集格式如下，如果拿V4练V3，建议是多整点变换

```
   dataset
   ├─images   #所有图片存放路径
   ├─label.txt #标签路径，每一行数据格式为 <序号>+<空格>+<类别>，如15 地球仪
   ├─train.txt #训练图片，每一行数据格式为 <图片路径>+<空格>+<类别>，如images/001.jpg 0
   └─验证集和测试集同上
```

##### a-1. 训练d-fine（可选）

数据集格式如d-fine中标识，如果不修改源码则num_classes需+1，采用coco格式即可，我用的320*320，dataloader注释掉了RandomZoomOut、RandomHorizontalFlip、RandomIoUCrop（这些我全写在数据集生成中了）

##### a-2. 训练基于dinov3和yolo的流水线（可选）

数据集格式我自己拟定的，因为一次加载使用一个锚点一个正面多个负面，所以我先组织了格式，当然原始标注时还是用的coco，将每个image上的所有标注全组合在两个列表，根据y轴划分top和bottom，以bottom为锚点（实际上没差，但是实际使用不涉及top组内比对就跳过了节省资源），top中1✅多❌

##### b. 如果要切V3的九宫格图用crop_image.py的crop_image_v3，切V4则使用crop_image，自行编写切图脚本

### 3.训练模型（可选）

- 训练resnet18运行 `python train.py`
- 如果训练PP-HGNetV2-B4运行`python train_paddle.py`
- 训练d-fine参照原项目，一个模型拿下，比ddddocr+相似性检测资源开销小点
- 训练代码极其简单，可以基于我提出的思路即数据集组织，使用llm直接生成，yolo训练参考其仓库即可，dinov3没训练，也没拿来做定位，因为定位头的规模大于yolo11n，不划算

### 4-a.PP-HGNetV2-B4模型和resnet模型转换为onnx（可选）

- 运行 `python convert.py`（自行进去修改需要转换的模型，一般是选loss小的）
- paddle模型转换要装paddle2onnx，详情参见https://www.paddlepaddle.org.cn/documentation/docs/guides/advanced/model_to_onnx_cn.html

### 4-b.d-fine转换为onnx（可选）

- 依原项目转换
- 推理时图像预处理应于训练时一致，d-fine仓库中onnx推理的预处理和训练不一致……

### 4-c. 复合模型转onnx（可选）

- yolo依原项目转换
- dinov3直接使用官方即可，只是拿来提取特征
- 分类的导出也是pytorch和onnx内置函数，由于太小所以没必要做什么操作
- 之所以不组合为一个模型主要还是考虑到未来如果更新，可以复用，dinov3提取的特征实际上可以完成上述所有任务，虽然定位的模型会大一点，但一个几百kb大小的头可以替代九宫格的分类模型，点选定位如果只划分上下的部分或许也能用更小的模型

### 5-a.启动fastapi服务（必须要有训练完成的onnx格式模型）

基于环境变量可以自定义加载哪些模型，目前支持use_pdl，use_dfine，use_multi，日志也有环境变量改，LOG_LEVEL

运行 `python main.py`（九宫格默认用的paddle的onnx模型，如果要用resnet18可以自己改注释）或者`uvicorn main:app --host 0.0.0.0 --port 9645 --reload`

由于轨迹问题，可能会出现验证正确但是结果失败，所以建议增加retry次数，训练后的paddle模型正确率在99.9%以上，
由于dinov3的onnx和pth不完全一致，导致基于pth训练的头精度低了一点，4613张图里面错了1张，如果采用量化的dinov3会多错几张，当然，可以使用onnx量化提取的特征训练，但是速度比pth慢得多就是了，再说吧

### 5-b.使用docker启动服务 

镜像地址为<span id="docker">luguoyixiazi/test_nine:25.7.2</span> 此版本特供只需要九宫格和便笺的

镜像地址为<span id="docker">luguoyixiazi/test_nine:25.11.2</span> 此版本在上述基础上支持🛤和3z

运行时只需指定绑定的port和两个环境变量`use_pdl`和`use_dfine`和`use_multi`，1为启用模型，0为不启用，默认均启用，api端口为/pass_uni，必填参数gt、challenge，单独的pass_nine和pass_icon也写了，有更多可选参数

### 6.api调用

python调用如：

```python
import httpx

def game_captcha(gt: str, challenge: str):
	res = httpx.get("http://127.0.0.1:9645/pass_uni",params={'gt':gt,'challenge':challenge},timeout=10)
	# 或者依旧使用pass_nine路径：
	# res = httpx.get("http://127.0.0.1:9645/pass_nine",params={'gt':gt,'challenge':challenge,'use_v3_model':True,"save_result":False},timeout=10)
	datas = res.json()['data']
    if datas['result'] == 'success':
        return datas['validate']
    return None # 失败返回None 成功返回validate
```

在snap hutao中的服务端口为/pass_hutao,返回值已做对齐，填写api如`(http://127.0.0.1:9645/pass_hutao?gt={0}&challenge={1})`即可

添加了辅助api加载卸载模型和查看模型，以及更改日志等级

具体调用代码看使用项目，此处示例仅为API url和参数示例

#### --宣传--

欢迎大家支持我的其他项目(搭配使用)喵~~~~~~~~
