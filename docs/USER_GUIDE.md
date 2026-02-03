# 📧 Email & SMS Messenger Pro - User Guide

## Getting Started

### 1. Start the App
```bash
# Windows
py -m streamlit run app.py

# Linux/Mac
python3 -m streamlit run app.py
```
Open your browser to: **http://localhost:8501**

---

## 📤 Sending Emails

### Step 1: Configure SMTP
Go to **⚙️ SMTP Settings** tab and either:
- Use a preset (Gmail, Outlook, Yahoo, etc.)
- Add your own SMTP server

### Step 2: Set Up Credentials
1. Select your SMTP configuration
2. Enter your email address
3. Enter your **App Password** (not your regular password!)
4. ✅ Check "Save credentials" to remember them

### Step 3: Add Recipients

**Option A - Manual Entry:**
```
email1@example.com
email2@example.com, email3@example.com
```

**Option B - Upload File (CSV or TXT):**
```csv
john@example.com
jane@example.com
bob@company.com
```

**Option C - Use Saved List:**
Select from previously saved recipient lists

### Step 4: Compose Message

**Plain Text:**
Just type your message in the text area.

**HTML Email:**
1. Select "HTML" or "Both" content type
2. Upload an HTML file OR paste HTML code directly
3. Example HTML:
```html
<html>
<body>
  <h1>Hello!</h1>
  <p>This is a <b>formatted</b> email.</p>
</body>
</html>
```

### Step 5: Add Attachments (Optional)
- Click "Upload attachments"
- Select multiple files
- Supported: Any file type (PDF, images, docs, etc.)

### Step 6: Enable Tracking (Optional)
- ✅ Check "Enable read tracking"
- Adds an invisible pixel to detect when email is opened
- View results in **📈 Tracking** tab

### Step 7: Send!
Click **📤 Send Emails** and watch the progress bar.

---

## 📱 Sending SMS

SMS works via carrier email-to-SMS gateways (US carriers only).

### Step 1: Configure SMTP
Same as email - you need an SMTP server to send.

### Step 2: Add Recipients

**Manual Entry:**
1. Enter phone number: `(555) 123-4567`
2. Select carrier: `AT&T`, `T-Mobile`, `Verizon`, etc.
3. Click ➕ to add more

**Upload CSV:**
```csv
5551234567,AT&T
5559876543,T-Mobile
5552468024,Verizon
```

### Step 3: Write Message
- Maximum 160 characters
- Character counter shows remaining

### Step 4: Send
Click **📤 Send SMS**

### Supported Carriers:
| Carrier | Gateway |
|---------|---------|
| AT&T | @txt.att.net |
| T-Mobile | @tmomail.net |
| Verizon | @vtext.com |
| Sprint | @messaging.sprintpcs.com |
| US Cellular | @email.uscc.net |
| Metro PCS | @mymetropcs.com |
| Boost Mobile | @sms.myboostmobile.com |
| Cricket | @sms.cricketwireless.net |
| Google Fi | @msg.fi.google.com |

---

## ⚙️ Managing SMTP Configurations

### Add New SMTP Server:
1. Go to **⚙️ SMTP Settings**
2. Fill in:
   - **Name:** My Custom Server
   - **Server:** smtp.example.com
   - **Port:** 587 (common) or 465 (SSL)
   - **TLS:** ✅ Enable for port 587
   - **SSL:** ✅ Enable for port 465
3. Click **💾 Save Configuration**

### Import/Export Configs:
- **Export:** Download all configs as JSON
- **Import:** Upload a JSON file with configs

### Common SMTP Settings:

| Provider | Server | Port | Security |
|----------|--------|------|----------|
| Gmail | smtp.gmail.com | 587 | TLS |
| Outlook | smtp.office365.com | 587 | TLS |
| Yahoo | smtp.mail.yahoo.com | 587 | TLS |
| iCloud | smtp.mail.me.com | 587 | TLS |
| SendGrid | smtp.sendgrid.net | 587 | TLS |
| Mailgun | smtp.mailgun.org | 587 | TLS |

---

## 👥 Managing Recipient Lists

### Create a List:
1. Go to **👥 Recipients** tab
2. Enter a list name
3. Upload CSV/TXT or paste emails
4. Click **💾 Save Recipient List**

### Use a Saved List:
1. Go to **📤 Send Email** tab
2. Under recipients, select from "Use saved list"

### Export a List:
- Click **📥 Export** on any saved list
- Downloads as CSV

---

## 📊 Viewing Message History

The **📊 History** tab shows all sent messages with:
- ✅ Success / ❌ Failed status
- Recipient address
- Timestamp
- Message type (Email/SMS)

### Filters:
- **Type:** All, Email, SMS
- **Status:** All, Success, Failed

### Actions:
- **📥 Export:** Download full history as JSON
- **🗑️ Clear:** Delete all history

---

## 📈 Email Tracking

### How It Works:
1. Enable tracking when sending
2. A tiny invisible image (tracking pixel) is added to HTML emails
3. When recipient opens the email and loads images, it's logged

### Limitations:
- Only works with HTML emails
- Recipient must have images enabled
- Some email clients block tracking pixels
- Full tracking requires a tracking server

### View Tracking Data:
Go to **📈 Tracking** tab to see tracking IDs and events.

---

## 🔐 App Passwords

Most email providers require "App Passwords" instead of your regular password.

### Gmail:
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification (enable if not on)
3. App passwords → Generate
4. Select "Mail" and your device
5. Copy the 16-character password

### Outlook/Microsoft:
1. Go to [account.microsoft.com](https://account.microsoft.com)
2. Security → Advanced security options
3. App passwords → Create new
4. Copy the password

### Yahoo:
1. Go to [login.yahoo.com/account/security](https://login.yahoo.com/account/security)
2. Generate app password
3. Select "Other App"
4. Copy the password

---

## 💡 Tips & Best Practices

### For Better Deliverability:
- Use a reputable SMTP provider (SendGrid, Mailgun, Amazon SES)
- Don't send to too many recipients at once
- Include an unsubscribe link in marketing emails
- Avoid spam trigger words

### For Bulk Sending:
- Upload recipients via CSV for large lists
- Save lists for reuse
- Monitor the History tab for failures
- Check sender reputation

### For HTML Emails:
- Test with different email clients
- Keep images hosted externally
- Include plain text fallback
- Use inline CSS (not external stylesheets)

---

## 🔧 Troubleshooting

### "Authentication failed"
- Check email/password are correct
- Use App Password, not regular password
- Enable "Less secure apps" if required

### "Connection refused"
- Check SMTP server address
- Verify port number (587 or 465)
- Check firewall/antivirus settings

### "Emails going to spam"
- Use a proper "From" address
- Add SPF/DKIM records (for custom domains)
- Avoid spam words in subject/body
- Don't send too many at once

### SMS not received
- Verify phone number format (10 digits)
- Check carrier is correct
- Some carriers block gateway messages
- Try a different carrier if available

---

## 📁 Data Storage

All data is stored locally in the `config/` folder:

| File | Contains |
|------|----------|
| `smtp_configs.json` | Saved SMTP configurations |
| `recipients.json` | Saved recipient lists |
| `sent_messages.json` | Message history |
| `tracking.json` | Email tracking data |

### Backup:
Copy the entire `config/` folder to backup your data.

### Reset:
Delete the `config/` folder to start fresh.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Submit form |
| `Tab` | Navigate between fields |
| `R` | Refresh page (in browser) |

---

## Need Help?

1. Check the **ℹ️ Help** tab in the app
2. Review this guide
3. Check error messages in the terminal
4. Look at the History tab for send failures
