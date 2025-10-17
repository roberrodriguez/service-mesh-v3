# https://medium.com/@yakovbeder/ossm-3-kiali-and-grafana-tempo-the-epic-quest-for-custom-certificates-mutual-trust-and-06004f2ab334

oc -n test-istio-v3 exec deploy/kiali -c kiali -- cat /var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt > service-ca.crt

cat root-ca.crt service-ca.crt > custom-ca.crt
oc create secret generic cacert \
  --from-file=ca.crt=custom-ca.crt \
  -n test-istio-v3


# Crear namespaces
oc create ns test-istio-v3
oc create ns istio-cni
oc create ns bookinfo
oc create ns istio-tempo

oc label namespace bookinfo istio.io/rev=test-istio-v3

oc apply -f tempo-stack
oc apply -f istio.yaml
oc apply -f otel-collector.yaml
oc apply -f tempo-rolebindings.yaml
oc apply -f telemetry.yaml

oc apply -f https://raw.githubusercontent.com/openshift-service-mesh/istio/release-1.24/samples/bookinfo/platform/kube/bookinfo.yaml -n bookinfo

oc -n bookinfo expose svc/productpage

oc apply -f monitoring.yaml