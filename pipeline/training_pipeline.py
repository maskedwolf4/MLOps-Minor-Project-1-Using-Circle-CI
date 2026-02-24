from src.data_processing import DataProcessing
from src.model_training import Model_Training

if __name__ == "__main__":
    data_processor = DataProcessing("artifacts/raw/data.csv")
    data_processor.run()
    
    trainer =  Model_Training()
    trainer.run()