import matplotlib.pyplot as plt
import pandas as pd

def graph1():
    data = {
        "Model": ["Base", "Fine-Tuned", "RAG"],
        "F1-score": [0.848, 0.909, 0.824]
    }

    df = pd.DataFrame(data)

    plt.figure()
    plt.bar(df["Model"], df["F1-score"])
    plt.xlabel("Model")
    plt.ylabel("F1-score")
    plt.title("F1-score comparison")
    plt.show()

def graph2():
    data = {
        "Model": ["Base", "Fine-Tuned", "RAG"],
        "F1-score": [0.84, 0.92, 0.86]
    }

    df = pd.DataFrame(data)

    plt.figure()
    plt.bar(df["Model"], df["F1-score"])
    plt.xlabel("Model")
    plt.ylabel("AUC")
    plt.title("AUC comparison")
    plt.show()

if "__main__" in __name__:
    graph1()
    graph2()
