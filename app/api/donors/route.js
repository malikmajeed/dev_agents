import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';
import { getAllDonors, createDonor } from '@/services/donorService';
import { z } from 'zod';

const JWT_SECRET = process.env.JWT_SECRET;

function verifyToken(request) {
  const authHeader = request.headers.get('authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing token');
  }
  const token = authHeader.split(' ')[1];
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (err) {
    throw new Error('Invalid token');
  }
}

const donorCreateSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
  phone: z.string().optional(),
  address: z.string().optional(),
});

export async function GET(request) {
  try {
    verifyToken(request);
    const donors = await getAllDonors();
    return NextResponse.json({ donors }, { status: 200 });
  } catch (err) {
    const status = err.message === 'Missing token' || err.message === 'Invalid token' ? 401 : 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}

export async function POST(request) {
  try {
    verifyToken(request);
    const body = await request.json();
    const parsed = donorCreateSchema.parse(body);
    const donor = await createDonor(parsed);
    return NextResponse.json({ donor }, { status: 201 });
  } catch (err) {
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: err.errors }, { status: 400 });
    }
    const status = err.message === 'Missing token' || err.message === 'Invalid token' ? 401 : 500;
    return NextResponse.json({ error: err.message }, { status });
  }
}
