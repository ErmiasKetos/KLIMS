import { NextResponse } from 'next/server'
import prisma from '../../../lib/db'

export async function GET() {
  const equipment = await prisma.equipment.findMany()
  return NextResponse.json(equipment)
}

export async function POST(request: Request) {
  const body = await request.json()
  const item = await prisma.equipment.create({
    data: body,
  })
  return NextResponse.json(item)
}

