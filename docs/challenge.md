# Challenge Report

## Part I: Model

### Chosen Model: Logistic Regression

### Rationale:

- **Interpretability:** Directly reveals the relationship between features and outcomes, making it easy to understand and communicate.
  
- **Efficiency:** Computationally fast and lightweight, ideal for large datasets and rapid deployment.

### Conclusion:

Logistic Regression was selected for its balance of interpretability and efficiency, making it the most suitable choice for this task.

### Model implementation

The model was implemented using the `LogisticRegression` with custom class weights to account for the imbalance in the delay vs. no-delay classes. The categorical features (e.g., airline, flight type, and month) were one-hot encoded to ensure they were properly represented in the model. A preprocessing pipeline was constructed to handle missing data and to ensure that the model received clean and well-structured input.

The entire model and its preprocessing steps were integrated into a `DelayModel` class, which encapsulates the training, prediction, and serialization (saving/loading) processes. This modular approach ensures that the model can be easily deployed and maintained in a production environment.

The model's artifacts, including the trained model and the preprocessing pipeline, are saved to disk using `joblib`, allowing for easy persistence and reusability. This also supports rapid deployment, as the model can be loaded and used for predictions without needing to retrain. This implementation could be changed to a save in a cloud storage. 

#### Key Components:
- **Preprocessing:** A pipeline that handles missing data and one-hot encodes categorical features.
- **Model Fitting:** Logistic Regression with custom class weights to address class imbalance.
- **Prediction Handling:** Includes error handling to load the model if it's not already fitted, ensuring robustness in production environments.
- **Artifact Management:** Functions to save and load model artifacts, facilitating deployment and scaling.

This approach provides a comprehensive solution that balances accuracy, interpretability, and operational efficiency, making it well-suited to the challenge of predicting flight delays.