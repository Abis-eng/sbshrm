# HRM Screen Capture Chrome Extension

This Chrome extension enables automatic screen capture for the HRM system without requiring repeated user interaction.

## Installation Instructions

1. **Open Chrome Extensions Page**
   - Open Google Chrome
   - Go to `chrome://extensions/` (or click Menu → Extensions → Manage Extensions)

2. **Enable Developer Mode**
   - Toggle the "Developer mode" switch in the top-right corner

3. **Load the Extension**
   - Click "Load unpacked"
   - Navigate to the `chrome_extension` folder in this project
   - Select the folder and click "Select Folder"

4. **Grant Permissions**
   - Chrome will ask for permissions - click "Allow" or "Add extension"
   - The extension is now installed

5. **First Time Setup**
   - When you first check in, Chrome will show a screen sharing dialog
   - **IMPORTANT**: Select "Entire screen" tab (not "Chrome tab" or "Window")
   - Click "Share"
   - Chrome may remember this choice for future sessions

## How It Works

- The extension automatically detects when an employee checks in
- It requests screen capture permission (one-time dialog)
- Once granted, it captures the entire screen every 3 minutes
- Screenshots are automatically uploaded to the HRM system
- When the employee checks out, screen capture stops automatically

## Troubleshooting

**Extension not working?**
- Make sure the extension is enabled in `chrome://extensions/`
- Refresh the HRM page after installing the extension
- Check browser console (F12) for any error messages

**Still seeing the dialog?**
- This is normal for the first time or if permissions were cleared
- Select "Entire screen" and click "Share"
- Chrome should remember your choice

**Screenshots not uploading?**
- Check your internet connection
- Make sure you're logged into the HRM system
- Verify you're clocked in (check-in status)

## Notes

- The extension only works on Chrome/Edge browsers
- Firefox users will need to use the standard browser method
- The extension requires the HRM website to be in the allowed domains
- Screen capture stops automatically when you check out

## Privacy

- Screenshots are only captured when you are clocked in
- Screenshots are sent only to your company's HRM system
- You can stop screen capture at any time by checking out


