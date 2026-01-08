// Content script that runs on HRM pages
// This script injects screen capture functionality

(function() {
  'use strict';
  
  // Get extension ID
  let extensionId = null;
  try {
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.id) {
      extensionId = chrome.runtime.id;
    }
  } catch (e) {
    console.log('Extension not available');
  }
  
  // Inject the helper script using a script file (CSP-compliant)
  // We use chrome.runtime.getURL to get the extension URL for the injected script
  function injectScript() {
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('injected.js');
    script.setAttribute('data-extension-id', extensionId || 'null');
    script.onload = function() {
      // Script loaded successfully
      this.remove();
    };
    script.onerror = function() {
      console.error('Failed to load injected script');
      this.remove();
    };
    
    // Inject into page
    if (document.head) {
      (document.head || document.documentElement).appendChild(script);
    } else if (document.documentElement) {
      document.documentElement.appendChild(script);
    } else {
      // Wait for document to be ready
      setTimeout(injectScript, 10);
    }
  }
  
  // Inject when document is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectScript);
  } else {
    injectScript();
  }
  
  if (extensionId) {
    console.log('HRM Screen Capture Extension: Content script loaded (Extension ID: ' + extensionId + ')');
  } else {
    console.log('HRM Screen Capture Extension: Content script loaded (Extension not detected)');
  }
})();

