import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats


class Design(BaseModel):
    """Дата-класс с описание параметров эксперимента.

    statistical_test - тип статтеста. ['ttest', 'bootstrap']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    stratification - постстратификация. 'on' - использовать постстратификация, 'off - не использовать.
    """
    statistical_test: str = 'ttest'
    effect: float = 3.
    alpha: float = 0.05
    beta: float = 0.1
    stratification: str = 'off'


class ExperimentsService:

    def _ttest_strat(self, metrics_strat_a_group, metrics_strat_b_group):
        """Применяет постстратификацию, возвращает pvalue.

        Веса страт считаем по данным обеих групп.
        Предполагаем, что эксперимент проводится на всей популяции.
        Веса страт нужно считать по данным всей популяции.

        :param metrics_strat_a_group (np.ndarray): значения метрик и страт группы A.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param metrics_strat_b_group (np.ndarray): значения метрик и страт группы B.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return (float): значение p-value
        """
        df_a = pd.DataFrame(metrics_strat_a_group, columns=['metric', 'strat'])
        df_b = pd.DataFrame(metrics_strat_b_group, columns=['metric', 'strat'])
        df = pd.concat([df_a, df_b])

        strats_share = df['strat'].value_counts(normalize=True)

        mean_a = (df_a.groupby('strat')['metric'].mean() * strats_share).sum()
        mean_b = (df_b.groupby('strat')['metric'].mean() * strats_share).sum()

        var_a = (df_a.groupby('strat')['metric'].var() * strats_share).sum()
        var_b = (df_b.groupby('strat')['metric'].var() * strats_share).sum()

        delta = mean_b - mean_a
        std = (var_a / len(df_a) + var_b / len(df_b)) ** 0.5

        t = delta / std
        p_val = (1 - stats.norm.cdf(np.abs(t))) * 2
        return p_val

    def get_pvalue(self, metrics_strat_a_group, metrics_strat_b_group, design):
        """Применяет статтест, возвращает pvalue.

        :param metrics_strat_a_group (np.ndarray): значения метрик и страт группы A.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param metrics_strat_b_group (np.ndarray): значения метрик и страт группы B.
            shape = (n, 2), первый столбец - метрики, второй столбец - страты.
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return (float): значение p-value
        """
        if design.statistical_test == 'ttest':
            if design.stratification == 'off':
                _, pvalue = stats.ttest_ind(metrics_strat_a_group[:, 0], metrics_strat_b_group[:, 0])
                return pvalue
            elif design.stratification == 'on':
                return self._ttest_strat(metrics_strat_a_group, metrics_strat_b_group)
            else:
                raise ValueError('Неверный design.stratification')
        else:
            raise ValueError('Неверный design.statistical_test')


if __name__ == '__main__':
    metrics_strat_a_group = np.zeros((10, 2,))
    metrics_strat_a_group[:, 0] = np.arange(10)
    metrics_strat_a_group[:, 1] = (np.arange(10) < 4).astype(float)
    metrics_strat_b_group = np.zeros((10, 2,))
    metrics_strat_b_group[:, 0] = np.arange(1, 11)
    metrics_strat_b_group[:, 1] = (np.arange(10) < 5).astype(float)
    design = Design(stratification='on')
    ideal_pvalue = 0.037056

    experiments_service = ExperimentsService()
    pvalue = experiments_service.get_pvalue(metrics_strat_a_group, metrics_strat_b_group, design)

    np.testing.assert_almost_equal(ideal_pvalue, pvalue, decimal=4, err_msg='Неверное значение pvalue')
    print('simple test passed')





