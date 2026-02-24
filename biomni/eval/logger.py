import json
import sqlite3
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

try:
    import wandb
except ImportError:
    wandb = None


class BaseLogger(ABC):
    @abstractmethod
    def log_config(self, config: Dict[str, Any]):
        """Log experiment configuration."""
        pass

    @abstractmethod
    def log_result(self, result: Dict[str, Any]):
        """Log a single evaluation result."""
        pass

    @abstractmethod
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log aggregated metrics."""
        pass

    @abstractmethod
    def finish(self):
        """Clean up and save final artifacts."""
        pass


class SQLiteLogger(BaseLogger):
    def __init__(self, db_path: str = str(Path("data") / "biomni_eval.db"), experiment_name: str = "default"):
        self.db_path = db_path
        self.experiment_name = experiment_name
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.experiment_id = None
        self._setup_db()
        self._create_experiment()

    def _setup_db(self):
        cursor = self.conn.cursor()

        # Experiments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            benchmark_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            config JSON
        )
        """)

        # Results table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER,
            task_name TEXT,
            instance_id TEXT,
            prompt TEXT,
            prediction TEXT,
            ground_truth TEXT,
            score REAL,
            success BOOLEAN,
            error TEXT,
            trajectory JSON,
            metrics JSON,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(experiment_id) REFERENCES experiments(id)
        )
        """)

        self.conn.commit()

    def _create_experiment(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO experiments (name, timestamp) VALUES (?, ?)", (self.experiment_name, datetime.now())
        )
        self.experiment_id = cursor.lastrowid
        self.conn.commit()
        print(f"Started SQLite experiment ID: {self.experiment_id}")

    def log_config(self, config: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE experiments SET config = ?, benchmark_id = ? WHERE id = ?",
            (json.dumps(config, default=str), config.get("benchmark_id", "unknown"), self.experiment_id),
        )
        self.conn.commit()

    def log_result(self, result: Dict[str, Any]):
        cursor = self.conn.cursor()

        # Extract fields
        task_name = result.get("task_name")
        instance_id = str(result.get("instance_id"))
        prompt = result.get("prompt")
        prediction = str(result.get("prediction"))
        ground_truth = str(result.get("ground_truth"))
        score = result.get("score", 0.0)
        success = bool(result.get("success", False))
        error = result.get("error")
        trajectory = json.dumps(result.get("trajectory", []), default=str)
        metrics = json.dumps(result.get("metrics", {}), default=str)

        cursor.execute(
            """
        INSERT INTO results (
            experiment_id, task_name, instance_id, prompt, prediction, 
            ground_truth, score, success, error, trajectory, metrics
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.experiment_id,
                task_name,
                instance_id,
                prompt,
                prediction,
                ground_truth,
                score,
                success,
                error,
                trajectory,
                metrics,
            ),
        )
        self.conn.commit()

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        # SQLite logger stores per-instance metrics in `results` table.
        # Global metrics can be computed from the table or stored in a separate table if needed.
        # For now, we rely on the `results` table for aggregation.
        pass

    def finish(self):
        self.conn.close()
        print(f"SQLite logging finished. Database: {self.db_path}")


class WandBLogger(BaseLogger):
    def __init__(
        self,
        project: str = "biomni-eval",
        entity: Optional[str] = None,
        name: Optional[str] = None,
        config: Optional[Dict] = None,
    ):
        if wandb is None:
            raise ImportError("wandb is not installed. Please install it with `pip install wandb`.")

        self.run = wandb.init(project=project, entity=entity, name=name, config=config, reinit=True)
        self.results_table = wandb.Table(
            columns=[
                "task_name",
                "instance_id",
                "prompt",
                "prediction",
                "ground_truth",
                "score",
                "success",
                "error",
                "trajectory_length",
            ]
        )

    def log_config(self, config: Dict[str, Any]):
        wandb.config.update(config, allow_val_change=True)

    def log_result(self, result: Dict[str, Any]):
        # Log basic metrics
        metrics = {
            f"{result['task_name']}/score": result.get("score", 0.0),
            f"{result['task_name']}/success": int(result.get("success", False)),
            "global_step": wandb.run.step,
        }

        # Add custom metrics from the result
        if "metrics" in result:
            for k, v in result["metrics"].items():
                metrics[f"{result['task_name']}/{k}"] = v

        wandb.log(metrics)

        # Add to table
        trajectory = result.get("trajectory", [])
        self.results_table.add_data(
            result.get("task_name"),
            str(result.get("instance_id")),
            result.get("prompt"),
            str(result.get("prediction")),
            str(result.get("ground_truth")),
            result.get("score", 0.0),
            result.get("success", False),
            result.get("error"),
            len(trajectory),
        )

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        wandb.log(metrics, step=step)

    def finish(self):
        # Log the final table
        wandb.log({"evaluation_results": self.results_table})
        wandb.finish()


class MultiLogger(BaseLogger):
    def __init__(self, loggers: List[BaseLogger]):
        self.loggers = loggers

    def log_config(self, config: Dict[str, Any]):
        for logger in self.loggers:
            logger.log_config(config)

    def log_result(self, result: Dict[str, Any]):
        for logger in self.loggers:
            logger.log_result(result)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        for logger in self.loggers:
            logger.log_metrics(metrics, step)

    def finish(self):
        for logger in self.loggers:
            logger.finish()
