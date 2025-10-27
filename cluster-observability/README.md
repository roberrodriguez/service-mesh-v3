# https://docs.redhat.com/en/documentation/red_hat_openshift_cluster_observability_operator/1-latest/html/installing_red_hat_openshift_cluster_observability_operator/index

MONITORING_NS=test-smcp-v2-monitoring-stack

oc create ns $MONITORING_NS
oc -n $MONITORING_NS apply -f monitoring-stack.yaml

oc label ns $MONITORING_NS monitoring.rhobs/stack=monitoring-stack
oc label ns bookinfo monitoring.rhobs/stack=monitoring-stack
oc label ns test-smcp-v2 monitoring.rhobs/stack=monitoring-stack
