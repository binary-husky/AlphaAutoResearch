#!/bin/bash
# Entry point for launching the research leader agent.
# Usage: bash begin_research.bash --blueprint=<path> [--attach=<url>] [--additional-prompt=<text>]


python -m rl_auto_research.opencode_runner leader \
    --skill="skills/leader_experiment.md" \
    "$@"


# python opencodex_leader.py run \
#     --attach=http://localhost:4096 \
#     --blueprint="/foo/bar/topic_07_math/ajet_auto_research_multi_experiment.md" \
#     --additional-prompt="注意：当前进度处于stage 1蓝图任务已经全部提交, 有些任务仍然在排队, 请先等待stage 1结束"