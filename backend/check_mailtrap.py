import urllib.request, json
req = urllib.request.Request(
    'https://mailtrap.io/api/accounts/2783302/inboxes/4775033/messages',
    headers={'Api-Token': '7cdaec8c6b7f8f22a1c348bfe84b41bf'}
)
resp = urllib.request.urlopen(req, timeout=15)
msgs = json.loads(resp.read())
print(f'Total emails in Mailtrap: {len(msgs)}')
for m in msgs:
    print(f'  To: {m.get("to_email")} | Subj: {m.get("subject")[:60]} | Attachments: {m.get("attachments_count", 0)}')
