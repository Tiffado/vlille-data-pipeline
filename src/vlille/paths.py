"""Organisation de la zone brute dans le bucket Cloud Storage."""

# Réponses GBFS archivées par vlille-collect : gbfs/<flux>/dt=AAAA-MM-JJ/...
GBFS_PREFIX = "gbfs"

# Messages Kafka écrits par vlille-consume : kafka/station_status/dt=AAAA-MM-JJ/...
KAFKA_PREFIX = "kafka/station_status"
