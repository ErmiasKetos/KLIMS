import { NextResponse } from 'next/server'
import prisma from '../../../lib/db'

export async function GET() {
  const inventory = await prisma.inventory.findMany()
  return NextResponse.json(inventory)
}

export async function POST(request: Request) {
  const body = await request.json()
  const item = await prisma.inventory.create({
    data: body,
  })
  return NextResponse.json(item)
}

