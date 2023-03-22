'''
@Author: WANG Maonan
@Date: 2022-08-17 13:16:46
@Description: 测试 Choose Phase 的结果
@LastEditTime: 2023-03-22 22:34:41
'''
import os
import shutil
import torch
import itertools
import argparse

from aiolos.utils.get_abs_path import getAbsPath
from aiolos.trafficLog.initLog import init_logging
from stable_baselines3 import A2C, PPO
from stable_baselines3.common.vec_env import VecNormalize, SubprocVecEnv

from lib import makeENV

if __name__ == '__main__':
    pathConvert = getAbsPath(__file__)
    init_logging(log_path=pathConvert('./'), log_level=0)

    # 路网参数
    parser = argparse.ArgumentParser("Run Choose Next Phase experiments.")
    parser.add_argument("--net_folder", type=str, required=True, help="路网的文件夹.")
    parser.add_argument("--net_id", type=str, required=True, help="不同的信号灯组合.")
    parser.add_argument("--delta_times", required=True, help="做动作的间隔.")

    args = parser.parse_args()
    net_folder, net_id = args.net_folder, args.net_id
    if args.delta_times == 'None':
        delta_times = None # 在传入环境的时候, 如果是 None 那么就 5s 控制一次
    else:
        delta_times = int(args.delta_times) # 做动作的间隔

    # 其他模型参数
    MODEL_TYPEs = ['best', 'last'] # best, last
    route_ids = ['stable', 'fluctuation']
    # MODEL_TYPEs = ['best', 'last'] # best, last
    # route_ids = ['stable']
    
    for MODEL_TYPE ,route_id in itertools.product(*[MODEL_TYPEs, route_ids]):
        print(f'===> 开始分析, {MODEL_TYPE}, {route_id}')
        # #######
        # 训练参数
        # #######    
        NUM_CPUS = 1
        MIN_GREEN = 5
        SHFFLE = False # 是否进行数据增强
        MODEL_NAME = 'PPO' # 后面选择算法
        MODEL_FOLDER = pathConvert(f'./models/{delta_times}/{net_folder}/{net_id}/{route_id}/')
        MODEL_PATH = os.path.join(MODEL_FOLDER, f'{MODEL_TYPE}_model.zip')
        VEC_NORM = os.path.join(MODEL_FOLDER, f'{MODEL_TYPE}_vec_normalize.pkl')
        LOG_PATH = pathConvert(f'./log/{delta_times}/{net_folder}/{net_id}/{route_id}/') 
        if not os.path.exists(LOG_PATH):
            os.makedirs(LOG_PATH)
            
        # 初始化环境
        tls_id = 'htddj_gsndj'
        sumo_cfg = pathConvert(f'../nets/{net_folder}/env/single_junction.sumocfg')
        net_file = pathConvert(f'../nets/{net_folder}/env/{net_id}.net.xml')
        route_list = [pathConvert(f'../nets/{net_folder}/routes/{route_id}.rou.xml')]
        # output 统计文件
        output_folder = pathConvert(f'./testResult/{delta_times}/{net_folder}/{net_id}/{route_id}/{MODEL_TYPE}')
        os.makedirs(output_folder, exist_ok=True) # 创建文件夹
        trip_info = os.path.join(output_folder, f'tripinfo.out.xml')
        statistic_output = os.path.join(output_folder, f'statistic.out.xml')
        summary = os.path.join(output_folder, f'summary.out.xml')
        queue_output = os.path.join(output_folder, f'queue.out.xml')
        tls_add = [
            # 探测器
            pathConvert(f'../nets/{net_folder}/detectors/e1_internal.add.xml'),
            pathConvert(f'../nets/{net_folder}/detectors/e2.add.xml'),
            # 信号灯
            pathConvert(f'../nets/{net_folder}/add/tls_programs.add.xml'),
            pathConvert(f'../nets/{net_folder}/add/tls_state.add.xml'),
            pathConvert(f'../nets/{net_folder}/add/tls_switch_states.add.xml'),
            pathConvert(f'../nets/{net_folder}/add/tls_switches.add.xml')
        ]
        params = {
            'tls_id':tls_id,
            'num_seconds':7000,
            'sumo_cfg':sumo_cfg,
            'net_file':net_file,
            'route_files':route_list,
            'is_shuffle':SHFFLE, # 不进行数据增强
            'is_libsumo':False,
            'use_gui':False,
            'min_green':MIN_GREEN,
            'delta_times':5 if delta_times == None else delta_times,
            'log_file':LOG_PATH,
            'trip_info':trip_info,
            'statistic_output':statistic_output,
            'summary':summary,
            'queue_output':queue_output,
            'tls_state_add': tls_add,
            'mode':'eval' # 不要对环境进行 reset
        }
        env = SubprocVecEnv([makeENV.make_env(env_index=f'evaluate_{i}', **params) for i in range(NUM_CPUS)])
        env = VecNormalize.load(load_path=VEC_NORM, venv=env) # 加载环境 Norm 参数
        env.training = False # 测试的时候不要更新
        env.norm_reward = False
        # 加载模型
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if MODEL_NAME == 'A2C':
            model = A2C.load(MODEL_PATH, env=env, device=device)
        else:
            model = PPO.load(MODEL_PATH, env=env, device=device)
        # 使用模型进行测试
        obs = env.reset()
        done = False # 默认是 False

        total_reward = 0
        while not done:
            action, _state = model.predict(obs, deterministic=True)
            # action = np.array([env.action_space.sample()]) # 随机动作
            obs, reward, done, info = env.step(action)
            total_reward += reward
        print(f'{MODEL_TYPE}, {route_id}, 累计奖励为, {reward}')
            
        env.close()

        # 把 add 文件复制到 testResult 文件夹下
        shutil.copytree(
            src=pathConvert(f'../nets/{net_folder}/add/'),
            dst=f'{output_folder}/add/',
            dirs_exist_ok=True # 有文件夹则覆盖
        )