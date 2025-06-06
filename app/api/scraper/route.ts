import { NextResponse } from 'next/server';
import { spawn } from 'child_process';

export async function POST() {
  return new Promise((resolve) => {
    const process = spawn('python', ['scripts/scrape_news_enhanced.py']);
    let output = '';
    let error = '';

    process.stdout.on('data', (data) => {
      output += data.toString();
    });
    process.stderr.on('data', (data) => {
      error += data.toString();
    });
    process.on('close', (code) => {
      if (code === 0) {
        resolve(NextResponse.json({ status: 'success', output }));
      } else {
        resolve(NextResponse.json({ status: 'error', error, code }));
      }
    });
  });
}

export async function GET() {
  // Optionally, return scraping status or last summary
  return NextResponse.json({ status: 'ready' });
}

