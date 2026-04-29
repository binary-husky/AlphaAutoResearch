#!/bin/bash

# clone code
git clone https://github.com/modelscope/AgentJet.git codebase/agentjet

alpha-new-plan \
    --runner=pai \
    --topic="research_topic/example_11_aime.md"

alpha-resume-plan \
    --runner=pai \
    --topic="research_topic/example_11_aime.md" \
    -r "remove unrelated scripts under agentjet_codebase/tutorial/opencode_build_aime/auto_research and PPO_EPOCH=1 and MINI_BATCH_NUM=1"

alpha-resume \
    --runner=pai \
    --topic="research_topic/example_11_aime.md" \
    -r "permission granted, begin research"


# ## topic 01
# # plan first
# alpha-new-plan \
#     --runner=ssh \
#     --topic="research_topic/example_01_content_madness_detect.md"
# # confirm execution
# alpha-resume \
#     --runner=ssh \
#     --topic="research_topic/example_01_content_madness_detect.md" \
#     -r "permission granted, begin research"



# ## topic 02
# # plan first
# alpha-new-plan \
#     --runner=ssh \
#     --topic="research_topic/example_02_kl_abl.md"
# # confirm execution
# alpha-resume \
#     --runner=ssh \
#     --topic="research_topic/example_02_kl_abl.md" \
#     -r "permission granted, begin research"

# # resume from broken (without context)
# alpha-new-plan \
#     --runner=ssh \
#     --topic="research_topic/example_02_kl_abl.md" \
#     -r "Experiment submission failed, but now the problem resolved, try again."



# ## topic 02-resume from blueprints
# # resume from broken (without context)
# alpha-auto \
#     --runner=ssh \
#     --topic="research_topic/example_02_kl_abl.md"
# alpha-resume \
#     --runner=ssh \
#     --topic="research_topic/example_02_kl_abl.md" \
#     -r "Why don't you try to analyze all possible outcomes while the experiment is running. write a report and keep waiting for the experiment result."



# ## topic 03
# # plan first
# alpha-new-plan \
#     --runner=pai \
#     --topic="research_topic/example_03_appworld.md"
# # polish plan
# alpha-resume-plan \
#     --runner=pai \
#     --topic="research_topic/example_03_appworld.md" \
#     -r "polish your plan"
# # confirm execution
# alpha-resume \
#     --runner=pai \
#     --topic="research_topic/example_03_appworld.md" \
#     -r "permission granted, begin research"

# # resume from broken (without context)
# alpha-new-plan \
#     --runner=pai \
#     --topic="research_topic/example_03_appworld.md" \
#     -r "Double check planning, revise it."
# #
# alpha-resume \
#     --runner=pai \
#     --topic="research_topic/example_03_appworld.md" \
#     -r "the experiment is finished, write report"

# # finalize
# alpha-new-plan \
#     --runner=pai \
#     --topic="research_topic/example_03_appworld.md" \
#     -r "the experiment is finished, write report"
# alpha-resume-plan \
#     --runner=pai \
#     --topic="research_topic/example_03_appworld.md" \
#     -r "use seaborn! show as many details as possible, make it look good! write report in markdown format with figures included."








# ## topic 04
# # plan first
# ccfq \
# alpha-new-plan \
#     --runner=pai \
#     --topic="research_topic/example_04_ppo_epoch.md"


# ## topic 04
# # plan first
# alpha-auto \
#     --runner=pai \
#     --topic="research_topic/example_04_ppo_epoch.md"


# ## topic 05
# # plan first
# alpha-auto \
#     --runner=ssh \
#     --topic="research_topic/example_05_regular_test.md"

# #
# alpha-resume \
#     --runner=pai \
#     --topic="research_topic/example_05_regular_test.md" \
#     -r "the experiment is running, keep monitoring"




# alpha-auto \
#     --runner=ssh \
#     --topic="research_topic/example_06_ppo_epoch_and_minibatch.md"


# alpha-auto \
#     --runner=ssh \
#     --topic="research_topic/example_07_aime_learner.md"

# alpha-auto \
#     --runner=ssh \
#     --topic="research_topic/example_08_werewolves_study.md"


# ## beta
# tmux new -s research
# cd /mnt/data_cpfs/qingxu.fu/alpha_auto_research
# source .venv/bin/activate
# beta research_topic/example_10_supress_log.md