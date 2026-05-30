import joblib
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ModelLoader:
    def __init__(self, model_path='artifacts/churn_model_final.joblib', preprocessor_path='artifacts/preprocessor.joblib'):
        self.model_path = model_path
        self.preprocessor_path = preprocessor_path
        self.model = None
        self.preprocessor = None

    def load(self):
        try:
            self.model = joblib.load(self.model_path)
            self.preprocessor = joblib.load(self.preprocessor_path)
            logger.info("Model and preprocessor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model/preprocessor: {e}")
            raise

    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет те же признаки, что были при обучении."""
        df = df.copy()
        # tenure_group
        df['tenure_group'] = pd.cut(df['tenure'], bins=[0,12,24,36,48,60,72],
                                    labels=['0-1y', '1-2y', '2-3y', '3-4y', '4-5y', '5-6y'])
        # TotalServices
        service_cols = ['PhoneService', 'MultipleLines', 'OnlineSecurity', 'OnlineBackup',
                        'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies']
        df['TotalServices'] = df[service_cols].apply(lambda x: (x != 'No').sum(), axis=1)
        # Взаимодействие
        df['Charges_Tenure_Interaction'] = df['MonthlyCharges'] * df['tenure']
        return df

    def predict(self, input_df: pd.DataFrame):
        """input_df: сырые признаки (без customerID и Churn)"""
        if self.preprocessor is None or self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        # Добавляем вычисляемые признаки
        input_df = self._add_features(input_df)
        X_processed = self.preprocessor.transform(input_df)
        proba = self.model.predict_proba(X_processed)[:, 1]
        return proba

loader = ModelLoader()