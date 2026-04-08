#!/bin/bash

# clone code
git clone https://github.com/modelscope/AgentJet.git codebase/agentjet


## plan -> human review -> experiment (human-in-the-loop)
`alpha_rl_research_new_planning`      = `python -m rl_auto_research.opencode_runner leader --skip-permissions --only-run-planning`
`alpha_rl_research_resume_planning`   = `python -m rl_auto_research.opencode_runner leader --skip-permissions --resume --only-run-planning`
`alpha_rl_research_begin_experiments` = `python -m rl_auto_research.opencode_runner leader --skip-permissions --resume`
`alpha_rl_research_resume_experiment` = `python -m rl_auto_research.opencode_runner leader --skip-permissions --resume`

## plan -> experiment (human-less)
`alpha_rl_research_new_research_no_human`          = `python -m rl_auto_research.opencode_runner leader --skip-permissions --no-human-in-the-loop`

## topic 01
# plan first
alpha_rl_research_new_planning \
    --research-topic="research_topic/example_01_content_madness_detect.md"
# confirm execution
alpha_rl_research_begin_experiments \
    --research-topic="research_topic/example_01_content_madness_detect.md" \
    --resume-instruction="permission granted, begin research"



## topic 02
# plan first
alpha_rl_research_new_planning \
    --research-topic="research_topic/example_02_kl_abl.md"
# polish plan
alpha_rl_research_resume_planning \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="study kl_type first, ahead of kl coef, try again"
# confirm execution
alpha_rl_research_begin_experiments \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="permission granted, begin research"

# resume from broken (without context)
alpha_rl_research_new_planning \
    --research-topic="research_topic/example_02_kl_abl.md" \
    --resume-instruction="Look at what you have done!!!  Yaml is all wrong, refer to agentjet/ajet/default_config/ajet_default.yaml, do not use actor_rollout_ref"
