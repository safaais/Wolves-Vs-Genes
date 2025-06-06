# -*- coding: utf-8 -*-
"""WolvesVsGenes.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/17xT5iB8HKP5hwsLUiFhKPVt6Q_p8KI-7
"""

# STEP 1: Install DEAP (for GA)
!pip install deap

# STEP 2: Import Libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam

import random
from deap import base, creator, tools, algorithms

# STEP 3: Load and Preprocess Data
data = load_breast_cancer()
X = data.data
y = data.target

# Normalize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# CNN Training Function
def train_evaluate_cnn(X_train, X_test, y_train, y_test):
    model = Sequential()
    model.add(Dense(16, input_dim=X_train.shape[1], activation='relu'))
    model.add(Dense(8, activation='relu'))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(optimizer=Adam(0.001), loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X_train, y_train, epochs=30, batch_size=10, verbose=0)

    y_pred = model.predict(X_test)
    y_pred_labels = (y_pred > 0.5).astype(int)

    return {
        'accuracy': accuracy_score(y_test, y_pred_labels),
        'precision': precision_score(y_test, y_pred_labels),
        'recall': recall_score(y_test, y_pred_labels),
        'f1_score': f1_score(y_test, y_pred_labels)
    }

# STEP 4: Genetic Algorithm Feature Selection
def evaluate_individual(individual):
    if sum(individual) == 0:
        return 0.0,
    selected_idx = [i for i, bit in enumerate(individual) if bit == 1]
    X_train_sel = X_train[:, selected_idx]
    X_test_sel = X_test[:, selected_idx]
    scores = train_evaluate_cnn(X_train_sel, X_test_sel, y_train, y_test)
    return scores['accuracy'],

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)
toolbox = base.Toolbox()
toolbox.register("attr_bool", lambda: random.randint(0, 1))
toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, n=X.shape[1])
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", evaluate_individual)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

def run_ga():
    pop = toolbox.population(n=10)
    hof = tools.HallOfFame(1)
    algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=5, halloffame=hof, verbose=False)
    return hof[0]

best_ga = run_ga()
selected_ga = [i for i, bit in enumerate(best_ga) if bit == 1]
X_train_ga = X_train[:, selected_ga]
X_test_ga = X_test[:, selected_ga]
ga_results = train_evaluate_cnn(X_train_ga, X_test_ga, y_train, y_test)

# STEP 5: Simple GWO for Comparison (Binary Version)
def gwo_feature_selection(num_agents=5, max_iter=5):
    dim = X.shape[1]
    alpha_pos = np.zeros(dim)
    alpha_score = -np.inf
    wolves = np.random.randint(0, 2, (num_agents, dim))

    for iter in range(max_iter):
        for i in range(num_agents):
            idx = [j for j in range(dim) if wolves[i, j] == 1]
            if not idx:
                continue
            acc = train_evaluate_cnn(X_train[:, idx], X_test[:, idx], y_train, y_test)['accuracy']
            if acc > alpha_score:
                alpha_score = acc
                alpha_pos = wolves[i].copy()

        # update wolves
        a = 2 - iter * (2 / max_iter)
        for i in range(num_agents):
            for j in range(dim):
                r1, r2 = np.random.rand(), np.random.rand()
                A = 2 * a * r1 - a
                C = 2 * r2
                D_alpha = abs(C * alpha_pos[j] - wolves[i, j])
                wolves[i, j] = 1 if abs(alpha_pos[j] - A * D_alpha) < 0.5 else 0

    return np.where(alpha_pos == 1)[0]

selected_gwo = gwo_feature_selection()
X_train_gwo = X_train[:, selected_gwo]
X_test_gwo = X_test[:, selected_gwo]
gwo_results = train_evaluate_cnn(X_train_gwo, X_test_gwo, y_train, y_test)

# STEP 6: Show Results
print("\n📊 GA Results:")
print(f"Selected Features: {len(selected_ga)}")
print(ga_results)

print("\n🐺 GWO Results:")
print(f"Selected Features: {len(selected_gwo)}")
print(gwo_results)

plt.savefig("GA_vs_GWO_Performance.png", dpi=300)
plt.show()