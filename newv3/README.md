# https://medium.com/@yakovbeder/ossm-3-kiali-and-grafana-tempo-the-epic-quest-for-custom-certificates-mutual-trust-and-06004f2ab334

oc -n test-istio-v3 exec deploy/kiali -c kiali -- cat /var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt > service-ca.crt

cat root-ca.crt service-ca.crt > custom-ca.crt
oc create secret generic cacert \
  --from-file=ca.crt=custom-ca.crt \
  -n test-istio-v3

# 0. Prerequisitos
## - Tener creado un TempoStack para guardar las trazas (carpeta tempo)
## - Haber creardo un IstioCNI (carpeta istio-cni)

# 1. Definimos las variables

CONTROL_PLANE_NS=test-istio-v3
INGRESS_NS=${CONTROL_PLANE_NS}-ingress
DATA_PLANE_NS=bookinfo-v3
TEMPO_NS=istio-tempo
TENANT=prod
CLUSTER_DNS=ocp4poc.example.com

# 2. Creamos el control Plane

## 2.1 Creamos el namespace
oc create ns ${CONTROL_PLANE_NS}
oc label ns ${CONTROL_PLANE_NS} istio.io/rev=${CONTROL_PLANE_NS}
oc label ns ${CONTROL_PLANE_NS} istio-injection=disabled

## 2.2 Creamos los objetos de control plane

cat istio.yaml | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | oc apply -f-
cat otel-collector.yaml | sed "s/_TEMPO_NAMESPACE_/$TEMPO_NS/g" | sed "s/_TENANT_/$TENANT/g" | oc -n ${CONTROL_PLANE_NS} apply -f-
oc -n ${CONTROL_PLANE_NS} apply -f telemetry.yaml
oc -n ${CONTROL_PLANE_NS} apply -f monitoring-control-plane.yaml

cat tempo-clusterrolebindings.yaml | sed "s/_TENANT_/$TENANT/g" | sed "s/_TEMPO_NAMESPACE_/$TEMPO_NS/g" | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | oc apply -f-

cat kiali.yaml | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | sed "s/_TENANT_/$TENANT/g" | sed "s/_TEMPO_NAMESPACE_/$TEMPO_NS/g" | sed "s/_CLUSTER_DNS_/$CLUSTER_DNS/g" | oc -n ${CONTROL_PLANE_NS} apply -f-
# El Kiali solo usa el discoverer_selector cuando se instala, si a posteriori se añade algun otro namespace al mesh
# hay que forzar a que lo recalcule con
# oc -n ${CONTROL_PLANE_NS} get kiali kiali -o yaml | oc apply -f-

# Si queremos que no se pueda acceder desde el exterior al mesh podemos habilitar el mTLS estricto
# oc -n ${CONTROL_PLANE_NS} apply -f peerauthentication.yaml



# 3. Creamos el namespace donde irá el ingressgateway

## 3.1 Cremos el namespace
oc create ns ${INGRESS_NS}
oc label ns ${INGRESS_NS} istio.io/rev=${CONTROL_PLANE_NS}

## 3.2 Desplegamos el ingress, para pruebas podemos tambien exponer el servicio con 
## oc -n ${INGRESS_NS} expose svc/ingressgateway --port=http2
oc -n ${INGRESS_NS} apply -f ingressgateway.yaml


# 4. Creamos el o los namespaces de aplicacion
## 4.1 Creamos el namespace  con el label de istio.io/rev
oc create ns ${DATA_PLANE_NS}
oc label ns ${DATA_PLANE_NS} istio.io/rev=${CONTROL_PLANE_NS}

# 4.2 Desplegamos el pod monitor para recoger métricas de los istio-proxy
oc -n ${DATA_PLANE_NS} apply -f monitoring-data-plane.yaml

## Se inyectará el sidecar a todos los pods, si no los queremos, se le tiene que poner la label 
##  sidecar.istio.io/inject=false
## a los pods que no han de tener sidecar

## 4.3 Desplegamos la aplicación como tal
oc apply -f https://raw.githubusercontent.com/openshift-service-mesh/istio/release-1.24/samples/bookinfo/platform/kube/bookinfo.yaml -n ${DATA_PLANE_NS}
oc apply -f https://raw.githubusercontent.com/openshift-service-mesh/istio/release-1.24/samples/bookinfo/networking/bookinfo-gateway.yaml -n ${DATA_PLANE_NS}


