![](_page_0_Picture_0.jpeg)

华南理工大学学报(自然科学版) *Journal of South China University of Technology(Natural Science Edition)* ISSN 1000-565X,CN 44-1251/T

# 《华南理工大学学报**(**自然科学版**)**》网络首发论文

题目: 基于集成深度学习模型的公路隧道交通流预测

作者: 钱超,李俊,李发强,赵一辰,周钟文,刘怡策,程剑英

收稿日期: 2025-08-08 网络首发日期: 2026-05-22

引用格式: 钱超,李俊,李发强,赵一辰,周钟文,刘怡策,程剑英.基于集成深度学

习模型的公路隧道交通流预测[J/OL].华南理工大学学报(自然科学版)**.**

https://link.cnki.net/urlid/44.1251.t.20260521.1658.006

![](_page_0_Picture_9.jpeg)

![](_page_0_Picture_10.jpeg)

网络首发:在编辑部工作流程中,稿件从录用到出版要经历录用定稿、排版定稿、整期汇编定稿等阶 段。录用定稿指内容已经确定,且通过同行评议、主编终审同意刊用的稿件。排版定稿指录用定稿按照期 刊特定版式(包括网络呈现版式)排版后的稿件,可暂不确定出版年、卷、期和页码。整期汇编定稿指出 版年、卷、期、页码均已确定的印刷或数字出版的整期汇编稿件。录用定稿网络首发稿件内容必须符合《出 版管理条例》和《期刊出版管理规定》的有关规定;学术研究成果具有创新性、科学性和先进性,符合编 辑部对刊文的录用要求,不存在学术不端行为及其他侵权行为;稿件内容应基本符合国家有关书刊编辑、 出版的技术标准,正确使用和统一规范语言文字、符号、数字、外文字母、法定计量单位及地图标注等。 为确保录用定稿网络首发的严肃性,录用定稿一经发布,不得修改论文题目、作者、机构名称和学术内容, 只可基于编辑规范进行少量文字的修改。

出版确认:纸质期刊编辑部通过与《中国学术期刊(光盘版)》电子杂志社有限公司签约,在《中国 学术期刊(网络版)》出版传播平台上创办与纸质期刊内容一致的网络版,以单篇或整期出版形式,在印刷 出版之前刊发论文的录用定稿、排版定稿、整期汇编定稿。因为《中国学术期刊(网络版)》是国家新闻出 版广电总局批准的网络连续型出版物(ISSN 2096-4188,CN 11-6037/Z),所以签约期刊的网络版上网络首 发论文视为正式出版。

第 XX 卷 第 XX 期 XXXX 年 XX 月

Vol. XX No. XX XX XXXX

doi:10. 12141/j. issn. 1000-565X. 250274

# 基于集成深度学习模型的公路隧道交通流预测

钱超<sup>1</sup> 李俊<sup>1</sup> 李发强<sup>2</sup> 赵一辰<sup>1</sup> 周钟文<sup>2</sup> 刘怡策<sup>1</sup> 程剑英<sup>2</sup> (1. 长安大学 电子与控制工程学院,陕西 西安 710064;2. 海南交控科技有限公司,海南 海口 570203)

摘 要:公路隧道交通流预测是合理优化隧道运营管控方案的重要技术基础。针对交 通流数据的非线性、时空耦合性以及降噪处理中扰动信息丢失等问题,提出了一种结 合趋势建模与残差补偿的公路隧道交通流预测模型。首先,基于对交通流数据的趋势 与统计特征分析,将原始数据划分为客车与货车两类;其次,结合平稳性检验结果, 对非平稳数据采用高斯平滑方法进行降噪处理;然后,将平稳数据与降噪数据输入融 合卷积神经网络、双向长短期记忆网络和时序自注意力机制的主干网络,以提取趋势 特征,并引入时序卷积网络对残差数据进行建模,以恢复降噪处理中丢失具有时序结 构的扰动特征;最后,通过融合趋势特征与扰动特征,生成最终预测结果。选取秦岭 终南山公路隧道的小时流量数据进行模型训练和测试,实验结果表明:在对总体流量 的连续预测中,集成深度学习模型预测的均方根误差为42. 29±5. 66 pcu,加权平均绝对 百分比误差为 4. 18%±1. 06%,与 其他预测模型的 最优结 果(64. 28±7. 84 pcu、6. 57% ±1. 08%)相比,两类误差分别降低了34. 20%、36. 37%。在消融实验中,残差补偿模块 对模型性能影响最显著,可使两类误差分别降低26. 97%、35. 00%。研究结果为公路隧 道智能交通系统的动态流量预测提供了理论基础。

关键词:智能交通;交通流预测;深度学习;公路隧道;残差建模

# 中图分类号:U491

随着交通出行需求和汽车保有量的持续增长, 公路交通面临的拥堵与事故问题日益严峻[1] 。隧道 作为公路网络的重要组成部分,由于结构封闭,一 旦发生交通拥堵或事故,不仅会显著降低通行效 率,还会带来更高的事故风险[2] 。相比开阔道路, 隧道交通流受空间与视距限制,行驶速度与换道条 件受限,流量数据呈现出更强的非线性与时空耦合 性。短时流量变化不仅反映交通运行状态,也直接 影响通风需求与运营安全[3] 。因此,针对隧道场景 开展高精度交通流预测研究,不仅能为通风控制与 运行调度提供科学依据,也有助于加快智能隧道

建设。

