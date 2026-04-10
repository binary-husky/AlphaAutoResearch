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
    --resume-instruction="- actor_rollout_ref.actor.kl_loss_coef: The coefficient of kl loss. Default is 0.001.- actor_rollout_ref.actor.kl_loss_type: Support kl(k1), abs, mse(k2), low_var_kl(k3) and full. Appending "+" in the end (e.g., 'k1+' and 'k3+') would apply straight through to employ k2 for unbiased gradient estimation, regardless of the kl value estimation (see https://github.com/volcengine/verl/pull/2953#issuecomment-3162113848 for more details). How to calculate the kl divergence between actor and reference policy. See this blog post for detailed analysis: http://joschu.net/blog/kl-approx.html"
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