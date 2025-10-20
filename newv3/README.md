# https://medium.com/@yakovbeder/ossm-3-kiali-and-grafana-tempo-the-epic-quest-for-custom-certificates-mutual-trust-and-06004f2ab334

oc -n test-istio-v3 exec deploy/kiali -c kiali -- cat /var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt > service-ca.crt

cat root-ca.crt service-ca.crt > custom-ca.crt
oc create secret generic cacert \
  --from-file=ca.crt=custom-ca.crt \
  -n test-istio-v3


# solo una vez, es comun para todos los istios
oc create ns istio-cni
oc apply -f istiocni.yaml

# Crear namespaces
oc create ns test-istio-v3
oc create ns bookinfo-v3
oc create ns istio-tempo
oc create ns test-istio-v3-ingress

oc label namespace test-istio-v3-ingress istio.io/rev=test-istio-v3
oc label namespace test-istio-v3 istio.io/rev=test-istio-v3
oc label namespace test-istio-v3 istio-injection=disabled
oc label namespace bookinfo istio.io/rev=test-istio-v3

oc apply -f tempo-stack
oc apply -f istio.yaml
oc apply -f otel-collector.yaml
oc apply -f tempo-rolebindings.yaml
oc apply -f telemetry.yaml
oc apply -f kiali.yaml

oc -n test-istio-v3-ingress apply -f ingressgateway.yaml


oc apply -f https://raw.githubusercontent.com/openshift-service-mesh/istio/release-1.24/samples/bookinfo/platform/kube/bookinfo.yaml -n bookinfo-v3
oc apply -f https://raw.githubusercontent.com/openshift-service-mesh/istio/release-1.24/samples/bookinfo/networking/bookinfo-gateway.yaml -n bookinfo-v3

oc -n test-istio-v3-ingress expose svc/ingressgateway --port=http2

oc apply -f monitoring.yaml

# Añadir label para inyectar sidecars
# Los pods que no han de tener sidecar se le tiene que poner la label sidecar.istio.io/inject=false

# El Kiali solo usa el discoverer_selector cuando se instala, si a posteriori se añade algun otro namespace al mesh
# hay que forzar a que lo recalcule con
# oc get kiali kiali -o yaml | oc apply -f-