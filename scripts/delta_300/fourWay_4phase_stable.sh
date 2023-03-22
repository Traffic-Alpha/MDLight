#!/bin/sh
###
 # @Author: WANG Maonan
 # @Date: 2022-08-22 21:40:18
 # @Description: 训练所有的动作
 # sbatch -J fourWay_4phase_stable_delta300 -p CPU -n 1 -c 30 -w st-node-159 fourWay_4phase_stable.sh > node_159_stable.log &
 # @LastEditTime: 2022-08-22 21:59:13
###

FOLDER="/mnt/nfs/data/wangmaonan/ActionsVSScenarios"

python ${FOLDER}/ChooseNextPhase/train.py --net_folder=fourWay --net_id=4phases --route_id=stable --delta_times=300
echo '完成 Choose Next Phase 的训练'

python ${FOLDER}/CyclePhaseAdjust_Discrete/train.py --net_folder=fourWay --net_id=4phases --route_id=stable --delta_times=300
echo '完成 Cycle Phase Adjustment (Discrete) 的训练'

python ${FOLDER}/CyclePhaseAdjust_MultiDiscrete/train.py --net_folder=fourWay --net_id=4phases --route_id=stable --delta_times=300
echo '完成 Cycle Phase Adjustment (Multi-Discrete) 的训练'

python ${FOLDER}/CycleSinglePhaseAdjust/train.py --net_folder=fourWay --net_id=4phases --route_id=stable --delta_times=300
echo '完成 Cycle Single Phase Adjustment 的训练'

python ${FOLDER}/NextorNot/train.py --net_folder=fourWay --net_id=4phases --route_id=stable --delta_times=300
echo '完成 Next or Not 的训练'

python ${FOLDER}/SetCurrentPhaseDuration/train.py --net_folder=fourWay --net_id=4phases --route_id=stable --delta_times=300
echo '完成 Set Phase Duration 的训练'