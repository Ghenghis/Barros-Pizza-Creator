#!/usr/bin/env node
// Compares two PNGs and writes diff. Exit 0 if >=threshold match, 1 otherwise.
import { readFileSync, writeFileSync } from 'fs';
import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';

const [mockupPath, screenshotPath, diffPath, thresholdArg] = process.argv.slice(2);
const threshold = parseFloat(thresholdArg || '0.98');

const mockup = PNG.sync.read(readFileSync(mockupPath));
const screenshot = PNG.sync.read(readFileSync(screenshotPath));
if (mockup.width !== screenshot.width || mockup.height !== screenshot.height) {
  console.error(`Dimension mismatch: mockup ${mockup.width}x${mockup.height} vs screenshot ${screenshot.width}x${screenshot.height}`);
  process.exit(1);
}
const diff = new PNG({ width: mockup.width, height: mockup.height });
const numDiff = pixelmatch(
  mockup.data, screenshot.data, diff.data,
  mockup.width, mockup.height, { threshold: 0.1 }
);
const totalPixels = mockup.width * mockup.height;
const matchRatio = 1 - (numDiff / totalPixels);
writeFileSync(diffPath, PNG.sync.write(diff));
console.log(`Match: ${(matchRatio * 100).toFixed(2)}% (${numDiff} diff pixels of ${totalPixels})`);
process.exit(matchRatio >= threshold ? 0 : 1);
