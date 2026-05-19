{{- define "app.name" -}}
{{- default .Release.Name .Values.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- include "app.name" . }}
{{- end }}
{{- end }}

{{- define "app.namespace" -}}
{{- .Values.namespace }}
{{- end }}

{{- define "app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "app.labels" -}}
helm.sh/chart: {{ include "app.chart" . }}
{{ include "app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{- define "app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "app.name" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- define "app.image" -}}
{{- $repo := required "image.repository is required" .Values.image.repository }}
{{- $tag := default .Chart.AppVersion .Values.image.tag }}
{{- printf "%s:%s" $repo $tag }}
{{- end }}

{{- define "app.servicePort" -}}
{{- default .Values.containerPort .Values.service.port }}
{{- end }}