目前,交通流预测模型可分为参数模型和非参 数模型[4] 。参数模型基于数理统计方法构建,如差 分自回归移动平均模型[5] (ARIMA)和卡尔曼滤波 器[6] 等,但由于对平稳性假设的依赖,使其在面 对复杂多变的交通时存在一定局限性。而非参数模 型则基于数据驱动方法构建,能更好适应交通流数 据的非线性特征,主要包括机器学习模型和深度学 习模型。常见的机器学习模型有支持向量机回归 (SVR)、随机森林(RF)和 K 近邻(KNN)。Lin 等[7] 通过 SVR 对交通流进行初步预测,引入 KNN 对预

收稿日期:2025**⁃**08**⁃**08

基金项目:海南省重点研发计划项目(ZDYF2025GXJS174)

Foundation item:Supported by the Key Research and Development Program of Hainan Province(ZDYF2025GXJS174) 作者简介:钱超(1984—),男,博士,副教授,主要从事公路隧道安全运营研究。E-mail: qianchao@chd. edu. cn

测误差进行建模修正,从而提高短时交通流预测 精度。田佳等[8] 将交通流数据分解为多尺度分量, 并分别输入RF进行建模,以增强模型对局部扰动 的表征能力。这些方法在一定程度上提升了机器 学习模型的预测精度,但在建模复杂特征关系方 面,其表达能力仍然有限,且依赖于人工设计特 征。随着深度学习模型在特征提取与时序关系建 模方面展现出优势, 其在交通流预测领域被广泛 应用。段中兴等[9]采用滑动平均方法对隧道交通流 数据进行降噪处理, 以降低数据的复杂性, 从而提 升长短期记忆网络(LSTM)的预测精度。Bharti等[10] 则基于交通流同时受历史与未来状态影响的特点, 构建双向长短期记忆网络(BiLSTM),以更充分地 捕捉交通流数据的双向时序依赖关系。Mendez 等[11] 提出使用卷积神经网络(CNN)优化 BiLSTM, 通过卷积操作与维度压缩,在提取局部时序特征 时增强对短期模式变化的感知能力。李桃迎等[12] 则提出一种面向高速公路的集成深度学习模型, 利用 CNN 提取上下游交通流的空间关联特征,并 结合LSTM与门控循环单元(Gated Recurrent Unit, GRU)捕捉交通流的时间长短期依赖,研究结果验 证了多模块融合的集成策略在交通流预测任务中 的有效性。为突出对重要信息的关注, 部分学者 开始尝试引入注意力机制(Attention Mechanism, AM)。 戢晓峰等 [13] 通过在 BiLSTM 中嵌入 AM, 动 态评估各时刻特征的重要程度,强化隐藏层对节 假日交通流非线性、突变性特征的捕捉能力。Ren 等[14]则提出了一种融合注意力机制与时序卷积网 络(Temporal Convolutional Network, TCN)的混合 模型,利用注意力机制来挖掘交通流数据的长期 依赖,同时通过并行TCN结构建模短期波动,从 而提升在长短期尺度上的预测性能。对于公路隧 道场景,现有研究主要关注交通流的时空特征, 王九胜等[2] 通过提取并融合不同时间尺度下的 粒度特征,增强模型对多变交通环境的适应性。 Zeng 等 [15] 则考虑构建全面的公共假期出行数据库 并结合上下游流量变化,以提高模型对关键时段 的预测精度。

尽管深度学习模型在交通流预测中具有良好的性能,现有研究仍存在以下不足:一是特征耦合不足,缺乏对目标场景下交通运行模式、车辆类型以及休息日与工作日等特征的综合考虑;二是残余信息利用不足,未充分挖掘降噪过程丢失的扰动特征,限制了整体预测精度的进一步提升。

针对上述不足,本文提出一种面向公路隧道交通流的集成深度学习模型(Integrated Deep Learning Model, IDLM)。模型创新主要体现在以下三方面:

- (1)设计由主干网络与残差补偿模块组成的双分支结构,对交通流全局趋势与局部扰动并行建模;
- (2)通过融合非平稳数据的趋势与扰动特征,补偿降噪处理产生的信息丢失,进一步提高模型预测的精确性;
- (3)针对隧道交通流的车型差异与时段规律,结合统计特征分析对数据进行分层建模与特征增强,提升模型在复杂交通场景下的泛化能力。

#### 1 问题描述

交通流预测旨在利用交通历史监测数据预测未来一段时间内的交通流变化,其预测精度常受原始数据的质量、完整性以及交通流结构动态变化等多种不确定因素的影响。

设给定交通流数据集X, 预测问题的一般处理 步骤如下:

**步骤**(1):通过插补函数进行缺失值填充和异常值处理,得到预处理后的流量数据 $X_0$ 。

$$X_0 = F_{line}(X) + F_{normal}(X) \tag{1}$$

步骤(2): 利用 ADF 平稳性检验将  $X_0$  划分为平稳流量数据  $\bar{X}$  和非平稳流量数据  $\tilde{X}_0$ 

$$ADF = \frac{\hat{\gamma}}{SE(\hat{\gamma})} \tag{2}$$

$$p = Pr\left(ADF \le ADF_{obs} \middle| H_0\right) \tag{3}$$

$$X_{0} \xrightarrow{ADF \stackrel{\text{def}}{\sim}} \begin{cases} \bar{X} & , \ p < p_{0} \\ \tilde{X} & , \ p > p_{0} \end{cases}$$

$$(4)$$

