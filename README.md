
# When Wavelets Meet Dynamic Graph: a Survey in Traffic Forecasting Graph based Models
This is the repo for the Graph Analysis's project. Baseline goal:

- Studying the traffic condition
- Evaluting some traffic forecast model

## Preprocessing

For create the graph in Neo4j go in graph_creation/ and see README.md

## 🚀 Run STWAVE

For run STWAVE model:

```
mkdir STWave/data/MO_D
mkdir STWave/cpt/MO_D
mkdir STWave/log/MO_D
cp data/* STWave/data/MO_D
cd STWave/
python main.py --config config/Modena.conf
```

## 🚀 Run DDGCRN

For training DDGCRN model:

```
mkdir DDGCRN/data/MO_D
cp data/data.npz DDGCRN/data/MO_D
python run.py --dataset MO_D --mode train
```

for testing put the model params inside DDGCRN/pre-trained with the name `MO_D.pth` and run:

```
python run.py --dataset MO_D --mode test
```
