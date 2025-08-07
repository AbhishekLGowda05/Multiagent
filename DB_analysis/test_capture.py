#!/usr/bin/env python3

from manager.agent import capture_analytics_after_response, LAST_ANALYTICS_RESULT, smart_send_email

# Test the capture function with sample financial data (like what you got)
financial_response = """Here's a summary of your financials:

Top Expense Ledgers:

HDFC BANK: $157,645,223.40
ABM TELE MOBILES INDIA Pvt Ltd: $150,211,125.74
GST Purchases @ 18%: $129,107,473.21
BUDHAL CELL WORLD BCW: $57,960,678.00
SRI SAI MOBILES GALARY: $30,293,773.00

Top Income Ledgers:

HDFC BANK: $159,553,857.94
ABM TELE MOBILES INDIA Pvt Ltd: $152,640,461.00
GST Sales @ 18%: $137,963,955.46
BUDHAL CELL WORLD BCW: $58,174,231.00
SRI SAI MOBILES GALARY: $29,838,207.00

Total Credit: $758,886,625.31 
Total Debit: $758,886,625.31"""

print('Testing analytics capture with financial data...')
print('='*60)

# Simulate what should happen after financial agent responds
capture_result = capture_analytics_after_response('get me the financial summary', financial_response)

print(f'\nCapture completed. LAST_ANALYTICS_RESULT length: {len(LAST_ANALYTICS_RESULT)}')
print(f'LAST_ANALYTICS_RESULT preview: {LAST_ANALYTICS_RESULT[:300]}...')

# Now test email function
print('\n' + '='*60)
print('Testing email function with captured data...')

email_result = smart_send_email('send this mail to abhisheklgowda05@gmail.com')
print(f'Email result status: {email_result["status"]}')
print(f'Email result message: {email_result["message"]}')

if email_result["status"] == "completed":
    print('\n✅ SUCCESS: Email flow now works correctly!')
    print('✅ Analytics data was captured and used for email')
else:
    print('\n❌ ISSUE: Email flow still has problems')
    print(f'❌ Details: {email_result}')
