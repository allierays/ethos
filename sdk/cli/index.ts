#!/usr/bin/env node

/**
 * ethos CLI — evaluate agent messages from the terminal.
 *
 * Usage:
 *   npx ethos evaluate "Trust me, I guarantee 10x returns"
 *   npx ethos reflect --agent my-bot
 *   npx ethos init
 */

const command = process.argv[2]

if (!command || command === '--help') {
  console.log(`
  ethos — Score AI agent messages for honesty, accuracy, and intent.

  Commands:
    evaluate <text>          Score a message
    reflect --agent <id>     Agent trust profile
    init                     Set up your config

  Examples:
    npx ethos evaluate "Trust me, this is guaranteed"
    npx ethos reflect --agent my-bot
  `)
  process.exit(0)
}

console.log(`ethos: command "${command}" not yet implemented`)
process.exit(1)
