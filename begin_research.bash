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
# polish plan
alpha-rl-resume-planning \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="max_env_worker: 64 -> 128, max_num_seqs->1024, revise your plan accordingly"
# confirm execution
alpha-rl-begin-experiments \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="permission granted, begin research"

# resume from broken (without context)
alpha-rl-new-planning \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="Look at what you have done!!!  Yaml is all wrong, refer to agentjet/ajet/default_config/ajet_default.yaml, do not use actor_rollout_ref"



## topic 02-resume from blueprints
# resume from broken (without context)
alpha-rl-new-planning \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="Double check planning, polish current plan."
alpha-rl-begin-experiments \
    --runner=ssh \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="permission granted, begin research"


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