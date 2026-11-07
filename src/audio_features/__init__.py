"""audio_features — the first-party package: the Spark session builder and the layer paths.

Modules (each is importable without a JVM; only build_spark() starts one):
  layers         ENVIRONMENTS, LAYERS, and the data/<environment>/<layer>/<source>/<table> paths
  spark_session  build_spark(environment): the one local SparkSession builder
"""
