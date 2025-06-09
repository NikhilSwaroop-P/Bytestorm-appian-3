#!/usr/bin/env node
/**
 * Extension Verification Script
 * This script helps verify that the modular refactoring was successful
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Browser Extension Modular Refactoring...\n');

const baseDir = __dirname;
const checkExists = (filePath) => {
  const fullPath = path.join(baseDir, filePath);
  const exists = fs.existsSync(fullPath);
  console.log(`${exists ? '✅' : '❌'} ${filePath}`);
  return exists;
};

// Check required files
console.log('📁 Checking Required Files:');
const requiredFiles = [
  'manifest.json',
  'content.js',
  'background.js',
  'checkout-automation/detector.js',
  'checkout-automation/processor.js', 
  'checkout-automation/ui-controller.js',
  'checkout-automation/loader.js',
  'checkout-automation/index.js',
  'checkout-automation/form_filling_actions.json',
  'css/overlay.css',
  'lib/checkout-automation.js'
];

let allFilesExist = true;
requiredFiles.forEach(file => {
  if (!checkExists(file)) {
    allFilesExist = false;
  }
});

console.log('\n📋 Checking File Contents:');

// Check manifest.json for web_accessible_resources
try {
  const manifest = JSON.parse(fs.readFileSync(path.join(baseDir, 'manifest.json'), 'utf8'));
  const hasWebAccessible = manifest.web_accessible_resources && 
    manifest.web_accessible_resources[0].resources.includes('checkout-automation/*.js');
  console.log(`${hasWebAccessible ? '✅' : '❌'} manifest.json has web_accessible_resources for checkout-automation`);
} catch (e) {
  console.log('❌ manifest.json parsing failed');
}

// Check if background.js references new JSON location
try {
  const background = fs.readFileSync(path.join(baseDir, 'background.js'), 'utf8');
  const hasNewPath = background.includes('checkout-automation/form_filling_actions.json');
  console.log(`${hasNewPath ? '✅' : '❌'} background.js references new JSON location`);
} catch (e) {
  console.log('❌ background.js reading failed');
}

// Check if content.js loads modules
try {
  const content = fs.readFileSync(path.join(baseDir, 'content.js'), 'utf8');
  const hasModuleLoading = content.includes('checkout-automation/loader.js');
  console.log(`${hasModuleLoading ? '✅' : '❌'} content.js loads modular architecture`);
} catch (e) {
  console.log('❌ content.js reading failed');
}

// Check if deprecated file has warnings
try {
  const deprecated = fs.readFileSync(path.join(baseDir, 'lib/checkout-automation.js'), 'utf8');
  const hasWarnings = deprecated.includes('deprecated') || deprecated.includes('DEPRECATED');
  console.log(`${hasWarnings ? '✅' : '❌'} lib/checkout-automation.js has deprecation warnings`);
} catch (e) {
  console.log('❌ lib/checkout-automation.js reading failed');
}

// Check temporary files cleanup
console.log('\n🧹 Checking Cleanup:');
const tempFiles = [
  'content.js.new',
  'content.js.new2', 
  'lib/checkout-automation.js.new'
];

let cleanupComplete = true;
tempFiles.forEach(file => {
  const exists = fs.existsSync(path.join(baseDir, file));
  console.log(`${!exists ? '✅' : '❌'} ${file} ${!exists ? 'removed' : 'still exists'}`);
  if (exists) cleanupComplete = false;
});

console.log('\n📊 Summary:');
console.log(`Files: ${allFilesExist ? '✅ All required files present' : '❌ Missing files'}`);
console.log(`Cleanup: ${cleanupComplete ? '✅ All temporary files removed' : '❌ Cleanup incomplete'}`);

const success = allFilesExist && cleanupComplete;
console.log(`\n${success ? '🎉 REFACTORING COMPLETE' : '⚠️  ISSUES DETECTED'}`);

if (success) {
  console.log(`
📋 Next Steps:
1. Load extension in Chrome/Edge developer mode
2. Test on checkout pages (including test-extension.html)
3. Verify UI overlay appears and functions correctly
4. Check browser console for any module loading errors
5. Test form filling functionality

🔗 Test page: file://${path.join(baseDir, 'test-extension.html').replace(/\\/g, '/')}
`);
}

process.exit(success ? 0 : 1);
