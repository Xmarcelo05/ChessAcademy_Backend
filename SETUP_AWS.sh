#!/bin/bash
# GUÍA PASO A PASO: CI/CD Y DESPLIEGUE EN AWS APP RUNNER
# =======================================================
# Este archivo contiene los comandos necesarios para configurar
# el pipeline completo de CI/CD y despliegue en AWS

# REQUISITOS PREVIOS:
# - Cuenta de AWS con permisos para ECR y App Runner
# - AWS CLI v2 instalado y configurado
# - GitHub acceso al repositorio
# - Docker instalado (para construir localmente si es necesario)

echo "========================================"
echo "CONFIGURACIÓN CI/CD CHESS BACKEND"
echo "========================================"

# ===================================
# PASO 1: CREAR ECR REPOSITORY
# ===================================

echo ""
echo "📦 PASO 1: Crear ECR Repository"
echo "================================"
echo ""
echo "Ejecuta este comando en AWS CLI:"
echo ""
echo 'aws ecr create-repository \'
echo '  --repository-name chess-backend \'
echo '  --encryption-configuration encryptionType=AES256 \'
echo '  --image-tag-mutability MUTABLE \'
echo '  --image-scanning-configuration scanOnPush=true \'
echo '  --region us-east-1'
echo ""
echo "Después copia el URI del repositorio (te lo dará como output)"
echo ""

read -p "Presiona Enter cuando hayas creado el ECR repository..."

# ===================================
# PASO 2: CREAR IAM USER PARA CI/CD
# ===================================

echo ""
echo "👤 PASO 2: Crear IAM User para GitHub Actions"
echo "=============================================="
echo ""
echo "1. Ve a AWS Console → IAM → Users"
echo "2. Click en 'Create User'"
echo "3. Nombre: 'github-actions-chess'"
echo "4. No seleccionar 'Provide user access to AWS Management Console'"
echo "5. Click Next"
echo ""
echo "6. Crear Inline Policy con este JSON:"
echo ""
cat << 'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "arn:aws:ecr:*:ACCOUNT_ID:repository/chess-backend"
    },
    {
      "Effect": "Allow",
      "Action": [
        "apprunner:StartDeployment",
        "apprunner:DescribeService"
      ],
      "Resource": "arn:aws:apprunner:*:ACCOUNT_ID:service/chess-backend/*"
    }
  ]
}
POLICY

echo ""
echo "7. Luego ve a 'Security Credentials' y crea 'Access Key'"
echo "8. Selecciona 'Command Line Interface (CLI)'"
echo "9. Copia los valores:"
echo "   - Access Key ID"
echo "   - Secret Access Key"
echo ""

read -p "Presiona Enter cuando hayas copiado las credentials..."

# ===================================
# PASO 3: CONFIGURAR GITHUB SECRETS
# ===================================

echo ""
echo "🔐 PASO 3: Configurar GitHub Secrets"
echo "===================================="
echo ""
echo "1. Ve a GitHub → Tu Repositorio → Settings"
echo "2. Izquierda: 'Secrets and variables' → Actions"
echo "3. Click 'New repository secret'"
echo ""
echo "4. Crea estos secrets:"
echo ""
echo "   Secret: AWS_ACCESS_KEY_ID"
echo "   Value:  (copia del paso anterior)"
echo ""
echo "   Secret: AWS_SECRET_ACCESS_KEY"
echo "   Value:  (copia del paso anterior)"
echo ""
echo "   Secret: AWS_APPRUNNER_SERVICE_ARN"
echo "   Value:  (lo crearemos en el siguiente paso)"
echo ""
echo "   Secret: SLACK_WEBHOOK_URL (OPCIONAL)"
echo "   Value:  (si quieres notificaciones en Slack)"
echo ""

read -p "Presiona Enter cuando hayas configurado los secrets..."

# ===================================
# PASO 4: CREAR APP RUNNER SERVICE
# ===================================

echo ""
echo "🚀 PASO 4: Crear AWS App Runner Service"
echo "========================================"
echo ""
echo "Opción A: Via AWS CLI (recomendado)"
echo ""
echo "Ejecuta este comando (reemplaza TU_ACCOUNT_ID y REGISTRY_URL):"
echo ""

ECR_URL="public.ecr.aws/TU_ACCOUNT_ID/chess-backend"

cat << APPRUNNER
aws apprunner create-service \
  --service-name chess-backend \
  --region us-east-1 \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "$ECR_URL:latest",
      "ImageRepositoryType": "ECR_PUBLIC",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "ENVIRONMENT": "production",
          "AZURE_FRONTEND_URL": "https://tu-landing-page.azurewebsites.net",
          "LOG_LEVEL": "INFO"
        }
      }
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration 'Cpu=1 vCPU,Memory=2GB,EphemeralStorageSize=1GB' \
  --tags 'Key=Project,Value=ChessAcademy' 'Key=Environment,Value=Production'
APPRUNNER

echo ""
echo "Opción B: Via AWS Console"
echo "1. Ve a AWS → App Runner"
echo "2. Click 'Create Service'"
echo "3. Source: ECR Public"
echo "4. Repository URI: $ECR_URL"
echo "5. Deployment Trigger: Automatic"
echo "6. Port: 8000"
echo "7. CPU: 1 vCPU, Memory: 2GB"
echo "8. Environment variables:"
echo "   - ENVIRONMENT=production"
echo "   - AZURE_FRONTEND_URL=https://tu-landing-page.azurewebsites.net"
echo "   - LOG_LEVEL=INFO"
echo "9. Click 'Create & Deploy'"
echo ""
echo "El output te dará: Service ARN"
echo "Cópialo para el siguiente paso"
echo ""

