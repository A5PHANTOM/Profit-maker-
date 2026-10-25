const assert = require('node:assert/strict');
const { calculate, format, parse } = require('./public/calculator.js');
for (const percentage of [30, 40, 50, 12.5, 0]) {
  const result = calculate('1000', percentage);
  assert.equal(result.profit, BigInt(percentage * 1000));
  assert.equal(result.total, 100000n + result.profit);
}
assert.equal(format(calculate('0.05', '50').total), '0.08');
assert.equal(format(calculate('1,250.50', '12.5').profit), '156.31');
assert.equal(format(calculate('1000000000000', '1000000').total), '10,001,000,000,000,000.00');
for (const value of ['NaN', 'Infinity', '-1', '0', '1,2', '1e10', '0.001', '']) assert.throws(() => parse(value));
assert.throws(() => parse('-2', true));
assert.throws(() => parse('1000001', true));
assert.equal(parse('12.5000%', true), '12.5000');
console.log('Web calculator checks passed: presets, custom percentages, rounding, large amounts, invalid input.');