步骤(3): 对 $\tilde{X}$ 进行降噪处理获得降噪数据 $\tilde{X}'$ 和残差数据 $\tilde{X}''$ 。

$$\tilde{X}' = G(\tilde{X}) \tag{5}$$

$$\tilde{X}'' = \tilde{X} - \tilde{X}' \tag{6}$$

步骤(4):模型提取交通流的时空特征,预测 未来M个时刻的流量数据。

$$X(T+1), \dots, X(T+M) = F_{\nu}(\bar{X}, \tilde{X}', \tilde{X}'') \tag{7}$$

式(1)-(7)中:  $F_{line}$ 、 $F_{normal}$ 分别为缺失值插补函数、异常值插补函数;  $\gamma$  为待检验值, $\hat{\gamma}$  为估计值; ADF 为检验统计量, $ADF_{obs}$  为由样本计算的统计值; p 为检验统计量对应的概率值, $p_0$  为平稳性判断阈值(边界值);  $SE(\cdot)$  为标准误差, $Pr(\cdot)$  为事件

发生概率;  $H_0$ 为原假设(序列非平稳); G为降噪函数;  $F_x$ 为时空特征的映射函数。

### 2 集成深度学习模型构建

考虑交通流的动态变化特性、复杂性及不同类型车辆出行行为的差异性,提出一种基于IDLM的交通流预测方法,总体研究框架如图1所示。首

先,结合对原始数据的趋势及统计特征分析结果,进行数据划分,并对预处理后的分类数据开展平稳性检验;然后,构建 CNN-BiLSTM-TSA 主干网络,用于提取平稳数据 $\bar{X}$ 和降噪数据 $\bar{X}'$ 的交通流趋势特征,并引入基于 TCN 的残差补偿模块,对残差数据 $\bar{X}''$ 进行建模。最后,融合趋势特征与扰动特征,从而实现对交通流的精准预测。

![](_page_3_Figure_7.jpeg)

图1 总体研究框架图

Fig. 1 Framework diagram of overall research

#### 2.1 数据预处理

为提高交通流数据集的质量,对缺失值和异常值根据文献 [16] 所提方法建立回归模型进行迭代插补和替换,以维持数据趋势的连续性和周期性。对非平稳数据采用高斯平滑(Gaussian Smoothing,GS)方法进行降噪处理,以降低噪声干扰、平滑局部波动。高斯核函数的标准差参数为1,数学表达式如下:

$$G_t = \sum_{n=1}^r x_{t+n} \cdot g_n \tag{8}$$

式中:  $G_t$ 为第t时刻平滑处理后的流量数据;  $x_t$ 为第t时刻的交通流量;  $g_n$ 为高斯权重函数; r为窗口半径。

为保留交通流与时间信息的关联性,构建包含小时信息的特征矩阵,并结合预测需求加入辅助特征(如工作日与休息日),以提升模型对不同时间场景的识别与适应能力。特征矩阵结构如下:

$$\begin{bmatrix} x_{t} & h_{t}^{(\sin)} & h_{t}^{(\cos)} & D_{t} \\ x_{t+1} & h_{t+1}^{(\sin)} & h_{t+1}^{(\cos)} & D_{t+1} \\ \vdots & \vdots & \vdots & \vdots \\ x_{T} & h_{T}^{(\sin)} & h_{T}^{(\cos)} & D_{T} \end{bmatrix}$$
(9)

式中:  $h_t^{(sin)}$ 和 $h_t^{(cos)}$ 为时间t的正余弦编码;  $D_t$ 为辅助

标签,取1为工作日,取0为休息日。

#### 2.2 卷积神经网络

CNN可扩展为一维卷积结构,用于在时间轴上 捕捉数据局部变化模式。其结构如图2所示,卷积 层和池化层计算公式如下:

$$x_t^{(conv)} = \sum_{n=0}^{k-1} w_n \cdot x_{t+n} + b_{conv}$$
 (10)

$$x_{t}^{(pool)} = \max\left(x_{t \cdot S}^{(conv)}, x_{t \cdot S+1}^{(conv)}, \dots, x_{t \cdot S+K-1}^{(conv)}\right)$$
(11)

![](_page_3_Picture_22.jpeg)

图2 CNN结构图

Fig. 2 Structure of CNN

式中:  $x_t^{(conv)}$ 为位置t处的卷积结果; k为卷积核大小; w为卷积核权重;  $b_{conv}$ 为偏置项;  $x_t^{(pool)}$ 为位置t处的池化结果; S为步长; K为池化核大小。

#### 2.3 双向长短期记忆网络

LSTM 通过引入门控机制有效缓解处理长序列时的信息遗失问题。LSTM 结构如图 3(a) 所示,相

![](_page_4_Figure_3.jpeg)

(a) LSTM

![](_page_4_Figure_5.jpeg)

(D) DILSTM

图3 网络结构

Fig. 3 Structure of network

#### 关计算公式如下:

$$f_t = \sigma \left( W_f x_t + U_f h_{t-1} + b_f \right) \tag{12}$$

$$i_t = \sigma(W_i x_t + U_i h_{t-1} + b_i)$$
(13)

$$\tilde{C}_t = \tanh(W_C x_t + U_C h_{t-1} + b_C) \tag{14}$$

$$C_t = f_t \cdot C_{t-1} + i_t \cdot \tilde{C}_t \tag{15}$$

$$o_t = \sigma \left( W_o x_t + U_o h_{t-1} + b_o \right) \tag{16}$$

$$h_{\cdot} = o_{\cdot} \cdot \tanh(C_{\cdot}) \tag{17}$$

式中: f, i, o分别为遗忘门、输入门和输出门; W, U为权重参数; b为偏置项; h, 为t时刻的记忆细胞;  $\tilde{C}_\iota$ 为候选记忆单元;  $C_\iota$ 为记忆单元;  $\sigma$ 和 tanh分别为Sigmoid激活函数和双曲正切激活函数。

考虑实际交通流演化具有连续性、时滞性等特征,当前时刻的交通流状态不仅依赖于过去,还可能受未来时刻的影响。为充分建模序列中前后时刻的信息关联,选择BiLSTM构建主干网络。BiLSTM由两个LSTM单元组成,分别沿时间的正序和逆序传递信息,将各自隐藏状态拼接后作为输出,其结构如图3(b)所示。

#### 2.4 时序自注意力机制

CNN和BiLSTM模块能够有效提取局部时序特征和捕捉双向依赖关系,但在建模全局时序关联性方面,特别是在跨时间步的重要信息识别上存在一定局限性。为此,引入时序自注意力机制,通过分配不同时间步的注意力权重,引导模型聚焦于关键

时间信息,从而提升整体预测性能。TSA模块的数据处理步骤如下:

(1) 对BiLSTM的输出序列 Xn进行线性变换:

$$Q = X_{Bi} \mathbf{W}_{O}, \quad K = X_{Bi} \mathbf{W}_{K}, \quad V = X_{Bi} \mathbf{W}_{V}$$
 (18)

(2) 通过点积注意力机制计算各时间步之间的相关性得分,并进行归一化处理:

$$A = Softmax \left( \frac{Q \cdot K^{T}}{\sqrt{d}} \right)$$
 (19)

(3) 通过残差连接与层归一化进行特征输出:

$$Y = LayerNorm(X_{Bi} + A \cdot V)$$
 (20)

式(18)-(20)中:  $Q \setminus K \setminus V$ 分别为查询、键和值矩阵; W为权重矩阵; A为注意力权重矩阵; d为每个时间步的特征维度; Y为加权特征矩阵。

#### 2.5 时序卷积网络

TCN作为一种针对时间序列数据的深度学习网络,通过结合因果卷积与扩张卷积,能够在保留数据前后因果关系的前提下,扩展卷积核的范围,有效捕捉长期时间依赖关系,其结构如图4所示。为降低TCN对噪声数据的敏感性,引入软阈值机制。机制基于输入数据的统计特征设定动态阈值,将小于阈值的特征值置为0,从而削弱无效信息的干扰,其数学公式如下:

$$\hat{x} = \begin{cases} x - \lambda, & x > \lambda \\ 0, & |x| \le \lambda \\ x + \lambda, & x < -\lambda \end{cases}$$
 (21)

式中:  $\hat{x}$  为软阈值化后的特征值; x 为输入特征值;  $\lambda$  为动态阈值。

![](_page_4_Figure_32.jpeg)

图4 TCN结构图

Fig. 4 Structure of TCN

## 3 实验分析

### 3.1 数据集与特征分析

秦岭终南山公路隧道北起西安市青盆村、南至 商洛市柞水县,是国高网包头至茂名高速公路

(G65)的控制性工程。实验使用的交通流数据集源 自隧道内车辆检测器的检测记录。记录内容涵盖了 检测起止时间、断面方向、车型、交通流量等多个 字段。数据集的时间跨度为 2023年 7月 1日至 8月 31日,采样汇总间隔为 1 h。该时段交通流量与气 候条件相对稳定,且未发生重大交通管制事件,能 够避免极端天气或外部事件对交通流规律的干扰。 此外,为更好地研究流量周期性规律,对不具有完 整周结构的时段(7 月 1 日至 2 日、8 月 28 日至 31 日)进行剔除。而8月21日至27日因原始数据缺失 严重也进行剔除处理。因此,实验筛选西线(西安 至安康方向)7月3日至8月20日7周完整的数据作 为基础,总计 1176 个时间节点。结合 《公路工程 技术标准》(JTG B01—2014)对六类车型流量进行 标准车流量折算,车辆折算系数见表1。

鉴于不同类型车辆在运行特性、交通行为上存 在差异,实验将折算后的数据集分为客车和货车两 类。数据集前 6周交通流变化趋势如图 5所示。其 中,8月1日12:00-14:00、8月12日3:00-5:00

表1 标准车折算系数

Table 1 Passenger car equivalency factors

| 数据集划分 | 车型    | 折算系数 | 说明           |
|-------|-------|------|--------------|
| 客车流量  | 中小客车  | 1. 0 | 座位≤19座       |
|       | 大型客车  | 1. 5 | 座位>19座       |
| 货车流量  | 小型货车  | 1. 0 | 载质量≤2t       |
|       | 中型货车  | 1. 5 | 2 t<载质量≤7 t  |
|       | 大型货车  | 3. 0 | 7 t<载质量≤20 t |
|       | 特大型货车 | 4. 0 | 载质量>20 t     |

和8月13日0:00-1:00及3:00-4:00等时段存在 数据缺失,而 7 月 21 日 18:00-19:00、7 月 28 日 21:00-22:00、8 月 1 日 0:00-1:00、8 月 4 日 7:00-9:00和8月7日9:00-10:00等时段存在数 据异常,这可能是由检测设备故障、数据传输异常 或隧道运营临时管控等因素引起。除去缺失值和异 常值的影响,工作日交通流表现出明显的周期性特 征,而休息日(特别是星期六)交通流则呈现出异质 性的演化趋势(即在相同的时间节点上,交通流量 的变化存在显著差异,呈现较强的非规律性与不确 定性)。

![](_page_5_Figure_9.jpeg)

Fig. 5 Tendency of variation in traffic flow for different vehicle categories

图6为一周内不同时段的平均小时流量变化趋 势。在工作日,客车与货车流量均呈现出一定的日 周期特征,且两者流量占比均衡;而在休息日,两 者的变化趋势则相对分化,具体表现为:客车流量 显著上升,成为主要交通构成部分,而货车流量则

小幅下降,通行需求有所减少。

为进一步验证划分和样本量的合理性,从统计 特征角度对两类数据进行对比分析,包括基本统计 量(均值、标准差、变异系数)、分布特征(偏度、 峰度)、平稳性检验(ADF检验)以及基于等效独立

![](_page_6_Figure_3.jpeg)

图 6 不同车型平均交通流量

Fig. 6 The average traffic volume for different vehicle categories

样本量的功效分析等,具体结果见表2。从基本统 计量来看,两类数据的均值水平接近,但客车流量 的标准差与变异系数明显高于货车流量,表明客车 交通流波动性更强,受时段或其他外部因素的影响 更为显著。从分布特征来看,客车流量的偏度为 0.59, 峰度为0.12, 分布轻微右偏且具有尖峰, 存 在流量陡增现象;而货车流量的偏度为0.06、峰度 为-0.83,分布近似对称且偏平,极端流量值较少。 从平稳性检验的结果来看,客车流量序列平稳,更 具规律性与周期性; 而货车流量序列非平稳, 可能 存在趋势性成分,需要进一步数据处理。综上所 述,两类数据在统计特征上存在显著差异,将其作 为独立子类进行建模与分析是合理的。而从功效分 析来看,两类数据对中等效应量(Cohen's d =0.5)的检验功效分别达到 0.91 和 0.85, 可以认为 当前样本量足以支持对中等及以上效应的检验。

表2 统计特征对比 Table 2 Statistical feature comparison

| 类别        | 客车      | 货车      |
|-----------|---------|---------|
| 均值        | 389. 14 | 408. 52 |
| 标准差       | 271. 74 | 147. 65 |
| 变异系数      | 0. 69   | 0.36    |
| 偏度        | 0. 59   | 0.06    |
| 峰度        | 0. 12   | -0. 83  |
| ADF检验(p值) | 0. 02   | 0. 53   |
| 检验功效      | 0.91    | 0.85    |
|           |         |         |

#### 3.2 实验设置

IDLM 是在 Python 3.8.19 环境下,基于 Py-Torch 框架,并使用 PyCharm 平台进行开发。CNN 模块的卷积层为2、池化层数为1,卷积核大小为3,卷积核个数分别为16、32,池化窗口大小为2。BiLSTM 模块的层数为3,隐藏层单元个数为32。

TCN模块的结构层数为3,每层通道数为32,卷积核大小为3,扩张因子分别为1、2、4。模型的迭代次数为200,时间窗口大小为24,批大小为32,学习率为1e-3,Dropout为0.3,采用Adam优化器和SmoothL1Loss损失函数优化训练误差,为避免过拟合,采用早停机制,容忍轮数设为30。

考虑交通流的时序特性,数据集按照5:1:1 的比例划分为训练集、验证集和测试集,以满足模型训练和效果评估的需求。选择均方根误差 (Root Mean Squared Error, RMSE)和加权平均绝对百分比误差(Weighted Mean Absolute Percentage Error, WMAPE)作为两类评价指标,计算公式分别为:

$$RMSE = \sqrt{\frac{1}{M} \sum_{i=1}^{M} (y_i - \hat{y}_i)^2}$$
 (22)

$$WMAPE = \frac{\sum_{i=1}^{M} |y_i - \hat{y}_i|}{\sum_{i=1}^{M} y_i}$$
 (23)

式中: M为测试集序列长度;  $y_i$ 和 $\hat{y}_i$ 分别为第i时刻流量的实测值和预测值。

#### 3.3 实验结果分析

#### 3.3.1 降噪处理及残差预测

对非平稳数据进行高斯降噪处理,降噪结果如图 7 所示。与原始数据相比,降噪后数据的 RMSE 为 43.02 pcu,WMAPE 为 8.22%,ADF 检验结果为 p=0.01。考虑到降噪处理可能导致局部细节的丢失,实验基于 TCN 对残差数据进行建模,以补偿局部变化特征。图 8 为残差预测结果,可以看出模型能够有效捕捉残差数据保留的扰动特征,同时整体拟合保持在合理范围内,避免对无效信息建模。

#### 3.3.2 模型预测效果对比

为验证所提方法在公路隧道交通流预测中的精

![](_page_6_Figure_21.jpeg)

图7 高斯降噪效果

Fig. 7 Results of Gaussian Smoothing

![](_page_7_Figure_3.jpeg)

图8 残差预测结果可视化

Fig. 8 Visualization of residual prediction results

确 性 , 将 IDLM 与 ARIMA、 RF、 BiLSTM、 CNN-BiLSTM (C-Bi)和 CNN-BiLSTM-TSA (C-Bi-T)进 行 对比分析。

图9为各模型对总体流量进行一周连续预测的

性能评估。可以观察到,相比 ARIMA、RF,BiL⁃ STM通过在正向与反向时间轴上建模流量数据的时 间依赖性,在处理长期依赖关系方面表现更出色, 其 RMSE 和 WMAPE 分 别 平 均 降 低 了 约 7. 33%、 7. 47%。C-Bi通过融合一维卷积神经网络,有效提 取交通流数据中相邻时间步的局部特征(如短期突 变与周期波动),使RMSE和WMAPE分别进一步降 低了 3. 26%、2. 36%。C-Bi-T则通过引入专为时序 数据设计的注意力机制TSA,通过保留时间顺序的 先后关系,自适应地为不同时间步分配权重,使模 型 更 关 注 重 要 时 刻 , 预 测 误 差 又 分 别 降 低 了 1. 37%、4. 27%。IDLM 则在上述基础上通过对不 同类型数据分别建模以及残差补偿方式,获得最优 预测精度,相比基准模型,RMSE 和 WMAPE 分别 平均降低了约33. 99%、35. 44%。

![](_page_7_Figure_9.jpeg)

图9 不同模型的预测性能评估

Fig. 9 Performance evaluation of predictions by different models

从预测稳定性来看,IDLM 的 RMSE 为 46. 82± 13. 06 pcu,WMAPE 为 4.71%±1. 70%。不考虑模型 对 8 月 14 日初始状态敏感带来的误差,IDLM 的 RMSE 为 42. 29±5. 66 pcu, WMAPE为 4. 18% ± 1. 06%,较基准模型最优值(64. 28±7. 84 和 6. 57% ±1. 08%),具有更高的预测精度和更稳定的性能。

表3为各模型对不同车型交通流预测结果的评 估。在客车流量预测中,通过逐步融合不同深度学 习模块可提升预测精度,IDLM 相较最优基准模型 的精度提升幅度约为6. 36%、5. 90%。而在货车流 量预测中,由于降噪过程削弱了货车数据的非线性 波动,使得单一模型(如ARIMA与BiLSTM)在提取 整体趋势或周期性成分方面表现较好,但 IDLM仍 具有最优的预测精度。这主要得益于集成模型的残 差补偿机制:主干网络基于降噪数据捕捉非平稳数 据的长期趋势,而残差补偿模块则基于残差数据提

|         | 表3<br>不同车型交通流预测结果评估                                                            |
|---------|--------------------------------------------------------------------------------|
| Table 3 | Evaluation of traffic flow prediction results for different vehicle categories |

| 模型     | 客车     |        | 货车     |        |
|--------|--------|--------|--------|--------|
|        | RMSE   | WMAPE  | RMSE   | WMAPE  |
| ARIMA  | 61. 80 | 12. 87 | 38. 98 | 7. 58  |
| RF     | 48. 69 | 8. 88  | 54. 71 | 10. 26 |
| BiLSTM | 47. 92 | 8. 89  | 44. 17 | 8. 64  |
| C-Bi   | 44. 19 | 8. 25  | 45. 43 | 8. 86  |
| C-Bi-T | 42. 60 | 8. 14  | 46. 34 | 8. 96  |
| IDLM   | 39. 89 | 7. 66  | 27. 52 | 5. 23  |

取局部扰动特征,补偿降噪处理产生的特征丢失。 从预测结果来看,与具有相同主干结构的C-Bi-T相 比,残差补偿机制为 IDLM 带来的精度提升约为 40. 61%、41. 62%,而与最优基准模型相比,精度 提升幅度约为29. 40%、31. 00%。

### 3. 3. 3 预测效果可视化

为更直观地比较 IDLM 与其他深度学习模型的 预测效果,对隧道西线 2023年 8月 14日至 20日的 实测流量数据和各模型的预测数据进行可视化处 理,结果如图 10 所示。从整体预测效果来看,所 有模型均能有效挖掘交通流周期变化规律,尤其对 变化幅度较大的时间段(如早高峰的上升阶段和晚 高峰后的下降阶段),预测曲线有较强的拟合效果。 各模型预测精度的差异主要在流量的谷值和峰值时 段。其中,BiLSTM 在谷值时段的拟合效果较差, 具体表现为预测值明显偏离实测值;IDLM 在峰值 时段对趋势变化的捕捉更为准确,滞后响应程度低 于其他模型,说明其具有更强的动态适应能力。

# 3. 4 消融实验

为分析各模块对所提模型性能的贡献,设计了 五组消融实验:w/o partition(去除数据划分)、w/o GS(替换高斯平滑降噪)、w/o CNN(去除 CNN 模 块)、w/o TSA(去除TSA模块)、w/o TCN(去除残差 补偿模块)。IDLM及其变体模型在公路隧道数据集 上的预测性能见表4。

可以看出,相较 IDLM,各变体模型对总体流 量的预测精度出现了不同程度的下降,表明各组 成部分对模型性能均有积极贡献。其中,TCN 模 块的性能贡献最大,移除后两类误差分别增大了 26. 97%、35. 00%,说明该模块在对降噪后扰动信 息建模及局部动态特征捕捉中发挥核心作用,是 模型性能提升的关键;而 TSA 模块的移除同样使 得模型性能显著下降,说明时序自注意力机制在 建模长时依赖关系和优化特征权重分配方面具有

![](_page_8_Figure_11.jpeg)

![](_page_8_Figure_12.jpeg)

![](_page_8_Figure_13.jpeg)

# (b) 客车交通流预测

![](_page_8_Figure_15.jpeg)

### (c) 货车交通流预测

图10 不同模型预测结果可视化

Fig. 10 Visualization of prediction results from different mod⁃ els

表4 消融实验结果

Table 4 Results of ablation experiment

| 模型            | RMSE(pcu) | WMAPE(%) |
|---------------|-----------|----------|
| w/o partition | 49. 88    | 5. 17    |
| w/o GS        | 53. 62    | 5. 18    |
| w/o CNN       | 52. 78    | 5. 14    |
| w/o TSA       | 56. 48    | 5. 41    |
| w/o TCN       | 61. 42    | 6. 21    |
| IDLM          | 48. 37    | 4. 60    |

重要贡献;相较之下,高斯平滑降噪方法和 CNN 模块对模型性能的贡献不及前两者,但合适的预 处理方法与卷积结构有助于模型提取交通流趋势 与空间特征;数据划分方法虽对模型整体性能贡 献最小,但通过趋势与统计特征分析划分数据, 能有效降低输入信息的复杂性,为深层模型提供 更清晰的交通流特征分布,从而进一步增强模型 稳定性。

# 4 结论

本文提出一种基于集成深度学习模型 IDLM 的 公路隧道交通流预测方法,得到的主要结论如下:

- (1)考虑交通流变化趋势与流量数据统计特征 的数据划分方法,可以减少不同交通组成间的信息 干扰,提升模型对各车型时序特征的表达能力。通 过主干网络(CNN-BiLSTM-TSA)提取交通流数据的 趋势特征,并引入基于TCN的残差补偿模块,恢复 降噪过程丢失的局部扰动信息,可以获得更高精度 的预测结果。
- (2)在一周连续预测的对比实验中,IDLM 对 初始状态存在一定敏感性,但评价指标仍优于其他 方法。在稳定状态下,IDLM 对总体流量预测的 RMSE 为 42. 29±5. 66 pcu, WMAPE 为 4. 18± 1. 06%,相较最优基准模型,预测精度提升约2. 39 个百分比。
- (3)消融实验验证了模型中数据划分、高斯平 滑降噪、卷积神经网络、时序自注意力机制和残差 补偿模块这五个组件,对模型预测精度的提升均起 到了不同程度的作用,其中残差补偿模块和时序自 注意力机制对预测精度提升最为显著。
- (4)下一步将结合多隧道与多区域交通数据, 对模型的泛化能力进行验证,同时在不同时间粒度 下引入气象、事故等多源影响因素,探讨模型在复 杂交通场景下的稳定性与适应性。

### 参考文献:

- [1] 田俊山, 曾俊铖, 丁峰, 等 . 基于时空关系的高速 公路交通流量预测 [J] . 工程科学学报, 2024,46 (09): 1623-1629.
  - TIAN Jun Shan, CENG Jun Cheng, DING Feng, et al. Highway traffic flow forecasting based on spatiotempo⁃ ral relationship [J] . Chinese Journal of Engineering, 2024,46(09): 1623-1629.
- [2] 王九胜, 许辉, 缪中岩 . 基于时空关系的多细粒度 隧道交通流预测模型研究与应用 [J] . 公路交通科 技, 2024,41(11): 86-93. WANG Jiu Sheng, XU Hui, MOU Zhong Yan. Study
  - and Application of Multi Fine-grained Tunnel Traffic Flow Prediction Model Based on Spatio-temporal Relation [J] . Journal of Highway and Transportation Research and Development, 2024,41(11): 86-93.
- [3] 苏开春, 付锐, 曾弘锐, 等 . 基于 DBO-A-LSTM 的 公 路 隧 道 短 时 多 步 交 通 量 预 测 [J] . 现 代 隧 道 技 术, 2025,62(4): 111-121.
  - SU Kai chun, FU Rui, CENG Hong rui, et al. Shortterm Multi-step Traffic Volume Prediction for Highway Tunnels Based on DBO-A-LSTM [J] . Modern Tunnel⁃ ling Technology, 2025,62(4): 111-121.
- [4] 崔建勋, 要甲, 赵泊媛 . 基于深度学习的短期交通 流预测方法综述 [J] . 交通运输工程学报, 2024, 24(2): 50-64. CUI Jian Xun, YAO Jia, ZHAO Bo Yuan. Review on short-term traffic flow prediction methods based on deep learning [J] . Journal of Traffic and Transportation Engi⁃
- [5] SHAHRIARI S, GHASRI M, SISSON S A, et al. En⁃ semble of ARIMA: combining parametric and bootstrap⁃ ping technique for traffic flow prediction [J] . Transport⁃ metrica A Transport Science, 2020, 16(3): 1552- 1573.

neering, 2024,24(2): 50-64.

- [6] EMAMI A, SARVI M, BAGLOEE S A. Using Kalman filter algorithm for short-term traffic flow prediction in a connected vehicle environment [J] . JOURNAL OF MODERN TRANSPORTATION, 2019, 27 (3) : 222-232.
- [7] LIN G, LIN A, GU D. Using support vector regression and K-nearest neighbors for short-term traffic flow predic⁃ tion based on maximal information coefficient [J] . In⁃ formation sciences, 2022,608: 517-531.
- [8] 田佳, 王德勇, 师文喜 . 基于集合经验模态分解和 随 机 森 林 的 短 时 交 通 流 预 测 [J] . 科 学 技 术 与 工 程, 2023,23(29): 12612-12619.

- TIAN Jia, WANG De yong, SHI Wen xi. Short-term traffic flow forecasting based on EEMD and random forest [J] . Science Technology and Engineering, 2023,23 (29): 12612-12619.
- [9] 段中兴, 杜婉欣 . 基于 GWO-LSTM 模型的隧道车流 量预测与照明调节研究 [J] . 现代隧道技术, 2024, 61(3): 157-165. DUAN Zhong Xing, DU Wan Xin. Study on Tunnel Traf⁃ fic Flow Prediction and Lighting Regulation Based on GWO-LSTM Model [J] . Modern Tunnelling Technol⁃
- [10] BHARTI, REDHU P, KUMAR K. Short-term traffic flow prediction based on optimized deep learning neural network: PSO-Bi-LSTM [J] . Physica A, 2023, 625: 129001.

ogy, 2024,61(3): 157-165.

- [11] MÉNDEZ M, MERAYO M G, NÚÑEZ M. Long-term traffic flow forecasting using a hybrid CNN-BiLSTM model [J] . Engineering Applications of Artificial Intel⁃ ligence, 2023,121: 106041.
- [12] 李桃迎, 王婷, 张羽琪. 考虑多特征的高速公路交 通流预测模型 [J] . 交通运输系统工程与信息, 2021,21(3): 101-111. LI Tao Ying, WANG Ting, ZHANG Yu Qi. Highway Traffic Flow Prediction Model with Multi-features [J] . Journal of Transportation Systems Engineering and Infor⁃ mation Technology, 2021,21(3): 101-111.

- [13] 戢晓峰, 孔晓丽, 陈方, 等 . 基于 ETC 数据和 A-BiLSTM神经网络的高速公路节假日短时交通流预测 模 型 [J] . 交 通 信 息 与 安 全 , 2023, 41(3): 166-174.
  - JI Xiao Feng, KONG Xiao Li, CHEN Fang, et al. A Forecasting Model of Short-term Traffic Flow on Ex⁃ pressways During Holidays Based on ETC Data and A-BiLSTM Neural Network Models [J] . Journal of Trans⁃ port Information and Safety, 2023,41(3): 166-174.
- [14] REN Q, LI Y, LIU Y. Transformer-enhanced peri⁃ odic temporal convolution network for long short-term traffic flow forecasting [J] . Expert Systems with Appli⁃ cations, 2023,227: 120203.
- [15] ZENG H, DONG C, FU R, et al. A gated Recurrent unit considering spatial correlation for short-term traffic volume forecasting in highway tunnels [J] . Engineer⁃ ing Applications of Artificial Intelligence, 2025, 159: 111796.
- [16] 钱超, 陈建勋, 罗彦斌, 等. 基于随机森林的公路 隧道运营缺失数据插补方法 [J] . 交通运输系统工 程与信息, 2016,16(03): 81-87. QIAN Chao, CHEN Jian xun, LUO Yan bin, et al. Random Forest Based Operational Missing Data Imputa⁃ tion for Highway Tunnel [J] . Journal of Transportation Systems Engineering and Information Technology, 2016,16(03): 81-87.

# Integrated Deep Learning Model Based Traffic Flow Prediction for Highway Tunnel

*QIAN Chao*<sup>1</sup> *LI Jun*<sup>1</sup> *LI Faqiang*<sup>2</sup> *ZHAO Yichen*<sup>1</sup> *ZHOU Zhongwen*<sup>2</sup> *LIU Yice*<sup>1</sup> *CHENG Jianying*<sup>2</sup> (1. School of Electronics and Control Engineering, Chang'an University, Xi'an 710064, Shaanxi, China;2. Hainan Jia⁃ okong Technology Co. , Ltd. , Haikou 570203, Hainan, China)

Abstract:Traffic flow prediction for highway tunnels is a crucial technical foundation for rationally optimizing tun⁃ nel operation and management strategies. To address the nonlinearity, spatiotemporal coupling of traffic flow data, and the loss of disturbance information during noise reduction, a highway tunnel traffic flow prediction model com⁃ bining trend modeling and residual compensation is proposed. Firstly, based on the analysis of the trend and statis⁃ tical characteristics of traffic flow data, the original data is divided into two categories: passenger cars and trucks. Secondly, combined with the stationarity test results, the Gaussian Smoothing method is applied to denoise the nonstationary data. Then, both the stationary and denoised data are input into a backbone network that integrates the Convolutional Neural Network, the Bidirectional Long Short-Term Memory network and the Temporal Self-Attention mechanism to extract trend features, and the Temporal Convolutional Network is introduced to model the residual data to restore the disturbance features with temporal structure lost during denoising. Finally, the trend features and disturbance features are fused to generate the final prediction results. The hourly traffic volume data of the Qinling Zhongnanshan Highway Tunnel is used for model training and testing. The experimental results show that in the

continuous prediction of the overall traffic volume, the Root Mean Square Error of the prediction by the Integrated Deep Learning Model is 42. 29±5. 66 pcu, and the Weighted Mean Absolute Percentage Error is 4. 18%±1. 06%. Compared with the best results of other prediction models (64. 28±7. 84 pcu, 6. 57%±1. 08%), the two types of errors are reduced by 34. 20% and 36. 37%, respectively. In the ablation experiment, the residual compensation module has the most significant impact on the model performance, reducing the two types of errors by 26. 97% and 35. 00%, respectively. The research results provide a theoretical basis for dynamic traffic flow prediction in intelli⁃ gent transportation systems of highway tunnels.

Key words:intelligent transportation;traffic flow prediction;deep learning;highway tunnel;residual modeling

![](_page_11_Picture_5.jpeg)