# https://docs.redhat.com/en/documentation/red_hat_openshift_cluster_observability_operator/1-latest/html/installing_red_hat_openshift_cluster_observability_operator/index

MONITORING_NS=test-smcp-v2-monitoring-stack
CONTROL_PLANE_NS=test-smcp-v2
cat monitoring-data-plane.yaml | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | oc -n ${DATA_PLANE_NS} apply -f-


oc create ns $MONITORING_NS
cat monitoring-stack.yaml | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | oc -n ${MONITORING_NS} apply -f-
cat monitoring-data-plane.yaml | sed "s/_CONTROL_PLANE_/$CONTROL_PLANE_NS/g" | oc -n ${DATA_PLANE_NS} apply -f-
