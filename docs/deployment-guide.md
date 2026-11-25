# Deployment guide (AWS Academy lab, console + CloudShell)

Step-by-step build of the stock tracker in the lab account. Each step ends with the screenshot it produces for the evidence checklist. Save screenshots in `evidence/` with the numbered names below.

**Before every screenshot:** hide the account ID (top-right account menu) and never show the API key value.

Time needed: about 45 minutes. Cost: about $0.01 (see the cost estimate in the [design brief](design-brief.md)).

---

## Step 0. Start the lab and open CloudShell

1. Start the lab, wait for the status to turn green, and open the AWS console.
2. Note the region in the top-right corner (for example `us-east-1`). Use this same region for every step.
3. Open **CloudShell** (terminal icon in the top bar) and run:

   ```bash
   git clone https://github.com/Nalen518/Cloud-Computing-Final-Project.git
   cd Cloud-Computing-Final-Project
   ```

📸 `01-console-region.png`: console home with the region visible.

## Step 1. DynamoDB table

1. In CloudShell run:

   ```bash
   bash scripts/create_table.sh
   ```

2. The output should show `"Status": "ACTIVE"` and `"Billing": "PAY_PER_REQUEST"`.
3. Open **DynamoDB → Tables → SmallBusinessItems** to see it in the console.

📸 `02-dynamodb-table-script.png`: the script output.
📸 `03-dynamodb-table-active.png`: the table overview showing Active, partition key `itemId`, on-demand.

## Step 2. Lambda function

1. **Lambda → Create function → Author from scratch**
   - Function name: `items-handler`
   - Runtime: the newest **Python 3.x** offered
   - Architecture: `x86_64`
   - **Change default execution role → Use an existing role → `LabRole`**
2. Click **Create function**.
3. In the **Code** tab, open `lambda_function.py`, replace its content with [src/items_handler/lambda_function.py](../src/items_handler/lambda_function.py), and click **Deploy**.
   The handler setting must stay `lambda_function.lambda_handler`.
4. **Configuration → Environment variables → Edit → Add**: key `TABLE_NAME`, value `SmallBusinessItems`. Save.
5. **Function test:** in the **Test** tab, create an event named `create-item` with this JSON and click **Test**:

   ```json
   {
     "httpMethod": "POST",
     "resource": "/items",
     "body": "{\"name\": \"Test item\", \"quantity\": 1, \"unit\": \"pcs\", \"reorderLevel\": 0}"
   }
   ```

   Expected: `"statusCode": 201` with the new item in `body`. This also proves LabRole can write to the table.

📸 `04-lambda-labrole.png`: the create page with `LabRole` selected (confirms the IAM assumption in section 6 of the brief).
📸 `05-lambda-config.png`: Configuration tab showing the role and `TABLE_NAME`.
📸 `06-lambda-test-201.png`: the test result with status 201.

## Step 3. API Gateway REST API

1. **API Gateway → Create API → REST API → Build**
   - New API, name `small-business-stock-tracker-api`, endpoint type **Regional**.
2. **Create resource** under `/`: resource name `items` → path `/items`.
3. Select `/items` → **Create resource**: resource name `{itemId}` → path `/items/{itemId}`.
4. Create the four methods. For **each** one:
   - Integration type: **Lambda function**
   - **Lambda proxy integration: ON**
   - Lambda function: `items-handler` (same region)
   - **Method request settings → API key required: ON**

   | Resource | Method |
   | --- | --- |
   | `/items` | `POST` |
   | `/items/{itemId}` | `GET` |
   | `/items/{itemId}` | `PUT` |
   | `/items/{itemId}` | `DELETE` |

   When the console asks to give API Gateway permission to invoke the function, accept.
5. **Deploy API → New stage → `dev`**. Copy the **Invoke URL** from the stage page.

📸 `07-api-resources.png`: Resources tree showing `/items` and `/items/{itemId}` with all four methods.
📸 `08-api-stage-url.png`: the `dev` stage with the invoke URL.

## Step 4. API key and usage plan (throttling)

1. **API Gateway → Usage plans → Create usage plan**
   - Name `stock-tracker-plan`
   - Throttling: rate `10` requests/second, burst `5`
   - Quota: `1000` requests per day
2. Open the plan → **Associated stages → Add API stage**: API `small-business-stock-tracker-api`, stage `dev`.
3. **Associated API keys → Add API key → Create and add new key**: name `stock-tracker-key`, auto-generate.
4. Go to **API keys → stock-tracker-key → Show** and copy the value (keep it private).
5. If you changed "API key required" after the first deploy, **Deploy API** to `dev` again.

📸 `09-usage-plan.png`: the usage plan with throttling, the `dev` stage, and the key listed (value hidden).

## Step 5. Run the API tests

In CloudShell (inside the repo folder):

```bash
export API_URL="<invoke URL from step 3>"
export API_KEY="<key value from step 4>"
bash scripts/test_api.sh
```

Expected last line: `Result: 7 passed, 0 failed`. The output is saved to `evidence/curl_outputs_<time>.txt` with the key masked.

To get the file onto your laptop: CloudShell **Actions → Download file**, path `Cloud-Computing-Final-Project/evidence/<file name>`. Put it in your local `evidence/` folder.

📸 `10-api-tests-pass.png`: the CloudShell output with all 7 PASS lines.

## Step 6. CloudWatch Logs

1. **CloudWatch → Log groups → `/aws/lambda/items-handler`**.
2. Open the newest log stream. You should see `START`, `END` and `REPORT` lines for each request.

📸 `11-cloudwatch-logs.png`: one request's log lines.

## Step 7. Commit the evidence (on your laptop)

```powershell
git add evidence
git commit -m "docs: add AWS evidence"
git push
```

Before committing, open each screenshot once more and check the account ID and the API key are not visible.

---

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `{"message":"Missing Authentication Token"}` | Wrong path or method, or the API was not deployed. Check the URL ends in `/dev` and deploy again. |
| `403 Forbidden` even with the key | The key is not in the usage plan, the plan is not attached to the `dev` stage, or the API was not redeployed after turning on "API key required". |
| Request without a key returns `200`, not `403` | "API key required" is off on that method. Turn it on and deploy again. |
| `500 {"message":"internal error"}` | Open the CloudWatch log: `AccessDenied` means LabRole cannot reach the table; `KeyError: 'TABLE_NAME'` means the environment variable is missing. |
| `502 Bad Gateway` | Lambda proxy integration is off, or the handler setting is not `lambda_function.lambda_handler`. |
| LabRole is not in the role list | The lab does not allow it; note this in the brief's IAM section and use the role the lab provides. |

## Cleanup after grading

Delete, in this order: the usage plan and API key (a stage still in a usage plan can block deleting the API), the API, the `items-handler` function, the `/aws/lambda/items-handler` log group, and the `SmallBusinessItems` table. Then end the lab session.
