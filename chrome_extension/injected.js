// Injected script that runs in page context
// This file is injected via script tag to avoid CSP violations

(function() {
  'use strict';
  
  // Get extension ID from the script's data attribute
  const scriptElement = document.currentScript;
  const extensionId = scriptElement ? scriptElement.getAttribute('data-extension-id') : null;
  
  // Make extension available to page scripts
  window.hrmScreenCaptureExtension = {
    available: extensionId !== null && extensionId !== 'null',
    requestScreen: function() {
      return new Promise((resolve, reject) => {
        if (!extensionId || extensionId === 'null' || !window.chrome || !window.chrome.runtime) {
          reject(new Error('Extension not available'));
          return;
        }
        
        // Send message to background script
        window.chrome.runtime.sendMessage(
          extensionId,
          { action: 'getScreenStream' },
          (response) => {
            // Check for errors first
            if (chrome.runtime.lastError) {
              reject(new Error(chrome.runtime.lastError.message));
              return;
            }
            
            if (response && response.success && response.streamId) {
              // Get user media with the stream ID
              // For Chrome extensions, we need to use the streamId from desktopCapture API
              const constraints = {
                video: {
                  mandatory: {
                    chromeMediaSource: 'desktop',
                    chromeMediaSourceId: response.streamId
                  }
                },
                audio: false
              };
              
              // Use getUserMedia (not getDisplayMedia) for extension-based capture
              if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia(constraints)
                  .then(stream => {
                    resolve(stream);
                  })
                  .catch(err => {
                    console.error('getUserMedia failed:', err);
                    reject(err);
                  });
              } else {
                reject(new Error('getUserMedia not available'));
              }
            } else {
              reject(new Error(response?.error || 'Failed to get screen stream'));
            }
          }
        );
      });
    }
  };
  
  console.log('HRM Screen Capture Extension: Injected script loaded');
})();

