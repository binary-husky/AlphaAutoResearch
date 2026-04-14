

## 第一阶段

针对当前的auto research进展，写一篇学术文章，使用markdown格式，包含 Introduction，Preliminary，Experiment，Conslusion


Introduction: 介绍 Alpha Auto Research，即本项目，主要是这个系统是如何执行自动化研究的，以及它的目标和意义。可以提到自动化研究在加速科学发现和创新方面的重要性。
Preliminary：介绍研究主题，注意需要web search，介绍相关的研究背景和现有的工作
Experiment：Auto Research 的步骤和结果
Conslusion：结论

默认语言：中文

强调：必须图文并茂，需要包含解释结果所需的曲线、表格、示意图等，并且需要对结果进行分析和解释，不能只展示结果，还要分析结果背后的原因和意义

写入 article_version_1.md 文件中

## 第二阶段

检查所有图表，确保它们绘制无误、布局无误、清晰美观、结论明显。

如果有问题，重新绘制并校验。

从基本的训练曲线和训练图表中，进行更深层的分析，发掘更多细节和规律，并绘制更具体的seaborn图标验证这些规律。

写入 article_version_2.md 文件中

## 第三阶段

- 使用以下skill生成炫酷的封面图
alpha_auto_research/skills/banana_image

- 检查一下章节、小节之间的衔接，如果衔接不好，进行润色修改。必要时，每个小节开头都要有一个过渡段，介绍一下这一小节的内容和它与前一小节的关系。

- 对不合理的表述进行修改，确保你是在跟读者沟通，而不是机械地完成任务。
  - 例如 “> 生成日期：2026-04-14” 这个是不合理的表述，因为它没有什么意义，读者也不关心这个日期，要予以移除。
  - 再例如 “与 v1 的差别：基于...” 这就很荒谬，你认为读者关心文章有没有 v1 版本吗？
  - 再比如 “**Alpha Auto Research（本项目）** 是一个面向大模...” 这个表述也不合理，因为读者并不知道什么是 Alpha Auto Research，所以你应该直接介绍 Alpha Auto Research 是什么，而不是先说它是“本项目”，再在后面介绍它是什么。总之，你要确保你的表述是合理的，能够让读者理解你的意思，而不是让读者感到困惑或者无聊。
  - 举一反三，找到其他类似的表述，并进行修改。

- 有些内容需要做成示意图（例如流程图、架构图等），以帮助读者更直观地理解复杂的概念和过程。例如 “PPO 在每个迭代中 ... 1, 2, 3 ppo_epochs ...mini_batch_num ...”，在文字表述的同时，需要用 banana_image 生成流程图并highlight这些参数如何起作用。另外这是GRPO训练，而不是PPO

- 把所有的图片通过以上的 skill 上传到图床中，方便分享和传输：使用图床处理所有图片
  alpha_auto_research/skills/banana_image

写入 article_version_3.md 文件中
