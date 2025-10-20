#!/bin/bash


# En principio un tempo por aplicacion
# Cada tempo tendra diferentes tenants uno por cada entorno: INT, PRE, FOR
# Namespace donde se instalara
TEMPO_NS=istio-tempo

oc create ns ${TEMPO_NS}
oc -n ${TEMPO_NS} apply -f s3-secret.yaml

# Se ha de modificar el tempo-stack.yaml para definir los tenants que sean necesarios
oc -n ${TEMPO_NS} apply -f tempo-stack.yaml


# Creamos ClusterRoles de read y write para cada uno de los tenants
TENANT_LIST=("dev" "prod")
for tenant in "${TENANT_LIST[@]}"; do
  cat tempo-clusterroles.yaml | sed "s/_TENANT_/$tenant/g" | sed "s/_TEMPO_NAMESPACE_/$TEMPO_NS/g" | oc apply -f-
done
