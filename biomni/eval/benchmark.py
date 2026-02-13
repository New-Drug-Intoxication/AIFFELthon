from abc import ABC, abstractmethod
from typing import Any, Dict, List

from biomni.eval.biomni_eval1 import BiomniEval1


class Benchmark(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @abstractmethod
    def get_tasks(self) -> List[str]:
        """Return a list of task names."""
        pass

    @abstractmethod
    def get_instances(self, task_name: str, split: str = "val") -> List[Dict[str, Any]]:
        """Return a list of instances for a given task."""
        pass

    @abstractmethod
    def evaluate_result(self, task_name: str, instance: Dict[str, Any], prediction: Any) -> float:
        """Evaluate a single result and return a score (0.0 to 1.0)."""
        pass


class BiomniEval1Adapter(Benchmark):
    def __init__(self):
        self.evaluator = BiomniEval1()
        self._id = "biomni_eval1"

    @property
    def id(self) -> str:
        return self._id

    def get_tasks(self) -> List[str]:
        return self.evaluator.list_tasks()

    def get_instances(self, task_name: str, split: str = "val") -> List[Dict[str, Any]]:
        # BiomniEval1 dataframe has columns: instance_id, task_instance_id, task_name, split, prompt, answer
        df = self.evaluator.get_instances_by_task(task_name, split)
        instances = []
        for _, row in df.iterrows():
            instances.append(
                {
                    "instance_id": row["instance_id"],  # Global ID
                    "task_instance_id": row["task_instance_id"],  # Task-local ID needed for evaluate()
                    "prompt": row["prompt"],
                    "ground_truth": row["answer"],
                    "task_name": row["task_name"],
                }
            )
        return instances

    def evaluate_result(self, task_name: str, instance: Dict[str, Any], prediction: Any) -> float:
        # BiomniEval1.evaluate takes (task_name, task_instance_id, user_answer)
        return self.evaluator.evaluate(task_name, instance["task_instance_id"], prediction)


# Placeholder for future benchmarks
class LabBenchAdapter(Benchmark):
    @property
    def id(self) -> str:
        return "lab_bench"

    def get_tasks(self) -> List[str]:
        raise NotImplementedError("LabBench not yet implemented")

    def get_instances(self, task_name: str, split: str = "val") -> List[Dict[str, Any]]:
        raise NotImplementedError("LabBench not yet implemented")

    def evaluate_result(self, task_name: str, instance: Dict[str, Any], prediction: Any) -> float:
        raise NotImplementedError("LabBench not yet implemented")


class BixBenchAdapter(Benchmark):
    @property
    def id(self) -> str:
        return "bixbench"

    def get_tasks(self) -> List[str]:
        raise NotImplementedError("BixBench not yet implemented")

    def get_instances(self, task_name: str, split: str = "val") -> List[Dict[str, Any]]:
        raise NotImplementedError("BixBench not yet implemented")

    def evaluate_result(self, task_name: str, instance: Dict[str, Any], prediction: Any) -> float:
        raise NotImplementedError("BixBench not yet implemented")
