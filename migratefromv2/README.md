# 1. CREAR EL SETUP INICIAL

# Crear namespaces
oc create ns test-smcp-v2
oc create ns bookinfo
# oc create ns istio-tempo

oc label namespace bookinfo istio-injection=enabled

# oc apply -f tempo-stack
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