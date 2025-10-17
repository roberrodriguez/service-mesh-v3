# Crear namespaces
oc create ns test-smcp-v2
oc create ns bookinfo
# oc create ns istio-tempo

oc label namespace bookinfo istio-injection=enabled

# oc apply -f tempo-stack
oc apply -f smcp-orig.yaml
oc apply -f smmr.yaml

oc apply -f https://raw.githubusercontent.com/openshift-service-mesh/istio/release-1.24/samples/bookinfo/platform/kube/bookinfo.yaml -n bookinfo

oc -n bookinfo expose svc/productpage

