// Background service worker for HRM Screen Capture Extension

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getScreenStream') {
    // Request desktop capture - this will show minimal dialog
    chrome.desktopCapture.chooseDesktopMedia(
      ['screen', 'window'], // Request screen or window
      sender.tab,
      (streamId) => {
        if (streamId) {
          sendResponse({ success: true, streamId: streamId });
        } else {
          sendResponse({ success: false, error: 'User cancelled or denied screen capture' });
        }
      }
    );
    return true; // Keep channel open for async response
  }
  
  if (request.action === 'checkExtension') {
    sendResponse({ installed: true });
    return true;
  }
});

// Listen for tab updates to inject content script if needed
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    // Content script will handle injection
  }
});

