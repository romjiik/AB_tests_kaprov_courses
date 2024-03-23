import numpy as np
import pandas as pd


class MetricsService:

    def calculate_linearized_metrics(
        self, control_metrics, pilot_metrics, control_user_ids=None, pilot_user_ids=None
    ):
        """Считает значения метрики отношения.

        Нужно вычислить параметр kappa (коэффициент в функции линеаризации) по данным из
        control_metrics и использовать его для вычисления линеаризованной метрики.

        :param control_metrics (pd.DataFrame): датафрейм со значениями метрики контрольной группы.
            Значения в столбце 'user_id' не уникальны.
            Измерения для одного user_id считаем зависимыми, а разных user_id - независимыми.
            columns=['user_id', 'metric']
        :param pilot_metrics (pd.DataFrame): датафрейм со значениями метрики экспериментальной группы.
            Значения в столбце 'user_id' не уникальны.
            Измерения для одного user_id считаем зависимыми, а разных user_id - независимыми.
            columns=['user_id', 'metric']
        :param control_user_ids (list): список id пользователей контрольной группы, для которых
            нужно рассчитать метрику. Если None, то использовать пользователей из control_metrics.
            Если для какого-то пользователя нет записей в таблице control_metrics, то его
            линеаризованная метрика равна нулю.
        :param pilot_user_ids (list): список id пользователей экспериментальной группы, для которых
            нужно рассчитать метрику. Если None, то использовать пользователей из pilot_metrics.
            Если для какого-то пользователя нет записей в таблице pilot_metrics, то его
            линеаризованная метрика равна нулю.
        :return lin_control_metrics, lin_pilot_metrics: columns=['user_id', 'metric']
        """

        control_data = control_metrics.groupby('user_id').agg(x=('metric', 'sum'), y=('metric', 'count')).reset_index()
        pilot_data = pilot_metrics.groupby('user_id').agg(x=('metric', 'sum'), y=('metric', 'count')).reset_index()

        kappa = np.sum(control_data['x']) / np.sum(control_data['y'])

        control_users = pd.Series(control_user_ids).to_frame(name='user_id')
        pilot_users = pd.Series(pilot_user_ids).to_frame(name='user_id')

        control_data = control_users.merge(control_data, how='left', on='user_id').fillna(0).copy() if control_user_ids is not None else control_data.copy()
        pilot_data = pilot_users.merge(pilot_data, how='left', on='user_id').fillna(0).copy()  if pilot_user_ids is not None else pilot_data.copy()

        control_data['metric'] = control_data['x'] - kappa * control_data['y']
        pilot_data['metric'] = pilot_data['x'] - kappa * pilot_data['y']

        return control_data[['user_id', 'metric']], pilot_data[['user_id', 'metric']]



def _chech_df(df, df_ideal, sort_by, reindex=False, set_dtypes=False, decimal=None):
    assert isinstance(df, pd.DataFrame), 'Функция вернула не pd.DataFrame.'
    assert len(df) == len(df_ideal), 'Неверное количество строк.'
    assert len(df.T) == len(df_ideal.T), 'Неверное количество столбцов.'
    columns = df_ideal.columns
    assert df.columns.isin(columns).sum() == len(df.columns), 'Неверное название столбцов.'
    df = df[columns].sort_values(sort_by)
    df_ideal = df_ideal.sort_values(sort_by)
    if reindex:
        df_ideal.index = range(len(df_ideal))
        df.index = range(len(df))
    if set_dtypes:
        for column, dtype in df_ideal.dtypes.to_dict().items():
            df[column] = df[column].astype(dtype)
    if decimal:
        ideal_values = df_ideal.astype(float).values
        values = df.astype(float).values
        np.testing.assert_almost_equal(ideal_values, values, decimal=decimal)
    else:
        assert df_ideal.equals(df), 'Итоговый датафрейм не совпадает с верным результатом.'


if __name__ == '__main__':
    control_metrics = pd.DataFrame({'user_id': [1, 1, 2], 'metric': [3, 5, 7],})
    pilot_metrics = pd.DataFrame({'user_id': [3, 3], 'metric': [3, 6], })
    ideal_lin_control_metrics = pd.DataFrame({'user_id': [1, 2], 'metric': [-2, 2],})
    ideal_lin_pilot_metrics = pd.DataFrame({'user_id': [3,], 'metric': [-1,],})

    metrics_service = MetricsService()
    lin_control_metrics, lin_pilot_metrics = metrics_service.calculate_linearized_metrics(
        control_metrics, pilot_metrics
    )
    _chech_df(lin_control_metrics, ideal_lin_control_metrics, ['user_id', 'metric'], True, True, decimal=3)
    _chech_df(lin_pilot_metrics, ideal_lin_pilot_metrics, ['user_id', 'metric'], True, True, decimal=3)
    print('simple test passed')

