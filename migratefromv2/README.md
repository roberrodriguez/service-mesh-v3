# 1. CREAR EL SETUP INICIAL

# Crear namespaces
oc create ns test-smcp-v2
oc create ns bookinfo

oc apply -f smcp-orig.yaml
oc apply -f smmr.yaml

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
oc scale deploy istio-ingressgateway --replicas=0

oc label service istio-ingressgateway app.kubernetes.io/managed-by-
oc patch service istio-ingressgateway --type='json' -p='[{"op": "remove", "path": "/metadata/ownerReferences"}]'
oc patch smcp ossm-controlplane-v2 --type='json' -p='[{"op": "replace", "path": "/spec/gateways/ingress/enabled", "value": false}]'


## 2.2 Deshabilitar extensiones del SMCP y activar opentelemetry (https://docs.redhat.com/en/documentation/red_hat_openshift_service_mesh/3.0/html-single/migrating_from_service_mesh_2_to_service_mesh_3/index#service-mesh-control-plane-resource-file_ossm-migrating-premigration-checklists)

oc apply -f otel-collector.yaml
oc apply -f tempo-rolebindings.yaml
oc apply -f 2.2.smcp-disabled-extensions.yaml
oc apply -f telemetry.yaml
oc apply -f kiali.yaml
oc apply -f monitoring.yaml

# Para borrar el pod del elasticsearch
oc delete pvc --all 

# solo una vez, es comun para todos los istios
oc create ns istio-cni
oc apply -f istiocni.yaml

oc apply -f istio.yaml

oc label namespace bookinfo istio.io/rev=test-smcp-v2

oc create ns test-smcp-v2-ingress
oc label namespace test-smcp-v2-ingress istio.io/rev=test-smcp-v2
oc -n test-smcp-v2-ingress apply -f ingressgateway-v3.yaml
oc delete -f 2.1.ingressgateway-migration.yaml
oc delete svc istio-ingressgateway

# en la doc ponia labelear para que no inyecte el v2 pero 
# oc label ns bookinfo maistra.io/ignore-namespace=true
# pero me daba error al reiniciar los pods, he tenido que eliminar en smcp y smmr antiguos
oc delete smmr --all
oc delete smcp --all

# Quitar la annotation para inyectar sidecars
for f in $(oc -n bookinfo get deploy --no-headers -o custom-columns=":metadata.name"); 
do 
    oc -n bookinfo patch deploy $f --type json -p='[{"op": "remove", "path": "/spec/template/metadata/annotations/sidecar.istio.io~1inject"}]'
done


oc rollout restart deployments -n bookinfo