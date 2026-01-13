# EventBridge Schedule Setup - Detailed Steps

## Step 1: Specify Schedule Details

### Schedule Name and Description
- **Schedule name:** `price-check-every-12-hours`
- **Description (optional):** `Checks Amazon product prices every 12 hours and sends notifications`
- **Schedule group:** Leave as "default"

### Schedule Pattern
**Choose:** `Recurring schedule`

**Schedule Type Options:**
1. **Rate-based schedule** ← **SELECT THIS**
2. Cron-based schedule

### Rate Expression
- **Value:** `12`
- **Unit:** Select `Hours` from dropdown

Your rate expression should show: `rate(12 hours)`

### Flexible Time Window
- **Select:** `Off`
- (This ensures the schedule runs exactly every 12 hours)

### Timeframe (Optional)
- **Start date and time:** Leave blank (starts immediately)
- **End date and time:** Leave blank (runs indefinitely)

**Click "Next"**

---

## Step 2: Select Target

### Target Details
- **Templated targets:** AWS Lambda Invoke

### Invoke Section
**Lambda function:** 
- Click the dropdown
- Select: `check-prices-scheduled`

### Lambda Function Input
- **Leave blank** (our function doesn't need input)

**Click "Next"**

---

## Step 3: Settings

### Action After Schedule Completion
- **Select:** `NONE`
- (Schedule runs indefinitely)

### Retry Policy
- **Maximum age of event:** `60` seconds (default)
- **Retry attempts:** `0` (default)
- (If it fails, it will try again in 12 hours anyway)

### Encryption
- **Leave default:** AWS owned key

**Click "Next"**

---

## Step 4: Review and Create

### Review Your Configuration

**Verify these details:**
- Schedule name: `price-check-every-12-hours`
- Schedule pattern: `rate(12 hours)`
- Target: Lambda function `check-prices-scheduled`
- State: Enabled

**Click "Create schedule"**

---

## ✅ Success!

You should see a success message:
> "Schedule price-check-every-12-hours was created successfully"

### What Happens Next?

- Your Lambda function will run **every 12 hours** automatically
- First run: 12 hours from now
- To test immediately: Go to Lambda and manually test the function

---

###  Manual Test (Immediate)
1. Go to **Lambda → Functions → check-prices-scheduled**
2. Click **Test** tab
3. Create new test event:
   - Event name: `test-schedule`
   - Event JSON: `{}`
4. Click **Test**
5. Check execution results
---

### View Execution Logs
1. **CloudWatch → Log groups**
2. Find: `/aws/lambda/check-prices-scheduled`
3. View latest log streams to see:
   - How many trackers were checked
   - Which prices changed
   - Which notifications were sent

---

## Troubleshooting

### Schedule Not Triggering?
- Check if schedule is **Enabled** (EventBridge → Schedules)
- Verify Lambda function name is correct
- Check Lambda execution role has proper permissions

### Lambda Errors?
- Go to CloudWatch Logs
- Look for error messages
- Common issues:
  - Missing environment variables
  - DynamoDB permissions
  - Gmail SMTP authentication
  - SerpAPI rate limits

### No Emails Sent?
- Verify Gmail app password is correct
- Check spam folder
- Look for Lambda logs showing "Email sent successfully"
- Test Gmail SMTP separately

---

## Cost Estimate

**EventBridge Schedules:**
- Free tier: 14 million invocations/month
- Usage: 60 invocations/month (2 per day)
- **Cost: $0.00** ✅

---

## Quick Reference

**Schedule Details:**
```
Name: price-check-every-12-hours
Pattern: rate(12 hours)
Target: Lambda function (check-prices-scheduled)
Status: Enabled
```