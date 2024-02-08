import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy import stats
from scipy.stats import norm, ttest_ind


class Design(BaseModel):
    """Дата-класс с описание параметров эксперимента.
    
    statistical_test - тип статтеста. ['ttest']
    effect - размер эффекта в процентах
    alpha - уровень значимости
    beta - допустимая вероятность ошибки II рода
    """
    statistical_test: str
    effect: float
    alpha: float
    beta: float


class ExperimentsService:

    def get_sample_size(self, mu, std, effect, alpha=0.05, beta=0.2):
        epsilon = effect / 100 * mu
        t_alpha = norm.ppf(1 - alpha / 2, loc=0, scale=1)
        t_beta = norm.ppf(1 - beta, loc=0, scale=1)
        z_scores_sum_squared = (t_alpha + t_beta) ** 2
        sample_size = int(
            np.ceil(
                z_scores_sum_squared * (2 * std ** 2) / (epsilon ** 2)
            )
        )
        return sample_size

    def estimate_sample_size(self, metrics, design):
        """Оцениваем необходимый размер выборки для проверки гипотезы о равенстве средних.
        
        Для метрик, у которых для одного пользователя одно значение просто вычислите размер групп по формуле.
        Для метрик, у которых для одного пользователя несколько значений (например, response_time),
            вычислите необходимый объём данных и разделите его на среднее количество значений на одного пользователя.
            Пример, если в таблице metrics 1000 наблюдений и 100 уникальных пользователей, и для эксперимента нужно
            302 наблюдения, то размер групп будет 31, тк в среднем на одного пользователя 10 наблюдений, то получится
            порядка 310 наблюдений в группе.

        :param metrics (pd.DataFrame): датафрейм со значениями метрик из MetricsService.
            columns=['user_id', 'metric']
        :param design (Design): объект с данными, описывающий параметры эксперимента
        :return (int): минимально необходимый размер групп (количество пользователей)
        """
        std = np.std(metrics['metric'])

        cnt_by_user = metrics.groupby('user_id')['metric'].nunique().mean()
        mean = metrics['metric'].mean()
        sample_size = self.get_sample_size(mu=mean, std=std, effect=design.effect,
                                            alpha=design.alpha, beta=design.beta)
        if metrics.shape[0] != metrics['user_id'].nunique():
            return np.ceil(sample_size / cnt_by_user)
        else:
            return sample_size
            



if __name__ == '__main__':
    metrics = pd.DataFrame({
        'user_id': [str(i) for i in range(10)],
        'metric': [i for i in range(10)]
    })
    design = Design(
        statistical_test='ttest',
        alpha=0.05,
        beta=0.1,
        effect=3.
    )
    ideal_sample_size = 9513

    experiments_service = ExperimentsService()
    sample_size = experiments_service.estimate_sample_size(metrics, design)
    assert sample_size == ideal_sample_size, 'Неверно'
    print('simple test passed')