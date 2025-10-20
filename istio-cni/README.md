# solo una vez, es comun para todos los istios
oc create ns istio-cni
oc apply -f istiocni.yaml

