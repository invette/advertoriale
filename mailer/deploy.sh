#!/usr/bin/env bash
# Synthagen Mailer: instalacja / aktualizacja panelu (uruchamiac w AWS CloudShell, region eu-north-1).
# Mozna odpalac wielokrotnie: niczego nie kasuje, tylko tworzy brakujace elementy i wgrywa nowy kod.
set -euo pipefail
REGION=eu-north-1
FN=synthagen-mailer
ROLE=synthagen-mailer-role
DIR=$(cd "$(dirname "$0")" && pwd)
DATA=${DATA:-$HOME/bm}
ACC=$(aws sts get-caller-identity --query Account --output text)
BUCKET=synthagen-mailer-$ACC
TABLE=synthagen-mailer-stats
RULE=synthagen-mailer-ses
CONFIG_SET=bm-pl
TMP=$(mktemp -d)
echo "== Konto $ACC, region $REGION"

# 1. Prywatny schowek na liste i szablon
if ! aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  aws s3api create-bucket --bucket "$BUCKET" --region $REGION --create-bucket-configuration LocationConstraint=$REGION >/dev/null
  echo "== Utworzono schowek $BUCKET"
fi
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-lifecycle-configuration --bucket "$BUCKET" --lifecycle-configuration '{"Rules":[{"ID":"stare-wersje","Status":"Enabled","Filter":{"Prefix":""},"NoncurrentVersionExpiration":{"NoncurrentDays":60}}]}'

# 1b. Baza na statystyki (otwarcia, klikniecia, odbicia...)
if ! aws dynamodb describe-table --table-name $TABLE --region $REGION >/dev/null 2>&1; then
  aws dynamodb create-table --table-name $TABLE --region $REGION --billing-mode PAY_PER_REQUEST \
    --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
    --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE >/dev/null
  aws dynamodb wait table-exists --table-name $TABLE --region $REGION
  echo "== Utworzono baze statystyk $TABLE"
fi

# 2. Dane startowe (tylko jesli jeszcze ich nie ma)
if ! aws s3api head-object --bucket "$BUCKET" --key contacts.csv >/dev/null 2>&1; then
  python3 "$DIR/init_data.py" "$DATA" "$TMP/init"
  aws s3 cp "$TMP/init/contacts.csv" "s3://$BUCKET/contacts.csv" --quiet
  aws s3 cp "$TMP/init/template.json" "s3://$BUCKET/template.json" --quiet
  echo "== Wgrano liste i szablon"
fi

# 3. Uprawnienia
if ! aws iam get-role --role-name $ROLE >/dev/null 2>&1; then
  aws iam create-role --role-name $ROLE --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name $ROLE --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  echo "== Utworzono role $ROLE"
fi
cat > "$TMP/policy.json" <<EOF
{"Version":"2012-10-17","Statement":[
 {"Effect":"Allow","Action":["ses:SendEmail","ses:SendRawEmail","ses:GetAccount","ses:GetSendStatistics","ses:ListContacts","ses:GetContact","ses:GetContactList","ses:ListContactLists","ses:ListEmailIdentities","ses:ListSuppressedDestinations"],"Resource":"*"},
 {"Effect":"Allow","Action":["s3:GetObject","s3:GetObjectVersion","s3:PutObject","s3:DeleteObject"],"Resource":"arn:aws:s3:::$BUCKET/*"},
 {"Effect":"Allow","Action":["s3:ListBucket","s3:ListBucketVersions"],"Resource":"arn:aws:s3:::$BUCKET"},
 {"Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:UpdateItem","dynamodb:Query","dynamodb:BatchGetItem"],"Resource":"arn:aws:dynamodb:$REGION:$ACC:table/$TABLE"},
 {"Effect":"Allow","Action":["lambda:InvokeFunction"],"Resource":"arn:aws:lambda:$REGION:$ACC:function:$FN"},
 {"Effect":"Allow","Action":["cloudwatch:GetMetricData"],"Resource":"*"}]}
EOF
aws iam put-role-policy --role-name $ROLE --policy-name mailer --policy-document "file://$TMP/policy.json"

# 4. Haslo do panelu (zachowuje dotychczasowe)
PW=$(aws lambda get-function-configuration --function-name $FN --region $REGION --query 'Environment.Variables.PANEL_PASSWORD' --output text 2>/dev/null || true)
if [ -z "$PW" ] || [ "$PW" = "None" ]; then
  PW=$(python3 -c "import secrets;a='abcdefghjkmnpqrstuvwxyz23456789';print('-'.join(''.join(secrets.choice(a) for _ in range(5)) for _ in range(3)))")
fi
python3 - "$TMP/env.json" "$BUCKET" "$PW" "$REGION" "$TABLE" "$CONFIG_SET" <<'EOF'
import json, sys
json.dump({'Variables': {'BUCKET': sys.argv[2], 'PANEL_PASSWORD': sys.argv[3], 'SES_REGION': sys.argv[4], 'TABLE': sys.argv[5], 'CONFIG_SET': sys.argv[6], 'CONTACT_LIST': 'synthagen-pl', 'TOPIC': 'promocje'}}, open(sys.argv[1], 'w'))
EOF