read -p "Presiona Enter cuando hayas creado el App Runner Service..."

# ===================================
# PASO 5: AGREGAR SERVICE ARN A SECRETS
# ===================================

echo ""
echo "🔗 PASO 5: Agregar Service ARN a GitHub"
echo "========================================"
echo ""
echo "1. Copia el ARN del App Runner Service (ej: arn:aws:apprunner:us-east-1:123456789:service/chess-backend/abcdef123)"
echo "2. Ve a GitHub → Settings → Secrets"
echo "3. Crea nuevo secret: AWS_APPRUNNER_SERVICE_ARN"
echo "4. Pega el ARN"
echo ""

read -p "Presiona Enter cuando hayas agregado el ARN..."

# ===================================
# PASO 6: PUSH A GITHUB
# ===================================

echo ""
echo "📤 PASO 6: Push al Repositorio"
echo "=============================="
echo ""
echo "Comandos:"
echo ""
echo "git add ."
echo "git commit -m 'Initial deployment configuration for AWS App Runner'"
echo "git push origin main"
echo ""
echo "Esto disparará el workflow de GitHub Actions automáticamente"
echo ""

read -p "Presiona Enter después de hacer el push..."

# ===================================
# PASO 7: MONITOREAR DESPLIEGUE
# ===================================

echo ""
echo "👀 PASO 7: Monitorear el Despliegue"
echo "==================================="
echo ""
echo "GitHub Actions:"
echo "1. Ve a GitHub → Tu Repo → Actions"
echo "2. Verás el workflow ejecutándose"
echo "3. Espera a que complete"
echo ""
echo "AWS App Runner:"
echo "1. Ve a AWS Console → App Runner"
echo "2. Selecciona 'chess-backend'"
echo "3. Monitorea el estado en 'Deployments'"
echo ""
echo "Comando AWS CLI para verificar:"
echo ""

SERVICE_ARN="arn:aws:apprunner:us-east-1:YOUR_ACCOUNT_ID:service/chess-backend/YOUR_SERVICE_ID"

echo "aws apprunner describe-service --service-arn $SERVICE_ARN --region us-east-1"
echo ""

read -p "Presiona Enter cuando el despliegue esté completo..."

# ===================================
# PASO 8: VERIFICAR SALUD DE LA API
# ===================================

echo ""
echo "✅ PASO 8: Verificar Health Check"
echo "=================================="
echo ""
echo "Tu aplicación debería estar en:"
echo "https://chess-backend.xxxxx.run.amazonaws.com"
echo ""
echo "Verifica que funciona:"
echo ""
echo "curl https://chess-backend.xxxxx.run.amazonaws.com/api/v1/health"
echo ""
echo "Deberías recibir:"
echo '{"status":"healthy","version":"1.0.0",...}'
echo ""

read -p "Presiona Enter..."

# ===================================
# PASO 9: VERIFICAR CORS
# ===================================

echo ""
echo "🔒 PASO 9: Verificar CORS"
echo "========================="
echo ""
echo "Si tu frontend está en Azure, verifica que CORS funciona:"
echo ""
echo 'curl -X OPTIONS https://chess-backend.xxxxx.run.amazonaws.com/api/v1/cursos \'
echo '  -H "Origin: https://tu-landing-page.azurewebsites.net" \'
echo '  -H "Access-Control-Request-Method: GET" \'
echo '  -v'
echo ""
echo "Deberías ver headers de CORS en la respuesta"
echo ""

read -p "Presiona Enter..."

# ===================================
# PASO 10: CONFIGURAR DOMINIO PERSONALIZADO (OPCIONAL)
# ===================================

echo ""
echo "🌐 PASO 10: Dominio Personalizado (Opcional)"
echo "==========================================="
echo ""
echo "1. Ve a AWS App Runner → chess-backend → Custom Domains"
echo "2. Click 'Associate Custom Domain'"
echo "3. Ingresa tu dominio (ej: api.chessacademy.com)"
echo "4. AWS te dará registros DNS para configurar"
echo "5. En tu proveedor de DNS, agrega los registros CNAME"
echo "6. Espera a que se valide (algunos minutos)"
echo ""

read -p "Presiona Enter..."

# ===================================
# RESUMEN FINAL
# ===================================

echo ""
echo "✨ CONFIGURACIÓN COMPLETADA ✨"
echo "=============================="
echo ""
echo "Resumen de lo que has hecho:"
echo ""
echo "✅ Crear ECR Repository"
echo "✅ Crear IAM User para CI/CD"
echo "✅ Configurar GitHub Secrets"
echo "✅ Crear App Runner Service"
echo "✅ Primer despliegue automático"
echo "✅ Verificar health checks"
echo ""
echo "Próximos pasos:"
echo ""
echo "1. El pipeline está configurado. Ahora cada push a 'main' se desplegará automáticamente"
echo "2. Para cambios en el código:"
echo "   git commit -am 'Mi cambio'"
echo "   git push origin main"
echo ""
echo "3. Monitorea en:"
echo "   - GitHub Actions: github.com/tuusername/chess-backend/actions"
echo "   - AWS Logs: aws logs tail /aws/apprunner/chess-backend --follow"
echo ""
echo "4. Para ver la API:"
echo "   - Health: https://tu-dominio/api/v1/health"
echo "   - Docs: https://tu-dominio/docs"
echo "   - WebSocket: wss://tu-dominio/ws/cliente_123"
echo ""
echo "========================================"
echo "¡Despliegue en AWS configurado! 🎉"
echo "========================================"
