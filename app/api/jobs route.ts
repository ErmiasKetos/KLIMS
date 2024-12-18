import { NextResponse } from 'next/server'
import prisma from '../../../lib/db'

export async function GET() {
  const jobs = await prisma.job.findMany()
  return NextResponse.json(jobs)
}

export async function POST(request: Request) {
  const body = await request.json()
  const job = await prisma.job.create({
    data: body,
  })
  return NextResponse.json(job)
}

