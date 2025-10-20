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

oc label namespace test-istio-v3 istio.io/rev=test-istio-v3
oc label namespace test-istio-v3 istio-injection=disabled
oc label namespace bookinfo istio.io/rev=test-istio-v3

oc apply -f tempo-stack
oc apply -f istio.yaml
oc apply -f otel-collector.yaml
oc apply -f tempo-rolebindings.yaml
oc apply -f telemetry.yaml
oc apply -f kiali.yaml

oc apply -f https://raw.githubusercontent.com/openshift-service-mesh/istio/release-1.24/samples/bookinfo/platform/kube/bookinfo.yaml -n bookinfo-v3

oc -n bookinfo-v3 expose svc/productpage

# Añadir label para inyectar sidecars
for f in $(oc -n bookinfo-v3 get deploy --no-headers -o custom-columns=":metadata.name"); 
do 
    oc -n bookinfo-v3 patch deploy $f --type merge -p '{"spec":{"template":{"metadata":{"labels":{"sidecar.istio.io/inject":"true"}}}}}'
done


oc apply -f monitoring.yaml