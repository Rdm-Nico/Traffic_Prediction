# Preprocessing data

For import and preprocess the graph data follow this task:

1. read the README.md in graph_creation/ folder
2. Create the adj mat and data mat by run:

```
python3 data_creation.py -n neo4j://localhost:7687 -u neo4j -p passwd -d 300
```

where d is max distance between two sensors for create the relations
