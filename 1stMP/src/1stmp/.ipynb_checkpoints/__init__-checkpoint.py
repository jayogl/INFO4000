import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

# Predict on Validation/Test Set
eval_split = "validation" if "validation" in transformed_dataset else "test"
predictions_output = trainer.predict(transformed_dataset[eval_split])

# Extract predicted class IDs and true ground-truth labels
y_pred_logits = predictions_output.predictions
y_pred = np.argmax(y_pred_logits, axis=-1)
y_true = predictions_output.label_ids

print(f"Overall Validation Accuracy: {predictions_output.metrics['test_accuracy'] * 100:.2f}%\n")

# Print Classification Report
print("--- Detailed Classification Report ---")
print(classification_report(y_true, y_pred, target_names=labels))

# Compute and Plot Confusion Matrix Heatmap
cm = confusion_matrix(y_true, y_pred)

plt.figure(figsize=(8, 6))
sns.heatmap(
    cm, 
    annot=True, 
    fmt="d", 
    cmap="Blues", 
    xticklabels=labels, 
    yticklabels=labels,
    cbar=True
)
plt.title("ViT Classification Confusion Matrix", fontsize=14, fontweight="bold")
plt.xlabel("Predicted Class Label", fontsize=12)
plt.ylabel("True Class Label", fontsize=12)
plt.xticks(rotation=45)
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()