# 1. CREAR EL SETUP INICIAL

# Crear namespaces
oc create ns test-smcp-v2
oc create ns bookinfo

oc apply -f smcp-orig.yaml
oc apply -f smmr.yaml

oc expose svc/istio-ingressgateway --port=http2

oc apply -f https://raw.githubusercontent.com/openshift-service-mesh/istio/release-1.24/samples/bookinfo/platform/kube/bookinfo.yaml -n bookinfo

oc apply -f https://raw.githubusercontent.com/openshift-service-mesh/istio/release-1.24/samples/bookinfo/networking/bookinfo-gateway.yaml -n bookinfo

# Añadir la annotation para inyectar sidecars
for f in $(oc -n bookinfo get deploy --no-headers -o custom-columns=":metadata.name"); 
do 
    oc -n bookinfo patch deploy $f --type merge -p '{"spec":{"template":{"metadata":{"annotations":{"sidecar.istio.io/inject":"true"}}}}}'
done

## Podemos acceder a productinfo con http://istio-ingressgateway-test-smcp-v2.apps.ocp4poc.example.com/productpage

# 2. MIGRACION

## 2.0 definir variables

CONTROL_PLANE_NS=test-smcp-v2
INGRESS_NS=${CONTROL_PLANE_NS}-ingress
DATA_PLANE_NS=bookinfo
TEMPO_NS=istio-tempo
TENANT=dev
CLUSTER_DNS=ocp4poc.example.com

## 2.1 Migrar la istio-ingressgateways (https://docs.redhat.com/en/documentation/openshift_container_platform/4.17/html/service_mesh/service-mesh-2-x#ossm-about-gateway-migration_gateway-migration)
oc -n ${CONTROL_PLANE_NS} apply -f ingressgateway-migration.yaml
oc -n ${CONTROL_PLANE_NS} scale deploy istio-ingressgateway --replicas=0

oc -n ${CONTROL_PLANE_NS} label service istio-ingressgateway app.kubernetes.io/managed-by-
oc -n ${CONTROL_PLANE_NS} patch service istio-ingressgateway --type='json' -p='[{"op": "remove", "path": "/metadata/ownerReferences"}]'
oc -n ${CONTROL_PLANE_NS} patch smcp ossm-controlplane-v2 --type='json' -p='[{"op": "replace", "path": "/spec/gateways/ingress/enabled", "value": false}]'


## 2.2 Deshabilitar extensiones del SMCP y activar opentelemetry (https://docs.redhat.com/en/documentation/red_hat_openshift_service_mesh/3.0/html-single/migrating_from_service_mesh_2_to_service_mesh_3/index#service-mesh-control-plane-resource-file_ossm-migrating-premigration-checklists)

cat otel-collector.yaml | sed "s/_TEMPO_NAMESPACE_/$TEMPO_NS/g" | sed "s/_TENANT_/$TENANT/g" | oc -n ${CONTROL_PLANE_NS} apply -f-
oc -n ${CONTROL_PLANE_NS} apply -f telemetry.yaml
oc -n ${CONTROL_PLANE_NS} apply -f monitoring-control-plane.yaml

cat tempo-clusterrolebindings.yaml | sed "s/_TENANT_/$TENANT/g" | sed "s/_TEMPO_NAMESPACE_/$TEMPO_NS/g" | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | oc apply -f-

cat smcp-disabled-extensions.yaml |  sed "s/_TEMPO_NAMESPACE_/$TEMPO_NS/g" | oc -n ${CONTROL_PLANE_NS} apply -f-

cat kiali.yaml | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | sed "s/_TENANT_/$TENANT/g" | sed "s/_TEMPO_NAMESPACE_/$TEMPO_NS/g" | sed "s/_CLUSTER_DNS_/$CLUSTER_DNS/g" | oc -n ${CONTROL_PLANE_NS} apply -f-

# Para borrar el pod del elasticsearch
oc -n ${CONTROL_PLANE_NS} delete pvc --all 

oc label ns ${CONTROL_PLANE_NS} istio.io/rev=${CONTROL_PLANE_NS}
oc label ns ${CONTROL_PLANE_NS} istio-injection=disabled
cat istio.yaml | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | oc apply -f-


# 3. Creamos el namespace donde irá el ingressgateway

## 3.1 Cremos el namespace
oc create ns ${INGRESS_NS}
oc label ns ${INGRESS_NS} istio.io/rev=${CONTROL_PLANE_NS}

# Teoricamente con ignore-namespace habria de funcionar pero no funciona hasta no borrar el smmr y el smcp
# oc label ns ${INGRESS_NS} maistra.io/ignore-namespace=true

# [rrodri11@bastionk8s migratefromv2]$ oc -n ${INGRESS_NS} get event --sort-by lastTimestamp
# LAST SEEN   TYPE      REASON              OBJECT                                       MESSAGE
# 71s         Normal    ScalingReplicaSet   deployment/istio-ingressgateway              Scaled up replica set istio-ingressgateway-57ffdb878d to 1
# 1s          Warning   FailedCreate        replicaset/istio-ingressgateway-57ffdb878d   Error creating: Internal error occurred: failed calling webhook "rev.namespace.sidecar-injector.istio.io": failed to call webhook: Post "https://istiod-test-smcp-v2.test-smcp-v2.svc:443/inject?timeout=10s": context deadline exceeded
# [rrodri11@bastionk8s migratefromv2]$
#
oc -n ${CONTROL_PLANE_NS} delete smmr --all
oc -n ${CONTROL_PLANE_NS} delete smcp --all


## 3.2 Desplegamos el ingress, para pruebas podemos tambien exponer el servicio con 
cat ingressgateway.yaml | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | oc -n ${INGRESS_NS} apply -f-


## 3.3 Mover rutas del control plane al namespace de ingress

for f in $(oc -n ${CONTROL_PLANE_NS} get route --output=jsonpath='{range .items[?(@.spec.to.name=="istio-ingressgateway")]}{.metadata.name}{"\n"}{end}')
do 
    oc -n ${CONTROL_PLANE_NS} get route $f -o yaml | yq 'del(.metadata.namespace)' | oc -n ${INGRESS_NS} apply -f -
    oc -n ${CONTROL_PLANE_NS} delete route $f
done

# 4. Migrar datos data plane

oc label ns ${DATA_PLANE_NS} istio.io/rev=${CONTROL_PLANE_NS}

oc -n ${CONTROL_PLANE_NS} delete -f ingressgateway-migration.yaml
oc -n ${CONTROL_PLANE_NS} delete svc istio-ingressgateway



# Quitar la annotation para inyectar sidecars
for f in $(oc -n ${DATA_PLANE_NS} get deploy --no-headers -o custom-columns=":metadata.name"); 
do 
    oc -n ${DATA_PLANE_NS} patch deploy $f --type json -p='[{"op": "remove", "path": "/spec/template/metadata/annotations/sidecar.istio.io~1inject"}]'
done


# oc rollout restart deployments -n bookinfo