# 5. Funkcja
(cd "$DIR" && zip -q -j "$TMP/mailer.zip" app.py panel.html starter.html)
if aws lambda get-function --function-name $FN --region $REGION >/dev/null 2>&1; then
  aws lambda update-function-code --function-name $FN --zip-file "fileb://$TMP/mailer.zip" --region $REGION >/dev/null
  aws lambda wait function-updated-v2 --function-name $FN --region $REGION
  aws lambda update-function-configuration --function-name $FN --timeout 900 --memory-size 512 --environment "file://$TMP/env.json" --region $REGION >/dev/null
  aws lambda wait function-updated-v2 --function-name $FN --region $REGION
  echo "== Zaktualizowano funkcje $FN"
else
  for i in $(seq 1 12); do
    if aws lambda create-function --function-name $FN --runtime python3.12 --handler app.handler \
        --role "arn:aws:iam::$ACC:role/$ROLE" --zip-file "fileb://$TMP/mailer.zip" --timeout 900 --memory-size 512 \
        --environment "file://$TMP/env.json" --region $REGION >/dev/null 2>"$TMP/err"; then break; fi
    if [ "$i" = 12 ]; then cat "$TMP/err"; exit 1; fi
    echo "   (czekam az AWS zobaczy nowa role...)"; sleep 8
  done
  aws lambda wait function-active-v2 --function-name $FN --region $REGION
  echo "== Utworzono funkcje $FN"
fi
aws lambda put-function-event-invoke-config --function-name $FN --maximum-retry-attempts 0 --maximum-event-age-in-seconds 3600 --region $REGION >/dev/null

# 6. Adres panelu
URL=$(aws lambda get-function-url-config --function-name $FN --region $REGION --query FunctionUrl --output text 2>/dev/null || true)
if [ -z "$URL" ] || [ "$URL" = "None" ]; then
  URL=$(aws lambda create-function-url-config --function-name $FN --auth-type NONE --region $REGION --query FunctionUrl --output text)
fi
aws lambda add-permission --function-name $FN --statement-id panel-url --action lambda:InvokeFunctionUrl --principal '*' --function-url-auth-type NONE --region $REGION >/dev/null 2>&1 || true
aws lambda add-permission --function-name $FN --statement-id panel-url-invoke --action lambda:InvokeFunction --principal '*' --invoked-via-function-url --region $REGION >/dev/null 2>&1 || true

# 7. Statystyki: SES -> EventBridge -> funkcja -> baza
aws events put-rule --name $RULE --region $REGION --event-pattern '{"source":["aws.ses"],"detail-type":["Email Sent","Email Delivered","Email Bounced","Email Complaint Received","Email Rejected","Email Opened","Email Clicked","Email Rendering Failed","Email Delivery Delayed","Email Subscribed"]}' >/dev/null
aws lambda add-permission --function-name $FN --statement-id ses-events --action lambda:InvokeFunction --principal events.amazonaws.com --source-arn "arn:aws:events:$REGION:$ACC:rule/$RULE" --region $REGION >/dev/null 2>&1 || true
aws events put-targets --rule $RULE --region $REGION --targets "Id=mailer,Arn=arn:aws:lambda:$REGION:$ACC:function:$FN" >/dev/null
DEST='{"Enabled":true,"MatchingEventTypes":["SEND","REJECT","BOUNCE","COMPLAINT","DELIVERY","OPEN","CLICK","RENDERING_FAILURE","DELIVERY_DELAY","SUBSCRIPTION"],"EventBridgeDestination":{"EventBusArn":"arn:aws:events:'$REGION':'$ACC':event-bus/default"}}'
if aws sesv2 get-configuration-set-event-destinations --configuration-set-name $CONFIG_SET --region $REGION --query 'EventDestinations[].Name' --output text | grep -qw eventbridge; then
  aws sesv2 update-configuration-set-event-destination --configuration-set-name $CONFIG_SET --event-destination-name eventbridge --event-destination "$DEST" --region $REGION
else
  aws sesv2 create-configuration-set-event-destination --configuration-set-name $CONFIG_SET --event-destination-name eventbridge --event-destination "$DEST" --region $REGION
fi
echo "== Statystyki podpiete (SES -> EventBridge -> $FN -> $TABLE)"
echo "   limit rownoleglych uruchomien Lambdy na koncie: $(aws lambda get-account-settings --region $REGION --query AccountLimit.ConcurrentExecutions --output text)"

mkdir -p "$DATA"
printf 'Panel: %s\nHaslo: %s\n' "$URL" "$PW" > "$DATA/panel.txt"
rm -rf "$TMP"
echo
echo "=============================================="
echo " PANEL GOTOWY"
echo " Adres: $URL"
echo " Haslo: $PW"
echo "=============================================="
