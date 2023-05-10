from ..datasources.gds import gds

### link prediction

pipe, _ = gds.beta.pipeline.linkPrediction.create("lp-pipe")

# Add FastRP as a property step producing "embedding" node properties
pipe.addNodeProperty("fastRP", embeddingDimension=128, mutateProperty="embedding", randomSeed=1337)

# Combine our "embedding" node properties with Hadamard to create link features for training
pipe.addFeature("hadamard", nodeProperties=["embedding"])

# Verify that the features to be used in model training are what we expect
steps = pipe.feature_steps()
assert len(steps) == 1
assert steps["name"][0] == "HADAMARD"

# Specify the fractions we want for our dataset split
pipe.configureSplit(trainFraction=0.2, testFraction=0.2, validationFolds=2)

# Add a random forest model with tuning over `maxDepth`
pipe.addRandomForest(maxDepth=(2, 20))

# Train the pipeline and produce a model named "friend-recommender"
friend_recommender, train_result = pipe.train(
    G,
    modelName="friend-recommender",
    targetRelationshipType="KNOWS",
    randomSeed=42
)
assert train_result["trainMillis"] >= 0



# Make sure we indeed obtained an AUCPR score
metrics = friend_recommender.metrics()
assert 'AUCPR' in metrics

# Predict on `G` and mutate it with the relationship predictions
mutate_result = friend_recommender.predict_mutate(G, topN=5, mutateRelationshipType="PRED_REL")
assert mutate_result["relationshipsWritten"] == 5 * 2  # Undirected relationships



#### node classifcation example


# Project the graph into the GDS Graph Catalog
# We call the object representing the projected graph `G_office`
G_office, project_result = gds.graph.project("neo4j-offices", "City", "FLY_TO")

# Run the mutate mode of the PageRank algorithm
mutate_result = gds.pageRank.mutate(G_office, tolerance=0.5, mutateProperty="rank")

# We can inspect the node properties of our projected graph directly
# via the graph object and see that indeed the new property exists
assert G_office.node_properties("City") == ["rank"]



pipe, _ = gds.beta.pipeline.nodeClassification.create("my-pipe")

# Add Degree centrality as a property step producing "rank" node properties
pipe.addNodeProperty("degree", mutateProperty="rank")

# Select our "rank" property as a feature for the model training
pipe.selectFeatures("rank")

# Verify that the features to be used in model training are what we expect
feature_properties = pipe.feature_properties()
assert len(feature_properties) == 1
assert feature_properties[0]["feature"] == "rank"

# Configure the model training to do cross-validation over logistic regression
pipe.addLogisticRegression(tolerance=(0.01, 0.1))
pipe.addLogisticRegression(penalty=1.0)

# Train the pipeline targeting node property "class" as label and "ACCURACY" as only metric
fraud_model, train_result = pipe.train(
    G,
    modelName="fraud-model",
    targetProperty="fraudster",
    metrics=["ACCURACY"],
    randomSeed=111
)
assert train_result["trainMillis"] >= 0