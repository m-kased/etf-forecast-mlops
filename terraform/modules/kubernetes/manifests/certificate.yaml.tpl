apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: etf-forecast-tls
  namespace: ${istio_system_namespace}
spec:
  secretName: etf-forecast-tls
  issuerRef:
    name: ${cluster_issuer_name}
    kind: ClusterIssuer
  dnsNames:
%{ for host in ingress_hosts ~}
    - ${host}
%{ endfor ~}
