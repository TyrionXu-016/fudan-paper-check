import type { Issue, IssueTypeKey, Paper, Rule, Stage, TypeMeta } from '../types'

export const TYPE_META: Record<IssueTypeKey, TypeMeta> = {
  FORMAT: { label: '格式规范', color: '#0f766e', bg: '#ccfbf1', short: '格' },
  TYPO: { label: '错别字', color: '#b91c1c', bg: '#fee2e2', short: '错' },
  GRAMMAR: { label: '语法病句', color: '#9333ea', bg: '#f3e8ff', short: '语' },
  POLISH: { label: '学术润色', color: '#0369a1', bg: '#e0f2fe', short: '润' },
  SPLIT: { label: '断句拆分', color: '#c2410c', bg: '#ffedd5', short: '句' },
  PARA_LOGIC: { label: '段落逻辑', color: '#4f46e5', bg: '#e0e7ff', short: '段' },
  LOGIC: { label: '逻辑一致性', color: '#be123c', bg: '#ffe4e6', short: '逻' },
}

export const GROUP_ORDER: IssueTypeKey[] = [
  'FORMAT',
  'TYPO',
  'GRAMMAR',
  'POLISH',
  'SPLIT',
  'PARA_LOGIC',
  'LOGIC',
]

export const STAGES: Stage[] = [
  { id: 'PARSE', label: '解析论文结构', pct: 12 },
  { id: 'FORMAT_CHECK', label: '检查格式规范', pct: 35 },
  { id: 'TYPO_CHECK', label: '识别错别字', pct: 52 },
  { id: 'GRAMMAR_CHECK', label: '检查语法病句', pct: 66 },
  { id: 'POLISH', label: '生成润色建议', pct: 78 },
  { id: 'LOGIC_CHECK', label: '校验逻辑一致性', pct: 90 },
  { id: 'REFERENCE_CHECK', label: '核对参考文献', pct: 96 },
  { id: 'DONE', label: '检测完成', pct: 100 },
]

export const RULES: Rule[] = [
  {
    id: 'generic',
    name: '通用论文规范',
    short: '通用',
    version: 'v1.0',
    summary: {
      格式规范: ['标题、摘要、关键词结构完整', '图表公式编号连续', '参考文献格式清晰'],
      错别字: ['识别常见中文错别字', '检查术语前后一致性'],
      学术润色: ['减少口语化表达', '提升句子精炼度'],
      参考文献: ['检查引用与文末条目匹配', '提示 GB/T 7714 著录风险'],
    },
  },
  {
    id: 'fudan_university',
    name: '复旦大学论文规范',
    short: '复旦',
    version: '2026 预检版',
    summary: {
      格式规范: ['封面、摘要、关键词、目录、正文结构完整', '图表公式编号连续且引用一致', '中英文摘要和关键词信息对应'],
      错别字: ['检查错别字、术语混用和标点误用', '识别中英文混排中的常见格式问题'],
      学术润色: ['保持客观、严谨、学术化表达', '提示长句拆分和摘要结论措辞优化'],
      参考文献: ['检查正文引用与文末条目对应', '提示著录字段缺失和编号体系不一致'],
    },
  },
  {
    id: 'scut_natural_science',
    name: '华南理工自然科学版',
    short: '华工',
    version: '2026 模板',
    summary: {
      格式规范: ['摘要、关键词、中图分类号、DOI 齐备', '图题表题和公式编号规范'],
      错别字: ['面向学术论文场景检查易混词'],
      学术润色: ['保持客观、严谨、第三人称表述'],
      参考文献: ['按 GB/T 7714 提醒著录项缺失'],
    },
  },
]

export const ISSUES: Issue[] = [
  {
    id: 'issue-format-doi',
    type: 'FORMAT',
    severity: 'high',
    location: '首页 DOI',
    summary: 'DOI 中存在多余空格',
    before: '10. 12141/j. issn.1000-565X.250274',
    after: '10.12141/j.issn.1000-565X.250274',
    explain: '规范要求 DOI 连续书写，空格会影响检索和引用。',
    spanId: 'abs-1',
  },
  {
    id: 'issue-typo-model',
    type: 'TYPO',
    severity: 'med',
    location: '摘要第 1 句',
    summary: '“模形”疑似错别字',
    before: '本文提出一种集成深度学习模形。',
    after: '本文提出一种集成深度学习模型。',
    explain: '上下文讨论的是机器学习模型，此处应使用“模型”。',
    spanId: 'abs-2',
  },
  {
    id: 'issue-polish-long',
    type: 'POLISH',
    severity: 'low',
    location: '第 1 节第 1 段',
    summary: '句子偏长，可拆分提升可读性',
    before: '随着交通流预测需求持续提升本文方法能够在复杂场景下取得较稳定表现。',
    after: '随着交通流预测需求持续提升，本文方法在复杂场景下取得了较稳定的表现。',
    explain: '增加停顿并调整语序后，句意更清晰。',
    spanId: 'sec1-1',
  },
  {
    id: 'issue-logic-value',
    type: 'LOGIC',
    severity: 'med',
    location: '摘要与实验结论',
    summary: '摘要指标与实验结论不一致',
    before: '摘要称平均误差降低 42.29%。',
    after: '请核对实验结论中的 40.29% 与摘要的 42.29%。',
    explain: '同一核心指标在不同位置不一致，需要作者确认最终数值。',
    spanId: 'sec2-1',
  },
]

export const PAPER: Paper = {
  title: '基于集成深度学习模型的公路隧道交通流预测',
  author: '张明',
  abstract: [
    [
      '摘 要：',
      {
        spanId: 'abs-1',
        original: '10. 12141/j. issn.1000-565X.250274',
        suggested: '10.12141/j.issn.1000-565X.250274',
        issueId: 'issue-format-doi',
      },
      '。针对公路隧道交通流短时预测问题，',
      {
        spanId: 'abs-2',
        original: '本文提出一种集成深度学习模形。',
        suggested: '本文提出一种集成深度学习模型。',
        issueId: 'issue-typo-model',
      },
      '实验表明，该方法能够提升预测稳定性。',
    ],
  ],
  sections: [
    {
      heading: '1 引言',
      paragraphs: [
        [
          {
            spanId: 'sec1-1',
            original: '随着交通流预测需求持续提升本文方法能够在复杂场景下取得较稳定表现。',
            suggested: '随着交通流预测需求持续提升，本文方法在复杂场景下取得了较稳定的表现。',
            issueId: 'issue-polish-long',
          },
          '相关研究表明，融合多源特征有助于改善短时预测结果。',
        ],
      ],
      paragraphLogic: { issueId: 'issue-polish-long', position: 'between-1-2' },
    },
    {
      heading: '2 实验与分析',
      paragraphs: [
        [
          {
            spanId: 'sec2-1',
            original: '摘要称平均误差降低 42.29%，但实验结论记录为 40.29%。',
            suggested: '请核对平均误差降低幅度，并统一摘要与实验结论中的数值。',
            issueId: 'issue-logic-value',
          },
          '建议在定稿前回查原始实验表格。',
        ],
      ],
    },
  ],
}

export const SPAN_INDEX = Object.fromEntries(
  [
    ...PAPER.abstract.flat(),
    ...PAPER.sections.flatMap((section) => section.paragraphs.flat()),
  ]
    .filter((node): node is Exclude<(typeof PAPER.abstract)[number][number], string> =>
      typeof node === 'object' && node !== null,
    )
    .map((node) => [node.spanId, node]),
)
