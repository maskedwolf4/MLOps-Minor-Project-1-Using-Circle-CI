import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
import os

from src.custom_exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)

class DataProcessing:
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.processed_data_path = "artifacts/processed"
        os.makedirs(self.processed_data_path, exist_ok=True)
        
    def load_data(self):
        try:
            self.df = pd.read_csv(self.file_path)
            logger.info("Data loaded sucessfully")
        except Exception as e:
            logger.error(f"Error while loading data {e}")
            raise CustomException(f"Error in loading data {e}")
        
    def handle_outliers(self, column):
        try:
            logger.info("Outlier handling started...")
            Q1 = self.df[column].quantile(0.25)
            Q3 = self.df[column].quantile(0.75)
            
            IQR = Q3 - Q1
            
            lower_value = Q1 - 1.5*IQR
            upper_value = Q3 - 1.5*IQR
            
            sepal_median = np.median(self.df[column])
            
            for i in self.df[column]:
                if i > upper_value or i < lower_value:
                    self.df[column] = self.df[column].replace(i,sepal_median)
                    
            logger.info("Handled outlier succesfully")
            
        except Exception as e:
            logger.error(f"Error while handling outlier {e}")
            raise CustomException(f"Error in handling outlier {e}")
        
    def split_data(self):
        try:
            logger.info("Initialised data splitting")
            
            X = self.df[['SepalLengthCm', 'SepalWidthCm', 'PetalLengthCm', 'PetalWidthCm']]
            y = self.df["Species"]
            X_train,X_test,y_train,y_test = train_test_split(X,y , test_size=0.2 , random_state=42)
            
            joblib.dump(X_train, os.path.join(self.processed_data_path, "X_train.pkl"))
            joblib.dump(X_test, os.path.join(self.processed_data_path, "X_test.pkl"))
            joblib.dump(y_train, os.path.join(self.processed_data_path, "y_train.pkl"))
            joblib.dump(y_test, os.path.join(self.processed_data_path, "y_test.pkl"))
        
            logger.info("Files saved sucesfully for Data processing step..")
                 
        except Exception as e:
            logger.error(f"Error while splitting data {e}")
            raise CustomException(f"Error in data splitting {e}")
                
    def run(self):
        self.load_data()
        self.handle_outliers("SepalWidthCm")
        self.split_data()

if __name__ == "__main__":
    data_processor = DataProcessing("artifacts/raw/data.csv")
    data_processor.run()
