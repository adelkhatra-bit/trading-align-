'use strict';

const fs = require('fs');
const path = require('path');

const LOG = path.join(__dirname, 'orders.log');

function logOrder(record) {
  fs.appendFileSync(LOG, JSON.stringify(record) + "\n");
  console.log("ORDER:", record);
}

function createPaperOrder(order) {
  return {
    ...order,
    status: 'filled',
    orderId: `paper-${Date.now()}`,
    timestamp: Date.now(),
    mode: 'paper'
  };
}

/**
 * ALIGN supports paper-only broker simulation.
 * Live broker execution is deliberately disabled even if the host environment
 * tries to set BROKER_MODE=live. No HTTP broker request is made from this adapter.
 */
async function placeOrder(order = {}) {
  const mode = String(process.env.BROKER_MODE || 'paper').toLowerCase();
  if (mode !== 'paper') {
    throw new Error('Live broker execution is disabled in ALIGN; only paper mode is permitted.');
  }

  const normalized = {
    symbol: order.symbol,
    direction: order.direction,
    quantity: order.quantity || order.qty || 1,
    price: order.price || 0,
    sl: order.sl || order.stopLoss || null,
    tp: order.tp || order.takeProfit || null,
    createdAt: new Date().toISOString()
  };
  const record = createPaperOrder(normalized);
  logOrder(record);
  return record;
}

module.exports = { placeOrder };
