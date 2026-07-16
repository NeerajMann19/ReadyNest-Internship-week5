"""
Machine Learning service orchestrating async training tasks and model predictions.
"""
import os
import time
import hashlib
import logging
import joblib
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.exceptions.base import BadRequestException, NotFoundException
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.ml_model import MLModel
from app.models.prediction_log import PredictionLog
from app.repositories.dataset import DatasetRepository
from app.repositories.dataset_version import DatasetVersionRepository
from app.repositories.ml_model import MLModelRepository
from app.repositories.prediction_log import PredictionLogRepository

from app.ml.preprocessing.detector import detect_problem_type
from app.ml.training.trainer import train_champion_model

logger = logging.getLogger(__name__)


class MLService:
    """
    MLService managing model training queues, prediction sandboxes, and logs auditing.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dataset_repo = DatasetRepository(session)
        self.version_repo = DatasetVersionRepository(session)
        self.model_repo = MLModelRepository(session)
        self.log_repo = PredictionLogRepository(session)

    async def create_training_job(
        self,
        user_id: UUID,
        dataset_id: UUID,
        target_column: str,
        features: Optional[List[str]] = None,
        problem_type: Optional[str] = None,
        candidate_algorithms: Optional[List[str]] = None,
        cross_validation: bool = False,
        random_state: int = 42
    ) -> MLModel:
        """
        Creates a training task in PENDING state and returns it.
        """
        # Ownership verification
        dataset = await self.dataset_repo.get_with_versions(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")

        version = next((v for v in dataset.versions if v.is_current), None)
        if not version:
            raise BadRequestException("Dataset contains no active version to train on")

        # Create MLModel metadata record
        next_ver = await self.model_repo.get_next_version_number(version.id)
        
        # Calculate dataset SHA-256 fingerprint
        local_path = version.storage_path.replace("local://", "", 1)
        dataset_hash = None
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                dataset_hash = hashlib.sha256(f.read()).hexdigest()

        # Deduce initial model name/config
        training_config = {
            "train_test_split": 0.2,
            "random_state": random_state,
            "cross_validation": cross_validation,
            "algorithms": candidate_algorithms or ["random_forest", "linear_model", "gradient_boosting"]
        }

        # Retrieve dataset quality score if profile exists
        quality_score = dataset.profile.quality_score if dataset.profile else None

        new_model = MLModel(
            id=uuid4(),
            dataset_id=dataset_id,
            dataset_version_id=version.id,
            model_version=next_ver,
            target_column=target_column,
            features=features or [],
            problem_type=problem_type or "auto",
            model_type="champion_search",
            status="PENDING",
            training_config=training_config,
            dataset_quality_score=quality_score,
            dataset_hash=dataset_hash,
            training_log=[{"timestamp": datetime.now().isoformat(), "message": "Training job created."}]
        )
        
        await self.model_repo.create(new_model)
        await self.session.commit()
        return new_model

    @staticmethod
    async def train_model_task(model_id: UUID) -> None:
        """
        Asynchronous background task executing preprocessing, champion selection,
        and serializing the final model pipeline to disk.
        """
        started_dt = datetime.now()
        started_ms = time.perf_counter()

        # Instantiate fresh session inside background task to ensure safety
        async with async_session() as db_session:
            model_repo = MLModelRepository(db_session)
            version_repo = DatasetVersionRepository(db_session)
            
            model = await model_repo.get(model_id)
            if not model:
                logger.error(f"MLModel training job {model_id} not found in database.")
                return

            model.status = "TRAINING"
            model.started_at = started_dt
            logs = list(model.training_log or [])
            
            def add_log(msg: str):
                logs.append({"timestamp": datetime.now().isoformat(), "message": msg})
                model.training_log = logs

            add_log("Training job initialized. Loading dataset version...")
            await db_session.commit()

            try:
                # Load current dataset version
                version = await version_repo.get(model.dataset_version_id)
                if not version:
                    raise FileNotFoundError("Dataset version metadata not found.")

                local_path = version.storage_path.replace("local://", "", 1)
                if not os.path.exists(local_path):
                    raise FileNotFoundError("Source dataset file missing from storage disk.")

                # Read dataset
                ext = os.path.splitext(local_path)[1].lower()
                if ext == ".csv":
                    df = pd.read_csv(local_path)
                elif ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(local_path)
                else:
                    raise ValueError(f"Unsupported file format '{ext}'")

                # Auto-detect target column type if not overridden
                target_col = model.target_column
                if target_col not in df.columns:
                    raise ValueError(f"Target column '{target_col}' not found in the dataset.")

                problem_type = model.problem_type
                if problem_type == "auto":
                    problem_type = detect_problem_type(df[target_col])
                    add_log(f"Auto-detected problem type: {problem_type}")

                # Execute multi-model search
                add_log("Starting training champion model search...")
                config = model.training_config
                
                pipeline, best_algo, best_score, metrics, importances, train_rows, test_rows = train_champion_model(
                    df=df,
                    target_column=target_col,
                    problem_type=problem_type,
                    features=model.features if model.features else None,
                    candidate_algorithms=config.get("algorithms"),
                    cross_validation=config.get("cross_validation", False),
                    random_state=config.get("random_state", 42),
                    logger_cb=add_log
                )

                # Save pipeline artifact
                os.makedirs("uploads/models", exist_ok=True)
                model_path = f"uploads/models/model_{model_id}.joblib"
                add_log(f"Serializing champion model to disk: {model_path}")
                joblib.dump(pipeline, model_path)
                
                # Fetch final metadata
                model_size = os.path.getsize(model_path)
                completed_dt = datetime.now()
                duration = int((time.perf_counter() - started_ms) * 1000.0)

                # Persist champion details
                model.model_type = best_algo
                model.problem_type = problem_type
                model.best_score = best_score
                model.evaluation_metrics = metrics
                model.feature_importances = importances
                model.model_path = model_path
                model.model_size_bytes = model_size
                model.training_rows = train_rows
                model.testing_rows = test_rows
                model.completed_at = completed_dt
                model.duration_ms = duration
                
                # Save feature names list
                model.features = pipeline.named_steps["preprocessor"].feature_names_in_.tolist()
                
                model.status = "COMPLETED"
                add_log("Training completed successfully.")
                await db_session.commit()

            except Exception as e:
                logger.error(f"Error training model {model_id}: {str(e)}", exc_info=True)
                completed_dt = datetime.now()
                duration = int((time.perf_counter() - started_ms) * 1000.0)
                
                model.status = "FAILED"
                model.error_message = str(e)
                model.completed_at = completed_dt
                model.duration_ms = duration
                add_log(f"Training job failed: {str(e)}")
                await db_session.commit()

    async def list_models(self, user_id: UUID, dataset_id: Optional[UUID] = None) -> List[MLModel]:
        """
        Lists all trained models belonging to a user, optionally filtered by dataset workspace.
        """
        if dataset_id:
            # Check ownership
            dataset = await self.dataset_repo.get(dataset_id)
            if not dataset or dataset.user_id != user_id:
                raise NotFoundException("Dataset workspace not found")
            return await self.model_repo.get_multi_by_dataset(dataset_id)

        # Retrieve all models for all user datasets
        stmt = (
            select(MLModel)
            .join(Dataset, Dataset.id == MLModel.dataset_id)
            .filter(Dataset.user_id == user_id)
            .order_by(MLModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_model_details(self, model_id: UUID, user_id: UUID) -> MLModel:
        """
        Retrieves details of a trained model including validation metrics.
        """
        model = await self.model_repo.get(model_id)
        if not model:
            raise NotFoundException("ML Model not found")

        dataset = await self.dataset_repo.get(model.dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("ML Model not found")
            
        return model

    async def make_prediction(self, model_id: UUID, user_id: UUID, input_data: Dict[str, Any]) -> Tuple[Any, Optional[float]]:
        """
        Loads the champion pipeline artifact and runs real-time predictions, logging to history.
        """
        model = await self.get_model_details(model_id, user_id)
        if model.status != "COMPLETED":
            raise BadRequestException(f"Cannot run predictions. Model status is {model.status}")

        if not model.model_path or not os.path.exists(model.model_path):
            raise NotFoundException("Trained model artifact binary file missing from storage.")

        try:
            # Load pipeline
            pipeline = joblib.load(model.model_path)
            
            # Format single row dataframe
            input_df = pd.DataFrame([input_data])
            
            # Decompose any datetime input columns required by the model features
            for col in list(input_df.columns):
                if f"{col}_year" in model.features:
                    try:
                        val = input_data.get(col)
                        if val is not None:
                            # Skip if value is a plain numeric represented as int/float/string
                            if isinstance(val, (int, float)) or (isinstance(val, str) and val.strip().replace('.', '', 1).isdigit()):
                                continue
                            dt = pd.to_datetime(val)
                            input_df[f"{col}_year"] = int(dt.year)
                            input_df[f"{col}_month"] = int(dt.month)
                            input_df[f"{col}_day_of_week"] = int(dt.dayofweek)
                            input_df[f"{col}_is_weekend"] = 1 if dt.dayofweek >= 5 else 0
                    except Exception as e:
                        logger.error(f"Failed to decompose inference input datetime '{col}': {str(e)}")
            
            # Ensure all features exist in payload
            for col in model.features:
                if col not in input_df.columns:
                    # Impute missing input parameters with None to trigger preprocessor pipeline default imputers
                    input_df[col] = None

            # Keep only feature columns
            input_df = input_df[model.features]

            # Run prediction
            pred = pipeline.predict(input_df)[0]
            prediction_val = float(pred) if isinstance(pred, (int, float, np.integer, np.floating)) else str(pred)

            # Resolve confidence if classification model has predict_proba
            confidence = None
            if model.problem_type == "classification" and hasattr(pipeline.named_steps["model"], "predict_proba"):
                probs = pipeline.predict_proba(input_df)[0]
                confidence = float(np.max(probs))

            # Log prediction
            log_record = PredictionLog(
                id=uuid4(),
                model_id=model_id,
                input_payload=input_data,
                prediction=str(prediction_val),
                confidence=confidence
            )
            await self.log_repo.create(log_record)
            await self.session.commit()

            return prediction_val, confidence

        except Exception as e:
            logger.error(f"Failed to calculate prediction for model {model_id}: {str(e)}", exc_info=True)
            raise BadRequestException(f"Prediction failed: {str(e)}")

    async def get_prediction_history(self, model_id: UUID, user_id: UUID, limit: int = 50) -> List[PredictionLog]:
        """
        Retrieves prediction auditing logs.
        """
        await self.get_model_details(model_id, user_id)
        return await self.log_repo.get_by_model(model_id, limit)

    async def delete_model(self, model_id: UUID, user_id: UUID) -> None:
        """
        Deletes the model metadata record and its serialized binary artifact.
        """
        model = await self.get_model_details(model_id, user_id)
        
        # Remove joblib file
        if model.model_path and os.path.exists(model.model_path):
            try:
                os.remove(model.model_path)
            except Exception as e:
                logger.error(f"Failed to remove model file {model.model_path}: {str(e)}")

        await self.model_repo.delete(model_id)
        await self.session.commit()
