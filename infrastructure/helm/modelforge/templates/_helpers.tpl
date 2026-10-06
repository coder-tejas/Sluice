{{- /* Scaffold helpers. */ -}}
{{- define "Sluice.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "Sluice.labels" -}}
app.kubernetes.io/part-of: Sluice
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
