#!/bin/bash

# clone code
git clone https://github.com/modelscope/AgentJet.git codebase/agentjet


## topic 01
# plan first
alpha-rl-new-planning \
    --runner=ssh \
    --research-topic="research_topic/example_01_content_madness_detect.md"
# confirm execution
alpha-rl-begin-experiments \
    --runner=ssh \
    --research-topic="research_topic/example_01_content_madness_detect.md" \
    --resume-instruction="permission granted, begin research"



## topic 02
# plan first
alpha-rl-new-planning \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md"
# confirm execution
alpha-rl-begin-experiments \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="permission granted, begin research"

# resume from broken (without context)
alpha-rl-new-planning \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="Experiment submission failed, but now the problem resolved, try again."



## topic 02-resume from blueprints
# resume from broken (without context)
alpha-rl-new-research-no-human \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md"
alpha-rl-resume-experiment \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="Why don't you try to analyze all possible outcomes while the experiment is running. write a report and keep waiting for the experiment result."



## topic 03
# plan first
alpha-rl-new-planning \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md"
# polish plan
alpha-rl-resume-planning \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="polish your plan"
# confirm execution
alpha-rl-begin-experiments \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="permission granted, begin research"

# resume from broken (without context)
alpha-rl-new-planning \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="Double check planning, revise it."
#
alpha-rl-resume-experiment \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="the experiment is finished, write report"

# finalize
alpha-rl-new-planning \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="the experiment is finished, write report"
alpha-rl-resume-planning \
    --runner=pai \
    --research-topic="research_topic/example_03_appworld.md" \
    --resume-instruction="use seaborn! show as many details as possible, make it look good! write report in markdown format with figures included."








## topic 04
# plan first
ccfq \
alpha-rl-new-planning \
    --runner=pai \
    --research-topic="research_topic/example_04_ppo_epoch.md"


## topic 04
# plan first
alpha-rl-new-research-no-human \
    --runner=pai \
    --research-topic="research_topic/example_04_ppo_epoch.md"


## topic 05
# plan first
alpha-rl-new-research-no-human \
    --runner=ssh \
    --research-topic="research_topic/example_05_regular_test.md"

#
alpha-rl-resume-experiment \
    --runner=pai \
    --research-topic="research_topic/example_05_regular_test.md" \
    --resume-instruction="the experiment is running, keep monitoring"




alpha-rl-new-research-no-human \
    --runner=ssh \
    --research-topic="research_topic/example_06_ppo_epoch_and_minibatch.md"
