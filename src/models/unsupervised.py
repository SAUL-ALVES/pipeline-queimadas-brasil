import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os

def run_unsupervised_analysis(df, features, output_path="outputs/graficos"):
    # 1. Preparação dos dados
    X = df[features].dropna()
    X_scaled = StandardScaler().fit_transform(X)
    
    # 2. Método do Cotovelo (Elbow Method)
    inercia = []
    K = range(1, 11)
    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inercia.append(kmeans.inertia_)
        
    plt.figure(figsize=(8, 5))
    plt.plot(K, inercia, 'bo-')
    plt.title('Método do Cotovelo para K ideal')
    plt.xlabel('Número de Clusters (k)')
    plt.ylabel('Inércia')
    plt.savefig(os.path.join(output_path, '06_grafico_cotovelo.png'))
    plt.close()

    # 3. PCA e Clusters (Assumindo k=3 como exemplo)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    plt.figure(figsize=(8, 5))
    scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap='viridis')
    plt.title('Clusters de Queimadas visualizados com PCA')
    plt.xlabel('Componente Principal 1')
    plt.ylabel('Componente Principal 2')
    plt.colorbar(scatter, label='Cluster')
    plt.savefig(os.path.join(output_path, '07_pca_clusters.png'))
    plt.close()
    
    return clusters