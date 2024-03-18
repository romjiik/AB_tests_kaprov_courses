class SplittingService:

    def __init__(self, buckets_count):
        """Класс для распределения экспериментов и пользователей по бакетам.

        :param buckets_count (int): количество бакетов.
        """
        self.buckets_count = buckets_count
        self.buckets = [[] for _ in range(buckets_count)]

    def add_experiment(self, experiment):
        """Проверяет можно ли добавить эксперимент, добавляет если можно.

        :param experiment (Experiment): параметры эксперимента, который нужно запустить
        :return success, buckets:
            success (boolean) - можно ли добавить эксперимент, True - можно, иначе - False
            buckets (list[list[int]]]) - список бакетов, в каждом бакете перечислены идентификаторы эксперименты,
                которые в нём проводятся.
        """
        # список из элементов [bucket_id, количество совместных экспериментов]
        available_buckets_meta = []
        for bucket_id, bucket in enumerate(self.buckets):
            if set(experiment.conflicts) & set(bucket):
                continue
            available_buckets_meta.append((bucket_id, len(bucket)))
        if len(available_buckets_meta) < experiment.buckets_count:
            return False, self.buckets
        sorted_available_buckets_meta = sorted(available_buckets_meta, key=lambda x: -x[1])
        for bucket_id, _ in sorted_available_buckets_meta[:experiment.buckets_count]:
            self.buckets[bucket_id].append(experiment.id)
        return True, self.buckets
