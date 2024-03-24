import json

import numpy as np
import pandas as pd


def calculate_metrics(data: pd.DataFrame):
    df_elevator_logs = data.copy()
    for str_colums in ['calls', 'orders']:
        df_elevator_logs[str_colums] = [
            json.loads(line.replace('(', '[').replace(')', ']'))
            for line in df_elevator_logs[str_colums].values
        ]
        df_elevator_logs[str_colums] = [
            [tuple(x) for x in row]
            for row in df_elevator_logs[str_colums].values
        ]
        
    df_ = (
        df_elevator_logs
        [df_elevator_logs[['user_in', 'user_out']].sum(axis=1) > 0]
        .drop('action', axis=1)
        .copy()
    )

    history = []
    # [[время посадки, этаж посадки, возможные этажи назначения, время окончания], ...]
    # [[time_begin, begin_floor, end_floors, time_end=None], ...]
    state_elevator = []
    for time_, out_, in_, total_, floor_, calls_, orders_ in df_.values:

        # ВЫХОДЫ
        len_old_ = len(history)
        count_out = 0     # количество вышедших
        new_state_ = []
        # Итерируемся по людям в лифте, если есть с точным выходом на этом этаже, то "убираем их"
        for time_begin, begin_floor, end_floors in state_elevator:
            if (len(end_floors) == 1) and (end_floors[0] == floor_):
                count_out += 1
                history.append((time_begin, begin_floor, end_floors, time_,))
            else:
                new_state_.append((time_begin, begin_floor, end_floors,))
        state_elevator = new_state_
        # если вышло больше, чем количество людей с точно определённым этажом, то идём по неточным
        if count_out < out_:
            new_state_ = []
            for time_begin, begin_floor, end_floors in sorted(state_elevator, key=lambda x: x[0]):
                if (floor_ in end_floors) and (count_out < out_):
                    count_out += 1
                    history.append((time_begin, begin_floor, end_floors, time_,))
                else:
                    new_state_.append((time_begin, begin_floor, end_floors,))
            state_elevator = new_state_

        len_new_ = len(history)

        # ЗАХОДЫ
        if in_ == 0:
            continue
        prev_calls = df_elevator_logs[df_elevator_logs['time'] == time_ - 10]['calls'].values[0]
        prev_orders = df_elevator_logs[df_elevator_logs['time'] == time_ - 10]['orders'].values[0]

        # найдём самое раннее время вызова на этот этаж
        prev_calls_with_cur_floor = [t for t, floor in prev_calls if floor == floor_]
        first_time_begin = prev_calls_with_cur_floor[0] if prev_calls_with_cur_floor else time_
        # times = [first_time_begin] if in_ == 1 else np.linspace(first_time_begin, time_, in_)
        # времена вызова, если зашедших много
        times = (
            [first_time_begin] if in_ == 1
            # else np.linspace(first_time_begin, time_ - (time_ - first_time_begin) / in_, in_)
            else np.linspace(first_time_begin, time_, in_)
        )
        np.random.shuffle(times)

        # найдём новые заказы, чтобы узнать куда хотят ехать зашедшие
        prev_order_floors = [floor for _, floor in prev_orders]
        cur_order_floors = [floor for _, floor in orders_]
        new_order_floors = list(set(cur_order_floors) - set(prev_order_floors) - {floor_})
        len_ = len(new_order_floors)
        for time, floor in zip(times[:len_], new_order_floors):
            state_elevator.append((time, floor_, [floor],))
            cur_order_floors = list(set(cur_order_floors) | {floor})
        for time in times[len_:]:
            state_elevator.append((time, floor_, cur_order_floors,))

    metric_my = np.array([end - begin for begin, _, _, end in history])
    return metric_my