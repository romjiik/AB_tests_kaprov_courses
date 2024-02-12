import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats
from scipy.stats import ttest_ind


class Design(BaseModel):
    """Дата-класс с описание параметров эксперимента.
    
    statistical_test - тип статтеста. ['ttest']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    sample_size - размер групп
    """
    statistical_test: str = 'ttest'
    effect: float
    alpha: float = 0.05
    beta: float = 0.1
    sample_size: int


class ExperimentsService:

    def get_pvalue(self, metrics_a_group, metrics_b_group, design):
        """Применяет статтест, возвращает pvalue.
        
        :param metrics_a_group (np.array): массив значений метрик группы A
        :param metrics_a_group (np.array): массив значений метрик группы B
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return (float): значение p-value
        """
        if design.statistical_test == 'ttest':
            _, pvalue = stats.ttest_ind(metrics_a_group, metrics_b_group)
            return pvalue
        else:
            raise ValueError('Неверный design.statistical_test')

    def _create_group_generator(self, metrics, sample_size, n_iter):
        """Генератор случайных групп.

        :param metrics (pd.DataFame): таблица с метриками, columns=['user_id', 'metric'].
        :param sample_size (int): размер групп (количество пользователей в группе).
        :param n_iter (int): количество итераций генерирования случайных групп.
        :return (np.array, np.array): два массива со значениями метрик в группах.
        """
        user_ids = metrics['user_id'].unique()
        for _ in range(n_iter):
            a_user_ids, b_user_ids = np.random.choice(user_ids, (2, sample_size), False)
            a_metric_values = metrics.loc[metrics['user_id'].isin(a_user_ids), 'metric'].values
            b_metric_values = metrics.loc[metrics['user_id'].isin(b_user_ids), 'metric'].values
            yield a_metric_values, b_metric_values

    def _estimate_errors(self, group_generator, design, effect_add_type):
        """Оцениваем вероятности ошибок I и II рода.

        :param group_generator: генератор значений метрик для двух групп.
        :param design (Design): объект с данными, описывающий параметры эксперимента.
        :param effect_add_type (str): способ добавления эффекта для группы B.
            - 'all_const' - увеличить всем значениям в группе B на константу (b_metric_values.mean() * effect / 100).
            - 'all_percent' - увеличить всем значениям в группе B в (1 + effect / 100) раз.
        :return pvalues_aa (list[float]), pvalues_ab (list[float]), first_type_error (float), second_type_error (float):
            - pvalues_aa, pvalues_ab - списки со значениями pvalue
            - first_type_error, second_type_error - оценки вероятностей ошибок I и II рода.
        """
        pvalues_aa = []
        pvalues_ab = []
        # итерируемся по группам
        for metric_values in group_generator:
            a_metric_values, b_metric_values = metric_values[0], metric_values[1]
            # считаем аа
            _, pval_aa = ttest_ind(a_metric_values, b_metric_values)
            pvalues_aa.append(pval_aa)
            # считаем аб
            if effect_add_type == 'all_const':
                b_metric_values = b_metric_values + (b_metric_values.mean() * design.effect / 100)
            else:
                b_metric_values = b_metric_values * (1 + design.effect / 100)
            _, pval_ab = ttest_ind(a_metric_values, b_metric_values)
            pvalues_ab.append(pval_ab)
        # оцениваем вероятности ошибок
        first_type_error = (np.array(pvalues_aa) < design.alpha).mean()
        second_type_error = (np.array(pvalues_ab) >= design.alpha).mean()
        return pvalues_aa, pvalues_ab, first_type_error, second_type_error

    def estimate_errors(self, metrics, design, effect_add_type, n_iter):
        """Оцениваем вероятности ошибок I и II рода.

        :param metrics (pd.DataFame): таблица с метриками, columns=['user_id', 'metric'].
        :param design (Design): объект с данными, описывающий параметры эксперимента.
        :param effect_add_type (str): способ добавления эффекта для группы B.
            - 'all_const' - увеличить всем значениям в группе B на константу (b_metric_values.mean() * effect / 100).
            - 'all_percent' - увеличить всем значениям в группе B в (1 + effect / 100) раз.
        :param n_iter (int): количество итераций генерирования случайных групп.
        :return pvalues_aa (list[float]), pvalues_ab (list[float]), first_type_error (float), second_type_error (float):
            - pvalues_aa, pvalues_ab - списки со значениями pvalue
            - first_type_error, second_type_error - оценки вероятностей ошибок I и II рода.
        """
        group_generator = self._create_group_generator(metrics, design.sample_size, n_iter)
        return self._estimate_errors(group_generator, design, effect_add_type)


if __name__ == '__main__':
    _a = np.array([1., 2, 3, 4, 5])
    _b = np.array([1., 2, 3, 4, 10])
    group_generator = ([a, b] for a, b in ((_a, _b),))
    design = Design(effect=50., sample_size=5)
    effect_add_type = 'all_percent'

    ideal_pvalues_aa = [0.579584]
    ideal_pvalues_ab = [0.260024]
    ideal_first_type_error = 0.
    ideal_second_type_error = 1.

    experiments_service = ExperimentsService()
    pvalues_aa, pvalues_ab, first_type_error, second_type_error = experiments_service._estimate_errors(
        group_generator, design, effect_add_type
    )
    np.testing.assert_almost_equal(ideal_pvalues_aa, pvalues_aa, decimal=4)
    np.testing.assert_almost_equal(ideal_pvalues_ab, pvalues_ab, decimal=4)
    assert ideal_first_type_error == first_type_error
    assert ideal_second_type_error == second_type_error
    print('simple test passed')