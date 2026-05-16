#!/bin/bash
# Elimina todo el namespace observabilidad
kubectl delete namespace observabilidad --ignore-not-found
echo "Namespace observabilidad deleted"
